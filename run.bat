@echo off
REM Create a virtual environment (first run), install dependencies, start the app.
REM To pick a specific Python, run:  set PYTHON=py -3.13   before this script.
cd /d "%~dp0"
if "%PYTHON%"=="" set PYTHON=python
if not exist .venv (
  %PYTHON% -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
