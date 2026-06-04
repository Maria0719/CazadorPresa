# test_agente_remoto.py

from agentes.agente_remoto import AgenteRemoto

from agentes.base import (
    EstadoJuego,
    Rol,
)

from laberinto.generador import Laberinto


def main():

    lab = Laberinto(
        filas=11,
        cols=11,
        semilla=123
    )

    estado = EstadoJuego(
        laberinto=lab,
        pos_propia=(1, 1),
        pos_oponente=(9, 9),
        rol=Rol.CAZADOR,
        tiempo_restante=120,
        salidas=tuple(lab.salidas),
        tick=1,
    )

    agente = AgenteRemoto(
        Rol.CAZADOR,
        "http://127.0.0.1:5000"
    )

    direccion = agente.decidir_movimiento(
        estado
    )

    print()
    print("DIRECCION RECIBIDA:")
    print(direccion)
    print()


if __name__ == "__main__":
    main()