"""
main.py — Punto de entrada del juego Evasor–Cazador en laberinto.

Uso básico
----------
    python main.py                  # semilla aleatoria
    python main.py --semilla 42     # semilla fija (reproducible)
    python main.py --debug          # muestra ruta del cazador
    python main.py --config B       # arranca con Config B por defecto
    python main.py --escenario 2    # arranca con cuello de botella

Modo versus (equipos externos)
-------------------------------
    python main.py --agente-cazador modulo:Clase
    python main.py --agente-evasor  modulo:Clase

    Ejemplo concreto:
    python main.py --agente-cazador agentes_externos.cazador_bfs:CazadorBFS

    Se pueden combinar ambos para enfrentar dos agentes externos:
    python main.py --agente-cazador equipo_A.agente:MiCazador \\
                   --agente-evasor  equipo_B.agente:MiEvasor

Modos disponibles en el menú
-----------------------------
  Paso 1 – Elegir escenario : obstáculos / caminos múltiples / cuello de botella
  Paso 2 – Elegir config    : A (Dijkstra cazador, DFS evasor) / B (inverso)
  Paso 3 – Elegir rol       : humano juega como evasor, cazador, o IA vs IA
"""

from __future__ import annotations
import sys               # Para sys.exit al cerrar el programa
import argparse          # Para parsear argumentos de línea de comandos
import importlib         # Para cargar módulos externos en tiempo de ejecución

import pygame            # Motor gráfico

import config            # Parámetros del proyecto
from config import (
    COLS, FILAS, SEMILLA, TAMANO_CELDA, FPS,
    MOSTRAR_CAMINO_DEBUG, COLOR_FONDO,
)
from laberinto.generador import Laberinto           # Generador de laberintos
from agentes.base import Agente, Rol                # Interfaz y roles
from agentes.humano import Humano                   # Control por teclado
from algoritmos.dijkstra import EstrategiaDijkstra  # Dijkstra reutilizable
from algoritmos.dfs_memo import EstrategiaDFSMemo   # DFS memo reutilizable
from juego.motor import Motor, ResultadoPartida     # Motor del juego
from ui.render import (
    dibujar_laberinto, dibujar_entidades, dibujar_hud,
    dibujar_resultado, dibujar_menu,
)

# ── Constantes de menú ─────────────────────────────────────────────────────
ALTO_HUD = 36    # Alto fijo de la barra HUD en píxeles

NOMBRES_ESCENARIOS = [
    "Con obstáculos",
    "Caminos múltiples",
    "Cuello de botella",
]

NOMBRES_CONFIGS = [
    "Config A: Cazador=Dijkstra  |  Evasor=DFS Memo",
    "Config B: Cazador=DFS Memo  |  Evasor=Dijkstra",
]

NOMBRES_ROLES = [
    "Jugar como EVASOR   (IA cazador)",
    "Jugar como CAZADOR  (IA evasor)",
    "IA vs IA            (demostración)",
]


# ── Cargador de agentes externos ──────────────────────────────────────────

def cargar_agente_externo(especificacion: str, rol: Rol) -> Agente:
    """
    Carga dinámicamente un agente desde un módulo externo usando importlib.

    La especificación sigue el formato "modulo.submodulo:NombreClase".
    El módulo debe estar en el PYTHONPATH (p. ej., en la carpeta del proyecto).

    Ejemplo:
        cargar_agente_externo("agentes_externos.cazador_bfs:CazadorBFS", Rol.CAZADOR)

    Args:
        especificacion : Cadena con formato "modulo:Clase".
        rol            : Rol.CAZADOR o Rol.PRESA que se asignará al agente.

    Returns:
        Instancia del agente externo ya construida con el rol indicado.

    Raises:
        SystemExit si el módulo o la clase no existen (muestra mensaje claro).
    """
    # Separar el nombre del módulo y el nombre de la clase
    if ":" not in especificacion:
        # La especificación no tiene el separador obligatorio ":"
        print(f"[ERROR] Formato incorrecto: '{especificacion}'")
        print("        Usa el formato  modulo:Clase  (p. ej. agentes_externos.cazador_bfs:CazadorBFS)")
        sys.exit(1)    # Terminar con mensaje de error

    nombre_modulo, nombre_clase = especificacion.split(":", 1)
    # nombre_modulo: p. ej. "agentes_externos.cazador_bfs"
    # nombre_clase : p. ej. "CazadorBFS"

    try:
        # Importar el módulo indicado en tiempo de ejecución
        modulo = importlib.import_module(nombre_modulo)
    except ModuleNotFoundError:
        # El módulo no existe o no está en el PYTHONPATH
        print(f"[ERROR] No se encontró el módulo '{nombre_modulo}'.")
        print(f"        Verifica que el archivo {nombre_modulo.replace('.', '/')}.py existe.")
        sys.exit(1)    # Terminar con mensaje claro

    try:
        # Obtener la clase del módulo importado por nombre
        clase = getattr(modulo, nombre_clase)
    except AttributeError:
        # El módulo existe pero no tiene la clase indicada
        print(f"[ERROR] El módulo '{nombre_modulo}' no tiene la clase '{nombre_clase}'.")
        print(f"        Clases disponibles: {[x for x in dir(modulo) if not x.startswith('_')]}")
        sys.exit(1)    # Terminar con mensaje claro

    # Instanciar la clase pasando el rol como único argumento (convención del contrato)
    instancia = clase(rol)

    return instancia   # Devolver el agente ya construido


# ── Parseo de argumentos de línea de comandos ─────────────────────────────

def parse_args() -> argparse.Namespace:
    """Define y parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description="Juego Evasor–Cazador en laberinto.")
    parser.add_argument("--semilla", type=int, default=None,
                        help="Semilla aleatoria (reproducible).")
    parser.add_argument("--debug", action="store_true",
                        help="Mostrar ruta del cazador en pantalla.")
    parser.add_argument("--config", choices=["A", "B"], default=None,
                        help="Configuración de agentes: A o B.")
    parser.add_argument("--escenario", type=int, choices=[0, 1, 2], default=None,
                        help="Tipo de escenario: 0=obstáculos, 1=múltiples, 2=cuello.")
    # ── Modo versus: cargar agentes externos ───────────────────────────────
    parser.add_argument(
        "--agente-cazador", type=str, default=None, dest="agente_cazador",
        help="Agente externo para el rol cazador. Formato: modulo:Clase. "
             "Ej: agentes_externos.cazador_bfs:CazadorBFS",
    )
    parser.add_argument(
        "--agente-evasor", type=str, default=None, dest="agente_evasor",
        help="Agente externo para el rol evasor. Formato: modulo:Clase. "
             "Ej: agentes_externos.cazador_bfs:CazadorBFS",
    )
    return parser.parse_args()


# ── Fábrica de agentes según configuración ────────────────────────────────

def crear_agentes(
    modo_rol: int,
    configuracion: str,
    agente_cazador_externo: Agente | None = None,
    agente_evasor_externo: Agente | None = None,
) -> tuple:
    """
    Devuelve (agente_evasor, agente_cazador) según el modo de rol y configuración.

    Si se pasan agentes externos, estos reemplazan a los agentes IA internos
    para el rol correspondiente.  Los humanos siempre tienen prioridad si
    modo_rol es 0 o 1.

    Args:
        modo_rol               : 0=humano evasor, 1=humano cazador, 2=IA vs IA.
        configuracion          : "A" o "B".
        agente_cazador_externo : Agente externo para el rol cazador (opcional).
        agente_evasor_externo  : Agente externo para el rol evasor (opcional).

    Config A: Cazador = Dijkstra (voraz),    Evasor = DFS Memoizado (PD).
    Config B: Cazador = DFS Memoizado (PD),  Evasor = Dijkstra (voraz).
    """
    # Determinar el agente cazador: externo > IA interna según config
    if agente_cazador_externo is not None:
        ia_cazador = agente_cazador_externo   # Usar agente externo si fue provisto
    elif configuracion == "A":
        ia_cazador = EstrategiaDijkstra(Rol.CAZADOR)   # Config A: Dijkstra caza
    else:
        ia_cazador = EstrategiaDFSMemo(Rol.CAZADOR)    # Config B: DFS memo caza

    # Determinar el agente evasor: externo > IA interna según config
    if agente_evasor_externo is not None:
        ia_evasor = agente_evasor_externo     # Usar agente externo si fue provisto
    elif configuracion == "A":
        ia_evasor = EstrategiaDFSMemo(Rol.PRESA)       # Config A: DFS memo evade
    else:
        ia_evasor = EstrategiaDijkstra(Rol.PRESA)      # Config B: Dijkstra evade

    if modo_rol == 0:
        # Humano juega como evasor; la IA (o externo) es el cazador
        return Humano(Rol.PRESA), ia_cazador
    elif modo_rol == 1:
        # Humano juega como cazador; la IA (o externo) es el evasor
        return ia_evasor, Humano(Rol.CAZADOR)
    else:
        # IA vs IA (modo demo/experimento); ambos pueden ser externos
        return ia_evasor, ia_cazador


# ── Input libre de tamaño ────────────────────────────────────────────────

def ejecutar_input_tamano(
    pantalla: pygame.Surface,
    reloj: pygame.time.Clock,
    fuentes: dict,
    ancho: int,
    alto: int,
) -> int | None:
    """
    Pantalla de ingreso libre del tamaño del laberinto.

    El usuario escribe cualquier número entero ≥ 5.
    Si ingresa un número par, se ajusta automáticamente al siguiente impar.

    Returns:
        Tamaño elegido (impar, ≥ 5), o None si el usuario sale con ESC.
    """
    TAMANO_MIN = 5
    TAMANO_MAX = 201   # Más grande ralentiza mucho; límite práctico

    texto = ""     # Dígitos que el usuario ha escrito
    error = ""     # Mensaje de error si la validación falla

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return None
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return None

                elif evento.key == pygame.K_RETURN:
                    # Validar y confirmar
                    try:
                        n = int(texto)
                    except ValueError:
                        error = "Ingresa un número entero"
                        continue

                    if n < TAMANO_MIN:
                        error = f"Mínimo: {TAMANO_MIN}"
                    elif n > TAMANO_MAX:
                        error = f"Máximo: {TAMANO_MAX}"
                    else:
                        if n % 2 == 0:
                            n += 1   # Ajustar a impar automáticamente
                        return n

                elif evento.key == pygame.K_BACKSPACE:
                    texto = texto[:-1]
                    error = ""

                elif evento.unicode.isdigit() and len(texto) < 3:
                    texto += evento.unicode
                    error = ""

        # ── Render ──────────────────────────────────────────────────────
        pantalla.fill(COLOR_FONDO)

        titulo = fuentes["titulo"].render("EVASOR  vs  CAZADOR", True, (220, 200, 80))
        pantalla.blit(titulo, (ancho // 2 - titulo.get_width() // 2, alto // 8))

        paso = fuentes["chica"].render(
            "Paso 1 — Elige el TAMAÑO del laberinto (n × n)",
            True, (160, 160, 220),
        )
        pantalla.blit(paso, (ancho // 2 - paso.get_width() // 2, alto // 8 + 55))

        rango = fuentes["chica"].render(
            f"Rango: {TAMANO_MIN} – {TAMANO_MAX}  |  Impares recomendados "
            "(si ingresas un par se ajusta solo)",
            True, (110, 110, 150),
        )
        pantalla.blit(rango, (ancho // 2 - rango.get_width() // 2, alto // 8 + 82))

        # Caja de texto
        box_w, box_h = 160, 54
        box_x = ancho // 2 - box_w // 2
        box_y = alto // 2 - box_h // 2
        pygame.draw.rect(pantalla, (30, 30, 60), (box_x, box_y, box_w, box_h), border_radius=8)
        pygame.draw.rect(pantalla, (150, 150, 230), (box_x, box_y, box_w, box_h), 2, border_radius=8)

        cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else " "
        sup_num = fuentes["grande"].render(texto + cursor, True, (255, 255, 100))
        pantalla.blit(sup_num, (ancho // 2 - sup_num.get_width() // 2, box_y + 7))

        if error:
            sup_err = fuentes["chica"].render(error, True, (255, 80, 80))
            pantalla.blit(sup_err, (ancho // 2 - sup_err.get_width() // 2, box_y + box_h + 12))

        ayuda = fuentes["chica"].render(
            "Escribe el tamaño   ENTER para confirmar   ESC para salir",
            True, (100, 100, 130),
        )
        pantalla.blit(ayuda, (ancho // 2 - ayuda.get_width() // 2, alto - 50))

        pygame.display.flip()
        reloj.tick(FPS)


# ── Bucle de una partida ──────────────────────────────────────────────────

def ejecutar_partida(
    pantalla: pygame.Surface,
    reloj: pygame.time.Clock,
    fuentes: dict,
    semilla: int | None,
    modo_rol: int,
    configuracion: str,
    tipo_escenario: int,
    ancho_ventana: int,
    alto_ventana: int,
    tamano_n: int = 21,
    tamano_celda: int = TAMANO_CELDA,
    agente_cazador_externo: Agente | None = None,
    agente_evasor_externo: Agente | None = None,
) -> bool:
    """
    Ejecuta una partida completa con rendering Pygame.

    Args:
        agente_cazador_externo : Agente externo para el cazador (None = usar IA interna).
        agente_evasor_externo  : Agente externo para el evasor  (None = usar IA interna).

    Returns:
        True  → el usuario quiere volver al menú / reiniciar.
        False → el usuario quiere salir del programa.
    """
    # Crear laberinto con el tamaño, escenario y semilla elegidos
    lab = Laberinto(tamano_n, tamano_n, semilla, tipo_escenario=tipo_escenario)

    # Crear agentes según la configuración (pasamos los externos si los hay)
    agente_evasor, agente_cazador = crear_agentes(
        modo_rol, configuracion,
        agente_cazador_externo=agente_cazador_externo,
        agente_evasor_externo=agente_evasor_externo,
    )

    # Crear el motor del juego
    motor = Motor(lab, agente_evasor, agente_cazador, tamano_celda,
                  configuracion=configuracion)

    # Superficie para el laberinto (por debajo del HUD)
    sup_lab = pygame.Surface((ancho_ventana, alto_ventana - ALTO_HUD))

    while True:
        # ── Eventos de Pygame ──────────────────────────────────────────────
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False     # Cerrar ventana: salir del programa
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return True  # ESC: volver al menú
                if evento.key == pygame.K_r:
                    return True  # R: reiniciar (volver al menú)
                motor.registrar_tecla(evento.key)    # Pasar tecla al motor

        # ── Actualización del estado del juego ─────────────────────────────
        motor.actualizar()

        # ── Renderizado ────────────────────────────────────────────────────
        sup_lab.fill(config.COLOR_FONDO)
        dibujar_laberinto(sup_lab, lab, motor)       # Dibujar laberinto
        dibujar_entidades(sup_lab, motor)             # Dibujar evasor y cazador

        pantalla.fill(config.COLOR_FONDO)
        pantalla.blit(sup_lab, (0, ALTO_HUD))        # Pegar laberinto debajo del HUD
        dibujar_hud(pantalla, motor, fuentes["hud"], ancho_ventana,
                    configuracion, lab.nombre_escenario())   # HUD con info

        # Mostrar resultado si la partida terminó
        if motor.resultado != ResultadoPartida.EN_CURSO:
            dibujar_resultado(
                pantalla, motor.resultado,
                fuentes["grande"], fuentes["chica"],
                ancho_ventana, alto_ventana,
            )

        pygame.display.flip()       # Actualizar pantalla
        reloj.tick(FPS)             # Controlar framerate


# ── Menús multi-paso ──────────────────────────────────────────────────────

def ejecutar_subMenu(
    pantalla: pygame.Surface,
    reloj: pygame.time.Clock,
    fuentes: dict,
    titulo: str,
    opciones: list[str],
    ancho: int,
    alto: int,
) -> int | None:
    """
    Muestra un submenú genérico y devuelve el índice elegido o None si sale.

    Navegación: ↑↓ o WS para mover, ENTER/ESPACIO para confirmar, ESC para atrás.
    """
    seleccion = 0    # Opción seleccionada actualmente

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return None                      # Cerrar ventana: salir
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return None                  # ESC: retroceder al menú anterior
                if evento.key in (pygame.K_UP, pygame.K_w):
                    seleccion = (seleccion - 1) % len(opciones)   # Subir selección
                if evento.key in (pygame.K_DOWN, pygame.K_s):
                    seleccion = (seleccion + 1) % len(opciones)   # Bajar selección
                if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return seleccion             # Confirmar selección actual

        # Dibujar el submenú en pantalla
        dibujar_menu(
            pantalla,
            fuentes["titulo"], fuentes["opcion"], fuentes["chica"],
            seleccion, opciones, ancho, alto,
            subtitulo=titulo,
        )
        pygame.display.flip()
        reloj.tick(FPS)


# ── Bucle principal ────────────────────────────────────────────────────────

def main() -> None:
    """Función principal: inicializa Pygame y gestiona el flujo de menús."""
    # Forzar UTF-8 en la consola de Windows para evitar mojibake con acentos
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except Exception:
            pass

    args = parse_args()    # Parsear argumentos de línea de comandos

    # Aplicar argumentos de línea de comandos a config
    semilla: int | None = args.semilla if args.semilla is not None else SEMILLA
    if args.debug:
        config.MOSTRAR_CAMINO_DEBUG = True     # Activar debug de ruta
    if args.config:
        config.CONFIGURACION = args.config     # Configuración A o B por argumento
    if args.escenario is not None:
        config.ESCENARIO = args.escenario      # Escenario por argumento

    # ── Cargar agentes externos (antes de Pygame para detectar errores rápido) ──
    # Si se pasaron --agente-cazador o --agente-evasor, cargar los módulos ahora.
    # Esto falla inmediatamente con mensaje claro si el módulo/clase no existe.
    agente_cazador_externo: Agente | None = None    # Cazador externo (None = usar IA interna)
    agente_evasor_externo:  Agente | None = None    # Evasor externo  (None = usar IA interna)

    if args.agente_cazador:
        # Cargar agente externo para el rol cazador
        agente_cazador_externo = cargar_agente_externo(args.agente_cazador, Rol.CAZADOR)
        print(f"[Versus] Cazador externo cargado: {args.agente_cazador}")

    if args.agente_evasor:
        # Cargar agente externo para el rol evasor
        agente_evasor_externo = cargar_agente_externo(args.agente_evasor, Rol.PRESA)
        print(f"[Versus] Evasor externo cargado: {args.agente_evasor}")

    # ── Inicializar Pygame ─────────────────────────────────────────────────
    pygame.init()
    pygame.display.set_caption("Evasor vs Cazador — Laberinto IA")

    ancho_ventana = COLS * TAMANO_CELDA             # Ancho total de la ventana
    alto_ventana  = FILAS * TAMANO_CELDA + ALTO_HUD # Alto total con HUD

    pantalla = pygame.display.set_mode((ancho_ventana, alto_ventana))
    reloj    = pygame.time.Clock()

    # ── Fuentes ────────────────────────────────────────────────────────────
    fuentes = {
        "titulo": pygame.font.SysFont("consolas", 36, bold=True),
        "opcion": pygame.font.SysFont("consolas", 24),
        "grande": pygame.font.SysFont("consolas", 38, bold=True),
        "hud":    pygame.font.SysFont("consolas", 18),
        "chica":  pygame.font.SysFont("consolas", 15),
    }

    # Ancho mínimo para que el texto de los submenús quepa sin recortarse.
    # 760 px garantiza que las opciones más largas (≈714 px) entren con margen.
    # El helper _blit_centrado de render.py añade auto-escala de seguridad.
    ANCHO_MIN_MENU = 760
    ALTO_MIN_MENU  = 560

    # ── Bucle de menús ─────────────────────────────────────────────────────
    while True:
        # Garantizar ventana mínima para los menús antes de cada iteración
        if ancho_ventana < ANCHO_MIN_MENU or alto_ventana < ALTO_MIN_MENU:
            ancho_ventana = ANCHO_MIN_MENU
            alto_ventana  = ALTO_MIN_MENU
            pantalla = pygame.display.set_mode((ancho_ventana, alto_ventana))

        # Paso 1: ingresar tamaño libre del laberinto
        tamano_n = ejecutar_input_tamano(
            pantalla, reloj, fuentes, ancho_ventana, alto_ventana,
        )
        if tamano_n is None:
            break    # ESC en el primer paso: salir del programa

        # Calcular tamaño de celda y dimensiones del juego SIN redimensionar aún.
        # La ventana apunta a ~85 % de la pantalla con un tope de 900 px.
        info = pygame.display.Info()
        ventana_obj = min(info.current_w * 85 // 100,
                          info.current_h * 85 // 100 - ALTO_HUD,
                          900)
        tamano_celda = max(4, min(64, ventana_obj // tamano_n))
        ancho_juego  = tamano_n * tamano_celda
        alto_juego   = tamano_n * tamano_celda + ALTO_HUD

        # Pasos 2-4: submenús en la ventana actual (suficientemente grande)
        # El resize ocurre solo cuando el juego va a empezar, no antes.
        idx_esc = ejecutar_subMenu(
            pantalla, reloj, fuentes,
            "Paso 2 — Elige el ESCENARIO",
            NOMBRES_ESCENARIOS,
            ancho_ventana, alto_ventana,
        )
        if idx_esc is None:
            continue   # ESC: volver al paso anterior

        idx_cfg = ejecutar_subMenu(
            pantalla, reloj, fuentes,
            "Paso 3 — Elige la CONFIGURACIÓN",
            NOMBRES_CONFIGS,
            ancho_ventana, alto_ventana,
        )
        if idx_cfg is None:
            continue   # ESC: volver al paso anterior

        idx_rol = ejecutar_subMenu(
            pantalla, reloj, fuentes,
            "Paso 4 — Elige tu ROL",
            NOMBRES_ROLES,
            ancho_ventana, alto_ventana,
        )
        if idx_rol is None:
            continue   # ESC: volver al paso anterior

        # Solo ahora redimensionar la ventana al tamaño del laberinto elegido
        config.TAMANO_CELDA = tamano_celda
        ancho_ventana = ancho_juego
        alto_ventana  = alto_juego
        pantalla = pygame.display.set_mode((ancho_ventana, alto_ventana))

        # Mapear índice de config a letra
        configuracion = "A" if idx_cfg == 0 else "B"

        # Ejecutar la partida con los parámetros elegidos
        continuar = ejecutar_partida(
            pantalla, reloj, fuentes,
            semilla, idx_rol, configuracion, idx_esc,
            ancho_ventana, alto_ventana,
            tamano_n=tamano_n,
            tamano_celda=tamano_celda,
            agente_cazador_externo=agente_cazador_externo,
            agente_evasor_externo=agente_evasor_externo,
        )
        if not continuar:
            break   # El usuario cerró la ventana o eligió salir

    # ── Cerrar Pygame limpiamente ──────────────────────────────────────────
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
