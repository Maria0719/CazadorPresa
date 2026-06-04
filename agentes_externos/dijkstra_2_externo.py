"""
Adaptador externo para Dijkstra 2 (greedy_dijkstra).
"""

from __future__ import annotations

from typing import Optional

from agentes.base import Agente, Direccion, EstadoJuego, Rol, Celda, celda_a_direccion
from algoritmos.Dijkstra_2 import greedy_dijkstra


class Dijkstra2Externo(Agente):
    def __init__(self, rol: Rol) -> None:
        super().__init__(rol)
        self._graph: dict[Celda, list[tuple[Celda, int]]] = {}

    def inicializar(self, laberinto, pos_inicial: Celda) -> None:
        self._graph = self._construir_grafo(laberinto)

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        if not self._graph:
            self._graph = self._construir_grafo(estado.laberinto)

        objetivo = self._seleccionar_objetivo(estado)
        if objetivo is None:
            return Direccion.NOOP

        distancias = greedy_dijkstra(self._graph, objetivo)
        siguiente = self._elegir_vecino(estado, distancias)
        if siguiente is None:
            return Direccion.NOOP

        return celda_a_direccion(estado.pos_propia, siguiente)

    def _elegir_vecino(self, estado: EstadoJuego, distancias: dict[Celda, float]) -> Optional[Celda]:
        vecinos = estado.laberinto.vecinos_transitables(estado.pos_propia)
        if not vecinos:
            return None
        return min(vecinos, key=lambda v: distancias.get(v, float("inf")))

    def _seleccionar_objetivo(self, estado: EstadoJuego) -> Optional[Celda]:
        if self.rol == Rol.CAZADOR:
            return estado.pos_oponente
        if not estado.salidas:
            return None
        return min(estado.salidas, key=lambda s: self._dist_manhattan(estado.pos_propia, s))

    @staticmethod
    def _dist_manhattan(a: Celda, b: Celda) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    @staticmethod
    def _construir_grafo(laberinto) -> dict[Celda, list[tuple[Celda, int]]]:
        grafo: dict[Celda, list[tuple[Celda, int]]] = {}
        for f in range(laberinto.filas):
            for c in range(laberinto.cols):
                if not laberinto.es_transitable(f, c):
                    continue
                celda = (f, c)
                vecinos = laberinto.vecinos_transitables(celda)
                grafo[celda] = [(v, 1) for v in vecinos]
        return grafo
