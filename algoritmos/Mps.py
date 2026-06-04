from collections import deque
import math

# PROCEDIMIENTO AUXILIAR

def vecinos(tablero, x, y):

    movimientos = [

        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1)
    ]

    lista_vecinos = []

    for dx, dy in movimientos:

        nx = x + dx
        ny = y + dy

        if tablero.es_valida(nx, ny):

            lista_vecinos.append((nx, ny))

    return lista_vecinos


# ALGORITMO PRINCIPAL

def construir_mps(tablero, destino):

    n = tablero.n
    dp = [
        [math.inf for _ in range(n)]
        for _ in range(n)
    ]

    x_destino, y_destino = destino
    dp[x_destino][y_destino] = 0
    cola = deque()
    cola.append(destino)

    while cola:
        x, y = cola.popleft()

        for nx, ny in vecinos(tablero, x, y):
            costo = dp[x][y] + 1

            if costo < dp[nx][ny]:

                dp[nx][ny] = costo
                cola.append((nx, ny))

    return dp

def reconstruir_camino(
        tablero,
        dp,
        inicio
):

    camino = []

    x, y = inicio

    camino.append((x, y))

    movimientos = [

        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1)

    ]

    while dp[x][y] != 0:

        mejor = None

        mejor_costo = dp[x][y]

        for dx, dy in movimientos:

            nx = x + dx
            ny = y + dy

            if tablero.es_valida(nx, ny):

                if dp[nx][ny] < mejor_costo:

                    mejor_costo = dp[nx][ny]
                    mejor = (nx, ny)

        if mejor is None:
            break

        x, y = mejor

        camino.append((x, y))

    return camino