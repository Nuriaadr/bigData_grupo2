from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["ia_bigdata_db"]

bd_grupo2 = db["bigdata_grupo2"]