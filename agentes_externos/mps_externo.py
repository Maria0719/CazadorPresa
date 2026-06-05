"""
Adaptador externo para MPS.
"""

from __future__ import annotations

from typing import Optional

from agentes.base import Agente, Direccion, EstadoJuego, Rol, Celda, celda_a_direccion
from algoritmos.Mps import construir_mps, reconstruir_camino


class _TableroRemoto:
    # Adaptador que expone la API que espera Mps.py (es_valida + n) sobre el Laberinto
    def __init__(self, laberinto) -> None:
        self._lab = laberinto
        self.n = laberinto.filas   # MPS usa un tablero cuadrado de lado n

    def es_valida(self, x: int, y: int) -> bool:
        # Delega a es_transitable del laberinto real
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
        self._tablero = _TableroRemoto(laberinto)   # Envolver laberinto para MPS

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        if self._tablero is None:
            self._tablero = _TableroRemoto(estado.laberinto)   # Lazy init si falta

        objetivo = self._seleccionar_objetivo(estado)
        if objetivo is None:
            return Direccion.NOOP

        dp = construir_mps(self._tablero, objetivo)                 # BFS desde objetivo
        camino = reconstruir_camino(self._tablero, dp, estado.pos_propia)  # Seguir pendiente
        if not camino or len(camino) < 2:
            return Direccion.NOOP   # Sin camino o ya en el objetivo

        siguiente = camino[1]   # camino[0] es pos actual; camino[1] es el primer paso
        return celda_a_direccion(estado.pos_propia, siguiente)

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
