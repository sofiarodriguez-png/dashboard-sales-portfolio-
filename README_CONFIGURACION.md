# 🚀 Configuración Dashboard con Actualización Automática

## ✅ Paso 1: Crear cuenta de GitHub

1. Ve a: https://github.com/signup
2. Usa tu email: sofia.rodriguez@mercadolibre.com
3. Elige un username (ejemplo: `sofia-meli`, `srodriguez-ml`, etc.)
4. Verifica tu email

**Una vez creada, anota tu username:** ___________________

---

## ✅ Paso 2: Crear repositorio en GitHub

1. Ve a: https://github.com/new
2. **Repository name:** `dashboard-sales-portfolio`
3. Marca como **Public** ✅
4. **NO** marques "Add a README file"
5. Click **Create repository**

---

## ✅ Paso 3: Conectar tu repositorio local con GitHub

Abre Git Bash (o tu terminal) y ejecuta (reemplaza `TU_USUARIO` con tu username de GitHub):

```bash
cd /c/Users/sorodriguez/dashboard-portfolio

# Configurar tu identidad en git
git config --global user.name "TU_NOMBRE"
git config --global user.email "sofia.rodriguez@mercadolibre.com"

# Conectar con GitHub
git remote add origin https://github.com/TU_USUARIO/dashboard-sales-portfolio.git
git branch -M main
git push -u origin main
```

GitHub te pedirá autenticación:
- **Username:** tu usuario de GitHub
- **Password:**
  - Si tienes 2FA: Crea un Personal Access Token en https://github.com/settings/tokens
  - Si no: tu contraseña

---

## ✅ Paso 4: Activar GitHub Pages

1. Ve a tu repositorio en GitHub
2. Click en **Settings** (⚙️)
3. En el menú izquierdo: **Pages**
4. En "Source": Selecciona **Deploy from a branch**
5. En "Branch": Selecciona **main** y **/root**
6. Click **Save**

¡Tu dashboard estará disponible en 1-2 minutos en:
```
https://TU_USUARIO.github.io/dashboard-sales-portfolio/
```

---

## ✅ Paso 5: Configurar actualización automática diaria

**Opción A: Con Task Scheduler (Recomendado)**

1. Click derecho en `configurar_actualizacion_automatica.bat`
2. Selecciona "Ejecutar como administrador"
3. ¡Listo! Se actualizará solo todos los días a las 8 AM

**Opción B: Manual**

Simplemente ejecuta `actualizar_y_publicar.bat` cuando quieras actualizar el dashboard.

---

## 🎉 ¡LISTO!

### 📊 Tu dashboard está en:
```
https://TU_USUARIO.github.io/dashboard-sales-portfolio/
```

### 🔄 ¿Cómo funciona la actualización automática?

1. **Todos los días a las 8:00 AM:**
   - Windows ejecuta `actualizar_y_publicar.bat`
   - El script consulta BigQuery
   - Genera el HTML actualizado
   - Lo sube automáticamente a GitHub
   - GitHub Pages lo publica

2. **Tu computadora debe estar encendida a las 8 AM**
   - Si está apagada, la tarea se ejecutará cuando la enciendas
   - O puedes ejecutar manualmente `actualizar_y_publicar.bat`

### 📧 Compartir con tus compañeros

Solo envíales el link:
```
https://TU_USUARIO.github.io/dashboard-sales-portfolio/
```

---

## 🛠️ Comandos útiles

**Actualizar manualmente:**
```bash
cd C:\Users\sorodriguez\dashboard-portfolio
actualizar_y_publicar.bat
```

**Ver tareas programadas:**
```
Windows + R → taskschd.msc → Buscar "Dashboard Sales Portfolio"
```

**Probar script manualmente:**
```bash
cd C:\Users\sorodriguez\dashboard-portfolio
python generate_dashboard.py
```

---

## ⚠️ Solución de Problemas

**Error: "Permission denied"**
- Necesitas configurar tu autenticación de GitHub
- Usa GitHub CLI o Personal Access Token

**Error: "git push failed"**
- Verifica que configuraste el remote: `git remote -v`
- Re-autentica con GitHub

**Dashboard no se actualiza:**
- Verifica que la tarea programada esté activa en Task Scheduler
- Ejecuta manualmente `actualizar_y_publicar.bat` para ver si hay errores

---

## 📞 ¿Necesitas ayuda?

Avísame en qué paso estás y te ayudo a resolverlo.
