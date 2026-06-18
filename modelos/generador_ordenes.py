from pypdevs.DEVS import AtomicDEVS
from pypdevs.infinity import INFINITY


class GeneradorOrdenes(AtomicDEVS):
    def __init__(self, name="GeneradorOrdenes"):
        AtomicDEVS.__init__(self, name)
        self.ordenMedica = self.addOutPort("ordenMedica")
        # TODO: definir el estado inicial correcto
        self.state = {
            "caudalProximo": 0.0,
            "interarribo": 10.0,
            "sigma": 0.0,
        }

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        return {self.ordenMedica: [self.state["caudalProximo"]]}

    def intTransition(self):
        return {
            "caudalProximo": self._next_caudal(),
            "sigma": self._next_time(),
        }

    # TODO: definir esto correctamente despues
    def _next_caudal(self):
        return self.state["caudalProximo"]

    def _next_time(self):
        return self.state["interarribo"]
