from conexion_mongo import coleccion_admisiones
from pprint import pprint

pprint(next(coleccion_admisiones.aggregate([{"$sample": {"size": 1}}])))