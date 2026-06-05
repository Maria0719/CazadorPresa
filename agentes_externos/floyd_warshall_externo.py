"""
Adaptador externo para Floyd-Warshall.
"""

from __future__ import annotations

from typing import Optional

from agentes.base import Agente, Direccion, EstadoJuego, Rol, Celda, celda_a_direccion
from algoritmos.FloydWarshall import dynamic_floyd_warshall


class FloydWarshallExterno(Agente):
    def __init__(self, rol: Rol) -> None:
        super().__init__(rol)
        self._vertices: list[Celda] = []
        self._indice: dict[Celda, int] = {}
        self._dist: list[list[float]] = []

    def inicializar(self, laberinto, pos_inicial: Celda) -> None:
        # Precomputar todas las distancias mínimas (costoso: O(n^6) en laberinto n×n)
        self._vertices, self._indice = self._construir_vertices(laberinto)
        self._dist = self._construir_matriz(laberinto, self._vertices, self._indice)
        self._dist = dynamic_floyd_warshall(self._dist)   # Llenar tabla de todos los pares

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        if not self._dist:
            self.inicializar(estado.laberinto, estado.pos_propia)   # Lazy init si falta

        objetivo = self._seleccionar_objetivo(estado)
        if objetivo is None:
            return Direccion.NOOP

        objetivo_idx = self._indice.get(objetivo)   # Índice numérico del objetivo en la matriz
        if objetivo_idx is None:
            return Direccion.NOOP

        siguiente = self._elegir_vecino(estado, objetivo_idx)
        if siguiente is None:
            return Direccion.NOOP

        return celda_a_direccion(estado.pos_propia, siguiente)

    def _elegir_vecino(self, estado: EstadoJuego, objetivo_idx: int) -> Optional[Celda]:
        vecinos = estado.laberinto.vecinos_transitables(estado.pos_propia)
        if not vecinos:
            return None
        mejor = None
        mejor_dist = float("inf")
        for v in vecinos:
            idx = self._indice.get(v)
            if idx is None:
                continue
            d = self._dist[idx][objetivo_idx]   # Distancia precomputada desde v al objetivo
            if d < mejor_dist:
                mejor_dist = d
                mejor = v
        return mejor   # Vecino más cercano al objetivo según Floyd-Warshall

    def _seleccionar_objetivo(self, estado: EstadoJuego) -> Optional[Celda]:
        if self.rol == Rol.CAZADOR:
            return estado.pos_oponente   # Cazador: perseguir al oponente
        if not estado.salidas:
            return None
        # Evasor: salida más cercana en distancia Manhattan
        return min(estado.salidas, key=lambda s: self._dist_manhattan(estado.pos_propia, s))

    @staticmethod
    def _dist_manhattan(a: Celda, b: Celda) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    @staticmethod
    def _construir_vertices(laberinto) -> tuple[list[Celda], dict[Celda, int]]:
        # Asignar un índice entero a cada celda transitable (para indexar la matriz)
        vertices: list[Celda] = []
        indice: dict[Celda, int] = {}
        for f in range(laberinto.filas):
            for c in range(laberinto.cols):
                if not laberinto.es_transitable(f, c):
                    continue
                celda = (f, c)
                indice[celda] = len(vertices)   # Índice = posición en la lista
                vertices.append(celda)
        return vertices, indice

    @staticmethod
    def _construir_matriz(laberinto, vertices: list[Celda], indice: dict[Celda, int]) -> list[list[float]]:
        n = len(vertices)
        dist = [[float("inf") for _ in range(n)] for _ in range(n)]   # inf = sin camino
        for i in range(n):
            dist[i][i] = 0.0   # Distancia a sí mismo es 0
        for celda in vertices:
            i = indice[celda]
            for v in laberinto.vecinos_transitables(celda):
                j = indice.get(v)
                if j is not None:
                    dist[i][j] = 1.0   # Aristas de peso 1 (pasos unitarios)
        return dist
