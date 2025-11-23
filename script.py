import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import calendar

# Configuración simple
plt.rcParams['font.size'] = 12
sns.set_style("whitegrid")

print("="*70)
print("ANÁLISIS DE DENGUE Y CLIMA - COSTA RICA (MEJORADO)")
print("="*70)

# ============================================
# CARGAR DATOS
# ============================================

# Leer datos de dengue
print("Leyendo datos de dengue...")
df = pd.read_csv('casos_dengue.csv')
df_cr = df[df['adm_0_name'] == 'COSTA RICA'].copy()

# Separar datos anuales y semanales
df_anual = df_cr[df_cr['T_res'] == 'Year'].copy()
df_semanal = df_cr[df_cr['T_res'] == 'Week'].copy()

# Leer datos de clima (NUEVO FORMATO DIARIO)
print("Leyendo datos de clima...")
df_clima = pd.read_csv('lluvias_temperatura.csv')

# Crear fecha a partir de YEAR, MO, DY
df_clima['Date'] = pd.to_datetime(df_clima[['YEAR', 'MO', 'DY']].rename(columns={'YEAR': 'year', 'MO': 'month', 'DY': 'day'}))
df_clima['Month'] = df_clima['Date'].dt.month

print(f"\n✓ Datos de dengue: {len(df_cr)} registros")
print(f"✓ Datos de clima: {len(df_clima)} registros diarios")
print(f"  Período clima: {df_clima['YEAR'].min()} - {df_clima['YEAR'].max()}\n")

# ============================================
# GRÁFICO 1: Últimos 10 años
# ============================================
print("Generando gráfico 1: Últimos 10 años...")
fig, ax = plt.subplots(figsize=(12, 6))
nacional = df_anual[df_anual['S_res'] == 'Admin0'].groupby('Year')['dengue_total'].sum()
ultimos_10 = nacional.tail(10)
colores = ['#e74c3c' if x == ultimos_10.max() else '#3498db' for x in ultimos_10.values]
ax.bar(ultimos_10.index.astype(str), ultimos_10.values, color=colores, width=0.7)
for i, v in enumerate(ultimos_10.values):
    ax.text(i, v + 500, f'{int(v):,}', ha='center', fontweight='bold', fontsize=11)
ax.set_title('Casos de Dengue en Costa Rica - Últimos 10 Años', fontsize=16, fontweight='bold', pad=15)
ax.set_ylabel('Número de Casos', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('1_ultimos_10_años.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================
# GRÁFICO 2: Evolución histórica
# ============================================
print("Generando gráfico 2: Evolución histórica...")
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(nacional.index, nacional.values, linewidth=3, color='#e74c3c', marker='o', markersize=4)
ax.fill_between(nacional.index, nacional.values, alpha=0.2, color='#e74c3c')
ax.set_title('Evolución Histórica de Dengue en Costa Rica (1980-2024)', fontsize=16, fontweight='bold', pad=15)
ax.set_ylabel('Número de Casos', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('2_evolucion_historica.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================
# GRÁFICO 3: Casos semanales 2024
# ============================================
print("Generando gráfico 3: Semanas 2024...")
fig, ax = plt.subplots(figsize=(14, 6))
sem_2024 = df_semanal[(df_semanal['Year'] == 2024) & (df_semanal['S_res'] == 'Admin0')].copy()
sem_2024 = sem_2024.sort_values('calendar_start_date')
sem_2024['semana'] = range(1, len(sem_2024) + 1)
ax.plot(sem_2024['semana'], sem_2024['dengue_total'], linewidth=3, color='#3498db', marker='o', markersize=5)
ax.fill_between(sem_2024['semana'], sem_2024['dengue_total'], alpha=0.2, color='#3498db')
ax.set_title('Casos de Dengue por Semana - Costa Rica 2024', fontsize=16, fontweight='bold', pad=15)
ax.set_xlabel('Semana del Año', fontsize=13, fontweight='bold')
ax.set_ylabel('Número de Casos', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('3_semanas_2024.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================
# GRÁFICO 4: Top Provincias
# ============================================
print("Generando gráfico 4: Top provincias...")
fig, ax = plt.subplots(figsize=(10, 6))
prov_2018 = df_anual[(df_anual['Year'] == 2018) & (df_anual['S_res'] == 'Admin1')]
if len(prov_2018) > 0:
    top5 = prov_2018.groupby('adm_1_name')['dengue_total'].sum().sort_values().tail(5)
    colores = ['#e74c3c', '#e67e22', '#f39c12', '#16a085', '#27ae60']
    ax.barh(top5.index, top5.values, color=colores)
    for i, v in enumerate(top5.values):
        ax.text(v + 50, i, f'{int(v):,}', va='center', fontweight='bold', fontsize=11)
    ax.set_title('Top 5 Provincias con Más Casos - 2018', fontsize=16, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig('4_top_provincias.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================
# PREPARACIÓN DE DATOS MENSUALES (ESTACIONALIDAD)
# ============================================
print("Procesando datos mensuales para estacionalidad...")

# 1. Clima Mensual Promedio (Promedio de todos los años por mes)
# Agrupamos por mes para obtener el promedio histórico de cada mes
clima_mensual = df_clima.groupby('Month')[['PRECTOTCORR', 'T2M']].mean()
# PRECTOTCORR es mm/día (aprox), multiplicamos por 30.4 para tener mm/mes estimado
clima_mensual['Lluvia_Mes'] = clima_mensual['PRECTOTCORR'] * 30.4 

# 2. Dengue Mensual Promedio
# Primero convertimos fechas de dengue
df_semanal['Date'] = pd.to_datetime(df_semanal['calendar_start_date'])
df_semanal['Month'] = df_semanal['Date'].dt.month

# Agrupamos por Año y Mes primero para tener el total mensual real de cada año
dengue_mensual_real = df_semanal[df_semanal['S_res'] == 'Admin0'].groupby(['Year', 'Month'])['dengue_total'].sum().reset_index()
# Ahora promediamos por mes (Promedio histórico por mes)
dengue_estacional = dengue_mensual_real.groupby('Month')['dengue_total'].mean()

# ============================================
# GRÁFICO 7 (REEMPLAZO): Patrón Estacional (Climograma)
# ============================================
print("Generando gráfico 7: Patrón Estacional (Climograma)...")

fig, ax1 = plt.subplots(figsize=(14, 7))

meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

# Barras de Lluvia (Eje Izquierdo)
color_lluvia = '#3498db' # Azul
ax1.set_xlabel('Mes', fontsize=13, fontweight='bold')
ax1.set_ylabel('Lluvia Promedio', color=color_lluvia, fontsize=13, fontweight='bold')
# Usamos clima_mensual['Lluvia_Mes']
bars = ax1.bar(meses, clima_mensual['Lluvia_Mes'], color=color_lluvia, alpha=0.5, label='Lluvia')
ax1.tick_params(axis='y', labelcolor=color_lluvia)
ax1.grid(False) # Quitar grid para limpieza visual

# Línea de Dengue (Eje Derecho)
ax2 = ax1.twinx()
color_dengue = '#27ae60' # Verde
ax2.set_ylabel('Promedio de Casos de Dengue', color=color_dengue, fontsize=13, fontweight='bold')
# Usamos dengue_estacional
line = ax2.plot(meses, dengue_estacional.values, color=color_dengue, linewidth=4, marker='o', markersize=8, label='Casos Dengue')
ax2.tick_params(axis='y', labelcolor=color_dengue)
ax2.grid(False)

# Título explicativo
plt.title('Patrón Estacional: ¿Cuándo llueve y cuándo hay Dengue?', 
          fontsize=16, fontweight='bold', pad=20)

# Añadir leyenda combinada
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=12)

plt.tight_layout()
plt.savefig('7_correlacion_clima.png', dpi=300, bbox_inches='tight')
print("✓ Guardado: 7_correlacion_clima.png (Reemplazado por Estacionalidad)")
plt.close()

# ============================================
# GRÁFICO 8: Tri-variado (Lluvia, Temp, Dengue)
# ============================================
print("Generando gráfico 8: Análisis Estacional Completo (3 variables)...")

fig, ax1 = plt.subplots(figsize=(14, 7))

# Eje 1 (Izquierda): Lluvia (Barras)
color_rain = '#3498db' # Azul
ax1.set_xlabel('Mes del Año', fontsize=12, fontweight='bold')
ax1.set_ylabel('Lluvia Promedio', color=color_rain, fontsize=12, fontweight='bold')
# Usamos clima_mensual['Lluvia_Mes']
ax1.bar(meses, clima_mensual['Lluvia_Mes'], color=color_rain, alpha=0.3, label='Lluvia')
ax1.tick_params(axis='y', labelcolor=color_rain)
ax1.grid(False) # Quitar grid para limpiar

# Eje 2 (Derecha): Dengue (Línea Sólida)
ax2 = ax1.twinx()
color_dengue = '#27ae60' # Verde
ax2.set_ylabel('Promedio Casos Dengue', color=color_dengue, fontsize=12, fontweight='bold')
# Usamos dengue_estacional
ax2.plot(meses, dengue_estacional.values, color=color_dengue, linewidth=3, marker='o', label='Dengue')
ax2.tick_params(axis='y', labelcolor=color_dengue)
ax2.grid(False)

# Eje 3 (Derecha Offset): Temperatura (Línea Punteada)
# Truco para tercer eje
ax3 = ax1.twinx()
ax3.spines["right"].set_position(("axes", 1.15)) # Mover el eje a la derecha
color_temp = '#e74c3c' # Rojo
ax3.set_ylabel('Temperatura', color=color_temp, fontsize=12, fontweight='bold')
# Usamos clima_mensual['T2M']
ax3.plot(meses, clima_mensual['T2M'], color=color_temp, linewidth=3, linestyle='--', marker='s', label='Temp')
ax3.tick_params(axis='y', labelcolor=color_temp)
ax3.grid(False)

plt.title('Ciclo Anual Completo: Lluvia, Temperatura y Dengue', fontsize=16, fontweight='bold', pad=20)

# Leyenda combinada manual para claridad
from matplotlib.lines import Line2D
custom_lines = [Line2D([0], [0], color=color_rain, lw=4, alpha=0.3),
                Line2D([0], [0], color=color_dengue, lw=3),
                Line2D([0], [0], color=color_temp, lw=3, linestyle='--')]
ax1.legend(custom_lines, ['Lluvia', 'Dengue', 'Temperatura'], loc='upper left')

plt.tight_layout()
plt.savefig('8_patron_estacional_completo.png', dpi=300, bbox_inches='tight')
print("✓ Guardado: 8_patron_estacional_completo.png")
plt.close()

# ============================================
# GRÁFICOS 5 y 6: Mantener Anuales (Actualizados)
# ============================================
# Para los anuales, agrupamos el clima diario a anual
clima_anual = df_clima.groupby('YEAR').agg({
    'PRECTOTCORR': 'sum', # Suma de lluvia diaria = lluvia anual (aprox)
    'T2M': 'mean'         # Promedio de temperatura
}).reset_index()
clima_anual.columns = ['Year', 'Lluvia_Anual', 'Temperatura_Media']

# Combinar con dengue anual
dengue_anual_total = nacional.reset_index()
dengue_anual_total.columns = ['Year', 'Casos_Dengue']

datos_combinados = dengue_anual_total.merge(clima_anual, on='Year', how='inner')

# Gráfico 5
print("Generando gráfico 5: Dengue vs Temperatura...")
fig, ax1 = plt.subplots(figsize=(14, 6))
color = '#27ae60' # Verde (Dengue)
ax1.set_xlabel('Año', fontsize=13, fontweight='bold')
ax1.set_ylabel('Casos de Dengue', color=color, fontsize=13, fontweight='bold')
ax1.plot(datos_combinados['Year'], datos_combinados['Casos_Dengue'], color=color, linewidth=3, marker='o', label='Dengue')
ax1.tick_params(axis='y', labelcolor=color)
ax2 = ax1.twinx()
color = '#e74c3c' # Rojo (Temp)
ax2.set_ylabel('Temperatura Media', color=color, fontsize=13, fontweight='bold')
ax2.plot(datos_combinados['Year'], datos_combinados['Temperatura_Media'], color=color, linewidth=3, marker='s', linestyle='--', label='Temp')
ax2.tick_params(axis='y', labelcolor=color)
plt.title('Relación Anual: Dengue vs Temperatura', fontsize=16, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig('5_dengue_vs_temperatura.png', dpi=300, bbox_inches='tight')
plt.close()

# Gráfico 6
print("Generando gráfico 6: Dengue vs Lluvia...")
fig, ax1 = plt.subplots(figsize=(14, 6))
color = '#27ae60' # Verde (Dengue)
ax1.set_xlabel('Año', fontsize=13, fontweight='bold')
ax1.set_ylabel('Casos de Dengue', color=color, fontsize=13, fontweight='bold')
ax1.plot(datos_combinados['Year'], datos_combinados['Casos_Dengue'], color=color, linewidth=3, marker='o', label='Dengue')
ax1.tick_params(axis='y', labelcolor=color)
ax2 = ax1.twinx()
color = '#3498db' # Azul (Lluvia)
ax2.set_ylabel('Lluvia Acumulada', color=color, fontsize=13, fontweight='bold')
ax2.plot(datos_combinados['Year'], datos_combinados['Lluvia_Anual'], color=color, linewidth=3, marker='s', linestyle='--', label='Lluvia')
ax2.tick_params(axis='y', labelcolor=color)
plt.title('Relación Anual: Dengue vs Lluvia', fontsize=16, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig('6_dengue_vs_lluvia.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n" + "="*70)
print("RESUMEN FINAL")
print("="*70)
print("Se han generado todos los gráficos con la nueva data diaria de clima.")
print("El Gráfico 7 ahora muestra el PATRÓN ESTACIONAL (Mes a Mes) para facilitar la explicación.")
print("El Gráfico 8 incluye las 3 variables (Lluvia, Temp, Dengue) en un solo climograma.")
