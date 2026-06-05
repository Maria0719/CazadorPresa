"""
Adaptador externo para Bellman-Ford.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Optional

from agentes.base import Agente, Direccion, EstadoJuego, Rol, Celda, celda_a_direccion


def _cargar_bellman_ford():
    # Carga dinámica necesaria porque "Bellman-ford.py" tiene guion en el nombre
    # (no es un identificador Python válido para import directo)
    base = Path(__file__).resolve().parents[1]
    ruta = base / "algoritmos" / "Bellman-ford.py"
    spec = importlib.util.spec_from_file_location("bellman_ford_ext", ruta)
    if spec is None or spec.loader is None:
        raise ImportError("No se pudo cargar Bellman-ford.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.bellman_ford


_bellman_ford = _cargar_bellman_ford()   # Función bellman_ford cargada en tiempo de módulo


class BellmanFordExterno(Agente):
    def __init__(self, rol: Rol) -> None:
        super().__init__(rol)
        self._vertices: list[Celda] = []
        self._aristas: list[tuple[Celda, Celda, int]] = []   # Aristas (u, v, peso=1)

    def inicializar(self, laberinto, pos_inicial: Celda) -> None:
        self._vertices, self._aristas = self._construir_grafo(laberinto)   # Pre-construir grafo

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        if not self._vertices:
            self._vertices, self._aristas = self._construir_grafo(estado.laberinto)

        objetivo = self._seleccionar_objetivo(estado)
        if objetivo is None:
            return Direccion.NOOP

        # Bellman-Ford desde el objetivo: las distancias dan el costo para llegar allí
        distancias = _bellman_ford(self._vertices, self._aristas, objetivo)
        if not distancias:
            return Direccion.NOOP   # Ciclo negativo detectado o grafo vacío

        siguiente = self._elegir_vecino(estado, distancias)
        if siguiente is None:
            return Direccion.NOOP

        return celda_a_direccion(estado.pos_propia, siguiente)

    def _elegir_vecino(self, estado: EstadoJuego, distancias: dict[Celda, float]) -> Optional[Celda]:
        vecinos = estado.laberinto.vecinos_transitables(estado.pos_propia)
        if not vecinos:
            return None
        # Elegir el vecino que minimiza el costo restante hacia el objetivo
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
    def _construir_grafo(laberinto) -> tuple[list[Celda], list[tuple[Celda, Celda, int]]]:
        # Representar el laberinto como lista de vértices y aristas dirigidas de peso 1
        vertices: list[Celda] = []
        aristas: list[tuple[Celda, Celda, int]] = []
        for f in range(laberinto.filas):
            for c in range(laberinto.cols):
                if not laberinto.es_transitable(f, c):
                    continue
                celda = (f, c)
                vertices.append(celda)
                for v in laberinto.vecinos_transitables(celda):
                    aristas.append((celda, v, 1))   # Arista con peso 1 (grafo no ponderado)
        return vertices, aristas
