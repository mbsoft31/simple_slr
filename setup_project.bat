@echo off
echo ==========================================
echo Simple SLR - Project Setup Script
echo ==========================================
echo.

echo [1/7] Creating directory structure...
mkdir slr\core 2>nul
mkdir slr\providers 2>nul
mkdir slr\dedup 2>nul
mkdir slr\utils 2>nul
mkdir slr\export 2>nul
mkdir slr\normalization 2>nul
mkdir slr\cli 2>nul
mkdir tests\unit\test_core 2>nul
mkdir tests\unit\test_providers 2>nul
mkdir tests\unit\test_dedup 2>nul
mkdir tests\unit\test_utils 2>nul
mkdir tests\integration 2>nul
mkdir tests\fixtures 2>nul
mkdir tests\benchmarks 2>nul
mkdir docs\getting-started 2>nul
mkdir docs\migration 2>nul
mkdir docs\user-guide 2>nul
mkdir docs\developer-guide 2>nul
mkdir docs\api-reference 2>nul
mkdir compat 2>nul
mkdir .github\workflows 2>nul
echo Done!

echo.
echo [2/7] Creating __init__.py files...
type nul > slr\__init__.py
type nul > slr\core\__init__.py
type nul > slr\providers\__init__.py
type nul > slr\dedup\__init__.py
type nul > slr\utils\__init__.py
type nul > slr\export\__init__.py
type nul > slr\normalization\__init__.py
type nul > slr\cli\__init__.py
type nul > tests\__init__.py
type nul > tests\unit\__init__.py
type nul > tests\integration\__init__.py
echo Done!

echo.
echo [3/7] Creating core module files...
type nul > slr\core\models.py
type nul > slr\utils\exceptions.py
type nul > slr\utils\logging.py
type nul > slr\utils\rate_limit.py
type nul > slr\utils\retry.py
type nul > slr\utils\config.py
type nul > tests\conftest.py
type nul > tests\fixtures\sample_data.py
echo Done!

echo.
echo [4/7] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)
echo Done!

echo.
echo [5/7] Creating virtual environment...
if exist .venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv .venv
    echo Done!
)

echo.
echo [6/7] Activating virtual environment and installing dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -e ".[dev]"
echo Done!

echo.
echo [7/7] Installing pre-commit hooks...
pre-commit install
echo Done!

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo   1. Activate virtual environment: .venv\Scripts\activate
echo   2. Start coding: slr\core\models.py
echo   3. Run tests: pytest
echo.
echo Happy coding! 🚀
echo.
pause

