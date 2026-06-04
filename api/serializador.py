# api/serializador.py

from agentes.base import EstadoJuego


def estado_a_json(estado: EstadoJuego) -> dict:
    """
    Convierte EstadoJuego a un diccionario JSON serializable.
    """

    return {
        "laberinto": {
            "filas": estado.laberinto.filas,
            "cols": estado.laberinto.cols,
            "grid": estado.laberinto.grid,
            "salidas": [list(s) for s in estado.laberinto.salidas],
        },
        "pos_propia": list(estado.pos_propia),
        "pos_oponente": list(estado.pos_oponente),
        "rol": estado.rol.name,
        "tiempo_restante": estado.tiempo_restante,
        "tick": estado.tick,
    }