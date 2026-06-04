import heapq


def recursive_dijkstra(graph, current, visited, distances):

    visited.add(current)

    for neighbor, weight in graph[current]:

        if neighbor not in visited:

            new_distance = distances[current] + weight

            if new_distance < distances[neighbor]:

                distances[neighbor] = new_distance

    next_node = None
    min_distance = float("inf")

    for node in graph:

        if node not in visited and distances[node] < min_distance:

            min_distance = distances[node]
            next_node = node

    if next_node is not None:

        recursive_dijkstra(graph, next_node, visited, distances)


def run_recursive_dijkstra(graph, source):


    distances = {node: float("inf") for node in graph}
    distances[source] = 0

    visited = set()

    recursive_dijkstra(graph, source, visited, distances)

    return distances



# cola de prioridad)


def greedy_dijkstra(graph, source):
 
    distances = {node: float("inf") for node in graph}
    distances[source] = 0

    visited = set()
    priority_queue = [(0, source)]

    while priority_queue:

        current_distance, current_node = heapq.heappop(priority_queue)

        if current_node in visited:
            continue

        visited.add(current_node)

        for neighbor, weight in graph[current_node]:

            distance = current_distance + weight

            if distance < distances[neighbor]:

                distances[neighbor] = distance
                heapq.heappush(priority_queue, (distance, neighbor))

    return distances