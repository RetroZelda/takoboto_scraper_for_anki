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
python3 ./python/scrape_takoboto.py ./data/words_to_scrape.csv ./.tmp/verbs.json

if [ -f "./.tmp/verbs.json" ]; then

    # Check if the anki is running
    program_name="anki"
    if ! pgrep -x "$program_name" >/dev/null; then
        # Start the program
        echo "Starting $program_name..."
        anki >/dev/null 2>&1 &

        # Wait for 1 seconds for it to start
        sleep 1
    fi

    # Check if the program started successfully
    if pgrep -x "$program_name" >/dev/null; then
        echo "$program_name connected successfully."

        # generate the decks
        python3 ./python/generate_anki.py ./.tmp/verbs.json

        # sythesize it
        #python3 ./python/generate_voice.py .tmp "Verb Conjugation"

        rm ./.tmp/verbs.json
    else
        echo "Failed to start $program_name."
    fi
else
    echo "No new data to import."
fi

rm -d -r -f .tmp

# Deactivate the virtual environment
deactivate
echo "Done."