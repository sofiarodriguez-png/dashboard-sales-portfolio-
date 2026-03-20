# 🚀 Instrucciones para Publicar Dashboard con Actualización Automática

## ✅ PASO 1: Crear cuenta de GitHub (si no tienes)

1. Ve a: https://github.com/signup
2. Crea tu cuenta (es gratis)
3. Verifica tu email

## ✅ PASO 2: Crear repositorio

1. Ve a: https://github.com/new
2. **Repository name:** `dashboard-sales-portfolio`
3. Marca como **Public** ✅
4. **NO** marques "Add a README file"
5. Click **Create repository**

## ✅ PASO 3: Obtener credenciales de BigQuery

Necesitas una Service Account Key de Google Cloud:

```bash
# En tu terminal:
gcloud iam service-accounts create github-actions-dashboard \
  --display-name="GitHub Actions Dashboard"

gcloud projects add-iam-policy-binding meli-bi-data \
  --member="serviceAccount:github-actions-dashboard@meli-bi-data.iam.gserviceaccount.com" \
  --role="roles/bigquery.user"

gcloud projects add-iam-policy-binding meli-bi-data \
  --member="serviceAccount:github-actions-dashboard@meli-bi-data.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud iam service-accounts keys create gcp-key.json \
  --iam-account=github-actions-dashboard@meli-bi-data.iam.gserviceaccount.com
```

Esto creará un archivo `gcp-key.json`. **Copia todo su contenido** (lo necesitarás en el paso 5).

## ✅ PASO 4: Subir código a GitHub

Abre tu terminal y ejecuta (reemplaza TU_USUARIO con tu usuario de GitHub):

```bash
cd /c/Users/sorodriguez/dashboard-portfolio
git remote add origin https://github.com/TU_USUARIO/dashboard-sales-portfolio.git
git branch -M main
git push -u origin main
```

Te pedirá usuario y password. Si tienes 2FA activado, usa un Personal Access Token en vez de password.

## ✅ PASO 5: Configurar Secret en GitHub

1. Ve a tu repositorio en GitHub
2. Click en **Settings** → **Secrets and variables** → **Actions**
3. Click en **New repository secret**
4. Name: `GCP_SA_KEY`
5. Value: Pega todo el contenido del archivo `gcp-key.json`
6. Click **Add secret**

## ✅ PASO 6: Activar GitHub Pages

1. Ve a tu repositorio → **Settings** → **Pages**
2. En "Source", selecciona: **GitHub Actions**
3. ¡Listo!

## ✅ PASO 7: Primera ejecución manual

1. Ve a tu repositorio → **Actions**
2. Click en "Actualizar Dashboard Diariamente"
3. Click en **Run workflow** → **Run workflow**
4. Espera 2-3 minutos

## 🎉 ¡LISTO!

Tu dashboard estará en:
```
https://TU_USUARIO.github.io/dashboard-sales-portfolio/
```

### 🔄 Actualización Automática

El dashboard se actualizará automáticamente **todos los días a las 8:00 AM UTC** (5:00 AM hora Argentina).

También puedes ejecutarlo manualmente desde Actions → Run workflow.

### 📧 Compartir con compañeros

Solo envíales el link:
```
https://TU_USUARIO.github.io/dashboard-sales-portfolio/
```

---

## ⚠️ Alternativa Rápida (sin GitHub Actions)

Si prefieres algo más simple sin actualización automática:

1. Ve a: https://app.netlify.com/drop
2. Arrastra el archivo `index.html`
3. Te da un link público instantáneo
4. Para actualizar: regenera el HTML y vuelve a arrastrarlo
