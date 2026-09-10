"""
Grafico de evolucion de zonas de manejo 2024-2026 - Lote de prueba
Correr desde el EDITOR de la Consola de Python de QGIS (pegar completo y Run).

A diferencia de zonas_manejo_evolucion.py, este script NO recalcula nada:
solo lee los tres rasters de zonas que ya generamos (Zonas_manejo_2024.tif,
Zonas_manejo_2025.tif, Zonas_manejo_2026.tif) y arma el grafico de linea.
"""

import matplotlib.pyplot as plt
from osgeo import gdal

# ==========================================================
# CONFIGURACION
# ==========================================================
CARPETA_PROYECTO = "./resultados"

ANIOS = ["2024", "2025", "2026"]
RUTAS_ZONAS = {
    "2024": CARPETA_PROYECTO + "/Zonas_manejo_2024.tif",
    "2025": CARPETA_PROYECTO + "/Zonas_manejo_2025.tif",
    "2026": CARPETA_PROYECTO + "/Zonas_manejo_2026.tif",
}

# ==========================================================
# 1) LEER LOS TRES RASTERS YA CALCULADOS
# ==========================================================
serie_baja = []
serie_media = []
serie_alta = []

for anio in ANIOS:
    ds = gdal.Open(RUTAS_ZONAS[anio])
    if ds is None:
        raise RuntimeError(f"No se pudo abrir {RUTAS_ZONAS[anio]}")

    zonas = ds.GetRasterBand(1).ReadAsArray()
    ds = None

    mask_valido = zonas != 0  # 0 = NoData
    total = mask_valido.sum()

    pct_baja = float((zonas == 1).sum() / total * 100)
    pct_media = float((zonas == 2).sum() / total * 100)
    pct_alta = float((zonas == 3).sum() / total * 100)

    serie_baja.append(pct_baja)
    serie_media.append(pct_media)
    serie_alta.append(pct_alta)

    print(f"{anio} -> Baja: {pct_baja:.1f}%  Media: {pct_media:.1f}%  Alta: {pct_alta:.1f}%")

# ==========================================================
# 2) GRAFICO DE LINEA
# ==========================================================
fig, ax = plt.subplots(figsize=(8, 6))

ax.plot(ANIOS, serie_baja, marker='o', linewidth=2, color='#d62728', label='Zona Baja (≤0.45)')
ax.plot(ANIOS, serie_media, marker='o', linewidth=2, color='#ffaa00', label='Zona Media (0.45-0.65)')
ax.plot(ANIOS, serie_alta, marker='o', linewidth=2, color='#2ca02c', label='Zona Alta (>0.65)')

for i, anio in enumerate(ANIOS):
    ax.text(i, serie_baja[i] + 2, f"{serie_baja[i]:.1f}%", ha='center', fontsize=8, color='#d62728')
    ax.text(i, serie_media[i] + 2, f"{serie_media[i]:.1f}%", ha='center', fontsize=8, color='#cc8800')
    ax.text(i, serie_alta[i] + 2, f"{serie_alta[i]:.1f}%", ha='center', fontsize=8, color='#2ca02c')

ax.set_ylim(0, 100)
ax.set_ylabel("% de superficie del lote")
ax.set_title("Evolución de las zonas de manejo (2024-2026)", fontsize=13, fontweight='bold')
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.08), ncol=3, frameon=False)
ax.grid(alpha=0.3)

# ==========================================================
# 3) CONCLUSION AL PIE - consistencia temporal de la zona Alta
# ==========================================================
variacion_alta = max(serie_alta) - min(serie_alta)

if variacion_alta < 15:
    conclusion = (
        f"La zona Alta se mantiene consistentemente predominante en las tres campañas "
        f"({min(serie_alta):.1f}% - {max(serie_alta):.1f}%), lo que sugiere que la "
        f"zonificación refleja un patrón estable del lote (relieve, tipo de suelo) y no "
        f"una condición puntual de una sola campaña, dando mayor respaldo a una "
        f"recomendación de manejo diferenciado (VRA)."
    )
else:
    conclusion = (
        f"La superficie en zona Alta varió considerablemente entre campañas "
        f"({min(serie_alta):.1f}% - {max(serie_alta):.1f}%), lo que indica que la "
        f"zonificación de una sola campaña puede no ser representativa por sí sola; "
        f"se recomienda considerar el promedio de varias campañas antes de definir "
        f"un plan de aplicación variable."
    )

fig.subplots_adjust(bottom=0.32)
fig.text(0.5, 0.02, conclusion, ha='center', va='bottom', fontsize=9, style='italic', wrap=True)

# ==========================================================
# 4) GUARDAR Y MOSTRAR
# ==========================================================
ruta_grafico = CARPETA_PROYECTO + "/zonas_manejo_evolucion_2024_2026.png"
plt.savefig(ruta_grafico, dpi=200)
plt.show()

print("Grafico guardado en:", ruta_grafico)
