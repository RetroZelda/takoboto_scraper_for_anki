import json
import requests
import argparse
from pykakasi import kakasi

deck_name = "Verb Conjugation"
def convert_to_ankiconnect_json(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)

    # setup our converter
    kks = kakasi()

    ankiconnect_json = {'decks': [], 'cards': []}

    for item in data:
        word_id = item['id']
        dict_deck = deck_name + "::00) Dictionary Forms"
        card = {
            "deckName": dict_deck,
            "modelName": "jp.takoboto",
            "fields": {
                "Japanese": item['kanji'],
                "Reading": item['hiragana'],
                "Meaning": "Dictionary" + "<br>".join(f"{i+1}. {definition['definition_text']}" for i, definition in enumerate(item['definitions'][:4])),
                "Note": item['definitions'][0]['conjugation_type'],
                "Sentence": "",
                "SentenceMeaning": "",
                "Link": f"intent:#Intent;package=jp.takoboto;action=jp.takoboto.WORD;i.word={word_id};S.browser_fallback_url=http%3A%2F%2Ftakoboto.jp%2F%3Fw%3D{word_id};end",
            },
            "options": {
                "allowDuplicate": False
            }
        }
        ankiconnect_json['decks'].append(dict_deck)
        ankiconnect_json['cards'].append(card)

        # adda card for each form
        for index, form in enumerate(item['forms']):
            form_deck = deck_name + "::" + str(index + 1).zfill(2) + ") " + form['form']
            
            def make_card(form_data, type):
                converted_raw = kks.convert(form_data['informal'])
                
                converted = {}
                for raw in converted_raw:
                    for key, value in raw.items():
                        converted.setdefault(key, "")
                        converted[key] += value

                description = form_data['description']

                # create the card
                card = {
                    "deckName": form_deck,
                    "modelName": "jp.takoboto",
                    "fields": {
                        "Japanese": converted['orig'],
                        "Reading": converted['hira'],
                        "Meaning": type + "<br>" + form['form'] + "<br><br>" + "<br>".join(f"{i+1}. {definition['definition_text']}" for i, definition in enumerate(item['definitions'][:4])),
                        "Note": type + "<br>" + description,
                        "Sentence": "",
                        "SentenceMeaning": "",
                        "Link": f"intent:#Intent;package=jp.takoboto;action=jp.takoboto.WORD;i.word={word_id};S.browser_fallback_url=http%3A%2F%2Ftakoboto.jp%2F%3Fw%3D{word_id};end",
                    },
                    "options": {
                        "allowDuplicate": False
                    }
                }
                return card
            ankiconnect_json['decks'].append(form_deck)
            ankiconnect_json['cards'].append(make_card(form['positive'], "formal"))
            ankiconnect_json['cards'].append(make_card(form['positive'], "informal"))
            ankiconnect_json['cards'].append(make_card(form['negative'], "formal"))
            ankiconnect_json['cards'].append(make_card(form['negative'], "informal"))


    return ankiconnect_json

parser = argparse.ArgumentParser(description='Convert a JSON file and upload it to Anki.  Required Anki Connect in the Desktop App')
parser.add_argument('file_in', help='Path to the JSON file describing our cards')

args = parser.parse_args()

# create our cards
json_file = args.file_in
ankiconnect_data = convert_to_ankiconnect_json(json_file)

# create the decks
deck_set = set(ankiconnect_data['decks'])
total_decks = len(deck_set)
added_decks = 0
for index, deck in enumerate(deck_set):
    payload = {
        "action": "createDeck",
        "version": 6,
        "params": {
            "deck": deck
        }
    }
    response = requests.post("http://localhost:8765", data=json.dumps(payload))
    result = response.json()
    if result['error'] is None:
        added_decks = added_decks + 1
    print(f"\rAdding Decks: {(100 * (index + 1) / total_decks):.0f}%", end="")
print()

# add the cards
total_cards = len(ankiconnect_data['cards'])
added_cards = 0
for index, card in enumerate(ankiconnect_data['cards']):
    payload = {
        "action": "addNote",
        "version": 6,
        "params": {
            "note": card
        }
    }
    response = requests.post("http://localhost:8765", data=json.dumps(payload))
    result = response.json()
    if result['error'] is None:
        added_cards = added_cards + 1
    print(f"\rAdding Cards: {(100 * (index + 1) / total_cards):.0f}%", end="")

print()
print(f"Imported {added_decks} new decks.")
print(f"Imported {added_cards} new cards.")
print("Done.")

