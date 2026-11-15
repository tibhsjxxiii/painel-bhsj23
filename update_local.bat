@echo off
setlocal enabledelayedexpansion

echo ================================================================
echo    Atualizacao Local - Seu PC (Desenvolvimento)
echo    Barco Hospital Sao Joao XXIII
echo ================================================================
echo.

rem ---------------------------------------------------------------
rem Este script:
rem 1. Gera o index.html atualizado com a planilha local
rem 2. Faz commit e push pro GitHub
rem
rem A VM do servidor fara o git pull + update_vm.bat depois.
rem ---------------------------------------------------------------

echo [1/2] Gerando painel com planilha local...
python gerar_dashboard.py "EXPEDICOES BHSJXXIII 2025_2026.ods" -o index.html --proxy-url https://api-ia-bhsj23.alsf.workers.dev
set GEN_RESULT=%ERRORLEVEL%

if not %GEN_RESULT%==0 (
    echo.
    echo [ERRO] Falha ao gerar. Corrija a planilha/codigo local primeiro.
    pause
    exit /b 1
)

echo [2/2] Enviando para o GitHub (git push)...
git add index.html
git commit -m "Atualizacao local - %date% %time%"
git push origin main
if errorlevel 1 (
    echo [ERRO] Falha no push. Verifique internet/credenciais GitHub.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo  SUCESSO! Alteracoes enviadas pro GitHub.
echo  Agora va na VM e rode: update_vm.bat
echo ================================================================
echo.
pause