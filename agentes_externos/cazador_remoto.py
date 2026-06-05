from agentes.agente_remoto import AgenteRemoto
from agentes.base import Rol


class CazadorRemoto(AgenteRemoto):
    # Agente remoto preconfigurado para conectarse al servidor local en el puerto 5000

    def __init__(self, rol: Rol):

        super().__init__(
            rol,
            "http://127.0.0.1:5000"   # URL del servidor Flask del agente local
        )