from conexion_mongo import coleccion_episodios
from pprint import pprint

pprint(next(coleccion_episodios.aggregate([{"$sample": {"size": 1}}])))