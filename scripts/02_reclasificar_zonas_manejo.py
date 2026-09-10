"""
02_reclasificar_zonas_manejo.py

Reclasifica un raster de NDVI en 3 zonas de manejo discretas (Baja/Media/
Alta vigor), calcula el porcentaje de superficie de cada zona, y aplica
simbologia categorica (rojo/amarillo/verde) a la capa resultante.

Correr desde el Editor de la Consola de Python de QGIS.
"""

import os
import numpy as np
from osgeo import gdal
from qgis.core import QgsRasterLayer, QgsProject, QgsPalettedRasterRenderer

# ==========================================================
# CONFIGURACION
# ==========================================================
ANIO = "2026"
CARPETA_RESULTADOS = "./resultados"

RUTA_NDVI = os.path.join(CARPETA_RESULTADOS, f"NDVI_{ANIO}.tif")
RUTA_ZONAS = os.path.join(CARPETA_RESULTADOS, f"Zonas_manejo_{ANIO}.tif")

NODATA_NDVI = -3.4028234663852886e+38  # NoData float32 estandar de GDAL

# Umbrales de reclasificacion (ajustar segun el cultivo/region si hace falta)
UMBRAL_BAJA = 0.45
UMBRAL_MEDIA = 0.65

# ==========================================================
# 1) LEER NDVI Y RECLASIFICAR
# ==========================================================
ds_ndvi = gdal.Open(RUTA_NDVI)
if ds_ndvi is None:
    raise RuntimeError(f"No se pudo abrir {RUTA_NDVI}")

arr_ndvi = ds_ndvi.GetRasterBand(1).ReadAsArray()
mask_valido = arr_ndvi != NODATA_NDVI

zonas = np.zeros(arr_ndvi.shape, dtype=np.uint8)
zonas[mask_valido & (arr_ndvi <= UMBRAL_BAJA)] = 1
zonas[mask_valido & (arr_ndvi > UMBRAL_BAJA) & (arr_ndvi <= UMBRAL_MEDIA)] = 2
zonas[mask_valido & (arr_ndvi > UMBRAL_MEDIA)] = 3

# ==========================================================
# 2) GUARDAR EL RASTER DE ZONAS
# ==========================================================
driver = gdal.GetDriverByName('GTiff')
ds_zonas = driver.Create(RUTA_ZONAS, ds_ndvi.RasterXSize, ds_ndvi.RasterYSize, 1, gdal.GDT_Byte)
ds_zonas.SetGeoTransform(ds_ndvi.GetGeoTransform())
ds_zonas.SetProjection(ds_ndvi.GetProjection())
ds_zonas.GetRasterBand(1).WriteArray(zonas)
ds_zonas.GetRasterBand(1).SetNoDataValue(0)
ds_zonas.FlushCache()
ds_zonas = None
ds_ndvi = None

print("Raster de zonas guardado en:", RUTA_ZONAS)

# ==========================================================
# 3) PORCENTAJE DE SUPERFICIE POR ZONA
# ==========================================================
total_pixeles = mask_valido.sum()
pct_baja = (zonas == 1).sum() / total_pixeles * 100
pct_media = (zonas == 2).sum() / total_pixeles * 100
pct_alta = (zonas == 3).sum() / total_pixeles * 100

print(f"Zona Baja (<={UMBRAL_BAJA}): {pct_baja:.1f}%")
print(f"Zona Media ({UMBRAL_BAJA}-{UMBRAL_MEDIA}): {pct_media:.1f}%")
print(f"Zona Alta (>{UMBRAL_MEDIA}): {pct_alta:.1f}%")

# ==========================================================
# 4) CARGAR AL PROYECTO Y APLICAR SIMBOLOGIA
# ==========================================================
zonas_layer = QgsRasterLayer(RUTA_ZONAS, f"Zonas_manejo_{ANIO}")
QgsProject.instance().addMapLayer(zonas_layer)

categorias = [
    QgsPalettedRasterRenderer.Class(1, QColor(214, 39, 40), f"Baja (<={UMBRAL_BAJA})"),
    QgsPalettedRasterRenderer.Class(2, QColor(255, 221, 51), f"Media ({UMBRAL_BAJA}-{UMBRAL_MEDIA})"),
    QgsPalettedRasterRenderer.Class(3, QColor(44, 160, 44), f"Alta (>{UMBRAL_MEDIA})"),
]
renderer = QgsPalettedRasterRenderer(zonas_layer.dataProvider(), 1, categorias)
zonas_layer.setRenderer(renderer)
zonas_layer.triggerRepaint()
