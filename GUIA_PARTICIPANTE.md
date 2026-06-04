# GUIA_PARTICIPANTE

Esta guia explica como conectar tu propio algoritmo al sistema de torneo.
No necesitas conocer la arquitectura interna del proyecto.

---

## 1. Requisitos minimos

- Python 3.10 o superior.
- Acceso a la red WiFi donde corre el servidor de torneo.
- Tu algoritmo implementado en Python.

---

## 2. Dependencias

Instala las dependencias del proyecto:

```
pip install -r requirements.txt
```

---

## 3. Estructura minima necesaria

Debes tener en tu carpeta:

- `api/servidor_agente.py` (o una copia de ese archivo).
- Tu archivo de algoritmo (por ejemplo: `mi_algoritmo.py`).
- El resto del proyecto (recomendado) o al menos las carpetas:
  - `agentes/`
  - `api/`
  - `laberinto/`

Si no tienes todo el proyecto, pide al profesor o al grupo anfitrion una copia.

---

## 4. Como implementar un algoritmo compatible

Crea un archivo, por ejemplo `mi_algoritmo.py`, con una clase que herede de
`Agente` y que implemente `decidir_movimiento(estado)`.

Ejemplo minimo:

```python
from agentes.base import Agente, Direccion, EstadoJuego

class MiAlgoritmo(Agente):
    def decidir_movimiento(self, estado: EstadoJuego) -> Direccion:
        # Tu logica aqui
        return Direccion.NOOP
```

Reglas:

- La clase debe heredar de `Agente`.
- Debe devolver una `Direccion` valida.
- Debe responder rapido (sin bloquear).

---

## 5. Como configurar nombre del grupo

Abre `api/servidor_agente.py` y edita:

```python
NOMBRE_GRUPO = "Tu Nombre de Grupo"
ALGORITMO = "Nombre de tu Algoritmo"
```

---

## 6. Como configurar puerto

En `api/servidor_agente.py` define:

```python
PUERTO_AGENTE = 5000
```

Cada grupo debe usar un puerto distinto si varios corren en el mismo equipo.

---

## 7. Como conectarse al servidor de torneo

En `api/servidor_agente.py` configura:

```python
IP_SERVIDOR_TORNEO = "IP_DEL_SERVIDOR"
PUERTO_TORNEO = 6000
```

El servidor de torneo te dara su IP (por ejemplo 192.168.1.11).

---

## 8. Como probar localmente

1. Abre una terminal.
2. Activa tu entorno virtual si lo usas.
3. Ejecuta:

```
python -m api.servidor_agente
```

Si todo esta bien, veras un mensaje de registro.

Puedes probar el algoritmo localmente con otro agente local o remoto.

---

## 9. Como participar desde otro computador en la misma red WiFi

1. Conecta tu computador a la misma red WiFi.
2. Configura `IP_SERVIDOR_TORNEO` con la IP del servidor principal.
3. Ejecuta:

```
python -m api.servidor_agente
```

4. Espera el mensaje de registro.
5. El organizador del torneo te podra seleccionar desde el menu.

---

## Resumen rapido

1. Implementa tu clase heredando de `Agente`.
2. Configura nombre, algoritmo, IP y puerto en `api/servidor_agente.py`.
3. Ejecuta `python -m api.servidor_agente`.
4. Asegurate de estar en la misma red WiFi.

Si tienes dudas, contacta al grupo anfitrion.
