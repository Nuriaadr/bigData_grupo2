# Gestión de urgencias hospitalarias

Aplicación Python en Docker para cargar un histórico, consultar episodios en MongoDB y gestionar ingresos y altas desde una API mediante Redis.

## Tecnologías

Python, Pandas, MongoDB 7, Redis 7 Alpine y Docker Compose.

## Estructura

```text
.
├── README.md
├── requirements.txt
├── Docker/
│   ├── .env
│   ├── Dockerfile
│   └── docker-compose.yml
├── data/
└── src/
    ├── app.py
    ├── carga_csv.py
    ├── unir_csv_json.py
    ├── conexion_mongo.py
    ├── consultas_mongo.py
    └── urgencias.py
```

## Configuración

Crear `Docker/.env` con las credenciales configuradas para MongoDB:

```env
MONGO_USER=tu_usuario
MONGO_PASSWORD=tu_contrasena
MONGO_HOST=mongo
MONGO_PORT=27017
MONGO_DB=ia_bigdata_db

REDIS_HOST=redis
REDIS_PORT=6379
```

Dependencias de `requirements.txt`:

```text
pandas
pymongo
redis
python-dotenv
requests
```

Los archivos de entrada del histórico deben estar en `data/`, con los nombres esperados por los scripts.

## Arranque

Ejecutar desde la raíz del proyecto:

```bash
docker compose --env-file Docker/.env -f Docker/docker-compose.yml up -d --build
```

Iniciar la aplicación:

```bash
docker compose --env-file Docker/.env -f Docker/docker-compose.yml exec python-app python app.py
```

## Menú

### 1. Reiniciar y cargar histórico

Ejecuta en orden:

1. `carga_csv.py`: prepara el CSV.
2. `unir_csv_json.py`: une el CSV limpio con los partes clínicos mediante `id_episodio`.
3. `conexion_mongo.py`: carga el resultado en `ia_bigdata_db.episodios_urgencias`.

Atención: esta opción borra todos los documentos existentes de la colección antes de cargar el histórico. No reinicia Redis.

Después permite realizar consultas o volver al menú principal.

Las consultas muestran:

- Estancia media en minutos por categoría patológica.
- Porcentaje de altas a domicilio e ingresos en planta por grupo de edad.

Estas consultas están preparadas para el histórico.

### 2. Gestionar urgencias

Disponible después de completar la carga del histórico en la sesión actual.

Consulta la API con una pausa de 5 segundos entre ciclos:

```text
http://10.201.59.248:28000/api/v1/urgencias/novedades
```

Redis almacena:

- Pacientes activos: `paciente:{id_episodio}`.
- Cola de espera: `urgencias:cola_espera`.
- Cinco boxes: `box:1` a `box:5`.

La cola utiliza prioridad EDF, atendiendo primero al paciente con menor límite de espera:

```text
deadline = timestamp_llegada + tiempo_max_espera_min × 60
```

Al recibir un alta, guarda el episodio completo en MongoDB, elimina al paciente de Redis, libera su box y asigna el siguiente paciente.

Se asume que cada alta tiene un ingreso previo registrado.

Pulsar `Ctrl+C` para detener el servicio y volver al menú.

### 3. Salir

Finaliza la aplicación sin detener los contenedores.

## Consideraciones

- Ejecutar una sola instancia del servicio de urgencias.
- La API no repite novedades: evitar consultas manuales mientras funciona la aplicación.
- No se implementa recuperación automática de eventos ante fallos.
- Los boxes existentes no se vacían al iniciar el servicio.
- Al reiniciar `app.py`, se solicita de nuevo la carga del histórico.
- No publicar el archivo `.env` con credenciales reales.

## Detener los servicios

```bash
docker compose --env-file Docker/.env -f Docker/docker-compose.yml stop
```

Si se modifican las dependencias, reconstruir el servicio Python:

```bash
docker compose --env-file Docker/.env -f Docker/docker-compose.yml up -d --build python-app
```