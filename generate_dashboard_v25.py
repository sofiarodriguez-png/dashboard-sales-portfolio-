"""
Dashboard V25 - Con Tarjetas, Top Agencias y Alertas
Mejoras:
- Tarjetas resumen con totales por país y producto
- Top Agencias por País y Producto
- Alertas de variación diaria (más/menos usuarios vs ayer)
"""
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import os

# Conectar a BigQuery
cliente = bigquery.Client(project='meli-bi-data')

print("[INFO] Consultando datos DIARIOS (LOG)...")

# Calcular fechas dinámicamente (últimos 30 días)
fecha_fin = datetime.now().strftime('%Y-%m-%d')
fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

# ====== QUERY 1: DATOS DIARIOS ======
query_diario = f"""
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
ORDER BY fecha DESC, pais, agencia, criterio, lista
"""

df_diario = cliente.query(query_diario).to_dataframe()
print(f"[OK] {len(df_diario)} registros diarios obtenidos")

# Clasificar producto basado en criterio
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

df_diario['producto'] = df_diario['criterio'].apply(clasificar_producto)

# Calcular variaciones
df_diario = df_diario.sort_values(['pais', 'agencia', 'criterio', 'lista', 'fecha'])
df_diario['var_dia_anterior'] = df_diario.groupby(['pais', 'agencia', 'criterio', 'lista'])['asignacion'].diff()
df_diario['dia_numero'] = df_diario['dia']
df_diario['var_mes_anterior'] = df_diario.groupby(['pais', 'agencia', 'criterio', 'lista', 'dia_numero'])['asignacion'].diff()
df_diario = df_diario.sort_values('fecha', ascending=False)

print("[INFO] Consultando datos MENSUALES (PORTFOLIO)...")

# Calcular últimos 3 meses dinámicamente
periodo_actual = int(datetime.now().strftime('%Y%m'))
periodo_anterior1 = periodo_actual - 1 if (periodo_actual % 100) > 1 else (periodo_actual // 100 - 1) * 100 + 12
periodo_anterior2 = periodo_anterior1 - 1 if (periodo_anterior1 % 100) > 1 else (periodo_anterior1 // 100 - 1) * 100 + 12

# ====== QUERY 2: DATOS MENSUALES ======
query_mensual = f"""
SELECT
  COL_MONTH_ID AS periodo,
  SIT_SITE_ID AS pais,
  COL_LAST_CALL_CENTER_ASSIGNED AS agencia,
  COL_LAST_ACTION_ASSIGNED_LIST_DESC AS lista,
  COL_ASSIGNED_CRITERIA_DESC AS criterio,
  COUNT(CUS_CUST_ID) AS asignacion
FROM `meli-bi-data.WHOWNER.BT_COL_SALES_PORTFOLIO`
WHERE COL_MONTH_ID IN ({periodo_anterior2}, {periodo_anterior1}, {periodo_actual})
  AND SIT_SITE_ID IN ('MLA','MLM','MLB')
GROUP BY periodo, pais, agencia, lista, criterio
ORDER BY periodo DESC, pais, agencia, lista, criterio
"""

df_mensual = cliente.query(query_mensual).to_dataframe()
print(f"[OK] {len(df_mensual)} registros mensuales obtenidos")

df_mensual['producto'] = df_mensual['criterio'].apply(clasificar_producto)
df_mensual = df_mensual.sort_values(['pais', 'agencia', 'criterio', 'lista', 'periodo'])
df_mensual['var_mes_anterior'] = df_mensual.groupby(['pais', 'agencia', 'criterio', 'lista'])['asignacion'].diff()

print("[INFO] Calculando métricas y alertas...")

# Convertir fecha a datetime
if not pd.api.types.is_datetime64_any_dtype(df_diario['fecha']):
    df_diario['fecha'] = pd.to_datetime(df_diario['fecha'])

# ===== CALCULAR TOTALES Y ALERTAS =====
fecha_mas_reciente = df_diario['fecha'].max()
fecha_dia_anterior = fecha_mas_reciente - timedelta(days=1)

# Totales del día más reciente por país y producto
totales_hoy = df_diario[df_diario['fecha'] == fecha_mas_reciente].groupby(['pais', 'producto'])['asignacion'].sum().reset_index()
totales_hoy.columns = ['pais', 'producto', 'total_hoy']

# Totales del día anterior
totales_ayer = df_diario[df_diario['fecha'] == fecha_dia_anterior].groupby(['pais', 'producto'])['asignacion'].sum().reset_index()
totales_ayer.columns = ['pais', 'producto', 'total_ayer']

# Merge para calcular variaciones
alertas = pd.merge(totales_hoy, totales_ayer, on=['pais', 'producto'], how='left')
alertas['variacion'] = alertas['total_hoy'] - alertas['total_ayer'].fillna(0)
alertas['variacion_pct'] = (alertas['variacion'] / alertas['total_ayer'].fillna(1)) * 100
alertas = alertas.sort_values('variacion', ascending=False)

# Top Agencias por País y Producto (mes actual)
df_mensual_actual = df_mensual[df_mensual['periodo'] == periodo_actual]
top_agencias = df_mensual_actual.groupby(['pais', 'producto', 'agencia'])['asignacion'].sum().reset_index()
top_agencias = top_agencias.sort_values(['pais', 'producto', 'asignacion'], ascending=[True, True, False])

print("[INFO] Generando HTML...")

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# Preparar listas para filtros
fechas_unicas = sorted(df_diario['fecha'].dt.strftime('%Y-%m-%d').unique(), reverse=True)
paises_unicos = sorted([p for p in df_diario['pais'].unique() if pd.notna(p)])
agencias_unicas = sorted([a for a in df_diario['agencia'].unique() if pd.notna(a)])
criterios_unicos = sorted([c for c in df_diario['criterio'].unique() if pd.notna(c)])
productos_unicos = sorted(df_diario['producto'].unique())

# ===== GENERAR HTML =====
html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Asignaciones - Sales Portfolio</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #667eea;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}
        .update-info {{
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 20px;
            text-align: center;
            color: #856404;
        }}

        /* TARJETAS DE TOTALES */
        .cards-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
        }}
        .card.consumer {{ border-left-color: #27ae60; }}
        .card.merchant {{ border-left-color: #e67e22; }}
        .card.mixtos {{ border-left-color: #9b59b6; }}
        .card-pais {{
            font-size: 0.9em;
            color: #666;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .card-producto {{
            font-size: 1.1em;
            color: #333;
            margin-bottom: 10px;
        }}
        .card-total {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}
        .card-variacion {{
            font-size: 0.9em;
            padding: 5px 10px;
            border-radius: 5px;
            display: inline-block;
        }}
        .card-variacion.positiva {{
            background: #d4edda;
            color: #155724;
        }}
        .card-variacion.negativa {{
            background: #f8d7da;
            color: #721c24;
        }}

        /* ALERTAS */
        .alertas-section {{
            background: #fff3cd;
            border-left: 5px solid #ffc107;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        .alertas-section h3 {{
            color: #856404;
            margin-bottom: 15px;
        }}
        .alerta-item {{
            background: white;
            padding: 10px 15px;
            border-radius: 5px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .alerta-item.critica {{
            border-left: 4px solid #e74c3c;
        }}
        .alerta-item.mejora {{
            border-left: 4px solid #27ae60;
        }}

        .section {{
            margin: 30px 0;
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        }}
        h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}

        /* TOP AGENCIAS */
        .top-agencias-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .top-agencia-card {{
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .top-agencia-card h4 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .agencia-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        .agencia-item:last-child {{
            border-bottom: none;
        }}
        .agencia-nombre {{
            font-weight: 500;
        }}
        .agencia-valor {{
            color: #667eea;
            font-weight: bold;
        }}

        .filters {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .filter-group {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .filter-group label {{
            display: block;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 8px;
        }}
        .filter-search {{
            width: 100%;
            padding: 8px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 0.9em;
            margin-bottom: 8px;
        }}
        .toggle-all-btn {{
            width: 100%;
            padding: 6px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.85em;
            margin-bottom: 8px;
        }}
        .toggle-all-btn:hover {{ background: #5568d3; }}
        .checkbox-group {{
            max-height: 150px;
            overflow-y: auto;
        }}
        .checkbox-group label {{
            display: block;
            font-weight: normal;
            color: #333;
            margin: 5px 0;
            cursor: pointer;
        }}
        .checkbox-group input {{ margin-right: 8px; }}
        .table-container {{
            overflow-x: auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            max-height: 700px;
            overflow-y: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e0e0e0;
            font-size: 0.9em;
        }}
        tr:hover {{ background-color: #f5f5f5; }}
        .positivo {{ color: #27ae60; font-weight: bold; }}
        .negativo {{ color: #e74c3c; font-weight: bold; }}
        .null-value {{ color: #999; font-style: italic; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Dashboard de Asignaciones - Sales Portfolio</h1>
        <p class="subtitle">Mercado Libre - Actualización Automática Diaria</p>

        <div class="update-info">
            🔄 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Datos más recientes: {fecha_mas_reciente.strftime('%Y-%m-%d')}
        </div>

        <!-- ALERTAS DE VARIACIÓN DIARIA -->
        <div class="alertas-section">
            <h3>⚠️ Alertas - Variación vs Día Anterior</h3>
"""

# Generar alertas
for _, alerta in alertas.iterrows():
    clase_alerta = 'critica' if alerta['variacion'] < 0 else 'mejora'
    signo = '+' if alerta['variacion'] > 0 else ''
    html += f"""
            <div class="alerta-item {clase_alerta}">
                <div>
                    <strong>{alerta['pais']} - {alerta['producto'].upper()}</strong>
                    <span style="margin-left: 15px; color: #666;">Hoy: {int(alerta['total_hoy']):,} | Ayer: {int(alerta['total_ayer']):,}</span>
                </div>
                <div style="font-weight: bold; font-size: 1.1em;">
                    {signo}{int(alerta['variacion']):,} ({signo}{alerta['variacion_pct']:.1f}%)
                </div>
            </div>
"""

html += """        </div>

        <!-- TARJETAS DE TOTALES -->
        <div class="cards-container">
"""

# Generar tarjetas
for _, row in totales_hoy.iterrows():
    variacion = alertas[(alertas['pais'] == row['pais']) & (alertas['producto'] == row['producto'])]['variacion'].values
    variacion_val = variacion[0] if len(variacion) > 0 else 0
    var_clase = 'positiva' if variacion_val > 0 else 'negativa'
    signo = '+' if variacion_val > 0 else ''

    html += f"""
            <div class="card {row['producto']}">
                <div class="card-pais">{row['pais']}</div>
                <div class="card-producto">{row['producto'].upper()}</div>
                <div class="card-total">{int(row['total_hoy']):,}</div>
                <div class="card-variacion {var_clase}">
                    {signo}{int(variacion_val):,} vs ayer
                </div>
            </div>
"""

html += """        </div>

        <!-- TOP AGENCIAS POR PAÍS Y PRODUCTO -->
        <div class="section">
            <h2>🏆 Top Agencias por País y Producto (Mes Actual: {periodo_str})</h2>
            <div class="top-agencias-grid">
""".replace('{periodo_str}', str(periodo_actual))

# Generar top agencias por cada combinación país-producto
for pais in ['MLA', 'MLM', 'MLB']:
    for producto in ['consumer', 'merchant']:
        top_data = top_agencias[(top_agencias['pais'] == pais) & (top_agencias['producto'] == producto)].head(5)
        if len(top_data) > 0:
            html += f"""
                <div class="top-agencia-card">
                    <h4>{pais} - {producto.upper()}</h4>
"""
            for _, ag in top_data.iterrows():
                html += f"""
                    <div class="agencia-item">
                        <span class="agencia-nombre">{ag['agencia']}</span>
                        <span class="agencia-valor">{int(ag['asignacion']):,}</span>
                    </div>
"""
            html += """
                </div>
"""

html += """            </div>
        </div>

        <!-- VISTA DIARIA -->
        <div class="section">
            <h2>Vista Diaria - PORTFOLIO_LOG (Total: {len(df_diario):,} registros)</h2>
            <div class="filters">
                <div class="filter-group">
                    <label>Fecha:</label>
                    <input type="text" id="search-fecha" class="filter-search" placeholder="Buscar...">
                    <button class="toggle-all-btn" onclick="toggleAll('filter-fecha')">Toggle All</button>
                    <div class="checkbox-group" id="filter-fecha">
"""

for fecha in fechas_unicas[:15]:
    html += f'                        <label><input type="checkbox" value="{fecha}" checked> {fecha}</label>\n'

html += """                    </div>
                </div>
                <div class="filter-group">
                    <label>Pais:</label>
                    <button class="toggle-all-btn" onclick="toggleAll('filter-pais')">Toggle All</button>
                    <div class="checkbox-group" id="filter-pais">
"""

for pais in paises_unicos:
    html += f'                        <label><input type="checkbox" value="{pais}" checked> {pais}</label>\n'

html += """                    </div>
                </div>
                <div class="filter-group">
                    <label>Producto:</label>
                    <button class="toggle-all-btn" onclick="toggleAll('filter-producto')">Toggle All</button>
                    <div class="checkbox-group" id="filter-producto">
"""

for producto in productos_unicos:
    html += f'                        <label><input type="checkbox" value="{producto}" checked> {producto}</label>\n'

html += """                    </div>
                </div>
                <div class="filter-group">
                    <label>Agencia:</label>
                    <input type="text" id="search-agencia" class="filter-search" placeholder="Buscar...">
                    <button class="toggle-all-btn" onclick="toggleAll('filter-agencia')">Toggle All</button>
                    <div class="checkbox-group" id="filter-agencia">
"""

for agencia in agencias_unicas:
    agencia_display = agencia if agencia else 'null'
    agencia_value = agencia if agencia else ''
    html += f'                        <label><input type="checkbox" value="{agencia_value}" checked> {agencia_display}</label>\n'

html += """                    </div>
                </div>
                <div class="filter-group">
                    <label>Criterio:</label>
                    <input type="text" id="search-criterio" class="filter-search" placeholder="Buscar...">
                    <button class="toggle-all-btn" onclick="toggleAll('filter-criterio')">Toggle All</button>
                    <div class="checkbox-group" id="filter-criterio">
"""

for criterio in criterios_unicos:
    criterio_display = criterio if criterio else 'null'
    criterio_value = criterio if criterio else ''
    html += f'                        <label><input type="checkbox" value="{criterio_value}" checked> {criterio_display}</label>\n'

html += """                    </div>
                </div>
            </div>

            <div class="table-container">
                <table id="tabla-diaria">
                    <thead>
                        <tr>
                            <th>Fecha</th>
                            <th>Dia</th>
                            <th>Pais</th>
                            <th>Producto</th>
                            <th>Agencia</th>
                            <th>Criterio</th>
                            <th>Lista</th>
                            <th>Asignacion</th>
                            <th>Var Dia Ant</th>
                            <th>Var Mes Ant</th>
                        </tr>
                    </thead>
                    <tbody>
"""

for _, row in df_diario.iterrows():
    fecha_str = row['fecha'].strftime('%Y-%m-%d')
    agencia_display = row['agencia'] if pd.notna(row['agencia']) else '<span class="null-value">null</span>'
    criterio_display = row['criterio'] if pd.notna(row['criterio']) else '<span class="null-value">null</span>'
    lista_display = row['lista'] if pd.notna(row['lista']) else '<span class="null-value">null</span>'

    agencia_value = row['agencia'] if pd.notna(row['agencia']) else ''
    criterio_value = row['criterio'] if pd.notna(row['criterio']) else ''

    var_dia = row['var_dia_anterior']
    var_mes = row['var_mes_anterior']
    var_dia_class = 'positivo' if pd.notna(var_dia) and var_dia > 0 else ('negativo' if pd.notna(var_dia) and var_dia < 0 else '')
    var_mes_class = 'positivo' if pd.notna(var_mes) and var_mes > 0 else ('negativo' if pd.notna(var_mes) and var_mes < 0 else '')
    var_dia_str = f"{var_dia:+,.0f}" if pd.notna(var_dia) else "-"
    var_mes_str = f"{var_mes:+,.0f}" if pd.notna(var_mes) else "-"

    html += f"""                        <tr data-fecha="{fecha_str}" data-pais="{row['pais']}" data-producto="{row['producto']}" data-agencia="{agencia_value}" data-criterio="{criterio_value}">
                            <td>{fecha_str}</td>
                            <td>{int(row['dia'])}</td>
                            <td>{row['pais']}</td>
                            <td><strong>{row['producto']}</strong></td>
                            <td>{agencia_display}</td>
                            <td>{criterio_display}</td>
                            <td>{lista_display}</td>
                            <td>{int(row['asignacion']):,}</td>
                            <td class="{var_dia_class}">{var_dia_str}</td>
                            <td class="{var_mes_class}">{var_mes_str}</td>
                        </tr>
"""

html += f"""                    </tbody>
                </table>
            </div>
        </div>

        <!-- VISTA MENSUAL -->
        <div class="section">
            <h2>Vista Mensual - PORTFOLIO (Total: {len(df_mensual):,} registros)</h2>
            <div class="filters">
                <div class="filter-group">
                    <label>Periodo:</label>
                    <button class="toggle-all-btn" onclick="toggleAll('filter-periodo')">Toggle All</button>
                    <div class="checkbox-group" id="filter-periodo">
"""

periodos_unicos = sorted([p for p in df_mensual['periodo'].unique() if pd.notna(p)], reverse=True)
for periodo in periodos_unicos:
    html += f'                        <label><input type="checkbox" value="{periodo}" checked> {periodo}</label>\n'

html += """                    </div>
                </div>
                <div class="filter-group">
                    <label>Pais:</label>
                    <button class="toggle-all-btn" onclick="toggleAll('filter-pais-mensual')">Toggle All</button>
                    <div class="checkbox-group" id="filter-pais-mensual">
"""

for pais in paises_unicos:
    html += f'                        <label><input type="checkbox" value="{pais}" checked> {pais}</label>\n'

html += """                    </div>
                </div>
                <div class="filter-group">
                    <label>Producto:</label>
                    <button class="toggle-all-btn" onclick="toggleAll('filter-producto-mensual')">Toggle All</button>
                    <div class="checkbox-group" id="filter-producto-mensual">
"""

productos_mensual = sorted(df_mensual['producto'].unique())
for producto in productos_mensual:
    html += f'                        <label><input type="checkbox" value="{producto}" checked> {producto}</label>\n'

html += """                    </div>
                </div>
                <div class="filter-group">
                    <label>Agencia:</label>
                    <input type="text" id="search-agencia-mensual" class="filter-search" placeholder="Buscar...">
                    <button class="toggle-all-btn" onclick="toggleAll('filter-agencia-mensual')">Toggle All</button>
                    <div class="checkbox-group" id="filter-agencia-mensual">
"""

agencias_mensual = sorted([a for a in df_mensual['agencia'].unique() if pd.notna(a)])
for agencia in agencias_mensual:
    agencia_display = agencia if agencia else 'null'
    agencia_value = agencia if agencia else ''
    html += f'                        <label><input type="checkbox" value="{agencia_value}" checked> {agencia_display}</label>\n'

html += """                    </div>
                </div>
                <div class="filter-group">
                    <label>Criterio:</label>
                    <input type="text" id="search-criterio-mensual" class="filter-search" placeholder="Buscar...">
                    <button class="toggle-all-btn" onclick="toggleAll('filter-criterio-mensual')">Toggle All</button>
                    <div class="checkbox-group" id="filter-criterio-mensual">
"""

criterios_mensual = sorted([c for c in df_mensual['criterio'].unique() if pd.notna(c)])
for criterio in criterios_mensual:
    criterio_display = criterio if criterio else 'null'
    criterio_value = criterio if criterio else ''
    html += f'                        <label><input type="checkbox" value="{criterio_value}" checked> {criterio_display}</label>\n'

html += """                    </div>
                </div>
            </div>

            <div class="table-container">
                <table id="tabla-mensual">
                    <thead>
                        <tr>
                            <th>Periodo</th>
                            <th>Pais</th>
                            <th>Producto</th>
                            <th>Agencia</th>
                            <th>Lista</th>
                            <th>Criterio</th>
                            <th>Asignacion</th>
                            <th>Var Mes Ant</th>
                        </tr>
                    </thead>
                    <tbody>
"""

for _, row in df_mensual.iterrows():
    agencia_display = row['agencia'] if pd.notna(row['agencia']) else '<span class="null-value">null</span>'
    criterio_display = row['criterio'] if pd.notna(row['criterio']) else '<span class="null-value">null</span>'
    lista_display = row['lista'] if pd.notna(row['lista']) else '<span class="null-value">null</span>'

    agencia_value = row['agencia'] if pd.notna(row['agencia']) else ''
    criterio_value = row['criterio'] if pd.notna(row['criterio']) else ''

    var_mes = row['var_mes_anterior']
    var_mes_class = 'positivo' if pd.notna(var_mes) and var_mes > 0 else ('negativo' if pd.notna(var_mes) and var_mes < 0 else '')
    var_mes_str = f"{var_mes:+,.0f}" if pd.notna(var_mes) else "-"

    html += f"""                        <tr data-periodo="{row['periodo']}" data-pais="{row['pais']}" data-producto="{row['producto']}" data-agencia="{agencia_value}" data-criterio="{criterio_value}">
                            <td>{row['periodo']}</td>
                            <td>{row['pais']}</td>
                            <td><strong>{row['producto']}</strong></td>
                            <td>{agencia_display}</td>
                            <td>{lista_display}</td>
                            <td>{criterio_display}</td>
                            <td>{int(row['asignacion']):,}</td>
                            <td class="{var_mes_class}">{var_mes_str}</td>
                        </tr>
"""

html += """                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function toggleAll(groupId) {
            const checkboxes = document.querySelectorAll(`#${groupId} input[type="checkbox"]`);
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            checkboxes.forEach(cb => cb.checked = !allChecked);
            if (groupId.includes('mensual')) aplicarFiltrosMensual(); else aplicarFiltrosDiario();
        }

        function setupSearchFilter(searchId, checkboxGroupId) {
            const searchInput = document.getElementById(searchId);
            const checkboxGroup = document.getElementById(checkboxGroupId);
            if (searchInput && checkboxGroup) {
                searchInput.addEventListener('input', function() {
                    const searchTerm = this.value.toLowerCase();
                    const labels = checkboxGroup.querySelectorAll('label');
                    labels.forEach(label => {
                        label.style.display = label.textContent.toLowerCase().includes(searchTerm) ? 'block' : 'none';
                    });
                });
            }
        }

        setupSearchFilter('search-fecha', 'filter-fecha');
        setupSearchFilter('search-agencia', 'filter-agencia');
        setupSearchFilter('search-criterio', 'filter-criterio');
        setupSearchFilter('search-agencia-mensual', 'filter-agencia-mensual');
        setupSearchFilter('search-criterio-mensual', 'filter-criterio-mensual');

        function aplicarFiltrosDiario() {
            const fechasSeleccionadas = Array.from(document.querySelectorAll('#filter-fecha input:checked')).map(cb => cb.value);
            const paisesSeleccionados = Array.from(document.querySelectorAll('#filter-pais input:checked')).map(cb => cb.value);
            const productosSeleccionados = Array.from(document.querySelectorAll('#filter-producto input:checked')).map(cb => cb.value);
            const agenciasSeleccionadas = Array.from(document.querySelectorAll('#filter-agencia input:checked')).map(cb => cb.value);
            const criteriosSeleccionados = Array.from(document.querySelectorAll('#filter-criterio input:checked')).map(cb => cb.value);

            const filas = document.querySelectorAll('#tabla-diaria tbody tr');
            filas.forEach(fila => {
                const mostrar = fechasSeleccionadas.includes(fila.dataset.fecha) &&
                               paisesSeleccionados.includes(fila.dataset.pais) &&
                               productosSeleccionados.includes(fila.dataset.producto) &&
                               agenciasSeleccionadas.includes(fila.dataset.agencia) &&
                               criteriosSeleccionados.includes(fila.dataset.criterio);
                fila.style.display = mostrar ? '' : 'none';
            });
        }

        function aplicarFiltrosMensual() {
            const periodosSeleccionados = Array.from(document.querySelectorAll('#filter-periodo input:checked')).map(cb => cb.value);
            const paisesSeleccionados = Array.from(document.querySelectorAll('#filter-pais-mensual input:checked')).map(cb => cb.value);
            const productosSeleccionados = Array.from(document.querySelectorAll('#filter-producto-mensual input:checked')).map(cb => cb.value);
            const agenciasSeleccionadas = Array.from(document.querySelectorAll('#filter-agencia-mensual input:checked')).map(cb => cb.value);
            const criteriosSeleccionados = Array.from(document.querySelectorAll('#filter-criterio-mensual input:checked')).map(cb => cb.value);

            const filas = document.querySelectorAll('#tabla-mensual tbody tr');
            filas.forEach(fila => {
                const mostrar = periodosSeleccionados.includes(fila.dataset.periodo) &&
                               paisesSeleccionados.includes(fila.dataset.pais) &&
                               productosSeleccionados.includes(fila.dataset.producto) &&
                               agenciasSeleccionadas.includes(fila.dataset.agencia) &&
                               criteriosSeleccionados.includes(fila.dataset.criterio);
                fila.style.display = mostrar ? '' : 'none';
            });
        }

        document.querySelectorAll('#filter-fecha input, #filter-pais input, #filter-producto input, #filter-agencia input, #filter-criterio input').forEach(cb => {
            cb.addEventListener('change', aplicarFiltrosDiario);
        });

        document.querySelectorAll('#filter-periodo input, #filter-pais-mensual input, #filter-producto-mensual input, #filter-agencia-mensual input, #filter-criterio-mensual input').forEach(cb => {
            cb.addEventListener('change', aplicarFiltrosMensual);
        });

        aplicarFiltrosDiario();
        aplicarFiltrosMensual();
    </script>
</body>
</html>
"""

archivo_salida = f"dashboard_{timestamp}.html"
with open(archivo_salida, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n[OK] Dashboard V25 creado: {archivo_salida}")
print(f"\n✨ NUEVAS FUNCIONALIDADES:")
print(f"  + Tarjetas de totales por país y producto")
print(f"  + Alertas de variación diaria (vs ayer)")
print(f"  + Top 5 agencias por país y producto")
print(f"\n[INFO] Registros diarios: {len(df_diario)}")
print(f"[INFO] Registros mensuales: {len(df_mensual)}")
