@echo off
call .\.venv\Scripts\activate.bat
pyinstaller --onefile --windowed --name "PhotoWatermark" --add-data "app;app" app\__main__.py
echo Packaging complete!
pause