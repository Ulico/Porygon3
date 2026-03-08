@echo off
cd /d "C:\Users\adria\Documents\Porygon3\Porygon3"

echo Pulling updates...
git pull origin main

echo Activating virtual environment...
call ".venv\Scripts\activate.bat"

echo Installing dependencies...
pip install -r requirements.txt

echo Restarting bot...
pm2 restart P3

echo Deploy complete.
pause