#!/bin/sh

echo "Starting QuickFeeds"

# Check if the secret key file exists, if not generate a new key
if [ ! -f /app/secret_key ]; then
    python -c 'import os; print(os.urandom(24).hex())' > /app/secret_key
fi

# Upgrade the database with error output
echo "Applying database migrations..."
flask db upgrade || { echo "Database migration failed!"; exit 1; }

# Debug: Check if migration was successful
echo "Database migration completed successfully"

# Run the application using the `run.py` script
exec python /app/run.py