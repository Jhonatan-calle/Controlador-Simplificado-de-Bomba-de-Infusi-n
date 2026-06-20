"""
modelos/sensor_flujo.py
 
Modelo atómico SensorFlujo.
Reporta periódicamente el caudal real cada PERIODO_SENSOR segundos.
Al recibir caudalActual del actuador, actualiza el valor medido.
"""

from pypdevs.DEVS import AtomicDEVS
from config import PERIODO_SENSOR


class SensorFlujo(AtomicDEVS):
    
    """
    Mide el caudal real y lo reporta al ControladorBomba cada 1 s.
 
    Puertos de entrada:
        caudalActual — float (valor físico del ActuadorBomba)
 
    Puertos de salida:
        sensorFlujo — float (medición enviada al Controlador)
    """
    
    def __init__(self, name: str = "SensorFlujo"):
        super().__init__(name)

        #Puerto de emtrada
        self.caudalActual = self.addInPort("caudalActual")
        #Puerto de salida
        self.sensorFlujo = self.addOutPort("sensorFlujo")

        # Estado inicial
        self.state = {
            "caudalMedido": 0.0,
            "sigma": PERIODO_SENSOR,
        }

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        return {self.sensorFlujo: self.state["caudalMedido"]}

    def extTransition(self, inputs):
        e = self.elapsed
        sigma_restante = max(0.0, self.state["sigma"] - e)

        nuevo_estado = dict(self.state)
        nuevo_estado["sigma"] = sigma_restante

        if self.caudalActual in inputs:
            nuevo_estado["caudalMedido"] = inputs[self.caudalActual]
 
        return nuevo_estado

    def intTransition(self):
        return {
            "caudalMedido": self.state["caudalMedido"],
            "sigma": PERIODO_SENSOR,
        }
