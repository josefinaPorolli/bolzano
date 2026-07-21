@echo off
echo Creando entorno virtual...
py -3.14 -m venv venv
echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo Instalando dependencias...
pip install -r src/requirements.txt

echo Generando ejecutable...
pyinstaller --clean --noconfirm --onefile --windowed --name Bolzonaro --icon=micon.ico --add-data "micon.ico;." --exclude-module pytest --distpath . src/GUI.py

echo Limpiando archivos temporales...
cd .
rmdir /s /q build
rmdir /s /q __pycache__
del /q Bolzonaro.spec
rmdir /s /q venv

echo Instalacion completada!
