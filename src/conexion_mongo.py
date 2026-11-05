from datetime import datetime
from pymongo import MongoClient

uri = "mongodb://root:secret@127.0.0.1/"

client = MongoClient(uri)

# 2. Seleccionar (o referenciar para crear) la base de datos
db = client["ia_bigdata_db"]

# 3. Seleccionar (o referenciar para crear) la colección
coleccion_sensores = db["lecturas_iot"]


# Insertar un único documento: insert_one()
lectura = {
    "sensor_id": "TEMP-01",
    "zona": "Sala Servidores",
    "temperatura": 24.5,
    "humedad": 45,
    "alertas": ["revision_anual"],
    "ubicacion": {"planta": 1, "rack": "A2"}, # Subdocumento anidado
    "fecha": datetime.now()
}

resultado = coleccion_sensores.insert_one(lectura)
