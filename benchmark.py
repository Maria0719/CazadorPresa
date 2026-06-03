"""
benchmark.py — Experimento headless: mide tiempos de cómputo vs tamaño de entrada.

Uso
---
    python benchmark.py                    # usa parámetros de config.py
    python benchmark.py --tamanos 11 31 51 # tamaños específicos
    python benchmark.py --reps 10          # 10 repeticiones por tamaño
    python benchmark.py --escenario 1      # solo escenario caminos múltiples
    python benchmark.py --no-graficas      # solo CSV, sin PNG

Salidas
-------
    salidas/benchmark_algoritmos.csv  — tiempos por algoritmo y tamaño
    salidas/benchmark_partidas.csv    — resultados de partidas IA vs IA
    salidas/grafica_dijkstra.png      — Tiempo vs Tamaño Dijkstra (exp + teórico)
    salidas/grafica_dfs_memo.png      — Tiempo vs Tamaño DFS Memo (exp + teórico)
    salidas/grafica_comparativa.png   — ambos algoritmos superpuestos
    salidas/grafica_partidas.png      — tasa de éxito vs tamaño

IMPORTANTE: este módulo NO importa pygame; todo es headless.
"""

from __future__ import annotations
import argparse         # Parseo de argumentos de línea de comandos
import math             # Para la curva teórica de Dijkstra (log)
import os               # Manejo de directorios
import statistics       # Para media y desviación estándar
import sys              # Reconfiguracion de stdout para UTF-8 en Windows
import time             # Medición de tiempos

from agentes.base import EstadoJuego, Rol   # Estado del juego y roles
from algoritmos.dijkstra import EstrategiaDijkstra, dijkstra_puro   # Dijkstra
from algoritmos.dfs_memo import EstrategiaDFSMemo                   # DFS memo
from laberinto.generador import Laberinto                            # Generador
from juego.motor import Motor, ResultadoPartida                      # Motor headless
from metricas.registro import exportar_benchmark_csv  # Exportación
from config import (
    BENCHMARK_TAMANOS, BENCHMARK_REPETICIONES, BENCHMARK_MAX_TICKS,
    SALIDAS_DIR, DFS_PROFUNDIDAD,
)

# ── Intentar importar matplotlib (no requerido para el CSV) ─────────────────
try:
    import matplotlib                   # Motor de gráficas
    matplotlib.use("Agg")               # Backend sin ventana (headless)
    import matplotlib.pyplot as plt     # API de alto nivel para graficar
    import numpy as np                  # Cálculos numéricos para la curva teórica
    _MATPLOTLIB_OK = True               # Bandera: matplotlib disponible
except ImportError:
    _MATPLOTLIB_OK = False              # Sin matplotlib: solo CSV


# ══════════════════════════════════════════════════════════════════════════════
# Funciones de medición (puras, sin Pygame)
# ══════════════════════════════════════════════════════════════════════════════

def medir_dijkstra_puro(
    laberinto: Laberinto,
    origen: tuple,
    destino: tuple,
) -> tuple[float, int]:
    """
    Mide el tiempo de UNA ejecución del algoritmo Dijkstra puro.

    No incluye overhead de agentes ni del motor; solo el algoritmo.
    Usada para la gráfica de tiempo de cómputo vs tamaño.

    Args:
        laberinto : Laberinto ya generado.
        origen    : Celda de inicio (fila, col).
        destino   : Celda de destino (fila, col).

    Returns:
        (tiempo_seg, nodos_expandidos)
    """
    t0 = time.perf_counter()                           # Iniciar cronómetro
    _, _, nodos = dijkstra_puro(laberinto, origen, destino, {})   # Ejecutar
    t1 = time.perf_counter()                           # Detener cronómetro
    return t1 - t0, nodos                              # Devolver tiempo y nodos


def medir_dfs_memo(
    laberinto: Laberinto,
    pos_agente: tuple,
    pos_oponente: tuple,
    salidas: list,
    rol: Rol,
) -> tuple[float, int]:
    """
    Mide el tiempo de UNA decisión del DFS Memoizado.

    Crea un agente temporal, lo inicializa y llama a decidir_movimiento.

    Args:
        laberinto   : Laberinto ya generado.
        pos_agente  : Posición del agente que decide.
        pos_oponente: Posición del oponente.
        salidas     : Celdas de salida del mapa.
        rol         : Rol.CAZADOR o Rol.PRESA.

    Returns:
        (tiempo_seg, nodos_expandidos)
    """
    agente = EstrategiaDFSMemo(rol, profundidad=DFS_PROFUNDIDAD)   # Crear agente
    agente.inicializar(laberinto, pos_agente)                       # Inicializar

    # Construir un EstadoJuego mínimo para la llamada
    estado = EstadoJuego(
        laberinto=laberinto,
        pos_propia=pos_agente,
        pos_oponente=pos_oponente,
        rol=rol,
        tiempo_restante=999.0,   # Tiempo arbitrario (no afecta la lógica)
        salidas=tuple(salidas),
        tick=0,
    )

    t0 = time.perf_counter()                      # Iniciar cronómetro
    agente.decidir_movimiento(estado)             # Ejecutar decisión
    t1 = time.perf_counter()                      # Detener cronómetro
    return t1 - t0, agente.nodos_expandidos       # Devolver tiempo y nodos


# ══════════════════════════════════════════════════════════════════════════════
# Experimento principal: tiempos de algoritmos
# ══════════════════════════════════════════════════════════════════════════════

def experimento_algoritmos(
    tamanos: list[int],
    repeticiones: int,
    tipo_escenario: int = 0,
    semilla_base: int = 42,
) -> list[dict]:
    """
    Mide el tiempo de cada algoritmo sobre múltiples tamaños de laberinto.

    Para cada tamaño n y cada algoritmo:
      - Genera `repeticiones` laberintos distintos (semillas 0..rep-1).
      - Mide el tiempo de ejecución en cada uno.
      - Calcula media y desviación estándar.

    Args:
        tamanos       : Lista de lados n (cuadrícula n×n).
        repeticiones  : Número de laberintos distintos por tamaño.
        tipo_escenario: Tipo de escenario (0, 1 o 2).
        semilla_base  : Base para generar semillas distintas.

    Returns:
        Lista de dicts con los resultados (una fila por tamaño y algoritmo).
    """
    filas: list[dict] = []    # Acumula los resultados para el CSV

    print(f"\n{'='*60}")
    print(f"  EXPERIMENTO: Algoritmos (escenario {tipo_escenario})")
    print(f"  Tamaños: {tamanos}")
    print(f"  Repeticiones por tamaño: {repeticiones}")
    print(f"{'='*60}\n")

    for n in tamanos:
        print(f"  Tamaño n={n}...", end=" ", flush=True)

        tiempos_dij:     list[float] = []
        nodos_dij:       list[int]   = []
        tiempos_dfs_eva: list[float] = []   # DFS como EVASOR (Config A)
        nodos_dfs_eva:   list[int]   = []
        tiempos_dfs_caz: list[float] = []   # DFS como CAZADOR (Config B)
        nodos_dfs_caz:   list[int]   = []

        for rep in range(repeticiones):
            semilla = semilla_base + rep * 1000

            lab         = Laberinto(n, n, semilla=semilla, tipo_escenario=tipo_escenario)
            pos_evasor  = (1, 1)
            pos_cazador = lab.celda_libre_lejana(pos_evasor, min_distancia=n // 3)
            salidas     = lab.salidas

            # Dijkstra puro (sin rol: mide el algoritmo base)
            t_dij, n_dij = medir_dijkstra_puro(lab, pos_evasor, salidas[0])
            tiempos_dij.append(t_dij)
            nodos_dij.append(n_dij)

            # DFS como EVASOR (rol que tiene en Config A)
            t_eva, n_eva = medir_dfs_memo(lab, pos_evasor, pos_cazador, salidas, Rol.PRESA)
            tiempos_dfs_eva.append(t_eva)
            nodos_dfs_eva.append(n_eva)

            # DFS como CAZADOR (rol que tiene en Config B)
            t_caz, n_caz = medir_dfs_memo(lab, pos_cazador, pos_evasor, salidas, Rol.CAZADOR)
            tiempos_dfs_caz.append(t_caz)
            nodos_dfs_caz.append(n_caz)

        def _fila(algoritmo, tiempos, nodos):
            return {
                "tamano_n":       n,
                "tipo_escenario": tipo_escenario,
                "algoritmo":      algoritmo,
                "repeticiones":   repeticiones,
                "tiempo_medio_s": round(statistics.mean(tiempos), 8),
                "tiempo_std_s":   round(statistics.stdev(tiempos) if repeticiones > 1 else 0.0, 8),
                "nodos_medio":    round(statistics.mean(nodos), 1),
                "nodos_std":      round(statistics.stdev(nodos) if repeticiones > 1 else 0.0, 1),
            }

        filas.append(_fila("Dijkstra",     tiempos_dij,     nodos_dij))
        filas.append(_fila("DFS_Evasor",   tiempos_dfs_eva, nodos_dfs_eva))
        filas.append(_fila("DFS_Cazador",  tiempos_dfs_caz, nodos_dfs_caz))

        print(f"Dijkstra: {1000*statistics.mean(tiempos_dij):.3f} ms | "
              f"DFS-Eva: {1000*statistics.mean(tiempos_dfs_eva):.3f} ms | "
              f"DFS-Caz: {1000*statistics.mean(tiempos_dfs_caz):.3f} ms")

    return filas


# ══════════════════════════════════════════════════════════════════════════════
# Experimento de partidas completas IA vs IA
# ══════════════════════════════════════════════════════════════════════════════

def experimento_partidas(
    tamanos: list[int],
    repeticiones: int,
    tipo_escenario: int = 0,
    semilla_base: int = 42,
) -> list[dict]:
    """
    Simula partidas IA vs IA headless para Config A y Config B.

    Mide: resultado (quién ganó), ticks hasta el final, métricas de algoritmos.

    Args:
        tamanos       : Lista de lados n.
        repeticiones  : Repeticiones por tamaño y configuración.
        tipo_escenario: Tipo de escenario.
        semilla_base  : Base para semillas.

    Returns:
        Lista de dicts (una fila por partida simulada).
    """
    filas: list[dict] = []

    print(f"\n{'='*60}")
    print(f"  EXPERIMENTO: Partidas IA vs IA (escenario {tipo_escenario})")
    print(f"{'='*60}\n")

    for config in ["A", "B"]:                   # Probar ambas configuraciones
        for n in tamanos:
            victorias_caz = 0     # Contador de victorias del cazador
            victorias_eva = 0     # Contador de victorias del evasor

            for rep in range(repeticiones):
                semilla = semilla_base + rep * 1000

                # Generar laberinto
                lab = Laberinto(n, n, semilla=semilla, tipo_escenario=tipo_escenario)

                # Crear agentes según configuración
                if config == "A":
                    agente_evasor  = EstrategiaDFSMemo(Rol.PRESA)
                    agente_cazador = EstrategiaDijkstra(Rol.CAZADOR)
                else:
                    agente_evasor  = EstrategiaDijkstra(Rol.PRESA)
                    agente_cazador = EstrategiaDFSMemo(Rol.CAZADOR)

                # Crear motor headless con límite de ticks
                motor = Motor(
                    lab, agente_evasor, agente_cazador,
                    tamano_celda=32,
                    ticks_limite=BENCHMARK_MAX_TICKS,
                    configuracion=config,
                )

                # Simular partida sin render
                registro = motor.simular_headless()

                # Contar victorias
                if registro.resultado == "cazador_gana":
                    victorias_caz += 1
                else:
                    victorias_eva += 1

                # Guardar fila de la partida
                filas.append({
                    "configuracion":          config,
                    "tamano_n":               n,
                    "tipo_escenario":         tipo_escenario,
                    "repeticion":             rep,
                    "resultado":              registro.resultado,
                    "ticks_totales":          registro.ticks_totales,
                    "pasos_cazador":          registro.pasos_cazador,
                    "pasos_evasor":           registro.pasos_evasor,
                    "nodos_cazador":          registro.nodos_cazador,
                    "tiempo_total_cazador_s": registro.tiempo_total_cazador,
                    "tiempo_prom_cazador_s":  registro.tiempo_promedio_cazador,
                    "nodos_evasor":           registro.nodos_evasor,
                    "tiempo_total_evasor_s":  registro.tiempo_total_evasor,
                    "tiempo_prom_evasor_s":   registro.tiempo_promedio_evasor,
                })

            print(f"  Config {config} | n={n:3d} | "
                  f"Cazador gana: {victorias_caz}/{repeticiones} | "
                  f"Evasor gana: {victorias_eva}/{repeticiones}")

    return filas


# ══════════════════════════════════════════════════════════════════════════════
# Generación de gráficas
# ══════════════════════════════════════════════════════════════════════════════

def _curva_teorica_dijkstra(n_vals: list[int], t_med: list[float]) -> list[float]:
    """
    Calcula la curva teórica de Dijkstra: T(n) ≈ C · n² · log₂(n²).

    Ajusta C por mínimos cuadrados sobre todos los puntos experimentales
    (más robusto que usar solo el primer punto, que puede ser outlier).
    Complejidad: O(n² log n) ← O((V+E) log V) para cuadrícula n×n.
    """
    if not n_vals or not t_med:
        return [0.0] * len(n_vals)

    # Vector de la forma funcional evaluada en cada n
    x = np.array([n ** 2 * math.log2(n ** 2 + 1) for n in n_vals])
    y = np.array(t_med)

    # Mínimos cuadrados sin intercepto: C = (x·y) / (x·x)
    denom = float(np.dot(x, x))
    C = float(np.dot(x, y) / denom) if denom > 0 else 0.0

    return [C * n ** 2 * math.log2(n ** 2 + 1) for n in n_vals]


def _curva_teorica_dfs(n_vals: list[int], t_med: list[float]) -> list[float]:
    """
    Calcula la curva teórica del DFS memo: T(n) ≈ C · D · n² (práctica).

    Ajusta C por mínimos cuadrados sobre todos los puntos experimentales.
    Complejidad práctica: O(D · n²) donde D = DFS_PROFUNDIDAD (constante).
    """
    if not n_vals or not t_med:
        return [0.0] * len(n_vals)

    D = DFS_PROFUNDIDAD
    x = np.array([D * n ** 2 for n in n_vals])
    y = np.array(t_med)

    denom = float(np.dot(x, x))
    C = float(np.dot(x, y) / denom) if denom > 0 else 0.0

    return [C * D * n ** 2 for n in n_vals]


def generar_graficas(filas_algoritmos: list[dict]) -> None:
    """
    Genera y guarda las gráficas de Tiempo de Cómputo vs Tamaño de Entrada.

    Para cada algoritmo dibuja:
      - Curva experimental (puntos con barras de error).
      - Curva teórica (línea discontinua con la complejidad formal).

    También genera una gráfica comparativa con ambos algoritmos.
    """
    if not _MATPLOTLIB_OK:
        print("  [!] matplotlib no disponible — solo se generó el CSV.")
        return

    os.makedirs(SALIDAS_DIR, exist_ok=True)    # Crear carpeta si no existe

    # Separar datos por algoritmo
    dij_filas = [f for f in filas_algoritmos if f["algoritmo"] == "Dijkstra"]
    eva_filas = [f for f in filas_algoritmos if f["algoritmo"] == "DFS_Evasor"]
    caz_filas = [f for f in filas_algoritmos if f["algoritmo"] == "DFS_Cazador"]

    def _extraer(filas):
        return (
            [f["tamano_n"]       for f in filas],
            [f["tiempo_medio_s"] for f in filas],
            [f["tiempo_std_s"]   for f in filas],
        )

    ns_dij, t_dij, std_dij = _extraer(dij_filas)
    ns_eva, t_eva, std_eva = _extraer(eva_filas)
    ns_caz, t_caz, std_caz = _extraer(caz_filas)

    # Curvas teóricas ajustadas por mínimos cuadrados
    t_teo_dij = _curva_teorica_dijkstra(ns_dij, t_dij)
    t_teo_eva = _curva_teorica_dfs(ns_eva, t_eva)
    t_teo_caz = _curva_teorica_dfs(ns_caz, t_caz)

    # ── Gráfica 1: Dijkstra ────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.errorbar(ns_dij, t_dij, yerr=std_dij, fmt="o-",
                color="steelblue", capsize=4, label="Experimental")
    ax.plot(ns_dij, t_teo_dij, "--", color="tomato",
            label=r"Teórico: $O(n^2 \log n)$")
    ax.set_xlabel("Tamaño del laberinto (n)", fontsize=13)
    ax.set_ylabel("Tiempo de cómputo (segundos)", fontsize=13)
    ax.set_title("Dijkstra — Tiempo de cómputo vs Tamaño de entrada", fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.4)
    ruta_dij = os.path.join(SALIDAS_DIR, "grafica_dijkstra.png")
    fig.tight_layout()
    fig.savefig(ruta_dij, dpi=150)
    plt.close(fig)
    print(f"  Guardada: {ruta_dij}")

    # ── Gráfica 2: DFS Memoizado (ambos roles) ─────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.errorbar(ns_eva, t_eva, yerr=std_eva, fmt="s-",
                color="mediumseagreen", capsize=4, label="DFS Evasor (exp.)")
    ax.plot(ns_eva, t_teo_eva, "--", color="mediumseagreen", alpha=0.6,
            label=r"Teórico Evasor $O(D \cdot n^2)$")
    ax.errorbar(ns_caz, t_caz, yerr=std_caz, fmt="^-",
                color="darkorchid", capsize=4, label="DFS Cazador (exp.)")
    ax.plot(ns_caz, t_teo_caz, "--", color="darkorchid", alpha=0.6,
            label=r"Teórico Cazador $O(D \cdot n^2)$")
    ax.set_xlabel("Tamaño del laberinto (n)", fontsize=13)
    ax.set_ylabel("Tiempo de cómputo (segundos)", fontsize=13)
    ax.set_title("DFS Memoizado — Tiempo vs Tamaño (Evasor y Cazador)", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.4)
    ruta_dfs = os.path.join(SALIDAS_DIR, "grafica_dfs_memo.png")
    fig.tight_layout()
    fig.savefig(ruta_dfs, dpi=150)
    plt.close(fig)
    print(f"  Guardada: {ruta_dfs}")

    # ── Gráfica 3: Comparativa Dijkstra vs DFS ────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.errorbar(ns_dij, t_dij, yerr=std_dij, fmt="o-",
                color="steelblue", capsize=4, label="Dijkstra (exp.)")
    ax.plot(ns_dij, t_teo_dij, "--", color="steelblue", alpha=0.5,
            label=r"Dijkstra teórico $O(n^2\log n)$")
    ax.errorbar(ns_eva, t_eva, yerr=std_eva, fmt="s-",
                color="mediumseagreen", capsize=4, label="DFS Evasor (exp.)")
    ax.plot(ns_eva, t_teo_eva, "--", color="mediumseagreen", alpha=0.5,
            label=r"DFS teórico $O(D \cdot n^2)$")
    ax.errorbar(ns_caz, t_caz, yerr=std_caz, fmt="^-",
                color="darkorchid", capsize=4, label="DFS Cazador (exp.)")
    ax.set_xlabel("Tamaño del laberinto (n)", fontsize=13)
    ax.set_ylabel("Tiempo de cómputo (segundos)", fontsize=13)
    ax.set_title("Comparativa: Dijkstra vs DFS Memoizado (ambos roles)", fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.4)
    ruta_comp = os.path.join(SALIDAS_DIR, "grafica_comparativa.png")
    fig.tight_layout()
    fig.savefig(ruta_comp, dpi=150)
    plt.close(fig)
    print(f"  Guardada: {ruta_comp}")


def generar_grafica_partidas(filas_partidas: list[dict]) -> None:
    """
    Genera la gráfica de tasa de éxito del cazador vs tamaño de entrada,
    comparando Config A y Config B.
    """
    if not _MATPLOTLIB_OK or not filas_partidas:
        return

    # Agrupar por configuración y tamaño
    from collections import defaultdict
    datos: dict = defaultdict(lambda: defaultdict(list))  # config → n → [1=caz gana, 0=eva gana]

    for f in filas_partidas:
        gano_caz = 1 if f["resultado"] == "cazador_gana" else 0
        datos[f["configuracion"]][f["tamano_n"]].append(gano_caz)

    fig, ax = plt.subplots(figsize=(10, 5))
    colores = {"A": "steelblue", "B": "tomato"}

    for cfg in sorted(datos.keys()):
        ns     = sorted(datos[cfg].keys())              # Tamaños ordenados
        tasas  = [sum(v) / len(v) * 100 for v in [datos[cfg][n] for n in ns]]  # % victorias
        ax.plot(ns, tasas, "o-", color=colores[cfg], label=f"Config {cfg}")

    ax.set_xlabel("Tamaño del laberinto (n)", fontsize=13)
    ax.set_ylabel("Tasa de victoria del cazador (%)", fontsize=13)
    ax.set_title("Tasa de victoria del cazador vs Tamaño (Config A vs B)", fontsize=14)
    ax.set_ylim(0, 105)            # Escala 0-100 %
    ax.axhline(50, color="gray", linestyle="--", alpha=0.5)   # Línea de referencia 50 %
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.4)
    ruta = os.path.join(SALIDAS_DIR, "grafica_partidas.png")
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    print(f"  Guardada: {ruta}")


# ══════════════════════════════════════════════════════════════════════════════
# Punto de entrada
# ══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    """Define y parsea los argumentos de línea de comandos del benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark headless: mide tiempos de Dijkstra y DFS Memo."
    )
    parser.add_argument(
        "--tamanos", type=int, nargs="+", default=None,
        help="Tamaños de laberinto (impares). Ej: 11 21 31 51",
    )
    parser.add_argument(
        "--reps", type=int, default=None,
        help="Repeticiones por tamaño (promedia tiempos).",
    )
    parser.add_argument(
        "--escenario", type=int, choices=[0, 1, 2], default=0,
        help="Tipo de escenario: 0=obstáculos, 1=múltiples, 2=cuello.",
    )
    parser.add_argument(
        "--semilla", type=int, default=42,
        help="Semilla base para generar laberintos reproducibles.",
    )
    parser.add_argument(
        "--no-graficas", action="store_true",
        help="Generar solo CSV sin gráficas PNG.",
    )
    parser.add_argument(
        "--solo-algoritmos", action="store_true",
        help="Solo medir tiempos de algoritmos (sin simular partidas completas).",
    )
    return parser.parse_args()


def main() -> None:
    """Función principal del benchmark."""
    # Forzar UTF-8 en la consola de Windows para evitar mojibake con acentos
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except Exception:
            pass

    args = parse_args()

    # Leer parámetros de argumentos o de config.py
    tamanos      = args.tamanos    if args.tamanos else BENCHMARK_TAMANOS
    repeticiones = args.reps       if args.reps    else BENCHMARK_REPETICIONES
    escenario    = args.escenario
    semilla_base = args.semilla
    hacer_graficas = not args.no_graficas

    print("\n" + "="*60)
    print("  BENCHMARK — Análisis de Algoritmos — Proyecto Final")
    print("="*60)
    print(f"  Tamaños:      {tamanos}")
    print(f"  Repeticiones: {repeticiones}")
    print(f"  Escenario:    {escenario}")
    print(f"  Salidas en:   {SALIDAS_DIR}/")
    print("="*60)

    os.makedirs(SALIDAS_DIR, exist_ok=True)   # Crear carpeta de salidas

    # ── Experimento 1: tiempos de algoritmos ──────────────────────────────
    filas_alg = experimento_algoritmos(tamanos, repeticiones, escenario, semilla_base)

    ruta_alg = exportar_benchmark_csv(filas_alg, "benchmark_algoritmos.csv")
    print(f"\n  CSV guardado: {ruta_alg}")

    # ── Gráficas de tiempos ────────────────────────────────────────────────
    if hacer_graficas:
        print("\n  Generando gráficas de tiempo vs tamaño...")
        generar_graficas(filas_alg)

    # ── Experimento 2: partidas completas IA vs IA ─────────────────────────
    if not args.solo_algoritmos:
        filas_part = experimento_partidas(tamanos, repeticiones, escenario, semilla_base)

        ruta_part = exportar_benchmark_csv(filas_part, "benchmark_partidas.csv")
        print(f"\n  CSV guardado: {ruta_part}")

        if hacer_graficas:
            print("\n  Generando gráfica de partidas...")
            generar_grafica_partidas(filas_part)

    print("\n" + "="*60)
    print("  Benchmark completado.")
    print(f"  Archivos en: {os.path.abspath(SALIDAS_DIR)}/")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
