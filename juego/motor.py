"""
motor.py — Bucle principal del juego: ticks, movimiento, colisiones y victoria.

Arquitectura de tiempo real
----------------------------
Cada entidad tiene un contador `frames_restantes`. Cuando llega a 0,
se le pide al agente su próxima dirección y se mueve una celda.
Esto da movimiento continuo a velocidad controlada (FRAMES_POR_CELDA).

Soporte headless (benchmark)
-----------------------------
El motor funciona sin Pygame cuando se usa el método `simular_headless()`.
Esto permite ejecutar partidas completas para el benchmark sin renderizado.
"""

from __future__ import annotations
import time                         # Para medir tiempos reales de partida
from dataclasses import dataclass   # Para la estructura Entidad
from enum import Enum, auto         # Para ResultadoPartida
from typing import Optional

from agentes.base import Agente, Direccion, EstadoJuego, Rol, Celda
from agentes.humano import Humano
from laberinto.generador import Laberinto
from metricas.registro import AcumuladorMetricas, RegistroPartida
from config import FRAMES_POR_CELDA, TIEMPO_LIMITE_SEG

class ResultadoPartida(Enum):
    """Estado de la partida: en curso, gana cazador o gana evasor."""
    EN_CURSO      = auto()   # La partida aún no ha terminado
    GANA_CAZADOR  = auto()   # El cazador atrapó al evasor
    GANA_EVASOR   = auto()   # El evasor llegó a la salida o agotó el tiempo


@dataclass
class Entidad:
    """Estado completo de una entidad (evasor o cazador) en el tablero."""
    celda: Celda             # Celda actual (fila, col)
    agente: Agente           # Objeto agente que controla esta entidad
    rol: Rol                 # Rol de la entidad
    frames_restantes: int = 0   # Frames que faltan para el próximo movimiento
    # Posición de interpolación en píxeles (para animación suave en Pygame)
    px: float = 0.0          # Posición X visual actual (píxeles)
    py: float = 0.0          # Posición Y visual actual (píxeles)
    dest_px: float = 0.0     # Posición X visual destino (píxeles)
    dest_py: float = 0.0     # Posición Y visual destino (píxeles)


class Motor:
    """
    Gestiona el estado del juego y su actualización frame a frame.

    Soporta tanto el modo visual (Pygame) como el modo headless (benchmark).
    """

    def __init__(
        self,
        laberinto: Laberinto,
        agente_evasor: Agente,
        agente_cazador: Agente,
        tamano_celda: int,
        ticks_limite: Optional[int] = None,
        configuracion: str = "A",
    ) -> None:
        """
        Args:
            laberinto     : Laberinto ya generado.
            agente_evasor : Agente que controla al evasor (presa).
            agente_cazador: Agente que controla al cazador.
            tamano_celda  : Tamaño de celda en píxeles (para interpolación visual).
            ticks_limite  : Ticks máximos antes de declarar victoria del evasor.
                            None = usar TIEMPO_LIMITE_SEG en tiempo real.
            configuracion : "A" o "B" (para métricas).
        """
        self.lab = laberinto                   # Referencia al laberinto
        self.tamano_celda = tamano_celda       # Tamaño de celda en píxeles
        self.tick: int = 0                     # Tick actual (incrementa cada frame)
        self.resultado: ResultadoPartida = ResultadoPartida.EN_CURSO  # Estado inicial
        self.configuracion: str = configuracion  # Configuración A o B
        self._ticks_limite: Optional[int] = ticks_limite  # Límite de ticks headless

        # En modo headless (benchmark) cada tick = 1 movimiento: evita que
        # FRAMES_POR_CELDA reduzca los movimientos efectivos de 2000 a ~250,
        # lo que sesgaría los resultados Config A vs B en laberintos grandes.
        self._modo_rapido: bool = ticks_limite is not None

        # ── Posiciones iniciales ────────────────────────────────────────────
        pos_evasor: Celda = (1, 1)              # Evasor siempre en esquina superior-izquierda
        pos_cazador: Celda = laberinto.celda_libre_lejana(pos_evasor, min_distancia=8)

        # ── Inicializar agentes ─────────────────────────────────────────────
        agente_evasor.inicializar(laberinto, pos_evasor)       # Llamar hook de inicio
        agente_cazador.inicializar(laberinto, pos_cazador)     # Llamar hook de inicio

        # ── Crear entidades ─────────────────────────────────────────────────
        # En modo rápido (headless) arrancamos con frames_restantes=1 para que
        # la primera decisión ocurra en el tick 1 (igual que en modo visual).
        _frames_init = 1 if self._modo_rapido else FRAMES_POR_CELDA

        self.evasor = Entidad(
            celda=pos_evasor,
            agente=agente_evasor,
            rol=Rol.PRESA,
            frames_restantes=_frames_init,
            **self._px_desde_celda(pos_evasor),    # Posición inicial en píxeles
        )
        self.cazador = Entidad(
            celda=pos_cazador,
            agente=agente_cazador,
            rol=Rol.CAZADOR,
            frames_restantes=_frames_init,
            **self._px_desde_celda(pos_cazador),   # Posición inicial en píxeles
        )

        # ── Métricas ────────────────────────────────────────────────────────
        self._acumulador = AcumuladorMetricas()    # Acumulador de métricas tick a tick
        self._celda_anterior_evasor: Celda = pos_evasor    # Para detectar movimiento
        self._celda_anterior_cazador: Celda = pos_cazador  # Para detectar movimiento

        # ── Tiempo real ─────────────────────────────────────────────────────
        self.tiempo_inicio: float = time.time()    # Marca de inicio de la partida

    # ── Helpers de posición en píxeles ────────────────────────────────────

    def _px_desde_celda(self, celda: Celda) -> dict:
        """Convierte coordenadas de celda a píxeles (centro de la celda)."""
        tc = self.tamano_celda
        px = celda[1] * tc + tc // 2    # Centro horizontal de la celda
        py = celda[0] * tc + tc // 2    # Centro vertical de la celda
        return {"px": float(px), "py": float(py), "dest_px": float(px), "dest_py": float(py)}

    def tiempo_restante(self) -> float:
        """Segundos reales restantes de la partida (0.0 si ya se agotó)."""
        transcurrido = time.time() - self.tiempo_inicio
        return max(0.0, TIEMPO_LIMITE_SEG - transcurrido)

    # ── Construcción del estado para agentes ──────────────────────────────

    def _estado_para(self, entidad: Entidad) -> EstadoJuego:
        """Construye el EstadoJuego que se entrega al agente de esta entidad."""
        if entidad.rol == Rol.PRESA:
            pos_propia   = self.evasor.celda     # El evasor es 'propia'
            pos_oponente = self.cazador.celda    # El cazador es 'oponente'
        else:
            pos_propia   = self.cazador.celda    # El cazador es 'propio'
            pos_oponente = self.evasor.celda     # El evasor es 'oponente'

        return EstadoJuego(
            laberinto=self.lab,
            pos_propia=pos_propia,
            pos_oponente=pos_oponente,
            rol=entidad.rol,
            tiempo_restante=self.tiempo_restante(),
            salidas=tuple(self.lab.salidas),
            tick=self.tick,
        )

    # ── Movimiento ─────────────────────────────────────────────────────────

    def _mover_entidad(self, entidad: Entidad, estado: EstadoJuego) -> None:
        """
        Solicita movimiento al agente, aplica si es válido y actualiza la
        posición visual de destino para la interpolación.

        También registra métricas de tiempo y nodos expandidos.
        """
        celda_antes = entidad.celda                            # Guardar posición antes de mover
        direccion = entidad.agente.decidir_movimiento(estado)  # Pedir decisión al agente
        nueva_celda = direccion.aplicar(entidad.celda)          # Calcular nueva posición

        # Aplicar movimiento solo si la nueva celda es transitable
        if self.lab.es_transitable(nueva_celda[0], nueva_celda[1]):
            entidad.celda = nueva_celda    # Mover a la nueva celda

        # Actualizar destino de interpolación visual
        tc = self.tamano_celda
        entidad.dest_px = float(entidad.celda[1] * tc + tc // 2)
        entidad.dest_py = float(entidad.celda[0] * tc + tc // 2)
        # En modo rápido (headless) un tick = un movimiento; en modo visual
        # se usa FRAMES_POR_CELDA para animar suavemente el desplazamiento.
        entidad.frames_restantes = 1 if self._modo_rapido else FRAMES_POR_CELDA

        # ── Registrar métricas del agente ─────────────────────────────────
        # Leer nodos expandidos y tiempo del agente si los expone
        nodos = getattr(entidad.agente, "nodos_expandidos", 0)
        tiempo = getattr(entidad.agente, "tiempo_ultima_decision", 0.0)
        se_movio = (entidad.celda != celda_antes)    # Detectar si hubo movimiento real

        if entidad.rol == Rol.CAZADOR:
            self._acumulador.registrar_tick_cazador(nodos, tiempo, se_movio)
        else:
            self._acumulador.registrar_tick_evasor(nodos, tiempo, se_movio)

    def _interpolar(self, entidad: Entidad) -> None:
        """Mueve la posición visual suavemente hacia el destino (animación)."""
        if FRAMES_POR_CELDA <= 1:
            # Sin interpolación: saltar directamente al destino
            entidad.px = entidad.dest_px
            entidad.py = entidad.dest_py
            return

        # Avanzar una fracción proporcional a los frames restantes
        avance = 1.0 / max(entidad.frames_restantes + 1, 1)
        entidad.px += (entidad.dest_px - entidad.px) * avance * 4
        entidad.py += (entidad.dest_py - entidad.py) * avance * 4

    # ── Registrar tecla del humano ─────────────────────────────────────────

    def registrar_tecla(self, codigo_tecla: int) -> None:
        """Delega las pulsaciones de teclado al agente humano si existe."""
        for entidad in (self.evasor, self.cazador):
            if isinstance(entidad.agente, Humano):
                entidad.agente.registrar_tecla(codigo_tecla)

    # ── Condiciones de victoria ────────────────────────────────────────────

    def _verificar_resultado(self) -> None:
        """Comprueba si se ha cumplido alguna condición de fin de partida."""
        if self.resultado != ResultadoPartida.EN_CURSO:
            return   # Partida ya terminada: no re-verificar

        # Condición 1: el cazador atrapa al evasor (misma celda)
        if self.cazador.celda == self.evasor.celda:
            self.resultado = ResultadoPartida.GANA_CAZADOR
            self.evasor.agente.notificar_resultado(False)    # El evasor perdió
            self.cazador.agente.notificar_resultado(True)    # El cazador ganó
            return

        # Condición 2: el evasor llega a la salida
        if self.evasor.celda in self.lab.salidas:
            self.resultado = ResultadoPartida.GANA_EVASOR
            self.evasor.agente.notificar_resultado(True)     # El evasor ganó
            self.cazador.agente.notificar_resultado(False)   # El cazador perdió
            return

        # Condición 3: tiempo agotado en modo tiempo real
        if self._ticks_limite is None and self.tiempo_restante() <= 0.0:
            self.resultado = ResultadoPartida.GANA_EVASOR
            self.evasor.agente.notificar_resultado(True)
            self.cazador.agente.notificar_resultado(False)
            return

        # Condición 4: ticks agotados en modo headless (benchmark)
        if self._ticks_limite is not None and self.tick >= self._ticks_limite:
            self.resultado = ResultadoPartida.GANA_EVASOR
            self.evasor.agente.notificar_resultado(True)
            self.cazador.agente.notificar_resultado(False)

    # ── Actualización principal (un frame) ────────────────────────────────

    def actualizar(self) -> None:
        """
        Llamar UNA VEZ por frame desde el bucle de Pygame o desde simular_headless.

        Decrementa los contadores de frames, solicita movimientos cuando
        corresponde, interpola posiciones y verifica el resultado.
        """
        if self.resultado != ResultadoPartida.EN_CURSO:
            return   # Partida terminada: no actualizar más

        self.tick += 1   # Incrementar contador de ticks

        for entidad in (self.evasor, self.cazador):
            entidad.frames_restantes -= 1    # Decrementar contador de frames
            if entidad.frames_restantes <= 0:
                # Es el turno de este agente: pedir y aplicar su movimiento
                estado = self._estado_para(entidad)
                self._mover_entidad(entidad, estado)
            self._interpolar(entidad)    # Siempre interpolar para animación suave

        self._verificar_resultado()    # Comprobar condiciones de victoria

    # ── Modo headless (para benchmark) ────────────────────────────────────

    def simular_headless(self) -> RegistroPartida:
        """
        Ejecuta la partida completa sin rendering hasta que termine.

        Usa `_ticks_limite` como límite máximo (debe haberse fijado al crear el Motor).
        Devuelve el RegistroPartida con todas las métricas.
        """
        # Garantizar que hay un límite de ticks para no correr infinitamente
        limite = self._ticks_limite if self._ticks_limite else 5000

        while self.resultado == ResultadoPartida.EN_CURSO and self.tick < limite:
            self.actualizar()    # Ejecutar un tick sin render

        # Construir resultado textual
        if self.resultado == ResultadoPartida.GANA_CAZADOR:
            resultado_str = "cazador_gana"
        else:
            resultado_str = "evasor_gana"

        # Generar el RegistroPartida con todas las métricas acumuladas
        return self._acumulador.finalizar(
            tamano_n=self.lab.filas,
            tipo_escenario=self.lab.nombre_escenario(),
            configuracion=self.configuracion,
            resultado=resultado_str,
            ticks_totales=self.tick,
        )

