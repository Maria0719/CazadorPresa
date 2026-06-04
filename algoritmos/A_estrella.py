import heapq

class Nodo:
    def __init__(self, posicion):
        self.posicion = posicion
        self.g = 0
        self.h = 0
        self.f = 0
        self.padre = None

    def __lt__(self, otro):
        return self.f < otro.f


def heuristica(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def reconstruir_camino(nodo):
    camino = []

    while nodo:
        camino.append(nodo.posicion)
        nodo = nodo.padre

    return camino[::-1]


def a_estrella(laberinto, inicio, objetivo):

    abiertos = []
    cerrados = set()

    nodo_inicio = Nodo(inicio)
    nodo_objetivo = Nodo(objetivo)

    heapq.heappush(abiertos, nodo_inicio)

    while abiertos:

        actual = heapq.heappop(abiertos)

        if actual.posicion == nodo_objetivo.posicion:
            return reconstruir_camino(actual)

        cerrados.add(actual.posicion)

        movimientos = [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0)
        ]

        for dx, dy in movimientos:

            fila = actual.posicion[0] + dx
            columna = actual.posicion[1] + dy

            if (
                fila < 0 or fila >= len(laberinto) or
                columna < 0 or columna >= len(laberinto[0])
            ):
                continue

            if laberinto[fila][columna] == 1:
                continue

            vecino_pos = (fila, columna)

            if vecino_pos in cerrados:
                continue

            vecino = Nodo(vecino_pos)

            vecino.g = actual.g + 1
            vecino.h = heuristica(vecino_pos, objetivo)
            vecino.f = vecino.g + vecino.h
            vecino.padre = actual

            heapq.heappush(abiertos, vecino)

    return None

