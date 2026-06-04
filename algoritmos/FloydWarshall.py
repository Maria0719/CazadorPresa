

def recursive_floyd_warshall(matrix, i, j, k):
 

    if k < 0:
        return matrix[i][j]

    without_k = recursive_floyd_warshall(matrix, i, j, k - 1)

    with_k = (
        recursive_floyd_warshall(matrix, i, k, k - 1)
        + recursive_floyd_warshall(matrix, k, j, k - 1)
    )

    return min(without_k, with_k)




def dynamic_floyd_warshall(matrix):

    n = len(matrix)

    dist = [row[:] for row in matrix]

    for k in range(n):
        for i in range(n):
            for j in range(n):

                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])

    return dist