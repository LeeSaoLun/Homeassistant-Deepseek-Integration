@echo off
setlocal
REM 1) manifest + CHANGELOG entwurf  2) Pause zum Bearbeiten  3) commit + push dev
REM GitHub-Release: dev testen, dann dev -> main mergen (Release-Workflow auf main).
REM Usage: bump.bat 1.3.1

if "%~1"=="" (
  echo Usage: bump.bat ^<version^>
  echo Example: bump.bat 1.3.1
  exit /b 1
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
