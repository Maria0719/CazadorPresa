"""
humano.py — Agente controlado por el teclado (flechas o WASD).

El movimiento se registra a través de `registrar_tecla`, que debe ser
llamado desde el bucle de eventos de Pygame antes de `decidir_movimiento`.
"""

from __future__ import annotations
import pygame
from agentes.base import Agente, Direccion, EstadoJuego, Rol, Celda
from laberinto.generador import Laberinto


# Mapeo tecla → dirección
_TECLAS: dict[int, Direccion] = {
    pygame.K_UP: Direccion.ARRIBA,
    pygame.K_w: Direccion.ARRIBA,
    pygame.K_DOWN: Direccion.ABAJO,
    pygame.K_s: Direccion.ABAJO,
    pygame.K_LEFT: Direccion.IZQUIERDA,
    pygame.K_a: Direccion.IZQUIERDA,
    pygame.K_RIGHT: Direccion.DERECHA,
    pygame.K_d: Direccion.DERECHA,
}


class Humano(Agente):
    """Agente que traduce pulsaciones de teclado en direcciones de movimiento."""

    def __init__(self, rol: Rol) -> None:
        super().__init__(rol)
        self._pendiente: Direccion = Direccion.NOOP

    def inicializar(self, laberinto: Laberinto, pos_inicial: Celda) -> None:
        self._pendiente = Direccion.NOOP

    def registrar_tecla(self, codigo_tecla: int) -> None:
        """
        Registra la última tecla válida pulsada.
        Llamar desde el bucle de eventos Pygame (evento KEYDOWN).
        """
        if codigo_tecla in _TECLAS:
            self._pendiente = _TECLAS[codigo_tecla]

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        """Devuelve la dirección pendiente y la resetea a NOOP."""
        direccion = self._pendiente
        self._pendiente = Direccion.NOOP
        return direccion
