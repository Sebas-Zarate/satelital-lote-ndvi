"""
03_generar_prescripcion_vra.py

Convierte el raster de zonas de manejo en un mapa de prescripcion vectorial
para aplicacion variable (VRA): vectoriza las zonas, las disuelve en un
poligono por clase, y le asigna una dosis relativa sugerida a cada una.

Criterio agronomico aplicado (fertilizacion nitrogenada variable en estado
vegetativo): subir la dosis en zonas de bajo vigor (para compensar una
eventual deficiencia nutricional) y bajarla en zonas de alto vigor (donde
el cultivo ya presenta buen desarrollo), buscando homogeneizar el canopeo.

Correr desde el Editor de la Consola de Python de QGIS.
"""

import os
from qgis.core import (
    QgsVectorLayer, QgsVectorFileWriter, QgsProject, QgsField,
    QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsFillSymbol,
)
from qgis.PyQt.QtCore import QVariant
import processing

# ==========================================================
# CONFIGURACION
# ==========================================================
ANIO = "2026"
CARPETA_RESULTADOS = "./resultados"

RUTA_ZONAS_RASTER = os.path.join(CARPETA_RESULTADOS, f"Zonas_manejo_{ANIO}.tif")
RUTA_PRESCRIPCION = os.path.join(CARPETA_RESULTADOS, f"Prescripcion_VRA_{ANIO}.shp")

# Dosis relativa sugerida por zona (% sobre la dosis estandar del lote)
DOSIS_POR_ZONA = {
    1: (120, "Baja"),   # bajo vigor -> subir dosis
    2: (100, "Media"),  # vigor medio -> dosis estandar
    3: (80, "Alta"),    # alto vigor -> bajar dosis
}

# ==========================================================
# 1) VECTORIZAR EL RASTER DE ZONAS
# ==========================================================
ruta_poly_temp = os.path.join(CARPETA_RESULTADOS, "_zonas_poly_temp.shp")
ruta_dissolve_temp = os.path.join(CARPETA_RESULTADOS, "_zonas_dissolve_temp.shp")

resultado_poly = processing.run("gdal:polygonize", {
    'INPUT': RUTA_ZONAS_RASTER,
    'BAND': 1,
    'FIELD': 'zona_id',
    'EIGHT_CONNECTEDNESS': False,
    'OUTPUT': ruta_poly_temp,
})
zonas_poly = QgsVectorLayer(resultado_poly['OUTPUT'], "zonas_poly", "ogr")

# ==========================================================
# 2) DISOLVER (un poligono por clase, en vez de miles de celdas sueltas)
# ==========================================================
resultado_dissolve = processing.run("native:dissolve", {
    'INPUT': zonas_poly,
    'FIELD': ['zona_id'],
    'OUTPUT': ruta_dissolve_temp,
})
zonas_dissolve = QgsVectorLayer(resultado_dissolve['OUTPUT'], "zonas_dissolve", "ogr")

print("Zonas disueltas:", zonas_dissolve.featureCount(), "poligonos")

# ==========================================================
# 3) AGREGAR CAMPOS DE DOSIS RELATIVA Y NOMBRE DE ZONA
# ==========================================================
zonas_dissolve.startEditing()
zonas_dissolve.addAttribute(QgsField("dosis_rel", QVariant.Int))
zonas_dissolve.addAttribute(QgsField("zona_nom", QVariant.String))
zonas_dissolve.updateFields()

idx_dosis = zonas_dissolve.fields().indexOf("dosis_rel")
idx_nombre = zonas_dissolve.fields().indexOf("zona_nom")

for feature in zonas_dissolve.getFeatures():
    zona_id = feature["zona_id"]
    if zona_id in DOSIS_POR_ZONA:
        dosis, nombre = DOSIS_POR_ZONA[zona_id]
        zonas_dissolve.changeAttributeValue(feature.id(), idx_dosis, dosis)
        zonas_dissolve.changeAttributeValue(feature.id(), idx_nombre, nombre)

zonas_dissolve.commitChanges()

# ==========================================================
# 4) EXPORTAR COMO SHAPEFILE (formato compatible con equipos VRA)
# ==========================================================
QgsVectorFileWriter.writeAsVectorFormat(
    zonas_dissolve, RUTA_PRESCRIPCION, "UTF-8", zonas_dissolve.crs(), "ESRI Shapefile"
)

prescripcion_layer = QgsVectorLayer(RUTA_PRESCRIPCION, f"Prescripcion_VRA_{ANIO}", "ogr")
QgsProject.instance().addMapLayer(prescripcion_layer)

print("Prescripcion guardada en:", RUTA_PRESCRIPCION)
for f in prescripcion_layer.getFeatures():
    print(f["zona_nom"], "-> dosis:", f["dosis_rel"], "%")

# ==========================================================
# 5) SIMBOLOGIA POR ZONA + ETIQUETAS DE DOSIS
# ==========================================================
colores = {"Baja": QColor(214, 39, 40), "Media": QColor(255, 221, 51), "Alta": QColor(44, 160, 44)}
categorias = []
for nombre, color in colores.items():
    simbolo = QgsFillSymbol.createSimple({'color': color.name(), 'outline_color': 'black', 'outline_width': '0.3'})
    categorias.append(QgsRendererCategory(nombre, simbolo, nombre))

renderer = QgsCategorizedSymbolRenderer('zona_nom', categorias)
prescripcion_layer.setRenderer(renderer)
prescripcion_layer.triggerRepaint()
