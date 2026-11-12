@echo off
setlocal
if "%~1"=="" (
  echo Drag a block .json file onto this file to build it.
  pause
  exit /b 1
)
:next
if "%~1"=="" goto done
py -3 "%~dp0underground_block_builder.py" "%~f1"
shift
goto next
:done
pause
