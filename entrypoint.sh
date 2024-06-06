#!/bin/sh

# Check if the secret key file exists, if not generate a new key
if [ ! -f /app/secret_key ]; then
    python -c 'import os; print(os.urandom(24).hex())' > /app/secret_key
fi

# Upgrade the database
flask db upgrade

# Run the application using the `run.py` script
exec python /app/run.py
