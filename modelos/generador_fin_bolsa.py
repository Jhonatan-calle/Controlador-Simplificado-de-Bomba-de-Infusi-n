"""
modelos/generador_fin_bolsa.py

Modelo atómico autónomo que genera el evento finBolsa.
Sin entradas. Emite una única señal cuando la bolsa se agota.
"""

from pypdevs.DEVS import AtomicDEVS
from pypdevs.infinity import INFINITY
import random


class GeneradorFinBolsa(AtomicDEVS):
    """
    Genera el evento finBolsa una sola vez (o nunca, si tiempo_fijo=INFINITY).

    Puertos de salida:
        finBolsa — signal (valor = True)
    """

    def __init__(self, config: dict, name: str = "GeneradorFinBolsa"):
        super().__init__(name)

        #Puerto de salida  
        self.finBolsa = self.addOutPort("finBolsa")

        cfg = config["fin_bolsa"]
        self._modo = cfg["modo"]

        if self._modo == "deterministico":
            sigma_inicial = cfg["tiempo_fijo"]
        else:
            self._rng   = random.Random(cfg["semilla"])#Cambiar para hacer nuestro propio Random
            self._media = cfg["media"]
            self._std   = cfg["desvio_std"]
            sigma_inicial = round(max(0.1, self._rng.gauss(self._media, self._std)), 3)

        self.state = {"sigma": sigma_inicial, "emitido": False}

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        return {self.finBolsa: True}

    def intTransition(self):
        # Tras emitir, pasa a estado pasivo (no vuelve a emitir)
        return {"sigma": INFINITY, "emitido": True}
