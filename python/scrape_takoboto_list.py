import re
import csv
import json
import argparse
import requests
from bs4 import BeautifulSoup

def save_list_into_csv(filename, data_list):
    field_names = data_list[0].keys()
    with open(filename, 'w', newline='') as file:
        for key in field_names:
            file.write(f"{key},")
        file.write("\n")
        for data in data_list:
            for key in field_names:
                file.write(f"{data[key]},")
            file.write("\n")
        

parser = argparse.ArgumentParser(description='Parse a CSV file to scrape Takoboto IDs and save the results to JSON.')
parser.add_argument('takoboto_in', help='url for the Takoboto list to import')
parser.add_argument('file_out', help='Path to the CSV file to put Takoboto IDs')

args = parser.parse_args()

# load in our csv
filename = args.file_out
base_url = args.takoboto_in

# Load the webpage
scraped_data = []

# Get the updated page content
print(f"Opening: {base_url}")
page_data = requests.get(base_url).text
soup = BeautifulSoup(page_data, 'html.parser')

# get the list stats
container = soup.find('div', class_="SearchResultMainColumn")
list_title = container.contents[1].text
#list_author = container.contents[2].text

# get our number of pages
last_page = 1
cur_page = 1
maybe_page_element = container.find('span', class_="PageLink")
if maybe_page_element is not None:
    maybe_page_element = maybe_page_element.parent
    if "Page" in maybe_page_element.text:
        last_page = int(re.findall(r'\d+$', maybe_page_element.text)[-1])

# go through each page
while True:
    print(f"Page {cur_page}");
    container = soup.find('div', id="SearchResultContent")
    for list_element in container.children:
        link = list_element.find("a", string="See more >")
        
        # extract the ID
        href = link.get('href')
        match = re.search(r'\?w=(\d+)', href)        
        if match:            
            new_id = {}
            new_id['id_in'] = match.group(1)
            new_id['id_done'] = ""
            scraped_data.append(new_id)

    if cur_page >= last_page:
        break

    # load the next page
    cur_page = cur_page + 1
    page_url = base_url + f"?page={cur_page}"
    page_data = requests.get(page_url).text
    soup = BeautifulSoup(page_data, 'html.parser')

save_list_into_csv(filename, scraped_data)

print(f"Scraped {len(scraped_data)} items into {filename}")
