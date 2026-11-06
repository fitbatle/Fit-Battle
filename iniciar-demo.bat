@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")

if not exist ".venv\Scripts\python.exe" (
  %PY% -m venv .venv || goto erro
)
".venv\Scripts\python.exe" -m pip install -q -r backend\requirements.txt || goto erro

if "%FITBATTLE_REDE%"=="1" (set "ENDERECO=0.0.0.0") else (set "ENDERECO=127.0.0.1")

set "HOST=%ENDERECO%"
set "PORT=5000"
set "ADMIN_EMAILS=helena@fitbattle.dev"
start "FitBattle API" /D "%~dp0backend" "%~dp0.venv\Scripts\python.exe" tests\servidor_dev.py
start "FitBattle frontend" /D "%~dp0frontend" "%~dp0.venv\Scripts\python.exe" -m http.server 5500 --bind %ENDERECO%

echo.
echo FitBattle demo no ar.
echo   Tela de login (este computador): http://localhost:5500/login.html
echo   API: http://localhost:5000/healthz
echo   Login de demonstracao: helena@fitbattle.dev / senhaforte123
if "%ENDERECO%"=="0.0.0.0" (
  echo   Modo rede ativo ^(FITBATTLE_REDE=1^): outro aparelho da mesma rede pode abrir
  echo     http://IP_DESTE_COMPUTADOR:5500/login.html
  echo   Use so em rede de confianca: a conta de demonstracao tem senha publica.
) else (
  echo   Para abrir de outro aparelho da rede, defina FITBATTLE_REDE=1 antes de rodar ^(use so em rede de confianca^).
)
echo Para encerrar, feche as duas janelas "FitBattle".
echo.
pause
exit /b 0

:erro
echo Nao foi possivel preparar o ambiente. Verifique se o Python 3 esta instalado.
pause
exit /b 1
