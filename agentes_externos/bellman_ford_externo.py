"""
Adaptador externo para Bellman-Ford.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Optional

from agentes.base import Agente, Direccion, EstadoJuego, Rol, Celda, celda_a_direccion


def _cargar_bellman_ford():
    base = Path(__file__).resolve().parents[1]
    ruta = base / "algoritmos" / "Bellman-ford.py"
    spec = importlib.util.spec_from_file_location("bellman_ford_ext", ruta)
    if spec is None or spec.loader is None:
        raise ImportError("No se pudo cargar Bellman-ford.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.bellman_ford


_bellman_ford = _cargar_bellman_ford()


class BellmanFordExterno(Agente):
    def __init__(self, rol: Rol) -> None:
        super().__init__(rol)
        self._vertices: list[Celda] = []
        self._aristas: list[tuple[Celda, Celda, int]] = []

    def inicializar(self, laberinto, pos_inicial: Celda) -> None:
        self._vertices, self._aristas = self._construir_grafo(laberinto)

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        if not self._vertices:
            self._vertices, self._aristas = self._construir_grafo(estado.laberinto)

        objetivo = self._seleccionar_objetivo(estado)
        if objetivo is None:
            return Direccion.NOOP

        distancias = _bellman_ford(self._vertices, self._aristas, objetivo)
        if not distancias:
            return Direccion.NOOP

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
    def _construir_grafo(laberinto) -> tuple[list[Celda], list[tuple[Celda, Celda, int]]]:
        vertices: list[Celda] = []
        aristas: list[tuple[Celda, Celda, int]] = []
        for f in range(laberinto.filas):
            for c in range(laberinto.cols):
                if not laberinto.es_transitable(f, c):
                    continue
                celda = (f, c)
                vertices.append(celda)
                for v in laberinto.vecinos_transitables(celda):
                    aristas.append((celda, v, 1))
        return vertices, aristas
