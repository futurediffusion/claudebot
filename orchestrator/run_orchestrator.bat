@echo off
REM Multi-Model Orchestrator - Ejecuta tareas con enrutamiento inteligente
REM Uso: run_orchestrator.bat "tu tarea aqui"

cd /d %~dp0
python cli.py %*