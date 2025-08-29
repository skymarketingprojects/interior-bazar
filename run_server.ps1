# Simple Interior Bazzar Django Server Runner
Write-Host "Starting Interior Bazzar Django Server..." -ForegroundColor Green

# Activate virtual environment if it exists
if (Test-Path "env\Scripts\Activate.ps1") {
    & "env\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated" -ForegroundColor Blue
}

# Install requirements if needed
if (Test-Path "requirements.txt") {
    Write-Host "Installing requirements..." -ForegroundColor Blue
    pip install -r requirements.txt
}

# Run migrations
Write-Host "Running migrations..." -ForegroundColor Blue
python manage.py migrate

# Start the server
Write-Host "Starting server on http://127.0.0.1:8888/" -ForegroundColor Green
python -m uvicorn interior_bazzar.asgi:application --port 8888 --host 0.0.0.0 