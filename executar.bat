@echo off
cd /d %~dp0
echo Iniciando Controle Financeiro V8...
python -m pip install -r requirements.txt
python -m streamlit run app.py
pause
