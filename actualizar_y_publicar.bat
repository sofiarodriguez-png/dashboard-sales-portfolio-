@echo off
REM Script para actualizar y publicar dashboard automáticamente

echo ========================================
echo  Actualizando Dashboard Sales Portfolio
echo ========================================
echo.

cd /d C:\Users\sorodriguez\dashboard-portfolio

echo [1/4] Generando dashboard desde BigQuery...
python generate_dashboard.py
if errorlevel 1 (
    echo ERROR: Fallo al generar dashboard
    pause
    exit /b 1
)

echo.
echo [2/4] Copiando dashboard actualizado...
copy /Y dashboard_*.html index.html

echo.
echo [3/4] Commiteando cambios...
git add index.html
git commit -m "Dashboard actualizado %date% %time%"

echo.
echo [4/4] Publicando en GitHub...
git push

echo.
echo ========================================
echo  DASHBOARD ACTUALIZADO EXITOSAMENTE!
echo ========================================
echo.
echo URL: https://TU_USUARIO.github.io/dashboard-sales-portfolio/
echo.
pause
