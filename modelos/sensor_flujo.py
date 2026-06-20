"""
modelos/sensor_flujo.py

Modelo atómico SensorFlujo.
Reporta periódicamente el caudal real cada PERIODO_SENSOR segundos.
Al recibir caudalActual del actuador, actualiza el valor medido.
"""

import random

from pypdevs.DEVS import AtomicDEVS

from config import PERIODO_SENSOR, TASA_DERIVA_SENSOR


class SensorFlujo(AtomicDEVS):
    """
    Mide el caudal real y lo reporta al ControladorBomba cada 1 s.

    Puertos de entrada:
        caudalActual — float (valor físico del ActuadorBomba)

    Puertos de salida:
        sensorFlujo — float (medición enviada al Controlador)
    """

    def __init__(self, config: dict, name: str = "SensorFlujo"):
        super().__init__(name)

        # Puerto de emtrada
        self.caudalActual = self.addInPort("caudalActual")
        # Puerto de salida
        self.sensorFlujo = self.addOutPort("sensorFlujo")

        cfg = config["sensor"]
        self._ruido_std = cfg["ruido_std"]
        self._rng = random.Random() if self._ruido_std > 0 else None

        # Estado inicial
        self.state = {
            "caudalMedido": 0.0,
            "caudalActuador": 0.0,
            "tiempoActuador": 0.0,
            "sigma": PERIODO_SENSOR,
        }

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        return {self.sensorFlujo: self.state["caudalMedido"]}

    def extTransition(self, inputs):
        e = self.elapsed
        nuevo_estado = dict(self.state)
        nuevo_estado["sigma"] = max(0.0, self.state["sigma"] - e)

        if self.caudalActual in inputs:
            nuevo_estado["caudalActuador"] = inputs[self.caudalActual]
            nuevo_estado["caudalMedido"] = inputs[self.caudalActual]    
            nuevo_estado["tiempoActuador"] = 0.0

        return nuevo_estado

    def intTransition(self):
        caudal_base = self.state["caudalActuador"]
        t = self.state["tiempoActuador"]

        deriva = caudal_base * TASA_DERIVA_SENSOR * t
        ruido = (
            self._rng.gauss(0, self._ruido_std)
            if self._ruido_std > 0 and t > 0
            else 0.0
        )
        medido = max(0.0, caudal_base + deriva + ruido)

        return {
            "caudalMedido": medido,
            "caudalActuador": caudal_base,
            "tiempoActuador": t + self.state["sigma"],
            "sigma": PERIODO_SENSOR,
        }
