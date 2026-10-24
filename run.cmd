@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    set "TARGET=main.py"
) else (
    set "TARGET=%~1"
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3.12 "%TARGET%"
) else (
    python "%TARGET%"
)
