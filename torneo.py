import requests
from juego.motor import ResultadoPartida
from main import ejecutar_partida_torneo

URL_TORNEO = "http://127.0.0.1:6000"   # Dirección del servidor_torneo.py

ESCENARIOS = {
    1: "Con obstáculos",
    2: "Caminos múltiples",
    3: "Cuello de botella"
}

def obtener_equipos_online():
    # Consultar el servidor de torneo y filtrar solo los equipos con estado ONLINE

    try:

        r = requests.get(
            f"{URL_TORNEO}/equipos",
            timeout=5
        )

        r.raise_for_status()

        equipos = r.json()

        return [
            e
            for e in equipos
            if e["estado"] == "ONLINE"   # Solo equipos que respondieron al /ping
        ]

    except Exception as e:

        print()
        print("ERROR CONSULTANDO TORNEO")
        print(e)
        print()

        return []


def seleccionar_equipo(
    equipos,
    mensaje
):
    # Leer un número de la consola hasta que sea un índice válido

    while True:

        try:

            opcion = int(input(mensaje))

            if 1 <= opcion <= len(equipos):
                return equipos[opcion - 1]   # Devolver el equipo elegido

        except:
            pass

        print("Opción inválida")


def seleccionar_tamano():
    # Leer el tamaño del laberinto; si es par, ajustar al siguiente impar

    while True:

        try:

            n = int(
                input(
                    "\nTamaño del laberinto (mínimo 5): "
                )
            )

            if n >= 5:

                if n % 2 == 0:
                    n += 1   # El generador requiere tamaño impar

                return n

        except:
            pass

        print("Tamaño inválido")


def seleccionar_escenario():

    print()
    print("Escenarios disponibles:")
    print("1. Con obstáculos")
    print("2. Caminos múltiples")
    print("3. Cuello de botella")

    while True:

        try:

            opcion = int(
                input(
                    "\nSeleccione escenario: "
                )
            )

            if opcion in ESCENARIOS:
                return opcion - 1   # Convertir a índice 0-based que usa el motor

        except:
            pass

        print("Escenario inválido")


def main():

    print()
    print("=" * 40)
    print("TORNEO DE ALGORITMOS")
    print("=" * 40)

    equipos = obtener_equipos_online()

    if len(equipos) < 2:

        print()
        print(
            "Se necesitan al menos "
            "dos equipos ONLINE"
        )
        print()

        return

    print()
    print("Equipos disponibles:")
    print()

    for i, equipo in enumerate(
        equipos,
        start=1
    ):

        print(
            f"{i}. "
            f"{equipo['nombre']} "
            f"({equipo['algoritmo']})"
        )

    print()

    cazador = seleccionar_equipo(
        equipos,
        "Seleccione cazador: "
    )

    presa = seleccionar_equipo(
            equipos,
            "Seleccione presa: "
        )

    tamano = seleccionar_tamano()

    escenario = seleccionar_escenario()

    print()
    print("=" * 40)
    print("PARTIDA CONFIGURADA")
    print("=" * 40)
    print()

    print(
        f"CAZADOR : {cazador['nombre']}"
    )

    print(
        f"PRESA   : {presa['nombre']}"
    )

    print(
        f"TAMAÑO  : {tamano}"
    )

    print(
        f"ESCENARIO : "
        f"{ESCENARIOS[escenario + 1]}"
    )

    print()
    print("Iniciando partida...")
    print()

    # Ejecutar la partida con los agentes remotos seleccionados
    resultado = ejecutar_partida_torneo(
        cazador["url"],
        presa["url"],
        tamano,
        escenario
    )

    if resultado == ResultadoPartida.GANA_CAZADOR:
        print("\nGANADOR: CAZADOR")
    elif resultado == ResultadoPartida.GANA_EVASOR:
        print("\nGANADOR: PRESA")
    else:
        print("\nPartida cancelada o sin resultado")


if __name__ == "__main__":
    main()