# test_equipos.py

import requests

r = requests.get(
    "http://127.0.0.1:6000/equipos"
)

print(r.status_code)
print(r.text)