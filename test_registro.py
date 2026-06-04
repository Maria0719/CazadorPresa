import requests

r = requests.post(
    "http://127.0.0.1:6000/registrar",
    json={
        "nombre": "Grupo GBFS",
        "algoritmo": "Greedy Best First Search",
        "url": "http://127.0.0.1:5000"
    }
)

print(r.status_code)
print(r.text)