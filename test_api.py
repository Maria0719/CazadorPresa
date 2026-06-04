import requests

payload = {
    "laberinto": {
        "filas": 5,
        "cols": 5,
        "grid": [
            [1,1,1,1,1],
            [1,0,0,0,1],
            [1,0,1,0,1],
            [1,0,0,0,1],
            [1,1,1,1,1]
        ],
        "salidas": [[3,3]]
    },
    "pos_propia": [1,1],
    "pos_oponente": [3,3],
    "rol": "CAZADOR",
    "tiempo_restante": 120,
    "tick": 1
}

r = requests.post(
    "http://127.0.0.1:5000/movimiento",
    json=payload
)

print("STATUS:", r.status_code)
print("RESPUESTA:", r.text)