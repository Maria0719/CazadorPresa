"""
Adaptador externo para MPS.
"""

from __future__ import annotations

from typing import Optional

from agentes.base import Agente, Direccion, EstadoJuego, Rol, Celda, celda_a_direccion
from algoritmos.Mps import construir_mps, reconstruir_camino


class _TableroRemoto:
    def __init__(self, laberinto) -> None:
        self._lab = laberinto
        self.n = laberinto.filas

    def es_valida(self, x: int, y: int) -> bool:
        return (
            0 <= x < self._lab.filas
            and 0 <= y < self._lab.cols
            and self._lab.es_transitable(x, y)
        )


class MPSExterno(Agente):
    def __init__(self, rol: Rol) -> None:
        super().__init__(rol)
        self._tablero: Optional[_TableroRemoto] = None

    def inicializar(self, laberinto, pos_inicial: Celda) -> None:
        self._tablero = _TableroRemoto(laberinto)

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        if self._tablero is None:
            self._tablero = _TableroRemoto(estado.laberinto)

        objetivo = self._seleccionar_objetivo(estado)
        if objetivo is None:
            return Direccion.NOOP

        dp = construir_mps(self._tablero, objetivo)
        camino = reconstruir_camino(self._tablero, dp, estado.pos_propia)
        if not camino or len(camino) < 2:
            return Direccion.NOOP

        siguiente = camino[1]
        return celda_a_direccion(estado.pos_propia, siguiente)

    def _seleccionar_objetivo(self, estado: EstadoJuego) -> Optional[Celda]:
        if self.rol == Rol.CAZADOR:
            return estado.pos_oponente
        if not estado.salidas:
            return None
        return min(estado.salidas, key=lambda s: self._dist_manhattan(estado.pos_propia, s))

    @staticmethod
    def _dist_manhattan(a: Celda, b: Celda) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
