"""
Grafico comparativo de NDVI 2024-2026 - Lote de prueba
Correr desde el EDITOR de la Consola de Python de QGIS (pegar completo y Run,
no pegar linea por linea en el prompt interactivo).

Lee los tres rasters NDVI ya calculados (NDVI_2024.tif, NDVI_2025.tif,
NDVI_2026.tif), calcula media/min/max de cada uno, y genera un grafico de
barras con el rango como barras de error, mas una conclusion breve al pie.
Guarda el resultado como PNG en la carpeta del proyecto.
"""

import matplotlib.pyplot as plt
from osgeo import gdal

# ==========================================================
# CONFIGURACION
# ==========================================================
CARPETA_PROYECTO = "./resultados"
NODATA_NDVI = -3.4028234663852886e+38

ANIOS = ["2024", "2025", "2026"]
FECHAS = ["26/01/2024", "10/01/2025", "05/01/2026"]
RUTAS_NDVI = [
    CARPETA_PROYECTO + "/NDVI_2024.tif",
    CARPETA_PROYECTO + "/NDVI_2025.tif",
    CARPETA_PROYECTO + "/NDVI_2026.tif",
]

# ==========================================================
# 1) LEER LAS TRES CAPAS Y CALCULAR ESTADISTICAS
# ==========================================================
medias = []
minimos = []
maximos = []

for ruta in RUTAS_NDVI:
    ds = gdal.Open(ruta)
    if ds is None:
        raise RuntimeError(f"No se pudo abrir {ruta}")
    arr = ds.GetRasterBand(1).ReadAsArray()
    mask = arr != NODATA_NDVI
    medias.append(float(arr[mask].mean()))
    minimos.append(float(arr[mask].min()))
    maximos.append(float(arr[mask].max()))
    ds = None
    print(f"{ruta} -> media: {medias[-1]:.3f}  min: {minimos[-1]:.3f}  max: {maximos[-1]:.3f}")

# ==========================================================
# 2) ARMAR EL GRAFICO
# ==========================================================
fig, ax = plt.subplots(figsize=(8, 6))

colores = ['#2e7d32', '#43a047', '#558b2f']  # tonos de verde - los 3 años en rango similar
barras = ax.bar(ANIOS, medias, color=colores, width=0.5, zorder=3)

# Barras de error mostrando el rango min-max real de cada año
err_inf = [m - mn for m, mn in zip(medias, minimos)]
err_sup = [mx - m for m, mx in zip(medias, maximos)]
ax.errorbar(ANIOS, medias, yerr=[err_inf, err_sup], fmt='none',
            ecolor='black', capsize=6, zorder=4)

# Etiquetas con el valor medio arriba de cada barra
for i, valor in enumerate(medias):
    ax.text(i, valor + 0.03, f"{valor:.3f}", ha='center', fontweight='bold')

ax.set_ylim(0, 1)
ax.set_ylabel("NDVI")
ax.set_title("Comparación interanual de NDVI del lote (2024-2026)",
             fontsize=13, fontweight='bold')
ax.grid(axis='y', alpha=0.3, zorder=0)

# Fechas de cada campaña como sub-etiqueta del eje X
ax.set_xticklabels([f"{a}\n({f})" for a, f in zip(ANIOS, FECHAS)])

# ==========================================================
# 3) CONCLUSION AL PIE
# ==========================================================
# Arma la conclusion automaticamente: si los rangos min-max de los años se
# superponen entre si, remarca la consistencia; si no superponen (separación
# clara entre el mas bajo y el resto), senala el año que se aparta.
idx_min = medias.index(min(medias))
idx_max = medias.index(max(medias))

rangos_superponen = min(maximos) >= max(minimos)

if rangos_superponen:
    conclusion = (
        f"Los rangos de NDVI de las tres campañas se superponen entre sí (medias entre "
        f"{medias[idx_min]:.3f} y {medias[idx_max]:.3f}), indicando vegetación densa "
        f"y un comportamiento consistente del lote en las tres fechas analizadas."
    )
else:
    conclusion = (
        f"El NDVI medio de {ANIOS[idx_min]} ({medias[idx_min]:.3f}) fue notablemente inferior "
        f"al de {ANIOS[idx_max]} ({medias[idx_max]:.3f}), sin superposición entre sus rangos, "
        f"lo que sugiere una condición distinta del lote en esa fecha (posible barbecho, "
        f"cultivo recién sembrado, o cobertura de nubes) frente a los años con vegetación densa."
    )

fig.subplots_adjust(bottom=0.30)
fig.text(0.5, 0.02, conclusion, ha='center', va='bottom', fontsize=9,
         style='italic', wrap=True)

# ==========================================================
# 4) GUARDAR Y MOSTRAR
# ==========================================================
ruta_grafico = CARPETA_PROYECTO + "/comparacion_NDVI_2024_2026.png"
plt.savefig(ruta_grafico, dpi=200)
plt.show()

print("Grafico guardado en:", ruta_grafico)
