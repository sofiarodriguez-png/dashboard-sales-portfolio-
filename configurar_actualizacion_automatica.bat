@echo off
REM Configura tarea programada para actualizar dashboard diariamente

echo ========================================
echo  Configurar Actualizacion Automatica
echo ========================================
echo.

REM Crear tarea que se ejecuta todos los días a las 8:00 AM
schtasks /create /tn "Dashboard Sales Portfolio - Actualizacion Diaria" /tr "C:\Users\sorodriguez\dashboard-portfolio\actualizar_y_publicar.bat" /sc daily /st 08:00 /f

if errorlevel 1 (
    echo ERROR: No se pudo crear la tarea programada
    echo Ejecuta este script como Administrador
    pause
    exit /b 1
)

echo.
echo ========================================
echo  CONFIGURACION EXITOSA!
echo ========================================
echo.
echo La tarea programada se ejecutara:
echo  - Todos los dias a las 8:00 AM
echo  - Actualizara el dashboard automaticamente
echo  - Lo publicara en GitHub Pages
echo.
echo Para ver/editar la tarea:
echo  - Abre "Programador de tareas" (Task Scheduler)
echo  - Busca: "Dashboard Sales Portfolio - Actualizacion Diaria"
echo.
pause
