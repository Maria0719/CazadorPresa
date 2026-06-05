import heapq

def greedy_best_first_search(graph, heuristic, start, goal):
    # Greedy Best-First Search: expande siempre el nodo con menor heurística.
    # No garantiza camino óptimo, pero es rápido en la práctica.

    visited = set()
    priority_queue = []

    # Encolar el inicio con su valor heurístico
    heapq.heappush(priority_queue, (heuristic[start], start, [start]))

    while priority_queue:

        h, current, path = heapq.heappop(priority_queue)   # Nodo con menor h

        if current == goal:
            return path   # Camino encontrado

        if current not in visited:
            visited.add(current)   # Marcar como visitado

            for neighbor, cost in graph[current]:
                if neighbor not in visited:
                    heapq.heappush(
                        priority_queue,
                        # Prioridad solo por heurística (greedy: ignora costo acumulado)
                        (heuristic[neighbor], neighbor, path + [neighbor])
                    )

    return None   # No se encontró camino