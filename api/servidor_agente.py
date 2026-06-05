# api/servidor_agente.py

from flask import Flask, request, jsonify

import socket
import requests

from agentes.base import (
    EstadoJuego,
    Rol,
)

# ==================================================
# CONFIGURACION DEL EQUIPO
# ==================================================

NOMBRE_GRUPO = "Grupo BFS"

ALGORITMO = "BFS"

IP_SERVIDOR_TORNEO = "192.168.1.11"

PUERTO_TORNEO = 6000

PUERTO_AGENTE = 5000

# ==================================================
# ALGORITMO DEL EQUIPO
# ==================================================

from agentes_externos.cazador_bfs import CazadorBFS


# ==================================================
# UTILIDADES
# ==================================================

def obtener_ip_local():
    # Truco UDP: conectar a DNS de Google (sin enviar datos) para descubrir la IP local

    try:

        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        s.connect(("8.8.8.8", 80))

        ip = s.getsockname()[0]   # La IP local del socket creado

        s.close()

        return ip

    except Exception:

        return "127.0.0.1"   # Fallback si no hay red


def registrar_en_torneo():

    try:

        ip_local = obtener_ip_local()

        url_local = (
            f"http://{ip_local}:{PUERTO_AGENTE}"
        )

        respuesta = requests.post(
            f"http://{IP_SERVIDOR_TORNEO}:{PUERTO_TORNEO}/registrar",
            json={
                "nombre": NOMBRE_GRUPO,
                "algoritmo": ALGORITMO,
                "url": url_local,
            },
            timeout=5,
        )

        print()
        print("===================================")
        print(" REGISTRO EN TORNEO ")
        print("===================================")
        print(f"Grupo: {NOMBRE_GRUPO}")
        print(f"Algoritmo: {ALGORITMO}")
        print(f"IP Local: {ip_local}")
        print(f"URL: {url_local}")
        print(f"Respuesta: {respuesta.text}")
        print("===================================")
        print()

    except Exception as e:

        print()
        print("===================================")
        print(" ERROR REGISTRO TORNEO ")
        print("===================================")
        print(e)
        print("===================================")
        print()


# ==================================================
# LABERINTO REMOTO
# ==================================================

class LaberintoRemoto:

    def __init__(
        self,
        filas,
        cols,
        grid,
        salidas,
    ):

        self.filas = filas
        self.cols = cols
        self.grid = grid
        self.salidas = [
            tuple(s)
            for s in salidas
        ]

    def es_transitable(
        self,
        fila,
        col,
    ):

        return (
            0 <= fila < self.filas
            and 0 <= col < self.cols
            and self.grid[fila][col] == 0
        )

    def vecinos_transitables(
        self,
        celda,
    ):

        fila, col = celda

        candidatos = [
            (fila - 1, col),
            (fila + 1, col),
            (fila, col - 1),
            (fila, col + 1),
        ]

        return [
            c
            for c in candidatos
            if self.es_transitable(
                c[0],
                c[1],
            )
        ]


# ==================================================
# FLASK
# ==================================================

app = Flask(__name__)


@app.route("/movimiento", methods=["POST"])
def movimiento():
    datos = request.json   # Recibir estado del juego serializado desde el motor

    mapa = datos["laberinto"]

    lab = LaberintoRemoto(   # Reconstruir el laberinto desde los datos JSON
        filas=mapa["filas"],
        cols=mapa["cols"],
        grid=mapa["grid"],
        salidas=mapa["salidas"],
    )

    rol = Rol[datos["rol"]]   # Convertir string al enum Rol

    agente = CazadorBFS(rol)

    agente.inicializar(
        lab,
        tuple(
            datos["pos_propia"]
        )
    )

    estado = EstadoJuego(
        laberinto=lab,
        pos_propia=tuple(
            datos["pos_propia"]
        ),
        pos_oponente=tuple(
            datos["pos_oponente"]
        ),
        rol=rol,
        tiempo_restante=datos[
            "tiempo_restante"
        ],
        salidas=tuple(
            tuple(s)
            for s in mapa["salidas"]
        ),
        tick=datos["tick"],
    )

    direccion = (
        agente.decidir_movimiento(   # Delegar la decisión al algoritmo
            estado
        )
    )

    return jsonify(
        {
            "direccion":
            direccion.name   # Devolver el nombre del enum como string
        }
    )


@app.route("/ping")
def ping():
    # Endpoint de verificación de salud: el servidor de torneo lo usa para detectar ONLINE/OFFLINE
    return {
        "estado": "ok",
        "grupo": NOMBRE_GRUPO,
        "algoritmo": ALGORITMO,
    }


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":

    registrar_en_torneo()   # Anunciarse al servidor de torneo al iniciar

    app.run(
        host="0.0.0.0",   # Escuchar en todas las interfaces (accesible en red local)
        port=PUERTO_AGENTE,
        debug=False,
    )