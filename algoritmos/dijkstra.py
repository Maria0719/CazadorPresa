"""
dijkstra.py — Estrategia Dijkstra reutilizable como CAZADOR o EVASOR.

Descripción del enfoque (voraz / greedy)
-----------------------------------------
Dijkstra es un algoritmo voraz porque en cada paso elige localmente el
nodo de menor costo acumulado (decisión ávida) sin retroceder.  No evalúa
el futuro: confía en que el camino óptimo local lleva al óptimo global.

Roles
-----
• Como CAZADOR: calcula el camino de menor costo desde su posición hasta
  la posición actual del evasor; recalcula cada DIJKSTRA_RECALCULO ticks.

• Como EVASOR: calcula el camino de menor costo hacia la salida, asignando
  pesos altos a las celdas cercanas al cazador para esquivarlo.

Complejidad formal
------------------
  T(n) = O((V + E) · log V)

  En una cuadrícula n × n:
    V = n²          (vértices = celdas)
    E ≈ 4 · n²      (aristas = hasta 4 vecinos por celda)

  Sustituyendo:
    T(n) = O((n² + 4n²) · log n²) = O(n² · log n)

  Espacio: O(n²) para los diccionarios de costo y predecesor.
"""

from __future__ import annotations
import heapq                         # Montículo binario para la cola de prioridad
import time                          # Medición de tiempo por decisión
from collections import deque        # Cola para BFS de pesos del evasor
from typing import Optional

from agentes.base import Agente, Direccion, EstadoJuego, Rol, Celda, celda_a_direccion
from laberinto.generador import Laberinto
from config import DIJKSTRA_RECALCULO

# ── Constante de peligro ────────────────────────────────────────────────────
# Peso adicional que se asigna a celdas cercanas al cazador cuando el evasor
# calcula su ruta.  Un valor alto desanima al evasor a pasar cerca del cazador.
_PESO_PELIGRO: float = 20.0

# ── Radio de peligro ────────────────────────────────────────────────────────
# Celdas a esta distancia BFS del cazador reciben peso aumentado.
_RADIO_PELIGRO: int = 4


# ══════════════════════════════════════════════════════════════════════════════
# Función pura del algoritmo (usada también por benchmark.py)
# ══════════════════════════════════════════════════════════════════════════════

def dijkstra_puro(
    laberinto: Laberinto,
    origen: Celda,
    destino: Celda,
    pesos: dict[Celda, float],
) -> tuple[list[Celda], float, int]:
    """
    Algoritmo de Dijkstra puro sobre el grafo del laberinto.

    Complejidad: O(n² log n) para cuadrícula n×n con cola de prioridad heap.

    Args:
        laberinto : Objeto Laberinto con el mapa.
        origen    : Celda de inicio (fila, col).
        destino   : Celda objetivo (fila, col).
        pesos     : Mapa celda → costo de entrada.  Celdas ausentes usan 1.0.

    Returns:
        (ruta, costo_total, nodos_expandidos)
        ruta             : lista de celdas desde la siguiente al origen hasta destino.
        costo_total      : costo acumulado del camino (float).
        nodos_expandidos : cantidad de nodos sacados de la cola (métrica).
    """
    # Cola de prioridad: entradas (costo_acumulado, celda)
    cola: list[tuple[float, Celda]] = [(0.0, origen)]

    # Mejor costo conocido para llegar a cada celda
    costo: dict[Celda, float] = {origen: 0.0}

    # Celda predecesora para reconstruir la ruta al final
    predecesor: dict[Celda, Optional[Celda]] = {origen: None}

    # Contador de nodos expandidos (métrica para el informe)
    nodos_expandidos: int = 0

    while cola:
        costo_actual, actual = heapq.heappop(cola)   # Extraer nodo de menor costo
        nodos_expandidos += 1                         # Contar expansión

        if actual == destino:
            # Destino alcanzado: reconstruir y devolver la ruta
            ruta = _reconstruir_ruta(predecesor, destino)
            return ruta, costo_actual, nodos_expandidos

        # Descartar si ya conocemos un camino más barato (entrada obsoleta en la cola)
        if costo_actual > costo.get(actual, float("inf")):
            continue

        # Explorar vecinos transitables
        for vecino in laberinto.vecinos_transitables(actual):
            # Costo para entrar al vecino (1.0 por defecto = peso uniforme)
            w = pesos.get(vecino, 1.0)
            nuevo_costo = costo_actual + w          # Costo acumulado hasta el vecino

            if nuevo_costo < costo.get(vecino, float("inf")):
                # Encontramos un camino más barato al vecino: actualizar
                costo[vecino] = nuevo_costo
                predecesor[vecino] = actual         # Registrar predecesor para ruta
                heapq.heappush(cola, (nuevo_costo, vecino))  # Encolar con nuevo costo

    # Sin camino al destino
    return [], float("inf"), nodos_expandidos


def _reconstruir_ruta(
    predecesor: dict[Celda, Optional[Celda]],
    destino: Celda,
) -> list[Celda]:
    """
    Reconstruye la ruta desde el diccionario de predecesores.

    Recorre desde destino hacia atrás hasta None (el origen),
    luego invierte la lista para obtener origen→destino.

    Returns:
        Lista de celdas desde la siguiente al origen hasta destino (excluye origen).
    """
    ruta: list[Celda] = []            # Acumulará la ruta en orden inverso
    actual: Optional[Celda] = destino # Comenzar desde el destino
    while actual is not None:
        ruta.append(actual)           # Agregar celda actual a la ruta
        actual = predecesor[actual]   # Retroceder al predecesor
    ruta.reverse()                    # Invertir: ahora va de origen a destino
    return ruta[1:]                   # Excluir el origen (posición actual del agente)


def _calcular_pesos_evasor(
    laberinto: Laberinto,
    pos_cazador: Celda,
) -> dict[Celda, float]:
    """
    Genera un mapa de pesos para el evasor usando BFS desde el cazador.

    Celdas a distancia d < _RADIO_PELIGRO del cazador reciben un peso
    adicional proporcional a su cercanía: más cerca → más peligroso.

    Complejidad: O(n²) — BFS completo desde el cazador.
    """
    pesos: dict[Celda, float] = {}             # Mapa resultado (solo celdas peligrosas)
    visitados: dict[Celda, int] = {pos_cazador: 0}   # Distancia BFS desde cazador
    cola: deque[Celda] = deque([pos_cazador])         # Cola del BFS

    while cola:
        celda = cola.popleft()
        dist = visitados[celda]                # Distancia actual al cazador

        if dist < _RADIO_PELIGRO:
            # Factor de peligro: 1.0 (muy cerca) a ~0.0 (en el borde del radio)
            factor = (_RADIO_PELIGRO - dist) / _RADIO_PELIGRO
            pesos[celda] = 1.0 + _PESO_PELIGRO * factor   # Peso = base + peligro

            # Expandir a los vecinos transitables
            for vecino in laberinto.vecinos_transitables(celda):
                if vecino not in visitados:
                    visitados[vecino] = dist + 1   # Registrar distancia del vecino
                    cola.append(vecino)             # Encolar para continuar BFS

    return pesos   # Mapa de pesos: celdas no incluidas usan peso 1.0 por defecto


# ══════════════════════════════════════════════════════════════════════════════
# Agente estrategia Dijkstra (reutilizable para ambos roles)
# ══════════════════════════════════════════════════════════════════════════════

class EstrategiaDijkstra(Agente):
    """
    Agente que usa Dijkstra como estrategia de movimiento.

    Acepta Rol.CAZADOR o Rol.PRESA; el comportamiento cambia según el rol.

    Complejidad por decisión: O(n² log n) donde n es el lado del laberinto.
    Espacio adicional: O(n²) para los mapas de costo y predecesor.

    Atributos de métricas (accesibles desde motor/benchmark):
        nodos_expandidos        : nodos expandidos en la última decisión.
        tiempo_ultima_decision  : segundos que tardó la última decisión.
    """

    def __init__(
        self,
        rol: Rol,
        pesos_extra: Optional[dict[Celda, float]] = None,
    ) -> None:
        """
        Args:
            rol         : Rol.CAZADOR o Rol.PRESA.
            pesos_extra : Pesos adicionales por celda (opcional).
        """
        super().__init__(rol)                              # Inicializar clase base
        self._pesos_extra: dict[Celda, float] = pesos_extra or {}  # Pesos extra opcionales
        self._ruta: list[Celda] = []                       # Ruta calculada actualmente
        self._ticks_desde_recalculo: int = 0               # Ticks desde último cálculo
        self._laberinto: Optional[Laberinto] = None        # Referencia al laberinto

        # ── Métricas expuestas ──────────────────────────────────────────────
        self.nodos_expandidos: int = 0        # Nodos expandidos en la última decisión
        self.tiempo_ultima_decision: float = 0.0  # Tiempo de la última decisión (seg)

    def inicializar(self, laberinto: Laberinto, pos_inicial: Celda) -> None:
        """Guarda el laberinto y reinicia el estado interno al empezar la partida."""
        self._laberinto = laberinto    # Guardar referencia al laberinto
        self._ruta = []                # Limpiar ruta previa
        self._ticks_desde_recalculo = 0  # Reiniciar contador de recálculo

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        """
        Decide el próximo movimiento usando Dijkstra según el rol del agente.

        Mide el tiempo de cómputo y lo almacena en self.tiempo_ultima_decision.
        Los nodos expandidos quedan en self.nodos_expandidos.
        """
        t_inicio = time.perf_counter()   # Iniciar medición de tiempo

        if self.rol == Rol.CAZADOR:
            resultado = self._decidir_como_cazador(estado)   # Cazador: perseguir
        else:
            resultado = self._decidir_como_evasor(estado)    # Evasor: huir

        # Registrar tiempo total de esta decisión
        self.tiempo_ultima_decision = time.perf_counter() - t_inicio
        return resultado

    # ── Cazador ────────────────────────────────────────────────────────────

    def _decidir_como_cazador(self, estado: EstadoJuego) -> Direccion:
        """
        Como cazador: sigue el camino de menor costo hacia el evasor.

        Recalcula la ruta cada DIJKSTRA_RECALCULO ticks o cuando la ruta
        queda vacía (ya llegó a la última celda calculada).
        """
        # Determinar si es necesario recalcular la ruta
        recalcular = (
            self._ticks_desde_recalculo >= DIJKSTRA_RECALCULO   # Período de recálculo
            or not self._ruta                                     # Ruta vacía
        )

        if recalcular:
            # Calcular ruta desde posición propia hasta posición del evasor
            ruta, _, expandidos = dijkstra_puro(
                estado.laberinto,
                estado.pos_propia,
                estado.pos_oponente,
                self._pesos_extra,    # Pesos extra (uniforme por defecto)
            )
            self._ruta = ruta                       # Actualizar ruta calculada
            self.nodos_expandidos = expandidos      # Guardar métrica de expansiones
            self._ticks_desde_recalculo = 0         # Reiniciar contador
        else:
            self._ticks_desde_recalculo += 1        # Incrementar contador
            self.nodos_expandidos = 0               # No hubo cálculo este tick

        if not self._ruta:
            return Direccion.NOOP   # Sin ruta disponible: quedarse quieto

        # El primer elemento de _ruta es la siguiente celda a visitar
        siguiente = self._ruta[0]
        return celda_a_direccion(estado.pos_propia, siguiente)

    # ── Evasor ─────────────────────────────────────────────────────────────

    def _decidir_como_evasor(self, estado: EstadoJuego) -> Direccion:
        """
        Como evasor: sigue el camino de menor costo hacia la salida,
        penalizando celdas cercanas al cazador con pesos aumentados.

        Recalcula cada tick porque tanto el cazador como el evasor se mueven.
        """
        if not estado.salidas:
            return Direccion.NOOP   # Sin salidas definidas: no hacer nada

        # Calcular mapa de pesos con peligro basado en la posición del cazador
        pesos = _calcular_pesos_evasor(estado.laberinto, estado.pos_oponente)
        pesos.update(self._pesos_extra)   # Superponer pesos extra si los hay

        mejor_ruta: list[Celda] = []         # Mejor ruta encontrada hasta ahora
        mejor_costo: float = float("inf")    # Costo de la mejor ruta
        total_expandidos: int = 0            # Suma de nodos expandidos en todas las ejecuciones

        # Probar cada salida y quedarnos con la ruta de menor costo
        for salida in estado.salidas:
            ruta, costo, expandidos = dijkstra_puro(
                estado.laberinto,
                estado.pos_propia,
                salida,
                pesos,
            )
            total_expandidos += expandidos   # Acumular nodos expandidos

            if costo < mejor_costo and ruta:
                mejor_costo = costo          # Actualizar mejor costo
                mejor_ruta = ruta            # Actualizar mejor ruta

        self.nodos_expandidos = total_expandidos   # Guardar métrica total

        if not mejor_ruta:
            return Direccion.NOOP   # Sin ruta encontrada: quedarse quieto

        # Tomar el primer paso de la mejor ruta
        return celda_a_direccion(estado.pos_propia, mejor_ruta[0])

    # ── Propiedad de depuración ─────────────────────────────────────────────

    @property
    def ruta_actual(self) -> list[Celda]:
        """Expone la ruta calculada actualmente (útil para debug/visualización)."""
        return list(self._ruta)
