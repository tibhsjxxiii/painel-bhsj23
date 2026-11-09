
@echo off
cd /d C:\xampp\htdocs\painel-bhsj23

git add .
git commit -m "Atualização automática"
git push origin main

pause






python gerar_dashboard.py EXPEDICOES_BHSJXXIII_2025_2026.ods

