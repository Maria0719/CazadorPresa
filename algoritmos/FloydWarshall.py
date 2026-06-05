

def recursive_floyd_warshall(matrix, i, j, k):
    # Versión recursiva top-down: distancia mínima de i a j usando nodos intermedios 0..k

    if k < 0:
        return matrix[i][j]   # Caso base: distancia directa sin intermediarios

    without_k = recursive_floyd_warshall(matrix, i, j, k - 1)   # Camino sin pasar por k

    with_k = (
        recursive_floyd_warshall(matrix, i, k, k - 1)   # Camino de i a k
        + recursive_floyd_warshall(matrix, k, j, k - 1) # Camino de k a j
    )

    return min(without_k, with_k)   # Elegir el camino más corto




def dynamic_floyd_warshall(matrix):
    # Versión iterativa bottom-up: O(n³), considera cada nodo k como intermediario

    n = len(matrix)

    dist = [row[:] for row in matrix]   # Copiar la matriz original

    for k in range(n):           # Para cada nodo intermediario k
        for i in range(n):       # Para cada origen i
            for j in range(n):   # Para cada destino j
                # Si pasar por k es más corto, actualizar distancia i→j
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])

    return dist   # Matriz de distancias mínimas entre todos los pares