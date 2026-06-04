# PROYECTO FINAL - ANÁLISIS DE ALGORITMOS

## Contexto General

Este proyecto corresponde al trabajo final de la materia Análisis de Algoritmos.

El objetivo principal es desarrollar un sistema distribuido de simulación y torneo de algoritmos de búsqueda de rutas dentro de un juego de persecución en laberintos.

Actualmente el proyecto está implementado en Python utilizando:

* Pygame (visualización)
* Flask (comunicación entre computadores)
* Requests (consumo de APIs)
* Arquitectura cliente-servidor

---

# Objetivo Final

Permitir que múltiples grupos de estudiantes ejecuten sus algoritmos en computadores distintos conectados a la misma red WiFi.

Cada computador ejecutará un servidor Flask local que recibirá el estado actual de la partida y responderá con el siguiente movimiento calculado por su algoritmo.

El sistema debe permitir:

1. Descubrir automáticamente los equipos conectados.
2. Registrar automáticamente cada equipo.
3. Ejecutar partidas entre algoritmos remotos.
4. Organizar torneos entre los algoritmos.
5. Comparar rendimiento y comportamiento de los algoritmos.

---

# Arquitectura Actual

## Juego Base

Ya existe un juego funcional implementado con:

* Laberintos generados proceduralmente.
* Cazador.
* Presa.
* Motor del juego.
* Sistema de renderizado con Pygame.
* Dijkstra.
* DFS Memoizado.

El juego funciona correctamente de forma local.

---

# Arquitectura Distribuida

## Servidor de Algoritmo

Cada grupo ejecuta:

python -m api.servidor_agente

Este servidor:

* Expone un endpoint Flask.
* Recibe el estado completo de la partida.
* Reconstruye un laberinto remoto.
* Ejecuta el algoritmo del grupo.
* Devuelve un movimiento.

Endpoint principal:

POST /movimiento

Respuesta:

{
"direccion": "ARRIBA"
}

o

{
"direccion": "ABAJO"
}

etc.

---

## Agente Remoto

Existe una implementación:

agentes/agente_remoto.py

Este agente:

* Recibe un EstadoJuego.
* Lo serializa a JSON.
* Lo envía vía HTTP al computador remoto.
* Recibe la dirección calculada.
* La devuelve al motor.

El motor no sabe si el algoritmo es local o remoto.

---

## Serialización

Existe:

api/serializador.py

Convierte:

EstadoJuego

a

JSON

incluyendo:

* grid
* filas
* columnas
* salidas
* posición propia
* posición del oponente
* tiempo restante
* tick
* rol

---

# Servidor de Torneo

Existe:

python -m api.servidor_torneo

Funciones implementadas:

* Registro automático.
* Consulta de equipos.
* Detección ONLINE/OFFLINE.
* Descubrimiento automático de participantes.

Endpoints:

POST /registrar

GET /equipos

---

# Sistema de Torneo

Existe:

torneo.py

Actualmente permite:

1. Consultar equipos ONLINE.
2. Seleccionar cazador.
3. Seleccionar presa.
4. Seleccionar tamaño del laberinto.
5. Seleccionar escenario.
6. Iniciar una partida real.

---

# Sistema Bestia

Existe:

torneo_bestia.py

Actualmente permite:

* Seleccionar una bestia inicial.
* Enfrentar retadores.
* Actualizar la bestia.
* Determinar un campeón.

Actualmente el ganador se selecciona manualmente.

---

# Estado Actual del Proyecto

## Funciona

* Juego local.
* Motor.
* Laberintos.
* Pygame.
* Flask.
* Comunicación entre computadores.
* Agentes remotos.
* Descubrimiento de equipos.
* Registro automático.
* Partidas remotas.
* Sistema Bestia básico.

---

# Restricciones Importantes

NO modificar:

* Motor principal si no es estrictamente necesario.
* Generador de laberintos funcional.
* Sistema de render que ya funciona.
* Comunicación Flask existente salvo mejoras.

Mantener compatibilidad con:

* Agentes locales.
* Agentes remotos.
* Modo IA vs IA.
* Modo humano vs IA.

---

# Cómo Participa un Grupo

Cada grupo debe:

1. Tener el proyecto.
2. Instalar dependencias.
3. Conectarse a la misma red WiFi.
4. Configurar:

* Nombre del grupo.
* Algoritmo.
* Puerto.

5. Ejecutar:

python -m api.servidor_agente

El servidor debe registrarse automáticamente en el servidor de torneo.

---

# Dependencias

requirements.txt

pygame>=2.0
matplotlib>=3.5
numpy>=1.22
flask
requests

---

# Lo Que Falta Implementar

## Prioridad Alta

### Detección Automática del Ganador

Actualmente:

Partida termina
↓
Usuario selecciona ganador manualmente

Debe convertirse en:

Partida termina
↓
Motor devuelve ResultadoPartida
↓
Torneo detecta ganador automáticamente

---

### Integrar ResultadoPartida con torneo.py

Objetivo:

resultado = ejecutar_partida_torneo(...)

if resultado == ResultadoPartida.GANA_CAZADOR:
ganador = cazador
else:
ganador = presa

---

### Sistema Bestia Automático

Actualmente:

Usuario indica ganador.

Debe convertirse en:

Partida termina
↓
Ganador detectado automáticamente
↓
Actualizar bestia
↓
Siguiente enfrentamiento

---

## Prioridad Media

### Ranking

Registrar:

* Victorias
* Derrotas
* Participaciones

Por algoritmo.

---

### Historial de Partidas

Guardar:

* Fecha
* Participantes
* Ganador
* Escenario
* Tamaño del mapa

---

### Exportación de Resultados

CSV o JSON.

---

# Objetivo Final del Proyecto

Construir una plataforma distribuida donde múltiples algoritmos de distintos computadores puedan competir entre sí utilizando Flask, compartiendo información del estado del juego en tiempo real y permitiendo realizar torneos automáticos para comparar estrategias de búsqueda y toma de decisiones.
