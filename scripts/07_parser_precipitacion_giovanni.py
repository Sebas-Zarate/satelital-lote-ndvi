"""
07_parser_precipitacion_giovanni.py

Lee los CSV exportados desde NASA Giovanni (GPM IMERG) y calcula el
promedio de precipitacion de un mes especifico por campana.

Los CSV de Giovanni traen 8 lineas de metadata + 1 linea de encabezado
antes de los datos reales, y usan -9999.9 como valor de NoData. No se usa
pandas a proposito (no viene instalado por defecto en el interprete de
Python de QGIS) - se lee con el modulo estandar csv.

Se puede correr tanto en la Consola de QGIS como en cualquier Python 3
estandar (no depende de la API de QGIS).
"""

import csv
from datetime import datetime

# ==========================================================
# CONFIGURACION
# ==========================================================
ARCHIVO_MENSUAL = "./data/precipitacion_mensual_giovanni.csv"  # GPM_3IMERGM (mm/hr)
ARCHIVO_DIARIO = "./data/precipitacion_diaria_giovanni.csv"    # GPM_3IMERGDL (mm/dia)

ANIO_MENSUAL_A = 2024
ANIO_MENSUAL_B = 2025
ANIO_DIARIO = 2026
MES_OBJETIVO = 1  # enero

NODATA_GIOVANNI = -9999.9
LINEAS_METADATA = 9  # 8 de metadata + 1 de encabezado


def leer_csv_giovanni(ruta, formato_fecha):
    """Lee un CSV de Giovanni y devuelve lista de tuplas (fecha, valor)."""
    filas = []
    with open(ruta) as f:
        lector = csv.reader(f)
        todas = list(lector)
        datos = todas[LINEAS_METADATA:]
        for fila in datos:
            if len(fila) < 2:
                continue
            fecha_str, valor_str = fila[0].strip(), fila[1].strip()
            valor = float(valor_str)
            if valor == NODATA_GIOVANNI:
                continue
            fecha = datetime.strptime(fecha_str, formato_fecha)
            filas.append((fecha, valor))
    return filas


# ==========================================================
# 1) LEER AMBOS ARCHIVOS
# ==========================================================
filas_mensual = leer_csv_giovanni(ARCHIVO_MENSUAL, "%Y-%m-%d %H:%M:%S")
filas_diario = leer_csv_giovanni(ARCHIVO_DIARIO, "%Y-%m-%d")

print(f"Filas mensual: {len(filas_mensual)}  |  Filas diario: {len(filas_diario)}")

# ==========================================================
# 2) PROMEDIO DE ENERO POR CAMPANA (unificando a mm/dia)
# ==========================================================
valores_a = [v * 24 for f, v in filas_mensual if f.year == ANIO_MENSUAL_A and f.month == MES_OBJETIVO]
valores_b = [v * 24 for f, v in filas_mensual if f.year == ANIO_MENSUAL_B and f.month == MES_OBJETIVO]
valores_c = [v for f, v in filas_diario if f.year == ANIO_DIARIO and f.month == MES_OBJETIVO]

precip_a = valores_a[0] if valores_a else None
precip_b = valores_b[0] if valores_b else None
precip_c = sum(valores_c) / len(valores_c) if valores_c else None

print(f"Precipitacion media enero {ANIO_MENSUAL_A}: {precip_a:.2f} mm/dia (fuente mensual)")
print(f"Precipitacion media enero {ANIO_MENSUAL_B}: {precip_b:.2f} mm/dia (fuente mensual)")
print(f"Precipitacion media enero {ANIO_DIARIO}: {precip_c:.2f} mm/dia (promedio de {len(valores_c)} dias, fuente diaria)")
