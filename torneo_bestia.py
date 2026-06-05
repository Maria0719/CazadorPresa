import requests
from juego.motor import ResultadoPartida
from main import ejecutar_partida_torneo
from torneo import seleccionar_escenario, seleccionar_tamano, ESCENARIOS

URL_TORNEO = "http://127.0.0.1:6000"   # Dirección del servidor de torneo


def obtener_equipos_online():
    # Obtener equipos online sin manejo de errores (lanza excepción si el torneo no responde)

    r = requests.get(
        f"{URL_TORNEO}/equipos",
        timeout=5
    )

    r.raise_for_status()

    return [
        e
        for e in r.json()
        if e["estado"] == "ONLINE"   # Solo equipos con servidor activo
    ]


def seleccionar_equipo(
    equipos,
    mensaje
):
    # Devuelve el ÍNDICE del equipo elegido (a diferencia de torneo.py que devuelve el objeto)

    while True:

        try:

            opcion = int(
                input(mensaje)
            )

            if 1 <= opcion <= len(equipos):
                return opcion - 1   # Índice 0-based

        except:
            pass

        print("Opción inválida")


def main():

    print()
    print("=" * 50)
    print("TORNEO MODO BESTIA")
    print("=" * 50)

    equipos = obtener_equipos_online()

    if len(equipos) < 2:

        print(
            "Se necesitan mínimo "
            "2 equipos online"
        )

        return

    print()

    for i, equipo in enumerate(
        equipos,
        start=1
    ):

        print(
            f"{i}. "
            f"{equipo['nombre']}"
        )

    print()

    indice_bestia = seleccionar_equipo(
        equipos,
        "Seleccione la bestia inicial: "
    )

    bestia = equipos.pop(
        indice_bestia   # Sacar la bestia inicial de la lista de retadores
    )

    cola = equipos   # Los equipos restantes son los retadores en orden

    print()
    print(
        f"BESTIA INICIAL: "
        f"{bestia['nombre']}"
    )

    tamano = seleccionar_tamano()

    escenario = seleccionar_escenario()

    print()
    print(
        f"TAMAÑO  : {tamano}"
    )

    print(
        f"ESCENARIO : "
        f"{ESCENARIOS[escenario + 1]}"
    )

    print()

    while cola:

        retador = cola.pop(0)   # Siguiente retador en la cola (FIFO)

        print("=" * 50)
        print(
            f"{bestia['nombre']}"
            f" VS "
            f"{retador['nombre']}"
        )
        print("=" * 50)

        # La bestia siempre juega como CAZADOR; el retador como PRESA
        print()
        print(f"BESTIA ACTUAL  : {bestia['nombre']} (CAZADOR)")
        print(f"RETADOR ACTUAL : {retador['nombre']} (PRESA)")

        resultado = ejecutar_partida_torneo(
            bestia["url"],    # Cazador = bestia vigente
            retador["url"],   # Presa = retador
            tamano,
            escenario,
        )

        if resultado == ResultadoPartida.GANA_CAZADOR:
            ganador = bestia   # La bestia defiende su título
        elif resultado == ResultadoPartida.GANA_EVASOR:
            ganador = retador  # El retador derrota a la bestia
        else:
            print("\nPartida cancelada o sin resultado")
            break

        print(f"GANADOR        : {ganador['nombre']}")

        if ganador is retador:
            bestia = retador   # El retador toma el trono
            print(f"NUEVA BESTIA   : {bestia['nombre']}")
        else:
            print(f"NUEVA BESTIA   : {bestia['nombre']}")

        print()

    print("=" * 50)
    print("TORNEO FINALIZADO")
    print("=" * 50)

    print()

    print(
        "CAMPEÓN:"
    )

    print(
        bestia['nombre']
    )


if __name__ == "__main__":
    main()