#!/bin/bash

echo "Starting Interior Bazzar Django Server..."

# Activate virtual environment if it exists
if [ -f "env/bin/activate" ]; then
    source env/bin/activate
    echo "Virtual environment activated"
fi

# Install requirements if needed
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Start the server
echo "Starting server on http://127.0.0.1:8888/"
python -m uvicorn interior_bazzar.asgi:application --port 8888 --host 0.0.0.0 