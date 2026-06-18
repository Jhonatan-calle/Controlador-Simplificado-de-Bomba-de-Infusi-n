from pypdevs.DEVS import AtomicDEVS
from pypdevs.infinity import INFINITY
from config import LATENCIA_ACTUADOR

class ActuadorBomba(AtomicDEVS):
    def __init__(self, config: dict):
        super().__init__("ActuadorBomba")

        # Puertos de entrada y salida
        self.ajustarCaudal = self.addInPort("ajustarCaudal")
        self.detenerBomba = self.addInPort("detenerBomba")
        self.caudalActual = self.addOutPort("caudalActual")

        self.factor_falla = config.get("factor_falla", 1.0)

        # Estado formal
        self.state = {
            "caudalFisico": 0.0,
            "caudalObjetivo": 0.0,
            "sigma": INFINITY,
        }

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        # Emite el caudal nuevo (caudalObjetivo), no el viejo
        return {self.caudalActual: self.state["caudalObjetivo"]}

    def extTransition(self, inputs):
        # Actualizamos el sigma transcurrido
        self.state["sigma"] -= self.elapsed
        
        # Vemos por qué puerto entró el mensaje
        if self.detenerBomba in inputs:
            valor = inputs[self.detenerBomba]
            nuevo_objetivo = procesar_comando("detenerBomba", valor, self.factor_falla)
        elif self.ajustarCaudal in inputs:
            valor = inputs[self.ajustarCaudal]
            nuevo_objetivo = procesar_comando("ajustarCaudal", valor, self.factor_falla)
        else:
            return self.state


        self.state["caudalObjetivo"] = nuevo_objetivo
        
        # El actuador tarda LATENCIA_ACTUADOR (0.5s) en hacer efectivo el cambio
        self.state["sigma"] = LATENCIA_ACTUADOR
        
        return self.state

    def intTransition(self):
        # Se concreta el cambio físico
        self.state["caudalFisico"] = self.state["caudalObjetivo"]
        self.state["sigma"] = INFINITY
        return self.state
            

###################################################
def procesar_comando(puerto_nombre: str, valor: float, factor_falla: float) -> float:
    """
    Decide el nuevo caudal objetivo según el puerto que disparó extTransition.
    'ajustarCaudal' aplica el factor_falla (simula degradación mecánica);
    'detenerBomba' siempre lleva a 0 sin importar el factor_falla.
    """
    if puerto_nombre == "detenerBomba":
        return 0.0
    if puerto_nombre == "ajustarCaudal":
        if valor is None:
            return 0.0
        return valor * factor_falla
    raise ValueError(f"Puerto desconocido para ActuadorBomba: {puerto_nombre}")

#####################################################