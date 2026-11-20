@echo off
title NyayaSathi
echo Starting NyayaSathi AI Legal Helper...
if exist venv\Scripts\streamlit.exe (
    .\venv\Scripts\streamlit.exe run app.py
) else (
    echo Python virtual environment not found. Run python -m venv venv and pip install -r requirements.txt first.
    pause
) 
