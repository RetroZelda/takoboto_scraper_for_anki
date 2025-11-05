from gtts import gTTS

import requests
import argparse
import base64
import json
import re


parser = argparse.ArgumentParser(description='Convert a JSON file and upload it to Anki.  Required Anki Connect in the Desktop App')
parser.add_argument('output_path', help='Path to place generated files')
parser.add_argument('target_deck', help='Anki deck to generate voices for')
args = parser.parse_args()


# print the existing Takoboto->Anki deck to print the IDs that we will scrape
deck_name = args.target_deck
#deck_name = "adjectives"

# AnkiConnect API URL
url = "http://localhost:8765"

# Request parameters
params = {
    "action": "findNotes",
    "version": 6,
    "params": {
        "query": f'deck:"{deck_name}"'
    }
}

print(f"Scanning deck \"{deck_name}\" to generate a sythesized file for each word.")

# Send the request to AnkiConnect
response = requests.post(url, json=params)
data = response.json()

if "result" in data:
    note_ids = data["result"]
    print(f"Found {len(note_ids)} cards in the '{deck_name}' deck.")

    # gather all notes without a sound
    no_sound_list = []
    for note_index, note_id in enumerate(note_ids):
                
        print(f"\rScanning Notes: {(100 * (note_index + 1) / len(note_ids)):.0f}%", end="")

        params = {
            "action": "notesInfo",
            "version": 6,
            "params": {
                "notes": [note_id]
            }
        }
        response = requests.post(url, json=params)
        data = response.json()

        data_fields = data['result'][0]['fields']

        # check if sound is used directly on a field
        kanji = ""
        used_field = ""
        if data_fields.get('kanjis'):
            kanji = data_fields['kanjis']['value']
            used_field = "kanjis"
        if data_fields.get('Japanese'):
            kanji = data_fields['Japanese']['value']
            used_field = "Japanese"

        # check for sound embedded in name
        if kanji != "" and used_field != "":
            pattern = r'\[sound:(.*?)\]'
            matches = re.findall(pattern, kanji)
            if len(matches) == 0: # nothing embedded
                # check for a sound param
                sound_value = data_fields.get('sound')
                if sound_value is None or sound_value['value'] == "":
                    no_sound_list.append(data)
            if len(matches) > 1:
                # we have more than 1 so regenerate to fix it
                data_fields[used_field]['value'] = re.sub(r'\[.*?\]', '', kanji)
                no_sound_list.append(data)

    
    print(f"\n{len(no_sound_list)}/{len(note_ids)} notes dont have sound")
    total_sounds_to_generate = len(no_sound_list)
    for index, data in enumerate(no_sound_list):
        deck_data = data['result'][0]
        data_fields = deck_data['fields']
        note_id = deck_data['noteId']

        # get the kani from our deck types
        kanji = ""
        used_field = ""
        if data_fields.get('kanjis'):
            kanji = data_fields['Reading']['value']
            used_field = "kanjis"
        if data_fields.get('Japanese'):
            kanji = data_fields['Reading']['value']
            used_field = "Japanese"

            # HACK: fill empty readings with the japanese field.  usually from slang words in takoboto
            if kanji is None or kanji == "" or kanji == '':
                kanji = data_fields['Japanese']['value']
                data_fields['Reading']['value'] = kanji
                print(f"\nFixed empty 'Reading' field for \"{kanji}\"")
        
        if kanji == "" or used_field == "":
            continue
        print(f"Generating Sound: {(100 * (index + 1) / total_sounds_to_generate):.0f}% - {note_id} - {kanji}                                       ")

        # Create gTTS object and specify the language
        tts = gTTS(text=kanji, lang='ja', slow=False)

        # Save the speech as an audio file
        audio_file = f"{args.output_path}/{note_id}.wav"
        tts.save(audio_file)

        # grab the sound from disk
        sound_data = base64.b64encode(open(audio_file, "rb").read()).decode('utf-8')
        sound_field = {
            "filename": f"{note_id}.wav", 
            "data": sound_data, 
            "fields": [used_field], 
            "deleteExisting": True
            }

        # create our note update
        updated_note = {
            "id" : note_id,
            "fields" : {},
            "audio" : sound_field,
            "tags" : []
        }

        # convert our existing fields over
        for key, value in data_fields.items():
            updated_note['fields'][key] = value['value']

        # clean the existing "used" field
        updated_note['fields'][used_field] = re.sub(r'\[.*?\]', '', updated_note['fields'][used_field])
        

        # hack because anki api broke things:
        updated_note['fields'][used_field] = updated_note['fields'][used_field] + f"[sound:{note_id}.wav]"

        # insert the sound in our deck
        payload = json.dumps({
        "action": "updateNote",
        "version": 6,
        "params": {
            "note": updated_note
            }
        })
        response = requests.post(url, data=payload)
        result = response.json()
        if result['error'] is not None:
            print(f" ERROR: {result['error'] }")

    print(f"Generated {total_sounds_to_generate} sounds.                              ")

else:
    print("An error occurred while fetching notes.")
    if "error" in data:
        print(data["error"])
