"""
GBFS externo: adaptador para usar greedy_best_first_search como Agente.

No modifica la logica interna del algoritmo; solo adapta entradas/salidas.
"""

from __future__ import annotations

from typing import Optional

from agentes.base import Agente, Direccion, EstadoJuego, Rol, Celda, celda_a_direccion
from algoritmos.gbs import greedy_best_first_search


class GBFSExterno(Agente):
    """
    Agente que usa Greedy Best First Search (GBFS) como algoritmo base.

    - Rol.CAZADOR: objetivo = pos_oponente.
    - Rol.PRESA  : objetivo = salida mas cercana (si existe).
    """

    def __init__(self, rol: Rol) -> None:
        super().__init__(rol)
        self._laberinto = None
        self._graph: dict[Celda, list[tuple[Celda, int]]] = {}
        self._salidas: tuple[Celda, ...] = ()

    def inicializar(self, laberinto, pos_inicial: Celda) -> None:
        self._laberinto = laberinto
        self._graph = self._construir_grafo(laberinto)

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        if self._laberinto is None:
            self._laberinto = estado.laberinto
            self._graph = self._construir_grafo(estado.laberinto)

        self._salidas = estado.salidas

        objetivo = self._seleccionar_objetivo(estado)
        if objetivo is None:
            return Direccion.NOOP

        heuristica = self._heuristica_manhattan(objetivo)

        ruta = greedy_best_first_search(
            self._graph,
            heuristica,
            estado.pos_propia,
            objetivo,
        )

        if not ruta or len(ruta) < 2:
            return Direccion.NOOP

        siguiente = ruta[1]
        return celda_a_direccion(estado.pos_propia, siguiente)

    def _seleccionar_objetivo(self, estado: EstadoJuego) -> Optional[Celda]:
        if self.rol == Rol.CAZADOR:
            return estado.pos_oponente

        if not estado.salidas:
            return None

        return min(
            estado.salidas,
            key=lambda s: self._dist_manhattan(estado.pos_propia, s),
        )

    @staticmethod
    def _dist_manhattan(a: Celda, b: Celda) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _heuristica_manhattan(self, objetivo: Celda) -> dict[Celda, int]:
        return {
            celda: self._dist_manhattan(celda, objetivo)
            for celda in self._graph
        }

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
