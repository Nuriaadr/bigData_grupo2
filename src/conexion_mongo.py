from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["bigdata_grupo2"]

coleccion = db["urgencias"]