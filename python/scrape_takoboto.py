import csv
import json
import argparse
from bs4 import BeautifulSoup
from selenium import webdriver
from pykakasi import kakasi

def load_csv_into_list(filename):
    data_list = []
    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data_list.append(dict(row))
    return data_list


def save_list_into_csv(filename, data_list):
    field_names = data_list[0].keys()
    with open(filename, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(data_list)

parser = argparse.ArgumentParser(description='Parse a CSV file to scrape Takoboto IDs and save the results to JSON.')
parser.add_argument('file_in', help='Path to the CSV file with Takoboto IDs')
parser.add_argument('file_out', help='Path to the JSON file that will hold our scraped data')

args = parser.parse_args()

# load in our csv
filename = args.file_in
data_list = load_csv_into_list(filename)

print(f"Scraping {len(data_list)} items from {filename}")

# use these to execute javascript to get all the data
driver = webdriver.Chrome()
js_function = "showAllForms();"
url_format = "https://takoboto.jp/?w={}"

# scrape the page for each line
scraped_data = []
for row in data_list:
    if row['id'] is None or row['id'] == '':
        continue
    if row['imported'] is not None and row['imported'] != '':
        if row['imported'][0].upper() == "Y":
            continue
    
    word_data = {}
    word_data['id'] = row['id']
    url = url_format.format(word_data['id'])

    print("Loading " + word_data['id'] + " from " + url)
    
    # setup our converter
    kks = kakasi()

    # Load the webpage
    driver.get(url)
    driver.execute_script(js_function)

    # Wait for the page to load the additional information
    # You might need to adjust the wait time based on the webpage behavior
    driver.implicitly_wait(1)

    # Get the updated page content
    updated_content = driver.page_source
    soup = BeautifulSoup(updated_content, 'html.parser')

    # get the word stats
    kanji = soup.find('div', id="WordJapDiv0").text

    # flatten the list
    converted_raw = kks.convert(kanji)    
    converted = {}
    for raw in converted_raw:
        for key, value in raw.items():
            converted.setdefault(key, "")
            converted[key] += value

    word_data['kanji'] = kanji

    kana = converted['kana']
    word_data['kana'] = kana

    hiragana = converted['hira']
    word_data['hiragana'] = hiragana

    romaji = converted['hepburn']
    word_data['romaji'] = romaji

    row['kanji'] = kanji
    row['kana'] = kana
    row['hiragana'] = hiragana
    row['romaji'] = romaji

    # lets grab all translations
    definitions = []
    translations_element = soup.find('div', string="English")
    if translations_element is not None:
        translation = translations_element.next_sibling
        for child_element in translation.children:
            if child_element.name is None:
                continue  # Skip non-element children (e.g., NavigableStrings)

            if not child_element.text.strip():  # Skip empty children
                continue
            
            translation_strings = list(child_element.stripped_strings)
            conjugation_type = '\n'.join(translation_strings[:-1])
            definition_text = translation_strings[-1]

            definition = {'conjugation_type': conjugation_type,
                          'definition_text' : definition_text}
            definitions.append(definition)
    word_data['definitions'] = definitions
    row['definitions'] = definitions[0]["definition_text"]

    # Find the conjugated block
    conjugated_text_element = soup.find('div', string="Conjugated forms")

    forms = []
    if conjugated_text_element is not None:
        conjugated = conjugated_text_element.next_sibling
        for child_element in conjugated.children:
            if child_element.name is None:
                continue  # Skip non-element children (e.g., NavigableStrings)

            if not child_element.text.strip():  # Skip empty children
                continue
            
            verb = {}
            verb_form = child_element
            if 'id' in child_element.attrs:
                if child_element.attrs['id'] == "ConjugatedShowMore":
                    break
                verb_form = child_element.contents[1]
    
            form_name = verb_form.contents[1].text.strip()
            verb['form'] = form_name

            form_positive = verb_form.contents[3]

            positive_strings = list(form_positive.stripped_strings)
            form_positive_informal = positive_strings[0]
            if positive_strings[1].startswith(", "):
                form_positive_formal = positive_strings[1].lstrip(", ")
                form_positive_description = positive_strings[2] if len(positive_strings) > 2 else ""
            else:
                form_positive_formal = form_positive_informal
                form_positive_description = positive_strings[1]

            verb['positive'] = {
                "informal": form_positive_informal,
                "formal": form_positive_formal,
                "description": form_positive_description
            }
                
            form_negative_informal = ""
            form_negative_formal = ""
            form_negative_description = ""

            if len(verb_form.contents) > 5:
                form_negative = verb_form.contents[5]
                negative_strings = list(form_negative.stripped_strings)
                form_negative_informal = negative_strings[0]
                if negative_strings[1].startswith(", "):
                    form_negative_formal = negative_strings[1].lstrip(", ")
                    form_negative_description = negative_strings[2] if len(negative_strings) > 2 else ""
                else:
                    form_negative_formal = form_negative_informal
                    form_negative_description = negative_strings[1]

            verb['negative'] = {
                "informal": form_negative_informal,
                "formal": form_negative_formal,
                "description": form_negative_description
            }
            forms.append(verb)
    word_data['forms'] = forms

    scraped_data.append(word_data)

    row['imported'] = "Y"

save_list_into_csv(args.file_in, data_list)
with open(args.file_out, 'w') as file:
    json.dump(scraped_data, file, indent=4)

print(f"Scraped {len(scraped_data)} items into {args.file_out}")

# with open(args.file_out, 'w', newline='') as file:
#     writer = csv.DictWriter(file, fieldnames=data_list[0].keys())
#     writer.writeheader()
#     writer.writerows(scraped_data)

#close the browser 
driver.quit()