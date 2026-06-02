"""
cazador_bfs.py — Agente de ejemplo para modo versus entre equipos.

Propósito
---------
Este archivo demuestra cómo otro equipo puede entregar su agente para
enfrentarlo contra nuestro proyecto.  La ÚNICA restricción es:
  - La clase debe heredar de agentes.base.Agente.
  - Debe implementar decidir_movimiento(estado) → Direccion.

Estrategia de este ejemplo
---------------------------
BFS simple desde la posición del cazador hasta la posición del evasor.
No usa pesos ni heurísticas: siempre toma el paso óptimo en distancia.
Es menos sofisticado que Dijkstra (sin pesos de peligro) pero sirve para
demostrar que la interfaz funciona con código externo.

Complejidad
-----------
Por decisión: O(n²) — BFS completo en el laberinto n×n.
Espacio:      O(n²) — diccionario de visitados y cola.

Uso en línea de comandos
------------------------
    python main.py --agente-cazador agentes_externos.cazador_bfs:CazadorBFS
    python main.py --agente-cazador agentes_externos.cazador_bfs:CazadorBFS \\
                   --agente-evasor  algoritmos.dfs_memo:EstrategiaDFSMemo
"""

from __future__ import annotations          # Permite anotaciones de tipo diferidas
from collections import deque               # Cola FIFO para el BFS

# Importamos la interfaz del proyecto: Agente, Direccion, EstadoJuego, Rol
from agentes.base import Agente, Direccion, EstadoJuego, Rol, Celda


class CazadorBFS(Agente):
    """
    Agente cazador que usa BFS para encontrar el camino más corto al evasor.

    Hereda de Agente (obligatorio para todos los agentes externos).
    Solo implementa decidir_movimiento; los demás métodos son opcionales.
    """

    def __init__(self, rol: Rol) -> None:
        """
        Constructor: recibe el rol asignado por el cargador y lo pasa a Agente.

        Args:
            rol: Rol.CAZADOR o Rol.PRESA (asignado automáticamente por main.py).
        """
        super().__init__(rol)    # Llamar al constructor de la clase base Agente

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        """
        Decide el movimiento del tick actual usando BFS.

        Calcula el camino más corto (en pasos) desde la posición propia
        hasta la posición del oponente y devuelve la dirección del primer paso.

        Args:
            estado: Instantánea del juego en este tick (posiciones, laberinto…).

        Returns:
            Direccion hacia la que moverse (NOOP si no hay camino).
        """
        # Ejecutar BFS desde la posición propia hasta el oponente
        siguiente = self._bfs_primer_paso(
            estado.laberinto,       # El mapa del laberinto
            estado.pos_propia,      # Posición de este agente
            estado.pos_oponente,    # Posición del oponente (destino)
        )

        if siguiente is None:
            return Direccion.NOOP   # Sin camino: quedarse quieto

        # Convertir la celda siguiente en una dirección de movimiento
        return self._celda_a_direccion(estado.pos_propia, siguiente)

    # ── BFS ───────────────────────────────────────────────────────────────────

    def _bfs_primer_paso(
        self,
        laberinto,              # Laberinto con el mapa del juego
        origen: Celda,          # Celda de partida de este agente
        destino: Celda,         # Celda objetivo (el oponente)
    ):
        """
        BFS estándar para encontrar el camino más corto.

        En lugar de devolver la ruta completa, solo devuelve la celda
        inmediatamente siguiente al origen (el primer paso).

        Complejidad: O(n²) — visita a lo sumo todas las celdas del laberinto.

        Returns:
            Celda del primer paso hacia destino, o None si no hay camino.
        """
        # Caso trivial: ya estamos en el destino
        if origen == destino:
            return None

        # visitados guarda la celda predecesora de cada celda descubierta
        visitados: dict[Celda, Celda | None] = {origen: None}

        # Cola del BFS: comienza desde el origen
        cola: deque[Celda] = deque([origen])

        # Recorrer el laberinto en anchura hasta encontrar el destino
        while cola:
            actual = cola.popleft()   # Sacar la primera celda de la cola (FIFO)

            # Explorar todos los vecinos transitables de la celda actual
            for vecino in laberinto.vecinos_transitables(actual):
                if vecino in visitados:
                    continue                    # Ya fue visitado: ignorar

                visitados[vecino] = actual      # Registrar predecesor del vecino
                cola.append(vecino)             # Encolar para seguir explorando

                if vecino == destino:
                    # Encontramos el destino: reconstruir y devolver el primer paso
                    return self._primer_paso(visitados, origen, destino)

        return None   # No existe camino entre origen y destino

    @staticmethod
    def _primer_paso(
        visitados: dict[Celda, Celda | None],   # Mapa de predecesores del BFS
        origen: Celda,                           # Punto de partida
        destino: Celda,                          # Punto de llegada
    ) -> Celda:
        """
        Reconstruye la ruta hacia atrás desde destino y devuelve el segundo elemento,
        que es el primer paso a dar desde origen.

        Returns:
            La celda inmediatamente después del origen en el camino óptimo.
        """
        # Recorrer la cadena de predecesores desde destino hasta origen
        actual = destino                # Empezar desde el destino
        while visitados[actual] != origen:
            actual = visitados[actual]  # Retroceder al predecesor

        return actual   # Esta es la celda justo después del origen

    @staticmethod
    def _celda_a_direccion(origen: Celda, destino: Celda) -> Direccion:
        """
        Convierte un desplazamiento entre dos celdas adyacentes en una Direccion.

        Calcula la diferencia fila/columna y busca la Direccion que coincide.

        Returns:
            Direccion correspondiente al movimiento, o NOOP si no hay coincidencia.
        """
        df = destino[0] - origen[0]    # Diferencia de filas (−1=arriba, +1=abajo)
        dc = destino[1] - origen[1]    # Diferencia de columnas (−1=izq, +1=der)
        for d in Direccion:
            if d.value == (df, dc):
                return d               # Dirección que corresponde al desplazamiento
        return Direccion.NOOP          # Celdas no adyacentes o sin coincidencia
