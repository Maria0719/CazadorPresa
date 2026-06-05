"""
Adaptador externo para A* (a_estrella).
"""

from __future__ import annotations

from typing import Optional

from agentes.base import Agente, Direccion, EstadoJuego, Rol, Celda, celda_a_direccion
from algoritmos.A_estrella import a_estrella


class AEstrellaExterno(Agente):
    def __init__(self, rol: Rol) -> None:
        super().__init__(rol)

    def inicializar(self, laberinto, pos_inicial: Celda) -> None:
        pass

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        objetivo = self._seleccionar_objetivo(estado)
        if objetivo is None:
            return Direccion.NOOP

        ruta = a_estrella(estado.laberinto.grid, estado.pos_propia, objetivo)
        if not ruta or len(ruta) < 2:
            return Direccion.NOOP   # Sin camino o ya en el objetivo

        siguiente = ruta[1]   # ruta[0] es la posición actual; ruta[1] es el primer paso
        return celda_a_direccion(estado.pos_propia, siguiente)

    def _seleccionar_objetivo(self, estado: EstadoJuego) -> Optional[Celda]:
        if self.rol == Rol.CAZADOR:
            return estado.pos_oponente   # Cazador: perseguir al oponente
        if not estado.salidas:
            return None
        # Evasor: ir a la salida más cercana en distancia Manhattan
        return min(estado.salidas, key=lambda s: self._dist_manhattan(estado.pos_propia, s))

    @staticmethod
    def _dist_manhattan(a: Celda, b: Celda) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])   # Heurística de distancia sin obstáculos
