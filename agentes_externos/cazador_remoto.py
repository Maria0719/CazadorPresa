from agentes.agente_remoto import AgenteRemoto
from agentes.base import Rol


class CazadorRemoto(AgenteRemoto):

    def __init__(self, rol: Rol):

        super().__init__(
            rol,
            "http://127.0.0.1:5000"
        )