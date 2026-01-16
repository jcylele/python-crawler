@echo off
echo Starting Build Process...

REM 1. Activate Conda Environment
REM Try standard activation. If it fails, absolute path might be needed.
REM Note: 'call conda activate' sometimes fails in scripts depending on env config.
REM A more robust way is to call activate.bat directly.
call activate crawler
if %errorlevel% neq 0 (
    echo Failed to activate conda environment 'crawler'.
    echo Trying fallback method...
    REM If conda is in default location, try path below, else modify to your actual Anaconda/Miniconda path
    call "C:\ProgramData\miniconda3\Scripts\activate.bat" crawler
)

REM Check if activation succeeded (optional, by checking python path)
where python
echo Environment activated.

REM 2. Run PyInstaller
echo Running PyInstaller...
pyinstaller .\web.spec --noconfirm
if %errorlevel% neq 0 (
    echo PyInstaller failed! Exiting.
    pause
    exit /b %errorlevel%
)
echo PyInstaller finished successfully.

REM 3. Call deploy script
echo Calling deploy script...
call deploy.bat

echo All tasks completed successfully!
pause
