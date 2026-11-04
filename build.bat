@echo off
setlocal
cd /d "%~dp0"

echo Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo Building ApolloLander.exe ...
python -m PyInstaller --onefile --noconsole --name ApolloLander --clean main.py
if errorlevel 1 exit /b 1

echo.
echo Done: dist\ApolloLander.exe
endlocal
