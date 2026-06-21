"""
main.py — Punto de entrada del simulador de bomba de infusión.

Uso:
    python main.py                      # escenario normal por defecto
    python main.py --escenario 6        # escenario fin de bolsa
    python main.py --escenario 7        # escenario alarma crítica
    python main.py --tiempo 120         # duración de simulación en segundos
    python main.py --graficos            # generar gráficos al finalizar
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from pypdevs.simulator import Simulator
from sistema.sistema_bomba import SistemaBomba
from logger.event_logger import EventLogger
from verificacion.verificador_propiedades import VerificadorPropiedades

from config import (
    ESCENARIO_1_NORMAL,
    ESCENARIO_2_CAMBIO_ORDEN,
    ESCENARIO_3_ORDEN_CERO,
    ESCENARIO_4_DESVIO_LEVE,
    ESCENARIO_5_DESVIO_GRAVE,
    ESCENARIO_6_FIN_BOLSA,
    ESCENARIO_7_ALARMA_CRITICA,
    ESCENARIO_6_FIN_BOLSA_ESTOCASTICO,
    ESCENARIO_9_VIOLACION,
)

ESCENARIOS = {
    1: ESCENARIO_1_NORMAL,
    2: ESCENARIO_2_CAMBIO_ORDEN,
    3: ESCENARIO_3_ORDEN_CERO,
    4: ESCENARIO_4_DESVIO_LEVE,
    5: ESCENARIO_5_DESVIO_GRAVE,
    6: ESCENARIO_6_FIN_BOLSA,
    7: ESCENARIO_7_ALARMA_CRITICA,
    8: ESCENARIO_6_FIN_BOLSA_ESTOCASTICO,
    9: ESCENARIO_9_VIOLACION,
}

NOMBRES = {
    1: "Operación normal",
    2: "Cambio de orden médica",
    3: "Orden con caudal = 0",
    4: "Desvío leve (< 5 s)",
    5: "Desvío grave (> 5 s)",
    6: "Fin de bolsa (determinístico)",
    7: "Alarma crítica sin confirmación",
    8: "Fin de bolsa (estocástico)",
    9: "Violación deliberada de seguridad",
}


def correr_simulacion(num_escenario: int = 1, tiempo: float = 100.0,
                      verbose: bool = False, verificar: bool = False,
                      graficos: bool = False):
    config = ESCENARIOS[num_escenario]
    nombre = NOMBRES[num_escenario]

    print(f"\n{'='*60}")
    print(f"  Escenario {num_escenario}: {nombre}")
    print(f"  Duración: {tiempo} s")
    print(f"  {'[verbose] ' if verbose else ''}{'[verificar] ' if verificar else ''}{'[graficos] ' if graficos else ''}")
    print(f"{'='*60}\n")

    logger = EventLogger()
    modelo = SistemaBomba(config)
    sim    = Simulator(modelo)
    sim.setCustomTracer("logger.event_logger", "TracerEventLogger", [logger, verbose])
    sim.setClassicDEVS()
    sim.setTerminationTime(tiempo)
    sim.simulate()

    print(f"  Eventos capturados: {len(logger.todos())}")

    resultados = None
    if verificar or graficos:
        v = VerificadorPropiedades(logger, config)
        resultados = v.verificar_todo()
        if verificar:
            print(f"\n{'─'*60}")
            print("  Verificación de propiedades")
            print(f"{'─'*60}")
            for r in resultados:
                icon = "✓" if r.cumplida else "✗"
                print(f"  [{icon}] {r.propiedad} — {r.detalle}")

    if graficos:
        from graficos.graficar_resultados import graficar_escenario
        graficar_escenario(logger, num_escenario, nombre, tiempo,
                           config=config, resultados=resultados)

    print(f"\n{'='*60}")
    print("  Simulación completada")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulador Bomba de Infusión")
    parser.add_argument("--escenario", type=int, default=1,
                        choices=list(ESCENARIOS.keys()),
                        help=f"Número de escenario (1-{max(ESCENARIOS)})")
    parser.add_argument("--tiempo", type=float, default=100.0,
                        help="Duración de la simulación en segundos")
    parser.add_argument("--verbose", action="store_true",
                        help="Muestra eventos en tiempo real")
    parser.add_argument("--verificar", action="store_true",
                        help="Verifica propiedades al finalizar")
    parser.add_argument("--graficos", action="store_true",
                        help="Genera gráficos al finalizar")
    args = parser.parse_args()

    correr_simulacion(args.escenario, args.tiempo,
                      verbose=args.verbose, verificar=args.verificar,
                      graficos=args.graficos)
