@echo off
title VISION-GOD CORE SERVER (OmniParser V2.0)
echo ========================================================
echo   INICIALIZANDO OJOS DE DIOS - SERVIDOR DE FONDO
echo ========================================================
echo.
cd /d %~dp0
echo [1/3] Activando entorno virtual...
call .\venv_vision\Scripts\activate

echo [2/3] Verificando dependencias...
echo Buscando modelos en tools\vision-god\OmniParser\weights...

echo [3/3] Lanzando Servidor FastAPI en Puerto 8000...
echo (Este proceso mantendra los modelos cargados en la VRAM)
echo.
.\venv_vision\Scripts\python.exe tools\vision-god\server.py

pause
