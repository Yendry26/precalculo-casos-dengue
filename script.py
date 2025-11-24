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
# PREPARACIÓN DE DATOS ANUALES
# ============================================
nacional = df_anual[df_anual['S_res'] == 'Admin0'].groupby('Year')['dengue_total'].sum()




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
# GRÁFICO 1: Tri-variado (Lluvia, Temp, Dengue)
# ============================================
print("Generando gráfico 1: Análisis Estacional Completo (3 variables)...")

meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

fig, ax1 = plt.subplots(figsize=(14, 7))

# Eje 1 (Izquierda): Lluvia (Barras)
color_rain = '#3498db' # Azul
ax1.set_xlabel('Mes del Año', fontsize=12, fontweight='bold')
ax1.set_ylabel('Lluvia Promedio Mensual (mm)', color=color_rain, fontsize=12, fontweight='bold')
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
plt.savefig('1_patron_estacional_completo.png', dpi=300, bbox_inches='tight')
print("✓ Guardado: 1_patron_estacional_completo.png")
plt.close()

# ============================================
# GRÁFICOS 2 y 3: Mantener Anuales (Actualizados)
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

# Gráfico 2
print("Generando gráfico 2: Dengue vs Temperatura...")
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
plt.savefig('2_dengue_vs_temperatura.png', dpi=300, bbox_inches='tight')
plt.close()

# Gráfico 3
print("Generando gráfico 3: Dengue vs Lluvia...")
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
plt.savefig('3_dengue_vs_lluvia.png', dpi=300, bbox_inches='tight')
plt.close()

# ============================================
# GRÁFICO 4: Dispersión Multivariable (Burbujas)
# ============================================
print("Generando gráfico 4: Dispersión Multivariable...")
fig, ax = plt.subplots(figsize=(12, 8))

# Normalizar tamaño de burbujas para que sean visibles pero no enormes
# Factor de escala: ajustamos para que el máximo sea de un tamaño razonable
max_casos = datos_combinados['Casos_Dengue'].max()
sizes = (datos_combinados['Casos_Dengue'] / max_casos) * 2000 + 100

scatter = ax.scatter(datos_combinados['Temperatura_Media'], 
                     datos_combinados['Lluvia_Anual'], 
                     s=sizes, 
                     c=datos_combinados['Casos_Dengue'], 
                     cmap='YlOrRd', 
                     alpha=0.7, 
                     edgecolors='grey', 
                     linewidth=1)

# Añadir etiquetas de año en cada burbuja
for i, txt in enumerate(datos_combinados['Year']):
    ax.annotate(txt, (datos_combinados['Temperatura_Media'].iloc[i], datos_combinados['Lluvia_Anual'].iloc[i]),
                ha='center', va='center', fontsize=9, fontweight='bold')

# Barra de color
cbar = plt.colorbar(scatter)
cbar.set_label('Número de Casos de Dengue', fontsize=12, fontweight='bold')

ax.set_title('Relación Multivariable: Temperatura vs Lluvia vs Dengue (Tamaño)', fontsize=16, fontweight='bold', pad=15)
ax.set_xlabel('Temperatura Media Anual (°C)', fontsize=13, fontweight='bold')
ax.set_ylabel('Lluvia Anual Acumulada (mm)', fontsize=13, fontweight='bold')

# Grid para facilitar lectura
ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('4_dispersion_multivariable.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n" + "="*70)
print("RESUMEN FINAL")
print("="*70)
print("Se han generado todos los gráficos con la nueva data diaria de clima.")
print("El Gráfico 1 incluye las 3 variables (Lluvia, Temp, Dengue) en un solo climograma.")
print("El Gráfico 4 muestra la dispersión multivariable (Burbujas).")
