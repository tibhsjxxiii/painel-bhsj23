@echo off
setlocal enabledelayedexpansion

echo ================================================================
echo    Atualizacao do Painel - VM do Servidor (Producao)
echo    Barco Hospital Sao Joao XXIII
echo ================================================================
echo.

rem ---------------------------------------------------------------
rem CONFIGURACAO - CAMINHO DA PASTA NA VM (SERVIDOR)
rem ---------------------------------------------------------------
set "PROJECT_DIR=C:\xampp\htdocs\painel-bhsj23"

if not exist "%PROJECT_DIR%\" (
    echo [ERRO] Pasta do projeto nao encontrada: %PROJECT_DIR%
    echo Edite este arquivo (update_vm.bat) e corrija a variavel PROJECT_DIR.
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"

echo [1/3] Baixando atualizacoes do GitHub (Git Pull)...
git pull origin main
if errorlevel 1 (
    echo [AVISO] Falha no git pull. Verifique conexao/conflitos.
    echo Tentando continuar mesmo assim...
    echo.
)

echo [2/3] Gerando painel com dados atualizados...
python gerar_dashboard.py "EXPEDICOES BHSJXXIII 2025_2026.ods" -o index.html --proxy-url https://api-ia-bhsj23.alsf.workers.dev
set GEN_RESULT=%ERRORLEVEL%

if not %GEN_RESULT%==0 (
    echo.
    echo [ERRO] Falha ao gerar o painel. Causas comuns:
    echo   - Planilha .ods nao encontrada na pasta da VM
    echo   - Python/pandas nao instalados na VM
    echo   - Erro nos dados da planilha (execute localmente pra testar antes)
    echo.
    pause
    exit /b 1
)

echo [3/3] Publicando no GitHub (Netlify atualiza automaticamente)...
git add index.html
git commit -m "Atualizacao automatica VM - %date% %time%"
git push origin main
if errorlevel 1 (
    echo [AVISO] Falha no git push. Verifique credenciais/permissoes.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo  SUCESSO! Painel atualizado e publicado.
echo  O Netlify ja esta buildando a nova versao (uns 30 seg).
echo ================================================================
echo.
pause