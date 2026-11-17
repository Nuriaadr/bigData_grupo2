import os
from pathlib import Path
from dotenv import dotenv_values
from pymongo import MongoClient
from urllib.parse import quote_plus

BASE = Path(__file__).resolve().parent.parent
ruta_env = BASE / ".env"
print(".env existe:", ruta_env.exists(), "->", ruta_env)

v = dotenv_values(ruta_env)
print("usuario en .env:       ", repr(v.get("MONGO_USER")))
print("usuario en el entorno: ", repr(os.environ.get("MONGO_USER")))
pw = v.get("MONGO_PASSWORD") or ""
print("longitud pwd en .env:  ", len(pw), "| espacios en extremos:", pw != pw.strip())
print("longitud pwd entorno:  ", len(os.environ.get("MONGO_PASSWORD") or ""))

try:
    c = MongoClient(
        f"mongodb://{quote_plus(v['MONGO_USER'])}:{quote_plus(pw)}@localhost:27017/?authSource=admin",
        serverSelectionTimeoutMS=3000,
    )
    c.admin.command("ping")
    print("Conexión con los valores del .env: OK")
except Exception as e:
    print("Conexión con los valores del .env: FALLA ->", type(e).__name__)