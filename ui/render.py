"""
render.py — Dibuja el laberinto, entidades, HUD y pantallas de menú/fin.

Todas las funciones reciben superficies Pygame y no gestionan el clock:
eso es responsabilidad de main.py.

El tamaño de celda (TAMANO_CELDA) se lee en tiempo de llamada desde el
módulo, no en el momento del import, para que main.py pueda ajustarlo
dinámicamente según el tamaño de laberinto elegido por el usuario.
"""

from __future__ import annotations
import pygame
from typing import Optional

import config                                         # Leído en tiempo de llamada
from laberinto.generador import Laberinto, PARED
from juego.motor import Motor, ResultadoPartida
from algoritmos.dijkstra import EstrategiaDijkstra   # Para debug de ruta


# ── Helpers internos ───────────────────────────────────────────────────────

def _blit_centrado(
    superficie: pygame.Surface,
    sup_texto: pygame.Surface,
    y: int,
    margen: int = 24,
) -> None:
    """
    Dibuja `sup_texto` centrado horizontalmente en `superficie` a la altura `y`.

    Si el ancho del texto supera `superficie.get_width() - 2*margen`, lo escala
    proporcionalmente para que quepa sin recortarse.

    Args:
        superficie : Destino del dibujo.
        sup_texto  : Superficie de texto ya renderizada.
        y          : Coordenada Y donde colocar el texto.
        margen     : Margen horizontal mínimo a cada lado (píxeles).
    """
    ancho = superficie.get_width()
    max_w = max(10, ancho - 2 * margen)

    if sup_texto.get_width() > max_w:
        # Escalar manteniendo la proporción para que quepa en el ancho disponible
        factor  = max_w / sup_texto.get_width()
        nuevo_h = max(1, int(sup_texto.get_height() * factor))
        sup_texto = pygame.transform.smoothscale(sup_texto, (max_w, nuevo_h))

    x = (ancho - sup_texto.get_width()) // 2
    superficie.blit(sup_texto, (x, y))


def _tc() -> int:
    """Tamaño de celda actual (leído de config en cada llamada)."""
    return config.TAMANO_CELDA


def _radio(tc: int) -> int:
    """Radio de las entidades proporcional al tamaño de celda. Mínimo 3 px.
    Para celdas ≤ 12 px (tableros grandes) ocupa toda la celda; en celdas
    mayores deja un pequeño margen para que se vea bien la cuadrícula."""
    if tc <= 20:
        return max(4, tc // 2)
    return max(4, tc // 2 - max(1, tc // 8))


def _borde_r(radio: int) -> int:
    """Border-radius para el cuadrado del cazador, nunca mayor que el radio."""
    return min(radio, max(2, radio // 2))


def _grosor(tc: int) -> int:
    """Grosor de bordes proporcional al tamaño de celda. Mínimo 1 px."""
    return max(1, tc // 10)


# ── Dibujo del laberinto ───────────────────────────────────────────────────

def dibujar_laberinto(
    superficie: pygame.Surface,
    lab: Laberinto,
    motor: Optional[Motor] = None,
) -> None:
    """
    Dibuja la cuadrícula del laberinto: paredes, suelos, salidas y ruta debug.

    Args:
        superficie : Superficie Pygame donde dibujar.
        lab        : Objeto Laberinto con el mapa.
        motor      : Motor actual (para debug de ruta del cazador).
    """
    tc = _tc()

    for fila in range(lab.filas):
        for col in range(lab.cols):
            rect = pygame.Rect(col * tc, fila * tc, tc, tc)
            color = config.COLOR_PARED if lab.grid[fila][col] == PARED else config.COLOR_SUELO
            pygame.draw.rect(superficie, color, rect)

    # Salidas con color dorado; borde proporcional a la celda
    grosor_sal = _grosor(tc)
    for f, c in lab.salidas:
        rect = pygame.Rect(c * tc, f * tc, tc, tc)
        pygame.draw.rect(superficie, config.COLOR_SALIDA, rect)
        pygame.draw.rect(superficie, (180, 140, 0), rect, grosor_sal)

    # Ruta del cazador (solo si debug activo y agente es Dijkstra)
    if config.MOSTRAR_CAMINO_DEBUG and motor is not None:
        agente = motor.cazador.agente
        if isinstance(agente, EstrategiaDijkstra):
            margen = max(1, tc // 4)
            tam    = max(1, tc - margen * 2)
            br     = max(0, min(3, margen - 1))
            for f, c in agente.ruta_actual:
                rect = pygame.Rect(c * tc + margen, f * tc + margen, tam, tam)
                pygame.draw.rect(superficie, config.COLOR_CAMINO_DEBUG, rect,
                                 border_radius=br)


# ── Dibujo de entidades ────────────────────────────────────────────────────

def dibujar_entidades(superficie: pygame.Surface, motor: Motor) -> None:
    """
    Dibuja el evasor (círculo verde) y el cazador (cuadrado rojo)
    usando sus posiciones interpoladas para animación suave.

    Las dimensiones escalan automáticamente con el tamaño de celda.
    """
    tc     = _tc()
    radio  = _radio(tc)
    grosor = max(1, radio // 4)   # Grosor del borde proporcional al radio
    br     = _borde_r(radio)      # Border-radius para el cazador

    # ── Evasor (círculo verde) ────────────────────────────────────────────
    px = int(motor.evasor.px)
    py = int(motor.evasor.py)
    pygame.draw.circle(superficie, config.COLOR_PRESA,   (px, py), radio)
    pygame.draw.circle(superficie, (255, 255, 255), (px, py), radio, grosor)

    # ── Cazador (cuadrado redondeado rojo) ────────────────────────────────
    cx = int(motor.cazador.px)
    cy = int(motor.cazador.py)
    rect = pygame.Rect(cx - radio, cy - radio, radio * 2, radio * 2)
    pygame.draw.rect(superficie, config.COLOR_CAZADOR, rect, border_radius=br)
    pygame.draw.rect(superficie, (255, 255, 255), rect, grosor, border_radius=br)


# ── HUD ────────────────────────────────────────────────────────────────────

def dibujar_hud(
    superficie: pygame.Surface,
    motor: Motor,
    fuente: pygame.font.Font,
    ancho_ventana: int,
    configuracion: str = "A",
    nombre_escenario: str = "",
) -> None:
    """
    Dibuja la barra de información (HUD) en la parte superior de la ventana.
    Muestra: tiempo restante, indicadores de rol y la configuración activa.
    """
    alto_hud = 36
    pygame.draw.rect(superficie, (20, 20, 45), (0, 0, ancho_ventana, alto_hud))

    seg     = motor.tiempo_restante()
    minutos = int(seg) // 60
    segundos = int(seg) % 60

    texto_tiempo  = f"Tiempo: {minutos:02d}:{segundos:02d}"
    texto_evasor  = "[ EVASOR ]"
    texto_cazador = "[ CAZADOR ]"
    texto_cfg     = f"Config {configuracion}"

    sup_tiempo  = fuente.render(texto_tiempo,  True, config.COLOR_HUD)
    sup_evasor  = fuente.render(texto_evasor,  True, config.COLOR_PRESA)
    sup_cazador = fuente.render(texto_cazador, True, config.COLOR_CAZADOR)
    sup_cfg     = fuente.render(texto_cfg,     True, (200, 200, 100))

    # Layout: [EVASOR] [Config X]  ←  Tiempo: 00:00  →  [CAZADOR]
    # cfg_x parte del borde real del texto evasor (que se dibuja en x=10)
    evasor_x = 10
    cfg_x    = evasor_x + sup_evasor.get_width() + 10   # gap de 10 px tras evasor
    tiempo_x = ancho_ventana // 2 - sup_tiempo.get_width() // 2

    superficie.blit(sup_evasor, (evasor_x, 8))
    # Mostrar Config solo si cabe con margen de 8 px antes del bloque de Tiempo
    if cfg_x + sup_cfg.get_width() + 8 < tiempo_x:
        superficie.blit(sup_cfg, (cfg_x, 8))
    superficie.blit(sup_tiempo,  (tiempo_x, 8))
    superficie.blit(sup_cazador, (ancho_ventana - sup_cazador.get_width() - 10, 8))


# ── Pantalla de resultado ──────────────────────────────────────────────────

def dibujar_resultado(
    superficie: pygame.Surface,
    resultado: ResultadoPartida,
    fuente_grande: pygame.font.Font,
    fuente_chica: pygame.font.Font,
    ancho: int,
    alto: int,
) -> None:
    """
    Dibuja un overlay semitransparente con el resultado final de la partida.
    Se muestra sobre el laberinto cuando la partida termina.
    """
    overlay = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    superficie.blit(overlay, (0, 0))

    if resultado == ResultadoPartida.GANA_CAZADOR:
        msg   = "¡CAZADOR GANA!"
        color = config.COLOR_CAZADOR
    else:
        msg   = "¡EVASOR ESCAPA!"
        color = config.COLOR_PRESA

    sup = fuente_grande.render(msg, True, color)
    sub = fuente_chica.render("Pulsa R para reiniciar  |  ESC para salir",
                              True, config.COLOR_HUD)

    superficie.blit(sup, (ancho // 2 - sup.get_width() // 2, alto // 2 - 50))
    superficie.blit(sub, (ancho // 2 - sub.get_width() // 2, alto // 2 + 20))


# ── Pantalla de menú ───────────────────────────────────────────────────────

def dibujar_menu(
    superficie: pygame.Surface,
    fuente_titulo: pygame.font.Font,
    fuente_opcion: pygame.font.Font,
    fuente_chica: pygame.font.Font,
    seleccion: int,
    opciones: list[str],
    ancho: int,
    alto: int,
    subtitulo: str = "",
) -> None:
    """
    Dibuja un menú de selección con opciones navegables.

    Args:
        superficie  : Superficie Pygame donde dibujar.
        fuente_*    : Fuentes para título, opciones y texto pequeño.
        seleccion   : Índice de la opción actualmente seleccionada.
        opciones    : Lista de textos de opción.
        ancho, alto : Dimensiones de la superficie.
        subtitulo   : Texto secundario debajo del título principal.
    """
    superficie.fill(config.COLOR_FONDO)

    titulo = fuente_titulo.render("EVASOR  vs  CAZADOR", True, (220, 200, 80))
    _blit_centrado(superficie, titulo, alto // 8)

    if subtitulo:
        sup_sub = fuente_chica.render(subtitulo, True, (160, 160, 220))
        _blit_centrado(superficie, sup_sub, alto // 8 + 55)

    for i, opcion in enumerate(opciones):
        color   = (255, 255, 100) if i == seleccion else (180, 180, 200)
        prefijo = "▶  " if i == seleccion else "   "
        sup = fuente_opcion.render(prefijo + opcion, True, color)
        y   = alto // 2 - (len(opciones) * 52) // 2 + i * 52
        _blit_centrado(superficie, sup, y)   # auto-ajuste si supera el ancho

    ayuda = fuente_chica.render(
        "↑ ↓ para navegar   ENTER para seleccionar   ESC para atrás",
        True, (100, 100, 130),
    )
    _blit_centrado(superficie, ayuda, alto - 50)
