def bellman_ford(vertices, aristas, origen):

    distancia = {}

    for v in vertices:
        distancia[v] = float("inf")

    distancia[origen] = 0

    for _ in range(len(vertices) - 1):

        for u, v, peso in aristas:

            if distancia[u] != float("inf") and distancia[u] + peso < distancia[v]:

                distancia[v] = distancia[u] + peso

    for u, v, peso in aristas:

        if distancia[u] != float("inf") and distancia[u] + peso < distancia[v]:

            print("Existe un ciclo negativo")
            return None

    return distancia


