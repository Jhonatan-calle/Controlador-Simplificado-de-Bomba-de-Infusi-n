from pypdevs.DEVS import AtomicDEVS


class SensorFlujo(AtomicDEVS):
    def __init__(self, name="SensorFlujo"):
        AtomicDEVS.__init__(self, name)
        self.caudalActual = self.addInPort("caudalActual")
        self.sensorFlujo = self.addOutPort("sensorFlujo")

        # TODO: definir el estado inicial correcto
        self.state = {
            # tiempo transcurrido desde la ultima medicion, se resetea
            # cada vez que se recibe una nueva orden del actuador
            "tiempo_actuador": 0.0,
            # caudal rebido desde el actuador de bomba
            "caudalActuador": 0.0,
            "caudalMedido": 0.0,
            "sigma": 1.0,
        }

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        return {self.sensorFlujo: [self.state["caudalMedido"]]}

    def extTransition(self, inputs):
        if self.caudalActual in inputs:
            valor = inputs[self.caudalActual][0]
            return {
                "caudalMedido": self.state["caudalMedido"],
                "caudalActuador": valor,
                "sigma": self.state["sigma"] - self.elapsed,
                "tiempo_actuador": 0.0,
            }
        return self.state

    def intTransition(self):
        tiempo_pasado = self.state["sigma"]
        tiempo_actuador = (
            self.state["tiempo_actuador"] + tiempo_pasado
        )
        return {
            "caudalMedido": self._proxima_medicion(
                self.state["caudalActuador"], tiempo_actuador
            ),
            "caudalActuador": self.state["caudalActuador"],
            "sigma": 1.0,
            "tiempo_actuador": tiempo_actuador,
        }

    # TODO: definir esto correctamente despues
    def _proxima_medicion(self, caudal_actuador, tiempo_actuador):
        return caudal_actuador
