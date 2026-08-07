@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ================================================================
echo    Atualizando Painel - Barco Hospital Sao Joao XXIII
echo ================================================================
echo.

rem --- localizar a planilha .ods automaticamente nesta pasta ---
set ODS_FILE=
set ODS_COUNT=0
for %%f in (*.ods) do (
    set /a ODS_COUNT+=1
    set ODS_FILE=%%f
)

if "%ODS_FILE%"=="" (
    echo [ERRO] Nenhum arquivo .ods foi encontrado nesta pasta.
    echo.
    echo Coloque a planilha oficial ^(ex: EXPEDICOES_BHSJXXIII_2025_2026.ods^)
    echo na mesma pasta deste arquivo .bat e execute novamente.
    echo.
    pause
    exit /b 1
)

if %ODS_COUNT% GTR 1 (
    echo [AVISO] Mais de um arquivo .ods foi encontrado nesta pasta.
    echo         Usando: %ODS_FILE%
    echo         Se nao for o arquivo certo, apague os outros .ods ou rode manualmente:
    echo         python gerar_dashboard.py "nome_da_planilha.ods"
    echo.
)

echo Planilha encontrada: %ODS_FILE%
echo.
echo Gerando o painel atualizado, aguarde...
echo ----------------------------------------------------------------
python gerar_dashboard.py "%ODS_FILE%"
set GEN_RESULT=%ERRORLEVEL%
echo ----------------------------------------------------------------
echo.

if not %GEN_RESULT%==0 (
    echo [ERRO] Nao foi possivel gerar o painel. Veja a mensagem acima.
    echo.
    echo Erros comuns:
    echo   - "ModuleNotFoundError: No module named 'pandas'"
    echo     Solucao: abra este terminal e rode
    echo       pip install pandas odfpy openpyxl
    echo     e tente novamente.
    echo   - "Arquivo nao encontrado" ou aba de ano invalida
    echo     Confira se a planilha esta na pasta certa e se as abas
    echo     tem o ano no nome ^(ex: "2025", "2026"^).
    echo.
    pause
    exit /b 1
)

echo Painel gerado com sucesso! Abrindo no navegador...
start "" "index.html"

echo.
echo Tudo pronto. Voce pode fechar esta janela.
echo.
pause
