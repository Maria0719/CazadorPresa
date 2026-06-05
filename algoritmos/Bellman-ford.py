def bellman_ford(vertices, aristas, origen):

    distancia = {}

    # Inicializar todas las distancias en infinito
    for v in vertices:
        distancia[v] = float("inf")

    distancia[origen] = 0   # La distancia al origen es 0

    # Relajar todas las aristas V-1 veces (garantiza convergencia sin ciclos negativos)
    for _ in range(len(vertices) - 1):

        for u, v, peso in aristas:

            # Si encontramos un camino más corto hacia v, actualizar
            if distancia[u] != float("inf") and distancia[u] + peso < distancia[v]:

                distancia[v] = distancia[u] + peso

    # Verificar ciclos negativos: si aún se puede relajar, existe ciclo negativo
    for u, v, peso in aristas:

        if distancia[u] != float("inf") and distancia[u] + peso < distancia[v]:

            print("Existe un ciclo negativo")
            return None   # Resultado no válido con ciclos negativos

    return distancia   # Distancias mínimas desde el origen


