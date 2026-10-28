@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0"
if errorlevel 1 goto folder_error

rem Respect an explicit interpreter choice, then the owner's existing environment.
if defined STEAM_POSTER_PYTHON goto explicit_python
if exist "setup\python_path.txt" goto configured_python
if exist "E:\Anaconda\envs\comp5310\python.exe" (
    set "POSTER_PYTHON=E:\Anaconda\envs\comp5310\python.exe"
    goto run_python
)
if exist "%~dp0.venv\Scripts\python.exe" (
    set "POSTER_PYTHON=%~dp0.venv\Scripts\python.exe"
    goto run_python
)
where /q python
if not errorlevel 1 (
    set "POSTER_PYTHON=python"
    goto run_python
)
where /q py
if not errorlevel 1 goto run_launcher
echo Python was not found. Extract this ZIP before running the program.
echo Install Python with Tcl/Tk, or set STEAM_POSTER_PYTHON to python.exe.
echo See README.md for examples. Demo Mode needs no Steam API key.
goto launch_error

:explicit_python
if not exist "%STEAM_POSTER_PYTHON%" (
    echo STEAM_POSTER_PYTHON does not point to an existing python.exe file.
    goto launch_error
)
set "POSTER_PYTHON=%STEAM_POSTER_PYTHON%"
goto run_python

:configured_python
set "POSTER_PYTHON="
set /p "POSTER_PYTHON=" <"setup\python_path.txt"
if not defined POSTER_PYTHON (
    echo setup\python_path.txt is empty. Enter the full path to python.exe.
    goto launch_error
)
if not exist "%POSTER_PYTHON%" (
    echo The Python path in setup\python_path.txt does not exist.
    echo Use one line with the full path to python.exe and no surrounding quotes.
    goto launch_error
)

:run_python
echo Starting Steam Gaming Career Poster...
echo Python: "%POSTER_PYTHON%"
if not exist "output" mkdir "output"
if not exist "output" goto folder_error
"%POSTER_PYTHON%" "main.py" >"output\startup.log" 2>&1
set "POSTER_EXIT_CODE=%ERRORLEVEL%"
goto check_result

:run_launcher
echo Starting Steam Gaming Career Poster with the Windows Python launcher...
if not exist "output" mkdir "output"
if not exist "output" goto folder_error
py -3 "main.py" >"output\startup.log" 2>&1
set "POSTER_EXIT_CODE=%ERRORLEVEL%"

:check_result
if "%POSTER_EXIT_CODE%"=="0" (
    popd
    exit /b 0
)
echo.
echo The program could not start. Error details:
type "output\startup.log"
echo.
echo Check README.md. The error is saved in output\startup.log.
goto launch_error

:folder_error
echo Cannot access the application folder or create its output directory.
echo Extract the ZIP into a writable folder and try again.

:launch_error
echo.
pause
popd
exit /b 1
