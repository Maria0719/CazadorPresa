"""
registro.py — Captura de métricas de partida y exportación a CSV.

Qué se registra por cada partida
----------------------------------
  - tamaño n y tipo de escenario
  - configuración (A o B)
  - resultado (cazador captura o evasor escapa)
  - tick en que ocurrió el resultado
  - longitud del camino recorrido por cada agente
  - nodos expandidos por cada algoritmo (suma de todos los ticks)
  - tiempo de cómputo total por algoritmo (suma de todos los ticks)
  - tiempo de cómputo promedio por decisión

Formato del CSV
---------------
  Los datos se guardan en salidas/partidas.csv con cabecera en la primera fila.
"""

from __future__ import annotations
import csv                         # Módulo estándar para leer/escribir CSV
import os                          # Manejo de rutas y directorios
from dataclasses import dataclass  # Estructura de datos

from config import SALIDAS_DIR     # Directorio donde se guardan los resultados


# ══════════════════════════════════════════════════════════════════════════════
# Dataclass: un registro de partida
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class RegistroPartida:
    """Almacena todas las métricas de una partida completa."""

    # ── Configuración del experimento ──────────────────────────────────────
    tamano_n: int = 0              # Lado del laberinto (n en n×n)
    tipo_escenario: str = ""       # Nombre del escenario (texto)
    configuracion: str = "A"       # Configuración "A" o "B"

    # ── Resultado ──────────────────────────────────────────────────────────
    resultado: str = ""            # "cazador_gana" o "evasor_gana"
    ticks_totales: int = 0         # Tick en que terminó la partida

    # ── Camino recorrido ───────────────────────────────────────────────────
    pasos_cazador: int = 0         # Celdas distintas visitadas por el cazador
    pasos_evasor: int = 0          # Celdas distintas visitadas por el evasor

    # ── Métricas del algoritmo del cazador ─────────────────────────────────
    nodos_cazador: int = 0         # Suma de nodos expandidos en todos los ticks
    tiempo_total_cazador: float = 0.0    # Tiempo total de cómputo (seg)
    tiempo_promedio_cazador: float = 0.0 # Tiempo promedio por decisión (seg)

    # ── Métricas del algoritmo del evasor ─────────────────────────────────
    nodos_evasor: int = 0          # Suma de nodos expandidos en todos los ticks
    tiempo_total_evasor: float = 0.0    # Tiempo total de cómputo (seg)
    tiempo_promedio_evasor: float = 0.0 # Tiempo promedio por decisión (seg)


# ══════════════════════════════════════════════════════════════════════════════
# Acumulador tick a tick (para usar desde el motor)
# ══════════════════════════════════════════════════════════════════════════════

class AcumuladorMetricas:
    """
    Acumula métricas tick a tick durante una partida.

    Uso en el motor:
        acum = AcumuladorMetricas()
        # ... en cada tick:
        acum.registrar_tick_cazador(nodos, tiempo_seg)
        acum.registrar_tick_evasor(nodos, tiempo_seg)
        # Al final:
        registro = acum.finalizar(n, escenario, config, resultado, ticks)
    """

    def __init__(self) -> None:
        """Inicializa todos los acumuladores a cero."""
        self._nodos_cazador: int = 0          # Nodos totales del cazador
        self._tiempo_cazador: float = 0.0     # Tiempo total del cazador
        self._decisiones_cazador: int = 0     # Número de decisiones del cazador

        self._nodos_evasor: int = 0           # Nodos totales del evasor
        self._tiempo_evasor: float = 0.0      # Tiempo total del evasor
        self._decisiones_evasor: int = 0      # Número de decisiones del evasor

        self._pasos_cazador: int = 0          # Movimientos del cazador
        self._pasos_evasor: int = 0           # Movimientos del evasor

    def registrar_tick_cazador(
        self, nodos: int, tiempo: float, se_movio: bool = True
    ) -> None:
        """Registra las métricas de un tick de decisión del cazador."""
        self._nodos_cazador += nodos         # Acumular nodos expandidos
        self._tiempo_cazador += tiempo       # Acumular tiempo de cómputo
        self._decisiones_cazador += 1        # Contar esta decisión
        if se_movio:
            self._pasos_cazador += 1         # Contar paso efectivo

    def registrar_tick_evasor(
        self, nodos: int, tiempo: float, se_movio: bool = True
    ) -> None:
        """Registra las métricas de un tick de decisión del evasor."""
        self._nodos_evasor += nodos          # Acumular nodos expandidos
        self._tiempo_evasor += tiempo        # Acumular tiempo de cómputo
        self._decisiones_evasor += 1         # Contar esta decisión
        if se_movio:
            self._pasos_evasor += 1          # Contar paso efectivo

    def finalizar(
        self,
        tamano_n: int,
        tipo_escenario: str,
        configuracion: str,
        resultado: str,
        ticks_totales: int,
    ) -> RegistroPartida:
        """
        Produce un RegistroPartida con todas las métricas acumuladas.

        Args:
            tamano_n       : Lado del laberinto.
            tipo_escenario : Nombre del escenario (texto).
            configuracion  : "A" o "B".
            resultado      : "cazador_gana" o "evasor_gana".
            ticks_totales  : Tick en que terminó la partida.

        Returns:
            RegistroPartida con todos los campos calculados.
        """
        # Calcular tiempos promedio (evitar división por cero)
        prom_cazador = (
            self._tiempo_cazador / self._decisiones_cazador
            if self._decisiones_cazador > 0 else 0.0
        )
        prom_evasor = (
            self._tiempo_evasor / self._decisiones_evasor
            if self._decisiones_evasor > 0 else 0.0
        )

        return RegistroPartida(
            tamano_n=tamano_n,
            tipo_escenario=tipo_escenario,
            configuracion=configuracion,
            resultado=resultado,
            ticks_totales=ticks_totales,
            pasos_cazador=self._pasos_cazador,
            pasos_evasor=self._pasos_evasor,
            nodos_cazador=self._nodos_cazador,
            tiempo_total_cazador=round(self._tiempo_cazador, 6),
            tiempo_promedio_cazador=round(prom_cazador, 8),
            nodos_evasor=self._nodos_evasor,
            tiempo_total_evasor=round(self._tiempo_evasor, 6),
            tiempo_promedio_evasor=round(prom_evasor, 8),
        )


# ══════════════════════════════════════════════════════════════════════════════
# Exportador CSV
# ══════════════════════════════════════════════════════════════════════════════

def exportar_benchmark_csv(
    filas: list[dict],
    nombre_archivo: str = "benchmark.csv",
) -> str:
    """
    Exporta datos de benchmark (lista de dicts) a un archivo CSV.

    Acepta dicts genéricos; las columnas se deducen de las claves del primer
    elemento (todas las filas deben tener las mismas claves).

    Args:
        filas          : Lista de dicts con los datos del benchmark.
        nombre_archivo : Nombre del archivo CSV dentro de SALIDAS_DIR.

    Returns:
        Ruta completa del archivo CSV generado, o cadena vacía si no hay filas.
    """
    if not filas:
        return ""   # Nada que exportar si la lista está vacía

    os.makedirs(SALIDAS_DIR, exist_ok=True)    # Crear directorio si no existe

    ruta = os.path.join(SALIDAS_DIR, nombre_archivo)   # Ruta completa

    # Obtener campos del primer dict (todas las filas deben tener las mismas claves)
    campos = list(filas[0].keys())

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()          # Escribir cabecera
        writer.writerows(filas)       # Escribir todas las filas

    return ruta   # Devolver ruta del archivo generado
