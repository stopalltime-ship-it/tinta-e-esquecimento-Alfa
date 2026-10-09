@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")
%PY% -m venv .venv
if errorlevel 1 (echo Falha: instale o Python 3 e tente novamente.&pause&exit /b 1)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (echo Falha ao instalar pygame.&pause&exit /b 1)
python preparar_assets.py
if errorlevel 1 (echo Verifique a conexao e os assets.&pause&exit /b 1)
echo Pronto. Abra main.py no VS Code e pressione F5, ou use jogar.bat.
pause