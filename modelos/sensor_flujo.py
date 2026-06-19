"""
modelos/sensor_flujo.py
 
Modelo atómico SensorFlujo.
Reporta periódicamente el caudal real cada PERIODO_SENSOR segundos.
Al recibir caudalActual del actuador, actualiza el valor medido.
"""

from pypdevs.DEVS import AtomicDEVS
from config import PERIODO_SENSOR
import random #Hacer nuestro propio RANDOM


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

        #Puerto de emtrada
        self.caudalActual = self.addInPort("caudalActual")
        #Puerto de salida
        self.sensorFlujo = self.addOutPort("sensorFlujo")

        
        cfg = config["sensor"]
        self._ruido_std = cfg["ruido_std"]
        self._rng = random.Random() if self._ruido_std > 0 else None #Hacer nuestro propio RANDOM

        # Estado inicial: σ = PERIODO_SENSOR, caudal = 0
        self.state = {
            "caudalMedido": 0.0,
            "caudalActuador": 0.0,
            "sigma": PERIODO_SENSOR,
        }

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        return {self.sensorFlujo: self.state["caudalMedido"]}

    def extTransition(self, inputs):
        """Actualiza el caudal del actuador sin cambiar el cronograma."""
        e = self.elapsed
        sigma_restante = max(0.0, self.state["sigma"] - e)

        nuevo_estado = dict(self.state)
        nuevo_estado["sigma"] = sigma_restante

        if self.caudalActual in inputs:
            nuevo_estado["caudalActuador"] = inputs[self.caudalActual]
 
        return nuevo_estado

    def intTransition(self):
        """Genera la nueva medición y reinicia el período."""
        caudal_base = self.state["caudalActuador"]
        
        if self._ruido_std > 0:
            
            #Distribucion Normal(Gaussiana)
            medido = caudal_base + self._rng.gauss(0, self._ruido_std)
            medido = max(0.0, medido)
        
        else:
            
            medido = caudal_base
 
        return {
            "caudalMedido": medido,
            "caudalActuador": self.state["caudalActuador"],
            "sigma": PERIODO_SENSOR,
        }


        
