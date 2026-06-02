# Evasor vs Cazador — Laberinto IA

Proyecto final de **Análisis de Algoritmos** (ABET SO1 / SO6).  
Dos agentes autónomos compiten en un laberinto generado aleatoriamente usando
**Dijkstra** (enfoque voraz) y **DFS Memoizado** (programación dinámica).

---

## Requisitos

```
Python 3.10+
pygame
matplotlib
numpy
```

Instalar dependencias:

```bash
pip install pygame matplotlib numpy
```

---

## Ejecutar el juego

```bash
python main.py                          # menú interactivo, semilla aleatoria
python main.py --semilla 42             # laberinto reproducible (mismo mapa)
python main.py --debug                  # muestra la ruta del cazador
python main.py --config B               # arranca con Config B preseleccionada
python main.py --escenario 2            # arranca con cuello de botella
```

### Flujo del menú (3 pasos)

| Paso | Elige | Opciones |
|------|-------|----------|
| 1 | **Escenario** | Con obstáculos / Caminos múltiples / Cuello de botella |
| 2 | **Configuración** | Config A (Dijkstra caza, DFS evade) / Config B (DFS caza, Dijkstra evade) |
| 3 | **Rol** | Jugar como evasor / Jugar como cazador / IA vs IA |

### Controles durante la partida

| Tecla | Acción |
|-------|--------|
| Flechas / WASD | Mover la entidad humana |
| R | Reiniciar / volver al menú |
| ESC | Volver al menú / salir |

---

## Ejecutar el benchmark (experimento headless)

```bash
python benchmark.py                             # parámetros por defecto de config.py
python benchmark.py --tamanos 11 21 41 81       # tamaños específicos
python benchmark.py --reps 10                   # 10 repeticiones por tamaño
python benchmark.py --escenario 1               # solo caminos múltiples
python benchmark.py --no-graficas               # solo CSV, sin PNG
python benchmark.py --solo-algoritmos           # no simula partidas completas
```

El benchmark **no usa Pygame** y corre sin ventana.  
Al terminar imprime un resumen en consola y guarda los resultados en `salidas/`.

---

## Configuraciones A y B

| Config | Cazador | Evasor |
|--------|---------|--------|
| **A** | Dijkstra (voraz) | DFS Memoizado (PD) |
| **B** | DFS Memoizado (PD) | Dijkstra (voraz) |

Cada algoritmo está implementado como una **estrategia reutilizable** que
acepta cualquier rol. Las clases son `EstrategiaDijkstra(rol)` y
`EstrategiaDFSMemo(rol)` en `algoritmos/`.

---

## Tipos de escenario

| Nº | Nombre | Descripción |
|----|--------|-------------|
| 0 | Con obstáculos | Laberinto clásico, 15 % de ciclos adicionales |
| 1 | Caminos múltiples | 35 % de ciclos → muchas rutas alternativas |
| 2 | Cuello de botella | Barrera central con 1-2 aberturas (paso forzado) |

Todos los escenarios **garantizan conectividad** entre la posición inicial
del evasor y la salida (verificado por BFS antes de empezar).

---

## Cambiar tamaño / semilla / velocidad

Editar `config.py`:

```python
COLS = 31             # Columnas del laberinto (impar)
FILAS = 31            # Filas del laberinto (impar)
SEMILLA = 42          # None = aleatoria; int = reproducible
FRAMES_POR_CELDA = 4  # Menor = más rápido
TIEMPO_LIMITE_SEG = 120   # Segundos de partida
DFS_PROFUNDIDAD = 8       # Profundidad del DFS (más = mejor IA, más lento)
```

Para el benchmark:

```python
BENCHMARK_TAMANOS    = [11, 21, 31, 41, 51, 61, 71, 81, 91, 101]
BENCHMARK_REPETICIONES = 5
BENCHMARK_MAX_TICKS  = 2000   # Ticks máximos por partida simulada
```

---

## Archivos de salida (CSV y figuras)

Todos en la carpeta `salidas/` (se crea automáticamente):

| Archivo | Descripción |
|---------|-------------|
| `benchmark_algoritmos.csv` | Tiempos medios y nodos expandidos por algoritmo y tamaño |
| `benchmark_partidas.csv` | Resultados de partidas IA vs IA (ticks, pasos, nodos) |
| `grafica_dijkstra.png` | Tiempo vs Tamaño Dijkstra (experimental + teórico) |
| `grafica_dfs_memo.png` | Tiempo vs Tamaño DFS Memo (experimental + teórico) |
| `grafica_comparativa.png` | Ambos algoritmos superpuestos |
| `grafica_partidas.png` | Tasa de victoria del cazador vs tamaño (Config A vs B) |

---

## Algoritmos: complejidad formal

### Dijkstra — enfoque voraz

Usa una cola de prioridad (heap binario).  
En una cuadrícula `n × n` con `V = n²` vértices y `E ≈ 4n²` aristas:

```
T(n) = O((V + E) · log V) = O(n² · log n)
S(n) = O(n²)
```

Como evasor: aumenta el peso de las celdas cercanas al cazador para esquivarlo.

### DFS Memoizado — programación dinámica

Búsqueda en profundidad limitada a `D` niveles con tabla de memoización.  
Clave de memo: `(pos_agente, pos_oponente, profundidad)`.

```
T(n) = O(D · n²)   práctica (estados reachables en D pasos)
T(n) = O(D · n⁴)   teórica  (espacio completo de estados)
S(n) = O(D · n⁴)   tabla de memo
```

---

## Modo versus — Enfrentar agentes de otros equipos

Cualquier equipo puede entregar un archivo `.py` con su agente y enfrentarlo
contra nuestro proyecto **sin modificar nada del código fuente**.

### 1. Contrato del agente externo

El archivo del equipo rival debe:
1. Importar `Agente`, `Direccion`, `EstadoJuego` y `Rol` desde `agentes.base`.
2. Crear una clase que **herede de `Agente`**.
3. Implementar `decidir_movimiento(estado) → Direccion`.
4. Aceptar `rol: Rol` en el `__init__` (el cargador lo pasa automáticamente).

**Plantilla mínima** (copiar y pegar en un archivo, p. ej. `mi_equipo/agente.py`):

```python
# mi_equipo/agente.py
from agentes.base import Agente, Direccion, EstadoJuego, Rol

class MiAgente(Agente):
    def __init__(self, rol: Rol) -> None:
        super().__init__(rol)          # Obligatorio: pasar el rol a la clase base

    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        # Tu lógica aquí — debe responder inmediatamente (sin sleep ni IO)
        return Direccion.NOOP          # NOOP es siempre válido (quedarse quieto)
```

El método `inicializar(laberinto, pos_inicial)` es **opcional**; úsalo si
necesitas precomputar información del laberinto antes de que empiece la partida.

### 2. Campo `EstadoJuego` — contrato público

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `laberinto` | `Laberinto` | Mapa completo. Usa `.es_transitable(f,c)` y `.vecinos_transitables(celda)` |
| `pos_propia` | `(fila, col)` | Posición de TU agente |
| `pos_oponente` | `(fila, col)` | Posición del oponente |
| `rol` | `Rol.PRESA` / `Rol.CAZADOR` | Tu rol |
| `tiempo_restante` | `float` | Segundos restantes |
| `salidas` | `list[(fila,col)]` | Celdas de salida (evasor gana al pisarlas) |
| `tick` | `int` | Número de tick actual |

### 3. Correr un versus por línea de comandos

Usa el argumento `--agente-cazador` o `--agente-evasor` con el formato
`modulo.submodulo:NombreClase`:

```bash
# Nuestro Dijkstra (cazador) vs el agente BFS de ejemplo (evasor)
python main.py --agente-evasor agentes_externos.cazador_bfs:CazadorBFS

# El BFS de ejemplo (cazador) vs nuestra IA DFS interna (evasor)
python main.py --agente-cazador agentes_externos.cazador_bfs:CazadorBFS

# Dos agentes externos enfrentados (uno de cada equipo)
python main.py --agente-cazador equipo_a.agente:CazadorEquipoA \
               --agente-evasor  equipo_b.agente:EvasorEquipoB
```

El argumento acepta cualquier módulo que esté en el `PYTHONPATH`
(o en la carpeta raíz del proyecto).

### 4. Reglas del contrato

- `decidir_movimiento` debe **devolver inmediatamente** (sin `sleep` ni IO bloqueante).
- Si devuelve una dirección hacia una pared, el motor la ignora (entidad queda quieta).
- `Direccion.NOOP` siempre es válido.
- Exponer `self.nodos_expandidos: int` y `self.tiempo_ultima_decision: float` permite
  que el motor registre métricas de tu agente automáticamente.

### 5. Agente de ejemplo incluido

`agentes_externos/cazador_bfs.py` contiene `CazadorBFS`: un cazador que usa BFS
simple para demostrar la integración. Está comentado línea por línea.

```bash
# Probar el agente de ejemplo como cazador
python main.py --agente-cazador agentes_externos.cazador_bfs:CazadorBFS
```

---

## Estructura del proyecto

```
main.py                         Punto de entrada y menú multi-paso
benchmark.py                    Experimento headless + CSV + PNG
config.py                       Todos los parámetros configurables
algoritmos/
  dijkstra.py                   EstrategiaDijkstra (cazador o evasor)
  dfs_memo.py                   EstrategiaDFSMemo  (cazador o evasor)
agentes/
  base.py                       Clase Agente + EstadoJuego (contrato)
  humano.py                     Control por teclado
agentes_externos/
  cazador_bfs.py                Agente de ejemplo: cazador BFS (para versus)
laberinto/
  generador.py                  Recursive Backtracker + 3 escenarios + conectividad
juego/
  motor.py                      Ticks, colisiones, victoria, métricas, headless
metricas/
  registro.py                   Acumulador de métricas + exportación CSV
ui/
  render.py                     Dibujo del laberinto, entidades y HUD
salidas/                        CSV y figuras generados (creado automáticamente)
README.md
```

---

## Semilla para torneos

Para que ambos equipos jueguen en el **mismo laberinto**:

```bash
python main.py --semilla 12345 --config A --escenario 0
```

Misma semilla + mismo escenario → condiciones idénticas para todos los agentes.
