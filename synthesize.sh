#!/bin/bash
#!/bin/bash



# Create the virtual environment
venv_name="japanese_builder"
python3 -m venv "$venv_name"
source "$venv_name/bin/activate"

# Install dependencies
pip install -r requirements.txt >/dev/null 2>&1

mkdir .tmp

# scrape and upload to Anki(NOTE: Requires Anki Connect to be running)
python3 ./python/generate_voice.py .tmp "Japanese - Chiaki Sensei"

rm -d -r -f .tmp

# Deactivate the virtual environment
deactivate
echo "Done."