"""
modelos/generador_confirmacion.py

Modelo atómico autónomo que genera eventos confirmacionEnfermero.
Sin entradas. Simula el reconocimiento manual del personal médico.
"""

import math
import random  #LUEGO CAMBIAR A PROPIO RANDOM
from pypdevs.DEVS import AtomicDEVS
from pypdevs.infinity import INFINITY


class GeneradorConfirmacion(AtomicDEVS):
    """
    Genera la señal confirmacionEnfermero un número limitado de veces.

    Puertos de salida:
        confirmacionEnfermero — signal (valor = True)
    """

    def __init__(self, config: dict, name: str = "GeneradorConfirmacion"):
        super().__init__(name)

        #Puerto de salida   
        self.confirmacionEnfermero = self.addOutPort("confirmacionEnfermero")

        cfg = config["confirmacion"]
        self._modo = cfg["modo"]
        self._max_confirmaciones = cfg["max_confirmaciones"]

        if self._modo == "deterministico":
            
            self._tiempo_fijo = cfg["tiempo_fijo"]
            sigma_inicial = self._tiempo_fijo if self._max_confirmaciones > 0 else INFINITY
        
        else:
            
            self._rng = random.Random() #LUEGO CAMBIAR A PROPIO RANDOM
            self._mu = cfg["mu"]
            self._sigma_ln = cfg["sigma_ln"]
            sigma_inicial = (
                self._sample_lognormal()
                if self._max_confirmaciones > 0
                else INFINITY
            )

        self.state = {
            
            "sigma": sigma_inicial,
            "confirmaciones": 0,
       
        }

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        return {self.confirmacionEnfermero: True}

    def intTransition(self):
        
        nuevas = self.state["confirmaciones"] + 1
        return {
            "sigma": self._next_sigma(nuevas),
            "confirmaciones": nuevas,
        }
    

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sample_lognormal(self) -> float:
        #Distribucion Log-Normal
        return self._rng.lognormvariate(self._mu, self._sigma_ln)

    def _next_sigma(self, confirmaciones_actuales: int) -> float:
        if confirmaciones_actuales >= self._max_confirmaciones:
            return INFINITY
        if self._modo == "deterministico":
            return self._tiempo_fijo
        else:
            return self._sample_lognormal()
