@echo off
REM Quick Start Script for Netherlands Lottery Prediction System (Windows)
REM 
REM Usage:
REM   quickstart.bat predict          - Generate tickets
REM   quickstart.bat backtest         - Run backtest
REM   quickstart.bat demo             - Quick demo (short training)

setlocal enabledelayedexpansion

cls
echo =========================================================
echo Netherlands Lottery Prediction System - Quick Start
echo =========================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Python not found. Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

REM Check CSV
if not exist "nl_lotto_xl_history.csv" (
    echo [WARNING] nl_lotto_xl_history.csv not found
    pause
    exit /b 1
)

echo [OK] Data files found
echo.

REM Parse command
set MODE=%1
if "%MODE%"=="" set MODE=demo

if "%MODE%"=="predict" (
    echo [MODE] PREDICT ^(Generate Tickets^)
    echo Command: python main.py --csv nl_lotto_xl_history.csv --game xl --predict --epochs 30
    echo.
    python main.py --csv nl_lotto_xl_history.csv --game xl --predict --epochs 30
) else if "%MODE%"=="backtest" (
    echo [MODE] BACKTEST ^(Evaluate Strategy^)
    echo Command: python main.py --csv nl_lotto_xl_history.csv --game xl --backtest --start_tail 50
    echo.
    python main.py --csv nl_lotto_xl_history.csv --game xl --backtest --start_tail 50
) else if "%MODE%"=="demo" (
    echo [MODE] DEMO ^(Quick Test, 5 epochs^)
    echo Command: python main.py --csv nl_lotto_xl_history.csv --game xl --predict --epochs 5 --batch 32
    echo.
    python main.py --csv nl_lotto_xl_history.csv --game xl --predict --epochs 5 --batch 32
) else (
    echo Usage:
    echo   quickstart.bat [MODE]
    echo.
    echo Modes:
    echo   predict   - Generate tickets for play (30 epochs)
    echo   backtest  - Run strategy backtest (50 recent draws)
    echo   demo      - Quick test (5 epochs, for verification)
    echo.
    echo Examples:
    echo   quickstart.bat predict
    echo   quickstart.bat backtest
    echo   quickstart.bat demo
    pause
    exit /b 1
)

echo.
echo =========================================================
echo [OK] Complete
echo =========================================================
pause
