"""
Adaptador externo para DFS memoizado.
"""

from __future__ import annotations

from agentes.base import Agente, Direccion, EstadoJuego, Rol, Celda
from algoritmos.dfs_memo import EstrategiaDFSMemo


class DFSMemoExterno(Agente):
    def __init__(self, rol: Rol) -> None:
        super().__init__(rol)
        self._interno = EstrategiaDFSMemo(rol)

    def inicializar(self, laberinto, pos_inicial: Celda) -> None:
        self._interno.inicializar(laberinto, pos_inicial)

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        return self._interno.decidir_movimiento(estado)
