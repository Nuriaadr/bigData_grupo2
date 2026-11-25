import json
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pymongo import MongoClient

BASE = Path(__file__).resolve().parent.parent
RUTA_JSON= BASE / "data" / "admisiones_con_partes_clinicos.json"

#Las variables del entorno tienen prioridad
load_dotenv(BASE /"Docker"/ ".env")

user = quote_plus(os.environ["MONGO_USER"])
password = quote_plus(os.environ["MONGO_PASSWORD"])

host = os.getenv("MONGO_HOST", "mongo")
port = int(os.getenv("MONGO_PORT", "27017"))

#este es el unico cliente, el resto de los modulos deben importarlo desde aqui
client = MongoClient(f"mongodb://{user}:{password}@{host}:{port}/?authSource=admin")

db = client[os.getenv("MONGO_DB", "ia_bigdata_db")]
coleccion_episodios = db["episodios_urgencias"]

def comprobar_conexion():
    #Comprueba que MongoDB responde.
    client.admin.command("ping")
    print("Conexión con MongoDB correcta.")

def cargar_admisiones():
    #Carga el historico borrando los registros existentes y cargando los del json
    
    with RUTA_JSON.open(encoding="utf-8") as f:
        datos = json.load(f)

    if isinstance(datos, dict):
        datos = [datos]

    coleccion_episodios.delete_many({})  # evita duplicados al re-ejecutar
    resultado = coleccion_episodios.insert_many(datos)
    print(f"Insertados: {len(resultado.inserted_ids)} documentos desde {RUTA_JSON.name}")


if __name__ == "__main__":
    cargar_admisiones()