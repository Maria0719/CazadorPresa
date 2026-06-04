# api/servidor_agente_mps.py

from flask import Flask, request, jsonify

import socket
import requests

from agentes.base import EstadoJuego, Rol
from agentes_externos.mps_externo import MPSExterno

# ==================================================
# CONFIGURACION DEL EQUIPO
# ==================================================

NOMBRE_GRUPO = "Grupo MPS"

ALGORITMO = "MPS"

IP_SERVIDOR_TORNEO = "192.168.1.11"

PUERTO_TORNEO = 6000

PUERTO_AGENTE = 5009

# ==================================================
# UTILIDADES
# ==================================================

def obtener_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def registrar_en_torneo():
    try:
        ip_local = obtener_ip_local()
        url_local = f"http://{ip_local}:{PUERTO_AGENTE}"

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
    def __init__(self, filas, cols, grid, salidas):
        self.filas = filas
        self.cols = cols
        self.grid = grid
        self.salidas = [tuple(s) for s in salidas]

    def es_transitable(self, fila, col):
        return (
            0 <= fila < self.filas
            and 0 <= col < self.cols
            and self.grid[fila][col] == 0
        )

    def vecinos_transitables(self, celda):
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
            if self.es_transitable(c[0], c[1])
        ]


# ==================================================
# FLASK
# ==================================================

app = Flask(__name__)


@app.route("/movimiento", methods=["POST"])
def movimiento():
    datos = request.json

    mapa = datos["laberinto"]

    lab = LaberintoRemoto(
        filas=mapa["filas"],
        cols=mapa["cols"],
        grid=mapa["grid"],
        salidas=mapa["salidas"],
    )

    rol = Rol[datos["rol"]]

    agente = MPSExterno(rol)

    agente.inicializar(
        lab,
        tuple(datos["pos_propia"]),
    )

    estado = EstadoJuego(
        laberinto=lab,
        pos_propia=tuple(datos["pos_propia"]),
        pos_oponente=tuple(datos["pos_oponente"]),
        rol=rol,
        tiempo_restante=datos["tiempo_restante"],
        salidas=tuple(tuple(s) for s in mapa["salidas"]),
        tick=datos["tick"],
    )

    direccion = agente.decidir_movimiento(estado)

    return jsonify({"direccion": direccion.name})


@app.route("/ping")
def ping():
    return {
        "estado": "ok",
        "grupo": NOMBRE_GRUPO,
        "algoritmo": ALGORITMO,
    }


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":
    registrar_en_torneo()

    app.run(
        host="0.0.0.0",
        port=PUERTO_AGENTE,
        debug=False,
    )
