"""
Consultas de agregación sobre la colección de admisiones con partes clinicos del historico.

Usa la colección `coleccion_episodios` definida en conexion_mongo.py

"""
from conexion_mongo import coleccion_episodios

# ---------------------------------------------------------------------------
# CONSULTA 1: tiempo medio de estancia (minutos) por categoría patológica
# ---------------------------------------------------------------------------
# Se excluyen los episodios sin parte clínico (sin triaje_manchester) y los
# que tienen duracion_horas nulo o no positivo.
PIPELINE_ESTANCIA_MEDIA = [
    {"$match": {
        "triaje_manchester.categoria_patologia": {"$type": "string"},
        "duracion_horas": {"$type": "number", "$gt": 0},
    }},
    {"$group": {
        "_id": "$triaje_manchester.categoria_patologia",
        "estancia_media_min": {"$avg": {"$multiply": ["$duracion_horas", 60]}},
        "n_episodios": {"$sum": 1},
    }},
    {"$project": {
        "_id": 0,
        "categoria_patologia": "$_id",
        "estancia_media_min": {"$round": ["$estancia_media_min", 2]},
        "n_episodios": 1,
    }},
    {"$sort": {"estancia_media_min": -1}},
]


def estancia_media_por_categoria(coll=coleccion_episodios):
    """Devuelve una lista de dicts con la estancia media (min) por categoría."""
    return list(coll.aggregate(PIPELINE_ESTANCIA_MEDIA))


# ---------------------------------------------------------------------------
# CONSULTA 2: % de destino al alta (domicilio vs ingreso en planta) por edad
# ---------------------------------------------------------------------------
# - 'edad' puede venir como int o como string, se convierte con $convert.
# - Solo se comparan 'domicilio' e 'ingreso_planta'; el porcentaje se calcula
#   sobre la suma de ambos dentro de cada grupo de edad.
# - Grupos: 0-17, 18-39, 40-64, 65+ (se pueden cambiar en GRUPOS_EDAD).
GRUPOS_EDAD = [0, 18, 40, 65, 200]

PIPELINE_DESTINO_POR_EDAD = [
    {"$match": {"destino_alta": {"$in": ["domicilio", "ingreso_planta"]}}},
    {"$addFields": {
        "edad_num": {"$convert": {"input": "$edad", "to": "int",
                                  "onError": None, "onNull": None}},
    }},
    {"$match": {"edad_num": {"$ne": None}}},
    {"$bucket": {
        "groupBy": "$edad_num",
        "boundaries": GRUPOS_EDAD,
        "default": "otros",
        "output": {
            "total": {"$sum": 1},
            "domicilio": {"$sum": {"$cond": [{"$eq": ["$destino_alta", "domicilio"]}, 1, 0]}},
            "ingreso_planta": {"$sum": {"$cond": [{"$eq": ["$destino_alta", "ingreso_planta"]}, 1, 0]}},
        },
    }},
    {"$project": {
        "_id": 0,
        "grupo_edad": {"$switch": {
            "branches": [
                {"case": {"$eq": ["$_id", 0]},  "then": "0-17"},
                {"case": {"$eq": ["$_id", 18]}, "then": "18-39"},
                {"case": {"$eq": ["$_id", 40]}, "then": "40-64"},
                {"case": {"$eq": ["$_id", 65]}, "then": "65+"},
            ],
            "default": "otros",
        }},
        "orden": "$_id",
        "total": 1,
        "domicilio": 1,
        "ingreso_planta": 1,
        "pct_domicilio": {"$round": [{"$multiply": [{"$divide": ["$domicilio", "$total"]}, 100]}, 2]},
        "pct_ingreso_planta": {"$round": [{"$multiply": [{"$divide": ["$ingreso_planta", "$total"]}, 100]}, 2]},
    }},
    {"$sort": {"orden": 1}},
    {"$project": {"orden": 0}},
]


def destino_alta_por_edad(coll=coleccion_episodios):
    """Devuelve una lista de dicts con el % de domicilio/ingreso_planta por grupo de edad."""
    return list(coll.aggregate(PIPELINE_DESTINO_POR_EDAD))

if __name__ == "__main__":
    print("\n== Estancia media por categoría patológica (min) ==")
    for doc in estancia_media_por_categoria():
        print(doc)

    print("\n== Destino al alta por grupo de edad (%) ==")
    for doc in destino_alta_por_edad():
        print(doc)