"""
Dashboard en Tiempo Real con Streamlit
- Consulta BigQuery en vivo
- Sin necesidad de generar HTML estático
- Se actualiza automáticamente cuando recargas
"""
import streamlit as st
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard Sales Portfolio", page_icon="📊", layout="wide")

# Cache para no consultar constantemente
@st.cache_data(ttl=300)  # Cache por 5 minutos
def consultar_bigquery():
    cliente = bigquery.Client(project='meli-bi-data')

    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    query = f"""
    SELECT
      COL_PHOTO_DT AS fecha,
      EXTRACT(DAY FROM COL_PHOTO_DT) AS dia,
      SIT_SITE_ID AS pais,
      COL_CALL_CENTER_ASSIGNED AS agencia,
      COL_ASSIGNED_CRITERIA_DESC AS criterio,
      COL_ACTION_ASSIGNED_LIST_DESC AS lista,
      COUNT(CUS_CUST_ID) AS asignacion
    FROM `meli-bi-data.WHOWNER.BT_COL_SALES_PORTFOLIO_LOG`
    WHERE SIT_SITE_ID IN ('MLA', 'MLM', 'MLB')
      AND COL_PHOTO_DT >= '{fecha_inicio}'
      AND COL_PHOTO_DT <= '{fecha_fin}'
    GROUP BY fecha, dia, pais, agencia, criterio, lista
    ORDER BY fecha DESC
    """

    return cliente.query(query).to_dataframe()

# Título
st.title("📊 Dashboard Sales Portfolio - Tiempo Real")
st.caption(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Botón para refrescar
if st.button("🔄 Refrescar Datos"):
    st.cache_data.clear()
    st.rerun()

# Consultar datos
with st.spinner("Consultando BigQuery..."):
    df = consultar_bigquery()

# Clasificar productos
def clasificar_producto(criterio):
    if pd.isna(criterio):
        return 'otro'
    criterio_lower = str(criterio).lower()
    if 'mixtos' in criterio_lower:
        return 'mixtos'
    elif 'merchant' in criterio_lower:
        return 'merchant'
    elif 'consumer' in criterio_lower:
        return 'consumer'
    else:
        return 'otro'

df['producto'] = df['criterio'].apply(clasificar_producto)
df['fecha'] = pd.to_datetime(df['fecha'])

# Métricas del día más reciente
fecha_mas_reciente = df['fecha'].max()
df_hoy = df[df['fecha'] == fecha_mas_reciente]

st.subheader(f"📅 Datos del día: {fecha_mas_reciente.strftime('%Y-%m-%d')}")

# Tarjetas por país y producto
totales = df_hoy.groupby(['pais', 'producto'])['asignacion'].sum().reset_index()

cols = st.columns(4)
for idx, (_, row) in enumerate(totales.iterrows()):
    with cols[idx % 4]:
        st.metric(
            label=f"{row['pais']} - {row['producto'].upper()}",
            value=f"{int(row['asignacion']):,}"
        )

# Filtros
st.subheader("🔍 Filtros")
col1, col2, col3, col4 = st.columns(4)

with col1:
    paises = st.multiselect("País", df['pais'].unique(), default=df['pais'].unique())
with col2:
    productos = st.multiselect("Producto", df['producto'].unique(), default=df['producto'].unique())
with col3:
    agencias = st.multiselect("Agencia", sorted(df['agencia'].dropna().unique()), default=None)
with col4:
    fechas = st.multiselect("Fecha", sorted(df['fecha'].dt.strftime('%Y-%m-%d').unique(), reverse=True), default=None)

# Aplicar filtros
df_filtrado = df.copy()
df_filtrado = df_filtrado[df_filtrado['pais'].isin(paises)]
df_filtrado = df_filtrado[df_filtrado['producto'].isin(productos)]
if agencias:
    df_filtrado = df_filtrado[df_filtrado['agencia'].isin(agencias)]
if fechas:
    df_filtrado = df_filtrado[df_filtrado['fecha'].dt.strftime('%Y-%m-%d').isin(fechas)]

# Tabla interactiva
st.subheader(f"📋 Datos Filtrados ({len(df_filtrado):,} registros)")
st.dataframe(
    df_filtrado[['fecha', 'pais', 'producto', 'agencia', 'criterio', 'lista', 'asignacion']].sort_values('fecha', ascending=False),
    use_container_width=True,
    height=600
)

# Descargar CSV
csv = df_filtrado.to_csv(index=False)
st.download_button(
    label="📥 Descargar CSV",
    data=csv,
    file_name=f"dashboard_sales_portfolio_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.caption("💡 Los datos se refrescan automáticamente cada 5 minutos. Click en 'Refrescar Datos' para actualizar manualmente.")
