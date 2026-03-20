# 🔄 Dashboard en Tiempo Real - Opciones

## ✅ OPCIÓN 1: Actualización Automática a las 12:30 PM (RECOMENDADA)

**Más simple, usa tu dashboard actual de GitHub Pages**

### Configurar:
1. Click derecho en: `configurar_actualizacion_12_30pm.bat`
2. **Ejecutar como administrador**
3. ¡Listo! Se actualizará todos los días a las 12:30 PM

### Cómo funciona:
- BigQuery actualiza a las 12:00 PM
- El script se ejecuta a las 12:30 PM automáticamente
- Dashboard en GitHub Pages se actualiza
- Tus compañeros ven los datos frescos

### Ventajas:
- ✅ Fácil de configurar
- ✅ Usa el dashboard actual (GitHub Pages)
- ✅ No requiere servidor corriendo
- ✅ Gratis

### Desventajas:
- ❌ Solo se actualiza 1 vez al día
- ❌ Tu PC debe estar encendida a las 12:30 PM

---

## ⚡ OPCIÓN 2: Dashboard en Tiempo Real con Streamlit

**Consulta BigQuery EN VIVO cada vez que alguien accede**

### Instalar Streamlit:
```bash
pip install streamlit
```

### Ejecutar localmente (para probar):
```bash
cd C:\Users\sorodriguez\dashboard-portfolio
streamlit run streamlit_dashboard.py
```

Se abrirá en tu navegador en `http://localhost:8501`

### Publicar en Streamlit Cloud (GRATIS):
1. Ve a: https://streamlit.io/cloud
2. Conecta tu GitHub
3. Selecciona tu repositorio `dashboard-sales-portfolio-`
4. Archivo: `streamlit_dashboard.py`
5. Deploy!

Te darán una URL como: `https://tu-usuario-dashboard.streamlit.app`

### Configurar credenciales de BigQuery en Streamlit Cloud:
1. En Streamlit Cloud → Settings → Secrets
2. Pega tu `gcp-key.json` en formato TOML:
```toml
[gcp_service_account]
type = "service_account"
project_id = "meli-bi-data"
private_key_id = "..."
private_key = "..."
client_email = "..."
# ... resto del JSON
```

### Ventajas:
- ✅ Datos EN VIVO (consulta BigQuery en tiempo real)
- ✅ Se actualiza automáticamente al refrescar
- ✅ Filtros interactivos más potentes
- ✅ No necesita tu PC encendida
- ✅ Gratis en Streamlit Cloud

### Desventajas:
- ❌ Requiere configuración inicial
- ❌ Necesitas service account de GCP
- ❌ Streamlit Cloud tiene límites de uso (suficientes para uso interno)

---

## 🎯 RECOMENDACIÓN:

### Para empezar YA (hoy mismo):
**OPCIÓN 1** - Ejecuta `configurar_actualizacion_12_30pm.bat` como administrador

### Para el futuro (dashboard más profesional):
**OPCIÓN 2** - Streamlit en cloud

---

## 📊 Comparación:

| Característica | Opción 1 (GitHub Pages) | Opción 2 (Streamlit) |
|----------------|-------------------------|----------------------|
| Setup | 5 minutos | 30 minutos |
| Actualización | 1x día (12:30 PM) | Tiempo real |
| Hosting | GitHub (gratis) | Streamlit Cloud (gratis) |
| PC encendida | Sí (a las 12:30) | No |
| Credenciales GCP | No (usa las tuyas) | Sí (service account) |

---

## 🚀 ¿Qué prefieres?

**Dime cuál opción quieres y te ayudo a configurarla:**
- A: Opción 1 (actualización 12:30 PM)
- B: Opción 2 (tiempo real con Streamlit)
