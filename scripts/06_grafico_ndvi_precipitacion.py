"""
Grafico combinado NDVI + precipitacion (2024-2026) - Lote de prueba
Correr desde el EDITOR de la Consola de Python de QGIS (pegar completo y Run).

Sin loops complejos - valores ya calculados y confirmados en la consola,
hardcodeados directamente para evitar problemas de pegado.
"""

import matplotlib.pyplot as plt

CARPETA_PROYECTO = "./resultados"

ANIOS = ["2024", "2025", "2026"]
ndvi = [0.858, 0.699, 0.734]
precipitacion = [3.26, 1.48, 1.79]

fig, ax1 = plt.subplots(figsize=(8, 6))

color_ndvi = '#2e7d32'
barras = ax1.bar(ANIOS, ndvi, color=color_ndvi, width=0.4, alpha=0.85, label='NDVI medio', zorder=3)
ax1.set_ylabel("NDVI", color=color_ndvi, fontsize=11)
ax1.set_ylim(0, 1)
ax1.tick_params(axis='y', labelcolor=color_ndvi)

for i in range(3):
    ax1.text(i, ndvi[i] + 0.03, f"{ndvi[i]:.3f}", ha='center', fontweight='bold', color=color_ndvi)

ax2 = ax1.twinx()
color_precip = '#1565c0'
ax2.plot(ANIOS, precipitacion, marker='o', linewidth=2.5, color=color_precip, label='Precipitación enero (mm/día)', zorder=4)
ax2.set_ylabel("Precipitación (mm/día)", color=color_precip, fontsize=11)
ax2.set_ylim(0, 5)
ax2.tick_params(axis='y', labelcolor=color_precip)

for i in range(3):
    ax2.text(i, precipitacion[i] + 0.15, f"{precipitacion[i]:.2f}", ha='center', fontweight='bold', color=color_precip)

ax1.set_title("NDVI medio vs. precipitación de enero (2024-2026)", fontsize=13, fontweight='bold')
ax1.grid(axis='y', alpha=0.2, zorder=0)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=False)

conclusion = (
    "El orden de las tres campañas coincide en ambas variables (2024 > 2026 > 2025), "
    "tanto en NDVI como en precipitación de enero, lo que sugiere que la disponibilidad "
    "hídrica del mes fue un factor relevante en el vigor vegetal observado en cada campaña."
)

fig.subplots_adjust(bottom=0.28)
fig.text(0.5, 0.02, conclusion, ha='center', va='bottom', fontsize=9, style='italic', wrap=True)

ruta_grafico = CARPETA_PROYECTO + "/ndvi_vs_precipitacion_2024_2026.png"
plt.savefig(ruta_grafico, dpi=200)
plt.show()

print("Grafico guardado en:", ruta_grafico)
