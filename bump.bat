@echo off
setlocal
REM 1) manifest + CHANGELOG entwurf  2) Pause zum Bearbeiten  3) commit + push dev
REM Nur commit+push: bump.bat finalize 1.3.0
REM GitHub-Release: dev testen, dann dev -> main mergen (Release-Workflow auf main).
REM Usage: bump.bat 1.3.1

if "%~1"=="" (
  echo Usage: bump.bat ^<version^>
  echo        bump.bat finalize ^<version^>
  echo Example: bump.bat 1.3.1
  exit /b 1
)

if /I "%~1"=="finalize" (
  if "%~2"=="" (
    echo Usage: bump.bat finalize ^<version^>
    exit /b 1
  )
  python "%~dp0scripts\bump.py" finalize %2
  exit /b %ERRORLEVEL%
)

python "%~dp0scripts\bump.py" prepare %1
if errorlevel 1 exit /b 1

echo.
echo ============================================================
echo  CHANGELOG.md jetzt bearbeiten.
echo  Wenn fertig: beliebige Taste druecken - dann commit + push dev.
echo ============================================================
pause

python "%~dp0scripts\bump.py" finalize %1
exit /b %ERRORLEVEL%
