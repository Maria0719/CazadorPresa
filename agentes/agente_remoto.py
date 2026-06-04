# agentes/agente_remoto.py

from __future__ import annotations

import requests

from agentes.base import (
    Agente,
    Direccion,
    EstadoJuego,
    Rol,
)

from api.serializador import estado_a_json


class AgenteRemoto(Agente):
    """
    Agente que delega la decisión a otro computador vía HTTP.
    """

    def __init__(
        self,
        rol: Rol,
        url_servidor: str,
        timeout: float = 3.0,
    ) -> None:

        super().__init__(rol)

        self.url_servidor = url_servidor.rstrip("/")
        self.timeout = timeout

        self.nodos_expandidos = 0
        self.tiempo_ultima_decision = 0.0

    def decidir_movimiento(
        self,
        estado: EstadoJuego,
    ) -> Direccion:

        payload = estado_a_json(estado)

        try:

            respuesta = requests.post(
                f"{self.url_servidor}/movimiento",
                json=payload,
                timeout=self.timeout,
            )

            respuesta.raise_for_status()

            datos = respuesta.json()

            direccion = datos.get(
                "direccion",
                "NOOP"
            )

            return Direccion[direccion]

        except Exception as e:

            print(
                f"[ERROR AGENTE REMOTO] {e}"
            )

            return Direccion.NOOP