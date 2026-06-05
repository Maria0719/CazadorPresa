from collections import deque
import math

# PROCEDIMIENTO AUXILIAR

def vecinos(tablero, x, y):
    # Devuelve las celdas adyacentes (4-vecindad) que son transitables

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

        if tablero.es_valida(nx, ny):   # Solo celdas dentro del tablero y transitables

            lista_vecinos.append((nx, ny))

    return lista_vecinos


# ALGORITMO PRINCIPAL

def construir_mps(tablero, destino):
    # BFS desde el destino hacia atrás: llena dp[x][y] = pasos mínimos para llegar al destino

    n = tablero.n
    dp = [
        [math.inf for _ in range(n)]   # Inicializar todos los costos en infinito
        for _ in range(n)
    ]

    x_destino, y_destino = destino
    dp[x_destino][y_destino] = 0   # Costo 0 en el destino
    cola = deque()
    cola.append(destino)

    while cola:
        x, y = cola.popleft()

        for nx, ny in vecinos(tablero, x, y):
            costo = dp[x][y] + 1   # Cada paso tiene costo 1

            if costo < dp[nx][ny]:
                dp[nx][ny] = costo   # Actualizar si encontramos camino más corto
                cola.append((nx, ny))

    return dp   # Tabla de costos mínimos desde cada celda al destino

def reconstruir_camino(
        tablero,
        dp,
        inicio
):
    # Sigue la pendiente descendente en dp desde inicio hasta dp==0 (el destino)

    camino = []

    x, y = inicio

    camino.append((x, y))

    movimientos = [

        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1)

    ]

    while dp[x][y] != 0:   # Avanzar hasta llegar al destino (costo 0)

        mejor = None

        mejor_costo = dp[x][y]

        for dx, dy in movimientos:

            nx = x + dx
            ny = y + dy

            if tablero.es_valida(nx, ny):

                if dp[nx][ny] < mejor_costo:   # Vecino más cercano al destino

                    mejor_costo = dp[nx][ny]
                    mejor = (nx, ny)

        if mejor is None:
            break   # Sin vecinos válidos: detener

        x, y = mejor

        camino.append((x, y))

    return camino   # Lista de celdas desde inicio hasta el destino