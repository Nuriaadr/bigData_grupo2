import json
import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pymongo import MongoClient

BASE = Path(__file__).resolve().parent.parent
ruta = next((BASE / "src").glob("admisiones_con_partes*.json"))

load_dotenv(BASE / ".env")

user = quote_plus(os.environ["MONGO_USER"])
password = quote_plus(os.environ["MONGO_PASSWORD"])

client = MongoClient(f"mongodb://{user}:{password}@localhost:27017/?authSource=admin")
db = client["ia_bigdata_db"]
coleccion_admisiones = db["admisiones"]


def cargar_admisiones():
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)

    if isinstance(datos, dict):
        datos = [datos]

    coleccion_admisiones.delete_many({})  # evita duplicados al re-ejecutar
    resultado = coleccion_admisiones.insert_many(datos)
    print(f"Insertados: {len(resultado.inserted_ids)} documentos desde {ruta.name}")


if __name__ == "__main__":
    cargar_admisiones()