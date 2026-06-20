"""
modelos/generador_ordenes.py
 
Modelo atómico autónomo que genera eventos ordenMedica.
Sin entradas. Emite el caudal objetivo periódicamente.
"""

from pypdevs.DEVS import AtomicDEVS
from pypdevs.infinity import INFINITY
import random


class GeneradorOrdenes(AtomicDEVS):

    """
    Genera órdenes médicas (caudal objetivo) periódicamente.
 
    Puertos de salida:
        ordenMedica — valor de caudal (float, 0–200 ml/h)
    """

    def __init__(self,config: dict, name: str = "GeneradorOrdenes"):
        super().__init__(name)

        #Puerto de salida       
        self.ordenMedica = self.addOutPort("ordenMedica")

        cfg = config["ordenes"]
        self._modo = cfg["modo"]

        if self._modo == "deterministico":
           
           self._caudal_fijo     = cfg["caudal_fijo"]
           self._interarribo_fijo = cfg["interarribo_fijo"]
        
        else:
            
            self._rng = random.Random(cfg["semilla"]) #Cambiar para hacer nuestro propio Random
            self._media_caudal    = cfg["media_caudal"]
            self._desvio_caudal   = cfg["desvio_caudal"]
            self._media_tiempo    = cfg["media_tiempo"]


        #Estado inicial
        self.state = self._estado_inicial()


    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        return {self.ordenMedica: self.state["caudalProximo"]}

    def intTransition(self):
        
        nuevo_caudal = self._next_caudal()
        nuevo_interarribo = self._next_interarribo()
        return {
            "caudalProximo": nuevo_caudal,
            "interarribo": nuevo_interarribo,
            "sigma": nuevo_interarribo,
        }

    # ------------------------------------------------------------------
    # Helpers de estado
    # ------------------------------------------------------------------
 
    def _estado_inicial(self):
        if self._modo == "deterministico":
            return {
                "caudalProximo": self._caudal_fijo,
                "interarribo":   self._interarribo_fijo,
                "sigma":         self._interarribo_fijo,
            }
        else:
            return {
                "caudalProximo": self._media_caudal,
                "interarribo":   self._media_tiempo,
                "sigma":         self._media_tiempo,
            }
 
    def _next_caudal(self):
        if self._modo == "deterministico":
            return self._caudal_fijo
        else:
            import random
            return max(0.0, min(200.0,
                self._rng.gauss(self._media_caudal, self._desvio_caudal)))
 
    def _next_interarribo(self):
        if self._modo == "deterministico":
            return self._interarribo_fijo
        else:
            return max(1.0, self._rng.expovariate(1.0 / self._media_tiempo))
