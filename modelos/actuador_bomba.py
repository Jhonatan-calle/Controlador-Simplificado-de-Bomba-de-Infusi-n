from pypdevs.DEVS import AtomicDEVS
from pypdevs.infinity import INFINITY


class ActuadorBomba(AtomicDEVS):
    def __init__(self, name="ActuadorBomba"):
        AtomicDEVS.__init__(self, name)
        self.ajustarCaudal = self.addInPort("ajustarCaudal")
        self.detenerBomba = self.addInPort("detenerBomba")
        self.caudalActual = self.addOutPort("caudalActual")

        self.state = {
            "caudalFisico": 0.0,
            "caudalObjetivo": 0.0,
            "sigma": INFINITY,
        }

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        return {self.caudalActual: [self.state["caudalObjetivo"]]}

    def extTransition(self, inputs):
        if self.ajustarCaudal in inputs:
            valor = inputs[self.ajustarCaudal][0]
            return {
                "caudalFisico": self.state["caudalFisico"],
                "caudalObjetivo": valor,
                "sigma": 0.5,
            }
        if self.detenerBomba in inputs:
            return {
                "caudalFisico": self.state["caudalFisico"],
                "caudalObjetivo": 0.0,
                "sigma": 0.5,
            }
        return self.state

    def intTransition(self):
        return {
            "caudalFisico": self.state["caudalObjetivo"],
            "caudalObjetivo": self.state["caudalObjetivo"],
            "sigma": INFINITY,
        }
