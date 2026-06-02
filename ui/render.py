"""
render.py — Dibuja el laberinto, entidades, HUD y pantallas de menú/fin.

Todas las funciones reciben superficies Pygame y no gestionan el clock:
eso es responsabilidad de main.py.
"""

from __future__ import annotations
import pygame
from typing import Optional

from laberinto.generador import Laberinto, PARED
from juego.motor import Motor, ResultadoPartida
from algoritmos.dijkstra import EstrategiaDijkstra   # Para debug de ruta
from config import (
    COLOR_FONDO, COLOR_PARED, COLOR_SUELO, COLOR_PRESA,
    COLOR_CAZADOR, COLOR_SALIDA, COLOR_HUD, COLOR_CAMINO_DEBUG,
    MOSTRAR_CAMINO_DEBUG, TAMANO_CELDA,
)


def _ancho_laberinto(lab: Laberinto) -> int:
    """Devuelve el ancho en píxeles del laberinto."""
    return lab.cols * TAMANO_CELDA


def _alto_laberinto(lab: Laberinto) -> int:
    """Devuelve el alto en píxeles del laberinto."""
    return lab.filas * TAMANO_CELDA


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
    tc = TAMANO_CELDA   # Tamaño de celda en píxeles (alias corto)

    # Dibujar cada celda de la cuadrícula
    for fila in range(lab.filas):
        for col in range(lab.cols):
            rect = pygame.Rect(col * tc, fila * tc, tc, tc)    # Rect de la celda
            # Color según si es pared o suelo
            color = COLOR_PARED if lab.grid[fila][col] == PARED else COLOR_SUELO
            pygame.draw.rect(superficie, color, rect)            # Dibujar celda

    # Dibujar celda(s) de salida con color dorado
    for f, c in lab.salidas:
        rect = pygame.Rect(c * tc, f * tc, tc, tc)
        pygame.draw.rect(superficie, COLOR_SALIDA, rect)         # Relleno dorado
        pygame.draw.rect(superficie, (180, 140, 0), rect, 3)     # Marco dorado oscuro

    # Dibujar ruta del cazador si el modo debug está activado
    if MOSTRAR_CAMINO_DEBUG and motor is not None:
        agente = motor.cazador.agente
        if isinstance(agente, EstrategiaDijkstra):   # Solo para EstrategiaDijkstra
            for f, c in agente.ruta_actual:
                # Cuadrado pequeño en el centro de cada celda de la ruta
                rect = pygame.Rect(c * tc + tc // 4, f * tc + tc // 4, tc // 2, tc // 2)
                pygame.draw.rect(superficie, COLOR_CAMINO_DEBUG, rect, border_radius=3)


def dibujar_entidades(superficie: pygame.Surface, motor: Motor) -> None:
    """
    Dibuja el evasor (círculo verde) y el cazador (cuadrado rojo)
    usando sus posiciones interpoladas para animación suave.
    """
    tc = TAMANO_CELDA
    radio = tc // 2 - 4   # Radio ligeramente menor que la celda

    # ── Evasor (círculo) ──────────────────────────────────────────────────
    px = int(motor.evasor.px)     # Posición X interpolada
    py = int(motor.evasor.py)     # Posición Y interpolada
    pygame.draw.circle(superficie, COLOR_PRESA, (px, py), radio)        # Relleno
    pygame.draw.circle(superficie, (255, 255, 255), (px, py), radio, 2) # Borde blanco

    # ── Cazador (cuadrado redondeado) ──────────────────────────────────────
    cx = int(motor.cazador.px)    # Posición X interpolada
    cy = int(motor.cazador.py)    # Posición Y interpolada
    rect = pygame.Rect(cx - radio, cy - radio, radio * 2, radio * 2)
    pygame.draw.rect(superficie, COLOR_CAZADOR, rect, border_radius=5)  # Relleno rojo
    pygame.draw.rect(superficie, (255, 255, 255), rect, 2, border_radius=5)  # Borde blanco


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
    alto_hud = 36    # Alto fijo del HUD en píxeles
    # Fondo oscuro para el HUD
    pygame.draw.rect(superficie, (20, 20, 45), (0, 0, ancho_ventana, alto_hud))

    # Calcular tiempo restante y formatear como MM:SS
    seg = motor.tiempo_restante()
    minutos = int(seg) // 60
    segundos = int(seg) % 60
    texto_tiempo = f"Tiempo: {minutos:02d}:{segundos:02d}"

    # Textos de cada sección del HUD
    texto_evasor   = "[ EVASOR ]"
    texto_cazador  = "[ CAZADOR ]"
    texto_cfg      = f"Config {configuracion}"   # Indicador de configuración

    # Renderizar superficies de texto
    sup_tiempo  = fuente.render(texto_tiempo, True, COLOR_HUD)
    sup_evasor  = fuente.render(texto_evasor, True, COLOR_PRESA)
    sup_cazador = fuente.render(texto_cazador, True, COLOR_CAZADOR)
    sup_cfg     = fuente.render(texto_cfg, True, (200, 200, 100))   # Amarillo para config

    # Posicionar cada elemento en el HUD
    superficie.blit(sup_evasor,  (10, 8))                                         # Izquierda
    superficie.blit(sup_cfg,     (sup_evasor.get_width() + 20, 8))               # Centro-izq
    superficie.blit(sup_tiempo,  (ancho_ventana // 2 - sup_tiempo.get_width() // 2, 8))  # Centro
    superficie.blit(sup_cazador, (ancho_ventana - sup_cazador.get_width() - 10, 8))  # Derecha


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
    # Overlay negro semitransparente sobre toda la pantalla
    overlay = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))    # RGBA: negro con 62 % opacidad
    superficie.blit(overlay, (0, 0))

    # Mensaje y color según el resultado
    if resultado == ResultadoPartida.GANA_CAZADOR:
        msg = "¡CAZADOR GANA!"
        color = COLOR_CAZADOR    # Rojo para cazador
    else:
        msg = "¡EVASOR ESCAPA!"
        color = COLOR_PRESA      # Verde para evasor

    # Renderizar mensaje principal y sub-mensaje
    sup = fuente_grande.render(msg, True, color)
    sub = fuente_chica.render("Pulsa R para reiniciar  |  ESC para salir", True, COLOR_HUD)

    # Centrar en pantalla
    superficie.blit(sup, (ancho // 2 - sup.get_width() // 2, alto // 2 - 50))
    superficie.blit(sub, (ancho // 2 - sub.get_width() // 2, alto // 2 + 20))


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
    superficie.fill(COLOR_FONDO)    # Limpiar pantalla

    # Título principal
    titulo = fuente_titulo.render("EVASOR  vs  CAZADOR", True, (220, 200, 80))
    superficie.blit(titulo, (ancho // 2 - titulo.get_width() // 2, alto // 8))

    # Subtítulo (nombre del paso del menú)
    if subtitulo:
        sup_sub = fuente_chica.render(subtitulo, True, (160, 160, 220))
        superficie.blit(sup_sub, (ancho // 2 - sup_sub.get_width() // 2, alto // 8 + 55))

    # Dibujar cada opción, resaltando la seleccionada
    for i, opcion in enumerate(opciones):
        color  = (255, 255, 100) if i == seleccion else (180, 180, 200)   # Amarillo si elegida
        prefijo = "▶  " if i == seleccion else "   "    # Flecha indicadora
        sup = fuente_opcion.render(prefijo + opcion, True, color)
        y = alto // 2 - (len(opciones) * 52) // 2 + i * 52    # Centrar verticalmente
        superficie.blit(sup, (ancho // 2 - sup.get_width() // 2, y))

    # Texto de ayuda al fondo
    ayuda = fuente_chica.render("↑ ↓ para navegar   ENTER para seleccionar   ESC para atrás",
                                True, (100, 100, 130))
    superficie.blit(ayuda, (ancho // 2 - ayuda.get_width() // 2, alto - 50))
