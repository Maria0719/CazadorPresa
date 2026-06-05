import heapq

class Nodo:
    def __init__(self, posicion):
        self.posicion = posicion
        self.g = 0       # Costo desde el inicio hasta este nodo
        self.h = 0       # Heurística: estimación de costo hasta el objetivo
        self.f = 0       # f = g + h (costo total estimado)
        self.padre = None  # Nodo predecesor para reconstruir el camino

    def __lt__(self, otro):
        return self.f < otro.f   # Comparación por f para la cola de prioridad


def heuristica(a, b):
    # Distancia Manhattan: suma de diferencias absolutas en filas y columnas
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def reconstruir_camino(nodo):
    camino = []

    while nodo:
        camino.append(nodo.posicion)
        nodo = nodo.padre   # Recorrer hacia atrás siguiendo los padres

    return camino[::-1]   # Invertir para obtener el camino de inicio a fin


def a_estrella(laberinto, inicio, objetivo):

    abiertos = []    # Cola de prioridad (min-heap) con nodos por explorar
    cerrados = set() # Conjunto de posiciones ya procesadas

    nodo_inicio = Nodo(inicio)
    nodo_objetivo = Nodo(objetivo)

    heapq.heappush(abiertos, nodo_inicio)   # Agregar nodo inicial a la cola

    while abiertos:

        actual = heapq.heappop(abiertos)   # Extraer nodo con menor f

        if actual.posicion == nodo_objetivo.posicion:
            return reconstruir_camino(actual)   # Objetivo alcanzado

        cerrados.add(actual.posicion)   # Marcar como procesado

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
                continue   # Fuera de los límites del laberinto

            if laberinto[fila][columna] == 1:
                continue   # Celda bloqueada (pared)

            vecino_pos = (fila, columna)

            if vecino_pos in cerrados:
                continue   # Ya fue procesado: ignorar

            vecino = Nodo(vecino_pos)

            vecino.g = actual.g + 1                         # Costo acumulado +1 paso
            vecino.h = heuristica(vecino_pos, objetivo)     # Estimación al objetivo
            vecino.f = vecino.g + vecino.h                  # Costo total estimado
            vecino.padre = actual                           # Registrar predecesor

            heapq.heappush(abiertos, vecino)   # Encolar para explorar

    return None   # No existe camino al objetivo

