import requests
import json

# print the existing Takoboto->Anki deck to print the IDs that we will scrape
deck_name = "verbs"

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

# Send the request to AnkiConnect
response = requests.post(url, json=params)
data = response.json()

if "result" in data:
    note_ids = data["result"]
    print(f"Found {len(note_ids)} cards in the '{deck_name}' deck.")

    # Print each note ID
    for note_id in note_ids:        
        params = {
            "action": "notesInfo",
            "version": 6,
            "params": {
                "notes": [note_id]
            }
        }
        response = requests.post(url, json=params)
        data = response.json()

        # get teh takoboto ID
        string = data['result'][0]['fields']['Link']['value']

        start_index = string.find('i.word=') + len('i.word=')
        end_index = string.find(';', start_index)

        id = string[start_index:end_index]
        print(id)
else:
    print("An error occurred while fetching notes.")
    if "error" in data:
        print(data["error"])
