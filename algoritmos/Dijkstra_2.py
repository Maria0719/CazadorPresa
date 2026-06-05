import heapq


def recursive_dijkstra(graph, current, visited, distances):
    # Variante recursiva de Dijkstra: procesa el nodo actual y avanza al más cercano

    visited.add(current)   # Marcar el nodo actual como visitado

    for neighbor, weight in graph[current]:

        if neighbor not in visited:

            new_distance = distances[current] + weight

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance   # Relajar distancia si es menor

    # Buscar el nodo no visitado con menor distancia actual
    next_node = None
    min_distance = float("inf")

    for node in graph:

        if node not in visited and distances[node] < min_distance:

            min_distance = distances[node]
            next_node = node   # Candidato más cercano

    if next_node is not None:
        recursive_dijkstra(graph, next_node, visited, distances)   # Recursión


def run_recursive_dijkstra(graph, source):
    # Inicializar distancias: infinito para todos, 0 para el origen
    distances = {node: float("inf") for node in graph}
    distances[source] = 0

    visited = set()

    recursive_dijkstra(graph, source, visited, distances)

    return distances   # Distancias mínimas desde source


# Versión iterativa con cola de prioridad (más eficiente que la recursiva)
def greedy_dijkstra(graph, source):

    distances = {node: float("inf") for node in graph}
    distances[source] = 0

    visited = set()
    priority_queue = [(0, source)]   # (distancia, nodo)

    while priority_queue:

        current_distance, current_node = heapq.heappop(priority_queue)   # Nodo más cercano

        if current_node in visited:
            continue   # Ya procesado con distancia óptima

        visited.add(current_node)

        for neighbor, weight in graph[current_node]:

            distance = current_distance + weight

            if distance < distances[neighbor]:
                distances[neighbor] = distance                          # Actualizar distancia
                heapq.heappush(priority_queue, (distance, neighbor))   # Encolar con nueva distancia

    return distances   # Distancias mínimas desde source