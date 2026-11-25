import subprocess
import sys
from pathlib import Path


SRC = Path(__file__).resolve().parent


def ejecutar_script(nombre_archivo):
    """
    Ejecuta un archivo de la carpeta src.

    Devuelve True si termina correctamente.
    Devuelve False si falla o se interrumpe.
    """
    ruta = SRC / nombre_archivo

    if not ruta.is_file():
        print(f"\n[ERROR] No se encuentra el archivo: {ruta.name}")
        return False

    print(f"\nEjecutando {nombre_archivo}...\n")

    try:
        resultado = subprocess.run(
            [sys.executable, "-u", str(ruta)],
            cwd=SRC,
            check=False
        )

    except KeyboardInterrupt:
        print("\nEjecución interrumpida. Volviendo al menú.")
        return False

    except OSError as error:
        print(f"\n[ERROR] No se pudo ejecutar el archivo: {error}")
        return False

    if resultado.returncode != 0:
        print(
            f"\n[ERROR] {nombre_archivo} terminó "
            f"con código {resultado.returncode}."
        )
        return False

    return True


def menu_historico():
    """Permite consultar el histórico o volver al menú principal."""
    while True:
        print("\n" + "=" * 50)
        print("CONSULTAS DEL HISTÓRICO")
        print("=" * 50)
        print("1. Realizar consultas")
        print("2. Volver al menú principal")

        opcion = input("\nSelecciona una opción: ").strip()

        if opcion == "1":
            ejecutar_script("consultas_mongo.py")

        elif opcion == "2":
            return

        else:
            print("\nOpción no válida. Selecciona 1 o 2.")


def cargar_historico():
    """
    Ejecuta la preparación y carga del histórico en orden.

    La carga en MongoDB borra los episodios existentes.
    """
    print("\nEsta opción ejecutará:")
    print("1. carga_csv.py")
    print("2. unir_csv_json.py")
    print("3. conexion_mongo.py")

    print(
        "\nATENCIÓN: la carga en MongoDB borrará todos los "
        "documentos actuales de episodios_urgencias "
        "y los sustituirá por el histórico."
    )

    confirmacion = input(
        "\nEscribe SI para continuar: "
    ).strip().upper()

    if confirmacion != "SI":
        print("\nCarga cancelada.")
        return False

    archivos = [
        "carga_csv.py",
        "unir_csv_json.py",
        "conexion_mongo.py"
    ]

    for nombre_archivo in archivos:
        correcto = ejecutar_script(nombre_archivo)

        if not correcto:
            print(
                "\nNo se ha completado la carga del histórico. "
                "No se ejecutarán los pasos restantes."
            )
            return False

    print("\nHistórico cargado correctamente.")

    return True


def gestionar_urgencias():
    """Inicia el servicio de la API y Redis."""
    print("\nIniciando la gestión de urgencias...")
    print("Pulsa Ctrl+C para detener el servicio y volver al menú.")

    ejecutar_script("urgencias.py")


def main():
    # Solo se habilita urgencias tras completar los tres pasos
    # durante esta ejecución de app.py.
    historico_cargado = False

    try:
        while True:
            print("\n" + "=" * 50)
            print("GESTIÓN DE URGENCIAS")
            print("=" * 50)

            if historico_cargado:
                print("Estado: histórico cargado en esta sesión.")
            else:
                print("Estado: carga del histórico pendiente.")

            print("\n1. Reiniciar y cargar histórico")

            if historico_cargado:
                print("2. Gestionar urgencias")
            else:
                print("2. Gestionar urgencias [NO DISPONIBLE]")

            print("3. Salir")

            opcion = input("\nSelecciona una opción: ").strip()

            if opcion == "1":
                carga_correcta = cargar_historico()

                if carga_correcta:
                    historico_cargado = True
                    menu_historico()

            elif opcion == "2":
                if not historico_cargado:
                    print(
                        "\nPrimero debes seleccionar la opción 1 "
                        "y completar la preparación y carga "
                        "del histórico."
                    )
                    continue

                gestionar_urgencias()

            elif opcion == "3":
                print("\nAplicación finalizada.")
                break

            else:
                print("\nOpción no válida. Selecciona 1, 2 o 3.")

    except (KeyboardInterrupt, EOFError):
        print("\nAplicación finalizada.")


if __name__ == "__main__":
    main()