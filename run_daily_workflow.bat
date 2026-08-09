@echo off
REM =============================================================
REM Daily 4AM AI Workflow — Batch Launcher (Windows fallback)
REM Double-click this OR use it as the Task Scheduler action
REM if you prefer .bat over .ps1
REM =============================================================

SET SCRIPT_DIR=%~dp0
SET LOG_DIR=%SCRIPT_DIR%logs
SET DATE_STR=%DATE:~10,4%-%DATE:~4,2%-%DATE:~7,2%
SET LOG_FILE=%LOG_DIR%\workflow_%DATE_STR%.log

IF NOT EXIST "%LOG_DIR%" MKDIR "%LOG_DIR%"

echo [%TIME%] Starting Daily AI Workflow... >> "%LOG_FILE%"

REM Run the PowerShell script (preferred)
powershell.exe -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "%SCRIPT_DIR%run_daily_workflow.ps1" >> "%LOG_FILE%" 2>&1

IF %ERRORLEVEL% EQU 0 (
    echo [%TIME%] Workflow completed successfully. >> "%LOG_FILE%"
) ELSE (
    echo [%TIME%] Workflow failed with error %ERRORLEVEL%. >> "%LOG_FILE%"
)
