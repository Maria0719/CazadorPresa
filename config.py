"""
config.py — Parámetros globales configurables del juego y del benchmark.
Modifica estos valores para cambiar el comportamiento de la partida y los experimentos.
"""

# ── Laberinto ──────────────────────────────────────────────────────────────
COLS: int = 21          # Columnas del laberinto (debe ser impar para el generador)
FILAS: int = 21         # Filas del laberinto (debe ser impar)
SEMILLA: int | None = None  # None = aleatoria; int = reproducible

# ── Tipo de escenario ──────────────────────────────────────────────────────
# 0 = CON_OBSTACULOS     → laberinto clásico con paredes (comportamiento base)
# 1 = CAMINOS_MULTIPLES  → muchos ciclos, varias rutas alternativas
# 2 = CUELLO_DE_BOTELLA  → barrera central con pocas aberturas
ESCENARIO: int = 0

# ── Configuración de agentes (A o B) ──────────────────────────────────────
# "A" → Cazador = Dijkstra (voraz),        Evasor = DFS memoizado (PD)
# "B" → Cazador = DFS memoizado (PD),      Evasor = Dijkstra (voraz)
CONFIGURACION: str = "A"

# ── Ventana ────────────────────────────────────────────────────────────────
TAMANO_CELDA: int = 32  # Píxeles por celda
FPS: int = 60           # Frames por segundo objetivo

# ── Velocidad de movimiento ────────────────────────────────────────────────
# Cantidad de frames que tarda una entidad en avanzar UNA celda.
FRAMES_POR_CELDA: int = 8   # Menor = más rápido

# ── Tiempo de partida ──────────────────────────────────────────────────────
TIEMPO_LIMITE_SEG: int = 90  # Segundos antes de que la presa gane

# ── IA: profundidad del DFS memoizado ──────────────────────────────────────
DFS_PROFUNDIDAD: int = 6     # Profundidad máxima de búsqueda del DFS

# ── IA: recálculo de Dijkstra ──────────────────────────────────────────────
DIJKSTRA_RECALCULO: int = 1  # Recalcular el camino cada N ticks de movimiento

# ── Benchmark ──────────────────────────────────────────────────────────────
# Tamaños de laberinto (lado n de la cuadrícula n×n) para el experimento.
# Deben ser impares para el algoritmo generador.
BENCHMARK_TAMANOS: list = [11, 21, 31, 41, 51, 61, 71, 81, 91, 101]

# Repeticiones por tamaño: promedia para reducir varianza
BENCHMARK_REPETICIONES: int = 5

# Ticks máximos por partida simulada en benchmark (evita partidas infinitas)
BENCHMARK_MAX_TICKS: int = 2000

# Directorio de salida para CSV y PNG
SALIDAS_DIR: str = "salidas"

# ── Colores (R, G, B) ─────────────────────────────────────────────────────
COLOR_FONDO: tuple = (15, 15, 30)
COLOR_PARED: tuple = (40, 40, 80)
COLOR_SUELO: tuple = (200, 210, 230)
COLOR_PRESA: tuple = (80, 220, 100)
COLOR_CAZADOR: tuple = (220, 60, 60)
COLOR_SALIDA: tuple = (255, 215, 0)
COLOR_HUD: tuple = (255, 255, 255)
COLOR_CAMINO_DEBUG: tuple = (100, 100, 200)  # Ruta del cazador (debug)

MOSTRAR_CAMINO_DEBUG: bool = False  # True = dibuja la ruta del cazador
