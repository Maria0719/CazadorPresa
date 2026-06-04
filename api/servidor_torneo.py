# api/servidor_torneo.py

from flask import Flask, request, jsonify
from datetime import datetime
import requests

app = Flask(__name__)

# ==================================================
# Equipos registrados
# ==================================================

equipos_registrados = []


# ==================================================
# Utilidad
# ==================================================

def buscar_equipo(nombre: str):

    for equipo in equipos_registrados:

        if equipo["nombre"] == nombre:
            return equipo

    return None


# ==================================================
# Ping
# ==================================================

@app.route("/ping")
def ping():

    return {
        "estado": "ok",
        "equipos": len(equipos_registrados)
    }


# ==================================================
# Registro
# ==================================================

@app.route("/registrar", methods=["POST"])
def registrar():

    datos = request.json

    nombre = datos.get("nombre")
    algoritmo = datos.get("algoritmo")
    url = datos.get("url")

    if not nombre:
        return jsonify({
            "error": "nombre requerido"
        }), 400

    if not algoritmo:
        return jsonify({
            "error": "algoritmo requerido"
        }), 400

    if not url:
        return jsonify({
            "error": "url requerida"
        }), 400

    equipo_existente = buscar_equipo(nombre)

    if equipo_existente:

        equipo_existente["algoritmo"] = algoritmo
        equipo_existente["url"] = url
        equipo_existente["ultima_actualizacion"] = (
            datetime.now().isoformat()
        )

        return jsonify({
            "mensaje": "equipo actualizado"
        })

    equipos_registrados.append({
        "nombre": nombre,
        "algoritmo": algoritmo,
        "url": url,
        "fecha_registro": datetime.now().isoformat(),
        "ultima_actualizacion": datetime.now().isoformat(),
    })

    print()
    print("===================================")
    print("NUEVO EQUIPO REGISTRADO")
    print(f"Nombre: {nombre}")
    print(f"Algoritmo: {algoritmo}")
    print(f"URL: {url}")
    print("===================================")
    print()

    return jsonify({
        "mensaje": "equipo registrado"
    })


# ==================================================
# Listado
# ==================================================

@app.route("/equipos")
def equipos():

    resultado = []

    for equipo in equipos_registrados:

        copia = equipo.copy()

        copia["estado"] = verificar_equipo(
            equipo["url"]
        )

        resultado.append(copia)

    return jsonify(resultado)

def verificar_equipo(url):

    try:

        respuesta = requests.get(
            f"{url}/ping",
            timeout=2
        )

        if respuesta.status_code == 200:
            return "ONLINE"

        return "OFFLINE"

    except Exception:

        return "OFFLINE"
# ==================================================
# Inicio
# ==================================================

if __name__ == "__main__":

    print()
    print("===================================")
    print(" SERVIDOR DE TORNEO INICIADO ")
    print("===================================")
    print()

    app.run(
        host="0.0.0.0",
        port=6000,
        debug=False,
    )