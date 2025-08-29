@echo off
echo Starting Interior Bazzar Django Server...

REM Activate virtual environment if it exists
if exist "env\Scripts\activate.bat" (
    call env\Scripts\activate.bat
    echo Virtual environment activated
)

REM Install requirements if needed
if exist "requirements.txt" (
    echo Installing requirements...
    pip install -r requirements.txt
)

REM Run migrations
echo Running migrations...
python manage.py migrate

REM Start the server
echo Starting server on http://127.0.0.1:8888/
python -m uvicorn interior_bazzar.asgi:application --port 8888 --host 0.0.0.0

pause 