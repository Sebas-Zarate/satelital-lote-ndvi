"""
01_calcular_ndvi.py

Calcula el indice NDVI de un lote a partir de las bandas B04 (rojo) y B08
(infrarrojo cercano) de Sentinel-2 L2A, recortadas al poligono del lote.

Correr desde el Editor de la Consola de Python de QGIS (Complementos >
Consola de Python > icono de Editor), con el proyecto abierto y las
variables de configuracion ajustadas a tus rutas.

Flujo:
1. Carga B04 y B08 (bandas crudas descargadas de Copernicus Browser)
2. Recorta ambas al poligono del lote (gdal:cliprasterbymasklayer, con
   NODATA explicito para que el recorte respete la forma real del lote
   en vez de dejar un rectangulo solido)
3. Calcula NDVI = (B08 - B04) / (B08 + B04) con QgsRasterCalculator
4. Guarda el resultado como GeoTIFF y lo carga al proyecto
"""

import os
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsProject
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
import processing

# ==========================================================
# CONFIGURACION - ajustar por campana/anio
# ==========================================================
ANIO = "2026"

CARPETA_DATOS = "./data"          # carpeta con las bandas B04/B08 descargadas
CARPETA_SALIDA = "./resultados"   # carpeta de salida para los .tif generados

B04_NOMBRE = f"B04_{ANIO}.tiff"   # nombre del archivo B04 (Raw) descargado
B08_NOMBRE = f"B08_{ANIO}.tiff"   # nombre del archivo B08 (Raw) descargado
LOTE_GEOJSON = os.path.join(CARPETA_DATOS, "lote.geojson")  # poligono del lote

BUFFER_NEGATIVO = -2  # metros; reduce el poligono para evitar bordes vacios
                       # si el recorte falla porque el lote toca el borde
                       # de la imagen descargada

# ==========================================================
# RUTAS DERIVADAS
# ==========================================================
b04_path = os.path.join(CARPETA_DATOS, B04_NOMBRE)
b08_path = os.path.join(CARPETA_DATOS, B08_NOMBRE)

b04_clip_path = os.path.join(CARPETA_SALIDA, f"B04_{ANIO}_clip.tif")
b08_clip_path = os.path.join(CARPETA_SALIDA, f"B08_{ANIO}_clip.tif")
ndvi_output = os.path.join(CARPETA_SALIDA, f"NDVI_{ANIO}.tif")

# ==========================================================
# 1) CARGAR CAPAS DE ORIGEN Y VALIDAR
# ==========================================================
b04 = QgsRasterLayer(b04_path, f"B04_{ANIO}")
b08 = QgsRasterLayer(b08_path, f"B08_{ANIO}")
lote = QgsVectorLayer(LOTE_GEOJSON, "lote", "ogr")

for nombre, capa in [("B04", b04), ("B08", b08), ("Lote", lote)]:
    if not capa.isValid():
        raise RuntimeError(f"ERROR: no se pudo cargar la capa {nombre} desde {capa.source()}")
    print(f"OK - {nombre} cargada correctamente")

# Chequeo rapido de que las bandas no vengan vacias (paso critico: en este
# proyecto, algunas descargas de Copernicus vinieron con reflectancia 0 en
# toda la escena, algo que solo se detecta revisando los valores crudos)
stats_b04 = b04.dataProvider().bandStatistics(1)
if stats_b04.maximumValue == 0:
    raise RuntimeError("B04 tiene todos los valores en cero - descarga corrupta, volver a bajar la escena")

# ==========================================================
# 2) BUFFER NEGATIVO Y RECORTE AL POLIGONO DEL LOTE
# ==========================================================
buffer_resultado = processing.run("native:buffer", {
    'INPUT': LOTE_GEOJSON,
    'DISTANCE': BUFFER_NEGATIVO,
    'SEGMENTS': 5,
    'END_CAP_STYLE': 0,
    'JOIN_STYLE': 0,
    'MITER_LIMIT': 2,
    'DISSOLVE': False,
    'OUTPUT': 'memory:lote_reducido',
})
lote_reducido = buffer_resultado['OUTPUT']

def recortar(raster_path, mask_layer, output_path):
    resultado = processing.run("gdal:cliprasterbymasklayer", {
        'INPUT': raster_path,
        'MASK': mask_layer,
        'SOURCE_CRS': None,
        'TARGET_CRS': None,
        'NODATA': 0,          # clave: sin esto, el recorte queda como
                               # rectangulo solido en vez de respetar la
                               # forma real del poligono
        'ALPHA_BAND': False,
        'CROP_TO_CUTLINE': True,
        'KEEP_RESOLUTION': True,
        'OUTPUT': output_path,
    })
    return resultado['OUTPUT']

recortar(b04_path, lote_reducido, b04_clip_path)
recortar(b08_path, lote_reducido, b08_clip_path)

b04_clip = QgsRasterLayer(b04_clip_path, f"B04_{ANIO}_clip")
b08_clip = QgsRasterLayer(b08_clip_path, f"B08_{ANIO}_clip")

for nombre, capa in [("B04 recortada", b04_clip), ("B08 recortada", b08_clip)]:
    if not capa.isValid():
        raise RuntimeError(f"ERROR: el recorte de {nombre} no es valido")
    print(f"{nombre}: {capa.width()}x{capa.height()} px - OK")

QgsProject.instance().addMapLayer(b04_clip)
QgsProject.instance().addMapLayer(b08_clip)

# ==========================================================
# 3) CALCULAR NDVI = (B08 - B04) / (B08 + B04)
# ==========================================================
entries = []

e_b04 = QgsRasterCalculatorEntry()
e_b04.ref = 'B04@1'
e_b04.raster = b04_clip
e_b04.bandNumber = 1
entries.append(e_b04)

e_b08 = QgsRasterCalculatorEntry()
e_b08.ref = 'B08@1'
e_b08.raster = b08_clip
e_b08.bandNumber = 1
entries.append(e_b08)

formula = '(B08@1 - B04@1) / (B08@1 + B04@1)'

calc = QgsRasterCalculator(
    formula, ndvi_output, 'GTiff',
    b04_clip.extent(), b04_clip.width(), b04_clip.height(), entries,
)

resultado = calc.processCalculation()

if str(resultado) in ("0", "Result.Success"):
    print(f"NDVI {ANIO} calculado correctamente -> {ndvi_output}")
    ndvi_layer = QgsRasterLayer(ndvi_output, f"NDVI_{ANIO}")
    QgsProject.instance().addMapLayer(ndvi_layer)
    stats = ndvi_layer.dataProvider().bandStatistics(1)
    print(f"NDVI {ANIO} - min: {stats.minimumValue:.3f}  max: {stats.maximumValue:.3f}  media: {stats.mean:.3f}")
else:
    print(f"ERROR al calcular NDVI {ANIO}, codigo de resultado: {resultado}")
