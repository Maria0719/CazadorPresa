"""
generador.py — Generación aleatoria del laberinto con tres tipos de escenario
y verificación de conectividad garantizada.

Algoritmo base: Recursive Backtracker (DFS sobre celdas pares)
  1. Se parte de una cuadrícula toda-paredes.
  2. Se "talla" el camino saltando de celda par en celda par.
  3. Según el tipo de escenario se ajusta la densidad de ciclos y obstáculos.

Tipos de escenario
------------------
  0 — CON_OBSTACULOS    : laberinto clásico, 15 % de ciclos adicionales.
  1 — CAMINOS_MULTIPLES : laberinto con 35 % de ciclos → muchas rutas.
  2 — CUELLO_DE_BOTELLA : barrera central con 1-2 aberturas forzadas.
"""

from __future__ import annotations
import random
from collections import deque
from typing import Optional


# ── Tipo alias ─────────────────────────────────────────────────────────────
Celda = tuple[int, int]       # (fila, columna)

# ── Constantes de celda ─────────────────────────────────────────────────────
PARED: int = 1                # Celda bloqueada
SUELO: int = 0                # Celda transitable

# ── Tipos de escenario ──────────────────────────────────────────────────────
CON_OBSTACULOS: int    = 0    # Laberinto estándar con paredes (obstáculos)
CAMINOS_MULTIPLES: int = 1    # Más ciclos → múltiples rutas alternativas
CUELLO_DE_BOTELLA: int = 2    # Barrera central con pocas aberturas


class Laberinto:
    """Representa el laberinto como una cuadrícula de enteros (0=suelo, 1=pared)."""

    def __init__(
        self,
        filas: int,
        cols: int,
        semilla: Optional[int] = None,
        tipo_escenario: int = CON_OBSTACULOS,
    ) -> None:
        """
        Construye y genera el laberinto según el tipo de escenario.

        Args:
            filas:          Número de filas (se fuerza impar ≥ 5).
            cols:           Número de columnas (se fuerza impar ≥ 5).
            semilla:        Semilla aleatoria; None = aleatoria.
            tipo_escenario: 0=obstáculos, 1=caminos múltiples, 2=cuello de botella.
        """
        # Forzar impares mínimo 5 para que el algoritmo backtracker funcione
        self.filas: int = max(5, filas if filas % 2 == 1 else filas + 1)
        self.cols: int  = max(5, cols  if cols  % 2 == 1 else cols  + 1)
        self.semilla: Optional[int] = semilla          # Guardar para reproducibilidad
        self.tipo_escenario: int = tipo_escenario      # Tipo elegido

        # Generador aleatorio reproducible (misma semilla = mismo laberinto)
        self.rng = random.Random(semilla)

        # Cuadrícula principal: grid[fila][col] → PARED o SUELO
        self.grid: list[list[int]] = [
            [PARED] * self.cols for _ in range(self.filas)
        ]

        # Paso 1: generar el laberinto base (árbol de expansión)
        self._generar()

        # Paso 2: configurar según el tipo de escenario
        self._configurar_escenario(tipo_escenario)

        # Paso 3: elegir salida y verificar conectividad
        self.salidas: list[Celda] = self._elegir_salidas()
        self._garantizar_conectividad()   # Asegura que siempre hay un camino

    # ── Generación base (Recursive Backtracker) ─────────────────────────────

    def _generar(self) -> None:
        """Recursive Backtracker: talla caminos desde la celda (1,1)."""
        inicio: Celda = (1, 1)           # Punto de partida del tallado
        self.grid[1][1] = SUELO          # Marcar la celda inicial como suelo
        pila: list[Celda] = [inicio]     # Pila para el DFS iterativo

        while pila:
            actual = pila[-1]                                 # Celda en el tope
            vecinos = self._vecinos_sin_visitar(actual)       # Vecinos no visitados
            if vecinos:
                siguiente = self.rng.choice(vecinos)          # Elige al azar
                self._derribar_pared(actual, siguiente)       # Rompe la pared intermedia
                self.grid[siguiente[0]][siguiente[1]] = SUELO # Abre la celda destino
                pila.append(siguiente)                        # Avanza al siguiente
            else:
                pila.pop()                                    # Retrocede (backtrack)

    def _vecinos_sin_visitar(self, celda: Celda) -> list[Celda]:
        """Devuelve celdas par-vecinas (distancia 2) que aún son pared."""
        fila, col = celda
        candidatos = [
            (fila - 2, col),   # Norte (distancia 2)
            (fila + 2, col),   # Sur
            (fila, col - 2),   # Oeste
            (fila, col + 2),   # Este
        ]
        # Filtrar: dentro del borde interior y aún paredes
        return [
            c for c in candidatos
            if 0 < c[0] < self.filas - 1
            and 0 < c[1] < self.cols - 1
            and self.grid[c[0]][c[1]] == PARED
        ]

    def _derribar_pared(self, a: Celda, b: Celda) -> None:
        """Elimina la pared entre dos celdas par-vecinas (la celda intermedia)."""
        fila_medio = (a[0] + b[0]) // 2    # Fila de la pared entre a y b
        col_medio  = (a[1] + b[1]) // 2   # Columna de la pared entre a y b
        self.grid[fila_medio][col_medio] = SUELO   # Abrir la pared intermedia

    # ── Configuración por escenario ─────────────────────────────────────────

    def _configurar_escenario(self, tipo: int) -> None:
        """Aplica la transformación de escenario al laberinto base ya generado."""
        if tipo == CON_OBSTACULOS:
            # Escenario estándar: pocos ciclos adicionales (15 %)
            self._agregar_ciclos(fraccion=0.15)
        elif tipo == CAMINOS_MULTIPLES:
            # Muchos ciclos (35 %) → muchas rutas alternativas entre dos puntos
            self._agregar_ciclos(fraccion=0.35)
        elif tipo == CUELLO_DE_BOTELLA:
            # Pocos ciclos (5 %) y luego añade barrera horizontal con 1-2 aberturas
            self._agregar_ciclos(fraccion=0.05)
            self._crear_cuello_de_botella()

    # ── Ciclos adicionales ─────────────────────────────────────────────────

    def _agregar_ciclos(self, fraccion: float) -> None:
        """
        Perfora una fracción de las paredes internas para crear bucles.
        Esto hace que el laberinto NO sea un árbol perfecto y añade
        alternativas de ruta (más justo para la presa).
        """
        # Recolectar paredes internas donde tiene sentido abrir
        paredes_internas = [
            (f, c)
            for f in range(1, self.filas - 1)
            for c in range(1, self.cols - 1)
            if self.grid[f][c] == PARED
            and self._tiene_suelos_opuestos(f, c)
        ]
        # Calcular cuántas paredes abrir
        cantidad = max(1, int(len(paredes_internas) * fraccion))
        # Elegir aleatoriamente las paredes a eliminar
        elegidas = self.rng.sample(paredes_internas, min(cantidad, len(paredes_internas)))
        for f, c in elegidas:
            self.grid[f][c] = SUELO   # Abrir la pared → crear ciclo

    def _tiene_suelos_opuestos(self, fila: int, col: int) -> bool:
        """
        Comprueba si una pared tiene suelo en al menos dos lados opuestos
        (horizontal u vertical). Condición para que al abrirla cree un ciclo útil.
        """
        arriba = fila > 0 and self.grid[fila - 1][col] == SUELO
        abajo  = fila < self.filas - 1 and self.grid[fila + 1][col] == SUELO
        izq    = col  > 0 and self.grid[fila][col - 1] == SUELO
        der    = col  < self.cols - 1 and self.grid[fila][col + 1] == SUELO
        return (arriba and abajo) or (izq and der)   # Opuestos verticales u horizontales

    # ── Cuello de botella ─────────────────────────────────────────────────

    def _crear_cuello_de_botella(self) -> None:
        """
        Crea una barrera horizontal en el tercio central del laberinto con
        sólo 1-2 aberturas, forzando a ambos agentes a pasar por ese punto.

        Las aberturas se colocan en columnas impares (posiciones de celda del
        backtracker) y se fuerza suelo en la fila inmediatamente superior e
        inferior a cada abertura.  Esto garantiza que la abertura sea siempre
        atravesable sin necesidad de perforar celdas aleatorias.
        """
        # Fila de la barrera: al 40 % de la altura; siempre impar
        fila_barrera = max(2, int(self.filas * 0.40))
        if fila_barrera % 2 == 0:
            fila_barrera += 1
        # Asegurar al menos una fila interior arriba y abajo
        fila_barrera = max(2, min(self.filas - 3, fila_barrera))

        # Cerrar toda la fila de la barrera
        for col in range(1, self.cols - 1):
            self.grid[fila_barrera][col] = PARED

        # Número de aberturas según el ancho del laberinto
        num_aberturas = 1 if self.cols < 21 else 2

        # Usar solo columnas impares: en el backtracker son posiciones de celda,
        # por lo que la fila adyacente (par) puede forzarse a suelo sin romper
        # la estructura del laberinto.
        cols_impares = [c for c in range(1, self.cols - 1) if c % 2 == 1]
        paso = max(1, len(cols_impares) // (num_aberturas + 1))
        cols_aberturas = [
            cols_impares[min(paso * (i + 1), len(cols_impares) - 1)]
            for i in range(num_aberturas)
        ]

        for col in cols_aberturas:
            self.grid[fila_barrera][col] = SUELO             # Abertura en la barrera
            # Forzar suelo en las celdas adyacentes para garantizar paso
            if fila_barrera - 1 >= 1:
                self.grid[fila_barrera - 1][col] = SUELO
            if fila_barrera + 1 <= self.filas - 2:
                self.grid[fila_barrera + 1][col] = SUELO

    # ── Garantizar conectividad ─────────────────────────────────────────────

    def _garantizar_conectividad(self) -> None:
        """
        Verifica que (1,1) esté conectado a cada salida; si no, abre celdas
        aleatoriamente hasta lograr la conectividad. Máximo 1000 intentos.

        En el escenario CUELLO_DE_BOTELLA protege la fila de la barrera para
        no destruir el cuello al perforar celdas aleatorias.
        """
        # Calcular fila protegida para el cuello de botella
        fila_protegida: int | None = None
        if self.tipo_escenario == CUELLO_DE_BOTELLA:
            fila_protegida = max(2, int(self.filas * 0.40))
            if fila_protegida % 2 == 0:
                fila_protegida += 1

        for salida in self.salidas:
            intentos = 0
            while not self.verificar_conectividad((1, 1), salida) and intentos < 1000:
                fila = self.rng.randint(1, self.filas - 2)
                col  = self.rng.randint(1, self.cols - 2)
                # No perforar la barrera del cuello de botella
                if fila_protegida is not None and fila == fila_protegida:
                    intentos += 1
                    continue
                self.grid[fila][col] = SUELO
                intentos += 1

    # ── Salidas ────────────────────────────────────────────────────────────

    def _elegir_salidas(self) -> list[Celda]:
        """
        Busca la celda transitable más cercana a la esquina inferior-derecha
        para colocar la salida del laberinto.
        """
        objetivo = (self.filas - 2, self.cols - 2)   # Celda objetivo (esquina)
        # Buscar en espiral desde la esquina
        for df in range(self.filas):
            for dc in range(self.cols):
                for signo_f, signo_c in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    f = objetivo[0] + signo_f * df
                    c = objetivo[1] + signo_c * dc
                    if 0 <= f < self.filas and 0 <= c < self.cols:
                        if self.grid[f][c] == SUELO:
                            return [(f, c)]    # Devolver la primera celda transitable
        return [(self.filas - 2, self.cols - 2)]   # Fallback si todo falla

    # ── Utilidades públicas ─────────────────────────────────────────────────

    def es_transitable(self, fila: int, col: int) -> bool:
        """Devuelve True si la celda es suelo y está dentro del mapa."""
        return (
            0 <= fila < self.filas
            and 0 <= col < self.cols
            and self.grid[fila][col] == SUELO    # Solo suelo es transitable
        )

    def vecinos_transitables(self, celda: Celda) -> list[Celda]:
        """Devuelve las celdas adyacentes (4-vecindad) que son transitables."""
        fila, col = celda
        candidatos = [
            (fila - 1, col),   # Norte
            (fila + 1, col),   # Sur
            (fila, col - 1),   # Oeste
            (fila, col + 1),   # Este
        ]
        return [c for c in candidatos if self.es_transitable(c[0], c[1])]

    def verificar_conectividad(self, origen: Celda, destino: Celda) -> bool:
        """
        BFS para comprobar que existe un camino entre origen y destino.
        Usada en pruebas y al iniciar la partida para garantizar jugabilidad.
        """
        visitados: set[Celda] = {origen}          # Conjunto de celdas visitadas
        cola: deque[Celda] = deque([origen])      # Cola del BFS
        while cola:
            actual = cola.popleft()
            if actual == destino:
                return True                        # Camino encontrado
            for vecino in self.vecinos_transitables(actual):
                if vecino not in visitados:
                    visitados.add(vecino)
                    cola.append(vecino)
        return False                               # Sin camino

    def celda_libre_lejana(self, referencia: Celda, min_distancia: int = 10) -> Celda:
        """
        BFS desde 'referencia'; devuelve la celda transitable más lejana
        en pasos BFS que además esté a ≥ min_distancia pasos de referencia.

        Si no existe ninguna celda tan lejana (laberinto muy pequeño), devuelve
        la celda más lejana disponible como fallback.
        Garantiza que existe camino entre referencia y el retorno.

        Args:
            referencia    : Celda de origen del BFS.
            min_distancia : Distancia mínima deseada en pasos BFS.
        """
        visitados: dict[Celda, int] = {referencia: 0}    # Distancia BFS por celda
        cola: deque[Celda] = deque([referencia])          # Cola del BFS

        mas_lejana_global: Celda = referencia    # Celda más lejana sin restricción
        max_dist_global: int = 0                 # Su distancia
        mas_lejana_min: Celda = referencia       # Celda más lejana con ≥ min_distancia
        max_dist_min: int = 0                    # Su distancia

        while cola:
            actual = cola.popleft()
            dist = visitados[actual]

            # Candidato para la celda más lejana en general (sin filtro)
            if dist > max_dist_global:
                max_dist_global = dist
                mas_lejana_global = actual

            # Candidato para la celda más lejana que cumple min_distancia
            if dist >= min_distancia and dist > max_dist_min:
                max_dist_min = dist
                mas_lejana_min = actual

            for vecino in self.vecinos_transitables(actual):
                if vecino not in visitados:
                    visitados[vecino] = dist + 1
                    cola.append(vecino)

        # Preferir la celda que cumple la distancia mínima; si no existe, usar fallback
        return mas_lejana_min if max_dist_min > 0 else mas_lejana_global

    def nombre_escenario(self) -> str:
        """Devuelve el nombre legible del tipo de escenario."""
        nombres = {
            CON_OBSTACULOS:    "Con obstáculos",
            CAMINOS_MULTIPLES: "Caminos múltiples",
            CUELLO_DE_BOTELLA: "Cuello de botella",
        }
        return nombres.get(self.tipo_escenario, "Desconocido")
