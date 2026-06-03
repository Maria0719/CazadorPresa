"""
base.py — Interfaz abstracta que deben implementar TODOS los agentes.

CONTRATO PARA EQUIPOS EXTERNOS
================================
Para enchufar un agente propio:
  1. Crea un archivo en /agentes/ (p. ej. mi_equipo.py).
  2. Importa y subclasifica `Agente`.
  3. Implementa `decidir_movimiento(estado) -> Direccion`.
  4. En main.py (o motor.py) instancia tu agente y pásalo al motor.

Ejemplo mínimo::

    from agentes.base import Agente, Direccion, EstadoJuego

    class MiAgente(Agente):
        def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
            # Tu lógica aquí
            return Direccion.NOOP

El objeto `EstadoJuego` expone todo lo necesario (ver dataclass abajo).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from laberinto.generador import Laberinto

# Tipo alias
Celda = tuple[int, int]


class Direccion(Enum):
    """Movimientos posibles dentro de la cuadrícula."""
    ARRIBA = (-1, 0)
    ABAJO = (1, 0)
    IZQUIERDA = (0, -1)
    DERECHA = (0, 1)
    NOOP = (0, 0)   # No moverse

    def aplicar(self, celda: Celda) -> Celda:
        """Devuelve la celda resultante de aplicar esta dirección."""
        df, dc = self.value
        return (celda[0] + df, celda[1] + dc)


class Rol(Enum):
    """Rol que puede ocupar un agente en la partida."""
    PRESA = "presa"
    CAZADOR = "cazador"


@dataclass(frozen=True)
class EstadoJuego:
    """
    Instantánea del estado del juego en un tick dado.

    Campos accesibles por los agentes externos
    -------------------------------------------
    laberinto       : Objeto Laberinto con el mapa completo.
                      Usa laberinto.es_transitable(f, c) y
                      laberinto.vecinos_transitables(celda).
    pos_propia      : Celda (fila, col) donde está este agente.
    pos_oponente    : Celda (fila, col) donde está el oponente.
    rol             : Rol.PRESA o Rol.CAZADOR (rol de ESTE agente).
    tiempo_restante : Segundos flotantes que quedan en la partida.
    salidas         : Lista de celdas que son salida (gana la presa al pisarlas).
    tick            : Número de tick actual (útil para recálculos periódicos).
    """
    laberinto: "Laberinto"
    pos_propia: Celda
    pos_oponente: Celda
    rol: Rol
    tiempo_restante: float
    salidas: tuple[Celda, ...]   # tuple para que frozen=True sea realmente inmutable
    tick: int


class Agente(ABC):
    """
    Clase base abstracta para todos los agentes (IA o humano).

    Subclases obligatorias
    ----------------------
    - decidir_movimiento: lógica de decisión por tick.

    Métodos opcionales
    ------------------
    - inicializar: llamado una vez al inicio de la partida.
    - notificar_resultado: llamado al final con el resultado.
    """

    def __init__(self, rol: Rol) -> None:
        self.rol: Rol = rol

    def inicializar(self, laberinto: "Laberinto", pos_inicial: Celda) -> None:
        """
        Llamado UNA VEZ antes de que comience la partida.
        Úsalo para precomputar información del laberinto si lo necesitas.
        """

    @abstractmethod
    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        """
        Devuelve la dirección a moverse dado el estado actual del juego.

        Restricciones
        -------------
        - Debe devolver en tiempo real (sin bloquear el hilo).
        - Si devuelve una dirección hacia una pared, el motor la ignora
          (la entidad se queda quieta ese tick).
        - Devolver Direccion.NOOP es siempre válido.
        """

    def notificar_resultado(self, gano: bool) -> None:
        """
        Llamado al final de la partida.

        Args:
            gano: True si este agente ganó, False si perdió.
        """


# ── Utilidad compartida (usada por los módulos de algoritmos) ──────────────

def celda_a_direccion(origen: Celda, destino: Celda) -> Direccion:
    """
    Convierte un par de celdas adyacentes en la Direccion correspondiente.

    Función auxiliar compartida por algoritmos/dijkstra.py y algoritmos/dfs_memo.py
    para evitar duplicación de código.

    Args:
        origen  : Celda de partida (fila, col).
        destino : Celda destino adyacente (fila, col).

    Returns:
        Direccion correspondiente al desplazamiento, o NOOP si no son adyacentes.
    """
    df = destino[0] - origen[0]   # Diferencia en fila
    dc = destino[1] - origen[1]   # Diferencia en columna
    for d in Direccion:
        if d.value == (df, dc):
            return d              # Dirección que coincide con el desplazamiento
    return Direccion.NOOP         # No corresponde a ninguna dirección válida
