#!/usr/bin/env python3
"""
Une un CSV de admisiones con un JSON de partes clínicos por 'id_episodio'
y guarda el resultado en un nuevo JSON, conservando la estructura anidada.

Uso:
    Coloca este script en la misma carpeta que los dos archivos y ejecuta:
        python unir_csv_json.py

Requisitos:
    pip install pandas
"""

import json

import pandas as pd

# Columna que existe en ambos archivos y sirve para unirlos
CLAVE = "id_episodio"

# Columnas del JSON que NO se copian porque ya vienen en el CSV
COLUMNAS_REPETIDAS = (CLAVE, "sip_paciente")

# Columnas del CSV que son enteros, pero pandas lee como float por los vacíos
COLUMNAS_ENTERAS = ["frecuencia_cardiaca", "pa_sistolica", "pa_diastolica"]

ruta_csv = "./admisiones_limpio.csv"
ruta_json = "../data/partes_clinicos.json"
ruta_salida = "../data/admisiones_con_partes_clinicos.json"

def limpia(valor, columna):
    """Convierte un valor del CSV a un tipo que JSON pueda escribir."""
    if pd.isna(valor):
        return None  # NaN -> null
    if columna in COLUMNAS_ENTERAS:
        return int(valor)  # 62.0 -> 62
    if hasattr(valor, "item"):
        return valor.item()  # tipo numpy -> tipo nativo de Python
    return valor


def unir(ruta_csv, ruta_json, ruta_salida):
    # 1. Cargar los datos
    df = pd.read_csv(ruta_csv)

    with open(ruta_json, encoding="utf-8") as f:
        # Diccionario {id_episodio: parte_clinico_completo} para búsqueda directa
        partes = {p[CLAVE]: p for p in json.load(f)}

    # 2. Construir un registro por cada fila del CSV (equivale a un left join)
    resultado = []
    for fila in df.to_dict(orient="records"):
        registro = {col: limpia(valor, col) for col, valor in fila.items()}

        parte = partes.get(registro[CLAVE])
        if parte:
            registro.update(
                {k: v for k, v in parte.items() if k not in COLUMNAS_REPETIDAS}
            )

        resultado.append(registro)

    # 3. Guardar el resultado
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)


unir(
    "admisiones_limpio.csv",
    "partes_clinicos.json",
    "admisiones_con_partes_clinicos.json",
)
