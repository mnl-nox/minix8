@echo off
set "ROOT=%~dp0"
set "BIN=%ROOT%bin\minix8-windows-x86_64.exe"
set "ROM=%ROOT%examples\hello.rom"
if not exist "%BIN%" (
  echo No Windows executable was included in this distribution.
  pause
  exit /b 1
)
if /I "%~1"=="--gui" (
  py -3 "%ROOT%source\tools\minix8_gui.py" --binary "%BIN%" --rom "%ROM%"
  if errorlevel 1 exit /b 1
  exit /b 0
)
"%BIN%" --rom "%ROM%" --monitor
