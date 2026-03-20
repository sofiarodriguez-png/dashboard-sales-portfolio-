@echo off
REM Configura tarea programada para actualizar dashboard diariamente a las 12:30 AM

echo ========================================
echo  Configurar Actualizacion a las 12:30 AM
echo ========================================
echo.

REM Eliminar tarea anterior si existe
schtasks /delete /tn "Dashboard Sales Portfolio - Actualizacion Diaria" /f 2>nul

REM Crear nueva tarea que se ejecuta todos los días a las 12:30 AM (00:30)
schtasks /create /tn "Dashboard Sales Portfolio - Actualizacion Diaria" /tr "C:\Users\sorodriguez\dashboard-portfolio\actualizar_y_publicar.bat" /sc daily /st 00:30 /f

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
echo La tarea se ejecutara:
echo  - Todos los dias a las 12:30 AM (00:30 hs)
echo  - 30 minutos despues de que BigQuery actualice
echo  - Tu dashboard tendra datos del dia actual
echo.
echo IMPORTANTE: Tu PC debe estar encendida a las 12:30 AM
echo             (o la tarea se ejecutara cuando la enciendas)
echo.
pause
