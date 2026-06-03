"""
dfs_memo.py — Estrategia DFS Memoizado reutilizable como CAZADOR o EVASOR.

Descripción del enfoque (programación dinámica)
------------------------------------------------
El DFS memoizado es un ejemplo de programación dinámica descendente (top-down).
Explora estados futuros con búsqueda en profundidad hasta profundidad D y
almacena (memoiza) los resultados de sub-problemas ya evaluados para no
recalcularlos si se vuelven a encontrar.

Cada "estado" es la terna (pos_agente, pos_oponente, profundidad_restante).
Si ese estado fue evaluado antes, se devuelve el valor cacheado en O(1).

Roles
-----
• Como EVASOR: maximiza la utilidad de supervivencia:
    - Penaliza captura (pos_presa == pos_cazador → −∞)
    - Recompensa llegar a la salida (→ +∞)
    - Heurística: distancia al cazador (más es mejor) − distancia a salida (menos es mejor)

• Como CAZADOR: maximiza la utilidad de captura:
    - Recompensa captura (pos_cazador == pos_presa → +∞)
    - Heurística: −distancia BFS del cazador a la presa (más cerca = mejor para cazador)
    - El evasor responde greedy (se aleja del cazador)

Clave de memoización
--------------------
    (pos_agente, pos_oponente, profundidad)

  •  pos_agente   : celda (fila, col) del agente que toma la decisión.
  •  pos_oponente : celda (fila, col) del oponente (afecta la utilidad).
  •  profundidad  : profundidad restante (los mismos estados a diferente profundidad
                    tienen valores distintos porque el horizonte temporal cambia).

  La clave distingue ambas posiciones porque la utilidad de estar en (r,c) depende
  de dónde esté el oponente en ese mismo momento.

Complejidad formal
------------------
  Sin memoización: árbol de ramificación b (≤4) con profundidad D → O(b^D).

  Con memoización: cada estado único se calcula una sola vez.
    Estados únicos: |pos_agente| × |pos_oponente| × D = n² × n² × D = D · n⁴

  En la práctica, la búsqueda solo alcanza celdas dentro de D pasos del agente,
  lo que limita significativamente el espacio real explorado:
    Aprox. O(D · n²) estados relevantes por llamada.

  Complejidad por decisión (práctica): O(D · n²)
  Espacio de la memo: O(D · n⁴) teórico, limitado en práctica por _MAX_MEMO.
"""

from __future__ import annotations
import time                         # Medición de tiempo por decisión
from collections import deque       # Cola BFS para precalcular distancias
from typing import Optional

from agentes.base import Agente, Direccion, EstadoJuego, Rol, Celda, celda_a_direccion
from laberinto.generador import Laberinto
from config import DFS_PROFUNDIDAD

# ── Valores terminales ──────────────────────────────────────────────────────
_CAPTURADO: float = float("-inf")   # Utilidad si la presa es capturada (peor para evasor)
_ESCAPADO: float  = float("inf")    # Utilidad si la presa llega a la salida (mejor para evasor)
_CAPTURA_OK: float = float("inf")   # Utilidad si el cazador captura (mejor para cazador)

# ── Límite de la tabla de memoización ──────────────────────────────────────
# Evita que la memo crezca sin límite y agote la memoria en laberintos grandes.
_MAX_MEMO: int = 60_000


# ══════════════════════════════════════════════════════════════════════════════
# Función de utilidad BFS (compartida por ambos roles)
# ══════════════════════════════════════════════════════════════════════════════

def _bfs_distancias(
    laberinto: Laberinto,
    origen: Celda,
    cache: dict[Celda, dict[Celda, int]],
) -> dict[Celda, int]:
    """
    BFS desde `origen`; devuelve distancia en pasos a cada celda transitable.

    Usa `cache` para no repetir BFS desde el mismo origen.
    Complejidad: O(n²) la primera vez; O(1) si ya está en caché.
    """
    if origen in cache:
        return cache[origen]   # Devolver resultado cacheado si existe

    distancias: dict[Celda, int] = {origen: 0}   # Distancia al origen es 0
    cola: deque[Celda] = deque([origen])           # Cola del BFS

    while cola:
        actual = cola.popleft()
        for vecino in laberinto.vecinos_transitables(actual):
            if vecino not in distancias:
                distancias[vecino] = distancias[actual] + 1   # Distancia = padre + 1
                cola.append(vecino)

    # Guardar en caché si no está demasiado llena
    if len(cache) < 500:
        cache[origen] = distancias   # Cachear para futuras consultas

    return distancias


# ══════════════════════════════════════════════════════════════════════════════
# Agente estrategia DFS Memoizado (reutilizable para ambos roles)
# ══════════════════════════════════════════════════════════════════════════════

class EstrategiaDFSMemo(Agente):
    """
    Agente que usa DFS Memoizado como estrategia de movimiento.

    Acepta Rol.CAZADOR o Rol.PRESA; el comportamiento cambia según el rol.

    Complejidad por decisión: O(D · n²) práctica con memoización.
    Espacio adicional: O(D · n⁴) teórico, limitado a _MAX_MEMO entradas.

    Atributos de métricas (accesibles desde motor/benchmark):
        nodos_expandidos        : estados evaluados en la última decisión.
        tiempo_ultima_decision  : segundos que tardó la última decisión.
    """

    def __init__(self, rol: Rol, profundidad: int = DFS_PROFUNDIDAD) -> None:
        """
        Args:
            rol         : Rol.CAZADOR o Rol.PRESA.
            profundidad : Profundidad máxima del DFS (parámetro D).
        """
        super().__init__(rol)                              # Inicializar clase base
        self._profundidad: int = profundidad               # Profundidad máxima D
        self._laberinto: Optional[Laberinto] = None        # Referencia al laberinto
        self._salidas: list[Celda] = []                    # Celdas de salida del mapa

        # Tabla de memoización: (pos_agente, pos_oponente, depth) → utilidad float
        self._memo: dict[tuple[Celda, Celda, int], float] = {}

        # Caché de distancias BFS: origen → {celda: distancia}
        self._dist_cache: dict[Celda, dict[Celda, int]] = {}

        # ── Métricas expuestas ──────────────────────────────────────────────
        self.nodos_expandidos: int = 0        # Estados evaluados en la última decisión
        self.tiempo_ultima_decision: float = 0.0  # Tiempo de la última decisión (seg)
        self._contador_nodos: int = 0         # Contador interno durante el DFS

        # Celda visitada en el tick anterior: evita oscilar entre dos posiciones
        self._pos_anterior: Optional[Celda] = None

    def inicializar(self, laberinto: Laberinto, pos_inicial: Celda) -> None:
        """Guarda el laberinto y limpia el estado interno al empezar la partida."""
        self._laberinto = laberinto   # Guardar referencia al laberinto
        self._memo.clear()            # Limpiar tabla de memoización
        self._dist_cache.clear()      # Limpiar caché de distancias BFS
        self._pos_anterior = None     # Reiniciar historial anti-oscilación

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        """
        Decide el próximo movimiento usando DFS memoizado según el rol del agente.

        Mide el tiempo de cómputo y lo almacena en self.tiempo_ultima_decision.
        Los estados evaluados quedan en self.nodos_expandidos.
        """
        self._salidas = estado.salidas       # Actualizar salidas del estado actual
        self._contador_nodos = 0             # Reiniciar contador de nodos

        t_inicio = time.perf_counter()       # Iniciar medición de tiempo

        if self.rol == Rol.CAZADOR:
            resultado = self._decidir_como_cazador(estado)   # Cazador: capturar
        else:
            resultado = self._decidir_como_evasor(estado)    # Evasor: sobrevivir

        # Registrar métricas de esta decisión
        self.tiempo_ultima_decision = time.perf_counter() - t_inicio
        self.nodos_expandidos = self._contador_nodos

        # Limpiar memo si está muy llena para liberar memoria
        if len(self._memo) > _MAX_MEMO:
            self._memo.clear()

        return resultado

    # ══════════════════════════════════════════════════════════════════════
    # Lógica como EVASOR
    # ══════════════════════════════════════════════════════════════════════

    def _decidir_como_evasor(self, estado: EstadoJuego) -> Direccion:
        """
        Evalúa cada movimiento posible con DFS y elige el de mayor utilidad
        para el evasor (maximizar supervivencia y cercanía a la salida).
        """
        vecinos = self._laberinto.vecinos_transitables(estado.pos_propia)
        if not vecinos:
            return Direccion.NOOP   # Sin movimientos posibles

        # Inicializar con el primer vecino válido: garantiza movimiento incluso
        # cuando todos los valores son -inf (captura inevitable en horizonte D).
        mejor_dir: Direccion = celda_a_direccion(estado.pos_propia, vecinos[0])
        mejor_val: float = float("-inf")

        for vecino in vecinos:
            val = self._dfs_evasor(
                vecino,
                estado.pos_oponente,
                self._profundidad - 1,
            )
            # Penalizar levemente volver a la celda anterior para romper empates
            # y evitar que el evasor oscile entre dos posiciones indefinidamente.
            if vecino == self._pos_anterior:
                val -= 0.5
            if val > mejor_val:
                mejor_val = val
                mejor_dir = celda_a_direccion(estado.pos_propia, vecino)

        self._pos_anterior = estado.pos_propia
        return mejor_dir

    def _dfs_evasor(
        self,
        pos_evasor: Celda,
        pos_cazador: Celda,
        profundidad: int,
    ) -> float:
        """
        DFS recursivo desde la perspectiva del evasor.

        El evasor MAXIMIZA utilidad.
        El cazador responde de forma greedy (se mueve al vecino más cercano al evasor).
        La memoización evita recalcular el mismo estado (pos_evasor, pos_cazador, prof).

        Args:
            pos_evasor  : Celda actual del evasor.
            pos_cazador : Celda actual del cazador.
            profundidad : Profundidad restante en el árbol de búsqueda.

        Returns:
            Utilidad estimada del estado (float; mayor = mejor para el evasor).
        """
        self._contador_nodos += 1   # Contar este estado como evaluado

        # Caso base: captura inmediata → peor resultado para el evasor
        if pos_evasor == pos_cazador:
            return _CAPTURADO

        # Caso base: profundidad agotada → evaluar heurística del estado
        if profundidad == 0:
            return self._utilidad_evasor(pos_evasor, pos_cazador)

        # Clave para la tabla de memoización
        clave = (pos_evasor, pos_cazador, profundidad)
        if clave in self._memo:
            return self._memo[clave]   # Devolver resultado ya calculado

        # Turno del evasor: explorar sus movimientos posibles
        vecinos_evasor = self._laberinto.vecinos_transitables(pos_evasor)
        opciones = vecinos_evasor if vecinos_evasor else [pos_evasor]   # NOOP si no hay

        mejor = _CAPTURADO   # Peor caso inicial para el evasor
        for v_evasor in opciones:
            # Simular respuesta del cazador (movimiento greedy hacia el evasor)
            v_cazador = self._movimiento_greedy_cazador(pos_cazador, v_evasor)

            # Llamada recursiva con un nivel menos de profundidad
            val = self._dfs_evasor(v_evasor, v_cazador, profundidad - 1)
            if val > mejor:
                mejor = val   # El evasor elige el mejor resultado posible

        # Guardar en memo si hay espacio
        if len(self._memo) < _MAX_MEMO:
            self._memo[clave] = mejor

        return mejor

    def _utilidad_evasor(self, pos_evasor: Celda, pos_cazador: Celda) -> float:
        """
        Función heurística de utilidad para el evasor en el horizonte del DFS.

        Combina:
          - Distancia BFS al cazador × 2.0  (más lejos = mejor)
          - Distancia BFS a la salida × 1.0 (más cerca = mejor)

        Returns:
            Valor flotante; mayor es mejor para el evasor.
        """
        if pos_evasor == pos_cazador:
            return _CAPTURADO   # Capturado: utilidad mínima

        # Distancias BFS (con caché para evitar recalcular)
        dist_desde_evasor = _bfs_distancias(self._laberinto, pos_evasor, self._dist_cache)

        # Distancia al cazador (maximizar = alejarse)
        dist_cazador = dist_desde_evasor.get(pos_cazador, 999)

        # Distancia a la salida más cercana (minimizar = acercarse)
        dist_salida = min(
            (dist_desde_evasor.get(s, 999) for s in self._salidas),
            default=999,
        )

        if dist_salida == 0:
            return _ESCAPADO   # Llegó a la salida: utilidad máxima

        # Combinar: alejarse del cazador tiene doble peso que acercarse a salida
        return dist_cazador * 2.0 - dist_salida * 1.0

    def _movimiento_greedy_cazador(self, pos_cazador: Celda, objetivo: Celda) -> Celda:
        """
        Simula el movimiento greedy del cazador hacia el objetivo (el evasor).

        Elige el vecino del cazador con menor distancia BFS al objetivo.
        Si no hay vecinos, el cazador permanece quieto.

        Complejidad: O(n²) para el BFS (con caché: O(1)).
        """
        vecinos_caz = self._laberinto.vecinos_transitables(pos_cazador)
        if not vecinos_caz:
            return pos_cazador   # Sin movimientos: quedarse quieto

        # BFS desde el OBJETIVO para medir qué tan cerca está cada vecino del cazador al objetivo.
        # (BFS desde cazador daría distancia 1 a todos los vecinos → elección arbitraria.)
        dist_desde_objetivo = _bfs_distancias(self._laberinto, objetivo, self._dist_cache)

        mejor_vecino = min(
            vecinos_caz,
            key=lambda c: dist_desde_objetivo.get(c, 999),
        )
        return mejor_vecino

    # ══════════════════════════════════════════════════════════════════════
    # Lógica como CAZADOR
    # ══════════════════════════════════════════════════════════════════════

    def _decidir_como_cazador(self, estado: EstadoJuego) -> Direccion:
        """
        Evalúa cada movimiento posible con DFS y elige el de mayor utilidad
        para el cazador (maximizar probabilidad de captura).
        """
        vecinos = self._laberinto.vecinos_transitables(estado.pos_propia)
        if not vecinos:
            return Direccion.NOOP   # Sin movimientos posibles

        # Inicializar con el primer vecino válido: garantiza movimiento incluso
        # cuando todos los valores son -inf.
        mejor_dir: Direccion = celda_a_direccion(estado.pos_propia, vecinos[0])
        mejor_val: float = float("-inf")

        for vecino in vecinos:
            val = self._dfs_cazador(
                vecino,
                estado.pos_oponente,
                self._profundidad - 1,
            )
            if vecino == self._pos_anterior:
                val -= 0.5
            if val > mejor_val:
                mejor_val = val
                mejor_dir = celda_a_direccion(estado.pos_propia, vecino)

        self._pos_anterior = estado.pos_propia
        return mejor_dir

    def _dfs_cazador(
        self,
        pos_cazador: Celda,
        pos_evasor: Celda,
        profundidad: int,
    ) -> float:
        """
        DFS recursivo desde la perspectiva del cazador.

        El cazador MAXIMIZA utilidad de captura.
        El evasor responde de forma greedy (se aleja del cazador).
        La memoización evita recalcular el mismo estado (pos_cazador, pos_evasor, prof).

        Args:
            pos_cazador : Celda actual del cazador.
            pos_evasor  : Celda actual del evasor.
            profundidad : Profundidad restante en el árbol de búsqueda.

        Returns:
            Utilidad estimada (float; mayor = mejor para el cazador).
        """
        self._contador_nodos += 1   # Contar este estado como evaluado

        # Caso base: captura inmediata → mejor resultado para el cazador
        if pos_cazador == pos_evasor:
            return _CAPTURA_OK

        # Caso base: profundidad agotada → evaluar heurística del estado
        if profundidad == 0:
            return self._utilidad_cazador(pos_cazador, pos_evasor)

        # Clave para la tabla de memoización (orden: cazador, evasor para diferenciarlo del rol evasor)
        clave = (pos_cazador, pos_evasor, profundidad)
        if clave in self._memo:
            return self._memo[clave]   # Devolver resultado ya calculado

        # Turno del cazador: explorar sus movimientos posibles
        vecinos_cazador = self._laberinto.vecinos_transitables(pos_cazador)
        opciones = vecinos_cazador if vecinos_cazador else [pos_cazador]  # NOOP si no hay

        mejor = float("-inf")   # Peor caso inicial para el cazador
        for v_cazador in opciones:
            # Simular respuesta del evasor (movimiento greedy alejándose del cazador)
            v_evasor = self._movimiento_greedy_evasor(pos_evasor, v_cazador)

            # Llamada recursiva con un nivel menos de profundidad
            val = self._dfs_cazador(v_cazador, v_evasor, profundidad - 1)
            if val > mejor:
                mejor = val   # El cazador elige el mejor resultado posible

        # Guardar en memo si hay espacio
        if len(self._memo) < _MAX_MEMO:
            self._memo[clave] = mejor

        return mejor

    def _utilidad_cazador(self, pos_cazador: Celda, pos_evasor: Celda) -> float:
        """
        Función heurística de utilidad para el cazador en el horizonte del DFS.

        Cuanto más cerca esté el cazador del evasor, mayor la utilidad.
        Usa la distancia BFS negada: menor distancia → mayor utilidad.

        Returns:
            Valor flotante; mayor es mejor para el cazador.
        """
        if pos_cazador == pos_evasor:
            return _CAPTURA_OK   # Captura: utilidad máxima

        # Distancia BFS del cazador al evasor
        dist_desde_cazador = _bfs_distancias(self._laberinto, pos_cazador, self._dist_cache)
        dist_evasor = dist_desde_cazador.get(pos_evasor, 999)

        # Negado: menor distancia → mayor valor → cazador quiere acercarse
        return -float(dist_evasor)

    def _movimiento_greedy_evasor(self, pos_evasor: Celda, pos_cazador: Celda) -> Celda:
        """
        Simula el movimiento greedy del evasor alejándose del cazador.

        Elige el vecino del evasor con mayor distancia BFS al cazador.
        Si no hay vecinos, el evasor permanece quieto.

        Complejidad: O(n²) para el BFS (con caché: O(1)).
        """
        vecinos_evasor = self._laberinto.vecinos_transitables(pos_evasor)
        if not vecinos_evasor:
            return pos_evasor   # Sin movimientos: quedarse quieto

        # BFS desde el CAZADOR para medir qué tan lejos está cada vecino del cazador.
        # (BFS desde evasor daría distancia 1 a todos sus vecinos → elección arbitraria.)
        dist_desde_cazador = _bfs_distancias(self._laberinto, pos_cazador, self._dist_cache)

        mejor_vecino = max(
            vecinos_evasor,
            key=lambda c: dist_desde_cazador.get(c, 0),
        )
        return mejor_vecino
