#!/bin/bash
#!/bin/bash

# Create the virtual environment
venv_name="japanese_builder"
python3 -m venv "$venv_name"
source "$venv_name/bin/activate"

# Install dependencies
pip install -r requirements.txt >/dev/null 2>&1

mkdir .tmp

# scrape the list
src_url="https://takoboto.jp/lists/study/n5vocab/" 
python3 ./python/scrape_takoboto_list.py "$src_url" ./.tmp/imported_from_list.csv

if [ -f "./.tmp/imported_from_list.csv" ]; then

    # scrape
    python3 ./python/scrape_takoboto.py ./.tmp/imported_from_list.csv ./.tmp/words.json

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

        python3 ./python/generate_anki.py ./.tmp/words.json
        rm ./.tmp/words.json
    else
        echo "Failed to start $program_name."
    fi
       
    rm ./.tmp/imported_from_list.csv
else
    echo "No new data to import."
fi

rm -d .tmp

# Deactivate the virtual environment
deactivate
echo "Done."