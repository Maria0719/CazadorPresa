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
            "grid": estado.laberinto.grid,          # Matriz 2D completa del laberinto
            "salidas": [list(s) for s in estado.laberinto.salidas],  # Tuplas → listas
        },
        "pos_propia": list(estado.pos_propia),       # Tupla → lista para JSON
        "pos_oponente": list(estado.pos_oponente),
        "rol": estado.rol.name,                      # Enum → string ("CAZADOR"/"PRESA")
        "tiempo_restante": estado.tiempo_restante,
        "tick": estado.tick,
    }