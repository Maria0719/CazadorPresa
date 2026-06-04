import heapq

def greedy_best_first_search(graph, heuristic, start, goal):

    visited = set()
    priority_queue = []

    heapq.heappush(priority_queue, (heuristic[start], start, [start]))

    while priority_queue:

        h, current, path = heapq.heappop(priority_queue)

        if current == goal:
            return path

        if current not in visited:
            visited.add(current)

            for neighbor, cost in graph[current]:
                if neighbor not in visited:
                    heapq.heappush(
                        priority_queue,
                        (heuristic[neighbor], neighbor, path + [neighbor])
                    )

    return None