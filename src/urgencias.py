import json
import os
import time 

import requests
import redis

from conexion_mongo import coleccion_episodios, comprobar_conexion


API_URL = "http://10.201.59.248:28000/api/v1/urgencias/novedades"
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

NUM_BOXES = 5
INTERVALO_SEGUNDOS = 5

COLA="urgencias:cola_espera"

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def inicializar_boxes():
    #Crea los boxes
    for i in range(1, NUM_BOXES + 1):
        clave = f"box:{i}"
        if not r.exists(clave):
            r.hset(clave, mapping={
                "id_episodio": "",
                "timestamp_entrada": ""
            })


def boxes_libres():
    #devuelve los boxes libres
    libres = []

    for i in range(1, NUM_BOXES + 1):
        ocupante = r.hget(f"box:{i}", "id_episodio")

        if not ocupante:
            libres.append(i)

    return libres


def calcular_deadline(paciente):
    #Calcula el limite de espera en segundos epoch
    llegada = float(paciente["datos_admision"]["timestamp_llegada"])
    espera_max = float(paciente["datos_triaje"]["tiempo_max_espera_min"])

    return llegada + (espera_max * 60)


def registrar_nuevo_paciente(paciente):
    #Guarda el paciente en Redis y lo añade a la cola de espera
    id_episodio = str(paciente["id_episodio"])
   
    if r.exists(f"paciente:{id_episodio}"):
        print(f"[AVISO] {id_episodio} ya esta registrado en Redis")
        return

    deadline = calcular_deadline(paciente)

    with r.pipeline(transaction=True) as operaciones:
        operaciones.set(
            f"paciente:{id_episodio}",
            json.dumps(paciente, ensure_ascii=False)
        )
        operaciones.zadd(COLA, {id_episodio: deadline})
        operaciones.execute()


    print(
        f"[COLA] {id_episodio} añadido. "
        f"Nivel {paciente['datos_triaje']['nivel_manchester']} | "
        f"Deadline {deadline}"
    )


def asignar_paciente_a_box(id_box):
    #Asigna al box libre el paciente con menor deadline.
    clave_box = f"box:{id_box}"

    if r.hget(clave_box, "id_episodio"):
        return

    candidatos = r.zrange(
        COLA,
        0,
        0,
        withscores=True
    )

    if not candidatos:
        return

    id_episodio, deadline = candidatos[0]
    documento = r.get(f"paciente:{id_episodio}")

    if documento is None:
        raise RuntimeError(
            f"El episodio {id_episodio} está en la cola "
            "pero no tiene datos en Redis"
        )

    paciente = json.loads(documento)

    with r.pipeline(transaction=True) as operaciones:
        operaciones.zrem(COLA, id_episodio)
        operaciones.hset(
            clave_box,
            mapping={
                "id_episodio": id_episodio,
                "timestamp_entrada": time.time()
            }
        )
        operaciones.execute()

    print(
        f"[BOX {id_box}] Asignado {id_episodio} | "
        f"Deadline: {deadline} | "
        f"Triaje: {paciente['datos_triaje']['color']}"
    )


def intentar_asignar_pendientes():
    #Ocupa los boxes libres mientras haya pacientes esperando
    for id_box in boxes_libres():
        asignar_paciente_a_box(id_box)


def procesar_alta(alta):
    #Guarda el episodio con el alta en MongoDB y libera los recursos en Redis
    id_episodio = str(alta["id_episodio"])

    documento = r.get(f"paciente:{id_episodio}")

    if documento is None:
        print(
            f"[AVISO] Alta recibida del episodio {id_episodio}, "
            "pero no está registrado en Redis. Se ignora el alta."
        )
        return

    paciente = json.loads(documento)

    documento_mongo = {
        **paciente,
        "timestamp_alta": alta["timestamp_alta"],
        "fecha_hora_alta": alta["fecha_hora_alta"],
        "destino_alta": alta["destino_alta"]
    }

    #Primero se guarda en MongoDB
    #Si falla, no se elimina el paciente de Redis
    coleccion_episodios.insert_one(documento_mongo)

    box_liberado = None

    for i in range(1, NUM_BOXES + 1):
        ocupante = r.hget(f"box:{i}", "id_episodio")

        if ocupante == id_episodio:
            box_liberado = i
            break

    with r.pipeline(transaction=True) as operaciones:
        if box_liberado is not None:
            operaciones.hset(
                f"box:{box_liberado}",
                mapping={
                    "id_episodio": "",
                    "timestamp_entrada": ""
                }
            )

        operaciones.delete(f"paciente:{id_episodio}")
        operaciones.zrem(COLA, id_episodio)
        operaciones.execute()

    print(
        f"[ALTA] {id_episodio} dado de alta y guardado en MongoDB | "
        f"Destino: {alta['destino_alta']} | "
        f"Box liberado: {box_liberado}"
    )

    if box_liberado is not None:
        asignar_paciente_a_box(box_liberado)


def procesar_respuesta(datos):
    #Procesa primero los ingresos y despues las altas
    for paciente in datos.get("nuevos_ingresos", []):
        registrar_nuevo_paciente(paciente)

    for alta in datos.get("pacientes_alta", []):
        procesar_alta(alta)

    intentar_asignar_pendientes()


def main():
    try:
        comprobar_conexion()

        r.ping()
        print("Conexión con Redis correcta.")

        inicializar_boxes()

        print("Servicio de urgencias iniciado.")
        print("Pulsa Ctrl+C para detenerlo.")

        with requests.Session() as sesion:
            while True:
                try:
                    respuesta = sesion.get(
                        API_URL,
                        timeout=10
                    )
                    respuesta.raise_for_status()

                    datos = respuesta.json()
                    procesar_respuesta(datos)

                except requests.RequestException as error:
                    print(f"[ERROR API] {error}")
                    print(
                        "Si la API ya consumió las novedades, "
                        "podrían no recuperarse en la siguiente consulta."
                    )

                time.sleep(INTERVALO_SEGUNDOS)

    except KeyboardInterrupt:
        print("\nServicio de urgencias detenido.")

    except Exception as error:
        print(f"[ERROR] Servicio detenido: {error}")
        print(
            "Revisa el error antes de reiniciar. "
            "Las novedades recibidas no se reintentan automáticamente."
        )
        raise

    finally:
        r.close()


if __name__ == "__main__":
    main()