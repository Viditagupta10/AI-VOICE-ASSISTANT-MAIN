@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

rem Load a local .env file if it exists. This lets you keep keys outside the repo.
if exist ".env" (
    for /f "usebackq delims== tokens=1,*" %%A in (".env") do (
        set "%%A=%%B"
    )
)

if not defined OPENAI_API_KEY set "OPENAI_API_KEY=YOUR_OPENAI_API_KEY"
if not defined NEWS_API_KEY set "NEWS_API_KEY=YOUR_NEWS_API_KEY"

if /I "%OPENAI_API_KEY%" == "YOUR_OPENAI_API_KEY" (
    echo ERROR: OPENAI_API_KEY is still set to the placeholder value.
    echo Update the .env file or set the environment variable before running Jarvis.
    exit /b 1
)

if /I "%NEWS_API_KEY%" == "YOUR_NEWS_API_KEY" (
    echo ERROR: NEWS_API_KEY is still set to the placeholder value.
    echo Update the .env file or set the environment variable before running Jarvis.
    exit /b 1
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=py -3.11"
) else (
    set "PYTHON_CMD=python"
)

if not exist ".venv" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv .venv
)

call .venv\Scripts\activate.bat

echo Activating project environment...
python --version
python -m pip install --upgrade pip setuptools wheel
python -m pip install speechrecognition pyttsx3 openai gtts requests pygame==2.5.2

echo.
echo Starting Jarvis...
python main.py
