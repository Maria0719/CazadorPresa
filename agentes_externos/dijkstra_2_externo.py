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
        self._graph = self._construir_grafo(laberinto)   # Pre-construir grafo al inicio

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        if not self._graph:
            self._graph = self._construir_grafo(estado.laberinto)   # Lazy init si falta

        objetivo = self._seleccionar_objetivo(estado)
        if objetivo is None:
            return Direccion.NOOP

        # Dijkstra desde el objetivo: distancias dan costo para llegar a cada celda
        distancias = greedy_dijkstra(self._graph, objetivo)
        siguiente = self._elegir_vecino(estado, distancias)
        if siguiente is None:
            return Direccion.NOOP

        return celda_a_direccion(estado.pos_propia, siguiente)

    def _elegir_vecino(self, estado: EstadoJuego, distancias: dict[Celda, float]) -> Optional[Celda]:
        vecinos = estado.laberinto.vecinos_transitables(estado.pos_propia)
        if not vecinos:
            return None
        # Vecino con menor distancia restante al objetivo
        return min(vecinos, key=lambda v: distancias.get(v, float("inf")))

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
    def _construir_grafo(laberinto) -> dict[Celda, list[tuple[Celda, int]]]:
        # Grafo de adyacencia: cada celda mapea a su lista de (vecino, peso=1)
        grafo: dict[Celda, list[tuple[Celda, int]]] = {}
        for f in range(laberinto.filas):
            for c in range(laberinto.cols):
                if not laberinto.es_transitable(f, c):
                    continue
                celda = (f, c)
                vecinos = laberinto.vecinos_transitables(celda)
                grafo[celda] = [(v, 1) for v in vecinos]   # Peso 1 por cada paso
        return grafo
