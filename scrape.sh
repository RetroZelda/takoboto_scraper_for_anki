#!/bin/bash

# Create the virtual environment
venv_name="japanese_builder"
python3 -m venv "$venv_name"
source "$venv_name/bin/activate"

# Install dependencies
pip install -r requirements.txt

mkdir .tmp

# scrape and upload to Anki(NOTE: Requires Anki Connect to be running)
python3 ./python/scrape_takoboto.py ./data/verbs_to_scrape.csv ./.tmp/verbs.json
python3 ./python/generate_anki.py ./.tmp/verbs.json

# Deactivate the virtual environment
deactivate
