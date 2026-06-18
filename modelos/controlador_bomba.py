from pypdevs.DEVS import AtomicDEVS
from pypdevs.infinity import INFINITY

FASE_OCIOSO = "OCIOSO"
FASE_INFUNDIENDO = "INFUNDIENDO"
FASE_ALERTA_BOLSA = "ALERTA_BOLSA"
FASE_ALARMA_MEDIA = "ALARMA_MEDIA"
FASE_ALARMA_CRITICA = "ALARMA_CRITICA"

ALARMA_BAJA = "baja"
ALARMA_MEDIA = "media"
ALARMA_CRITICA = "critica"


class ControladorBomba(AtomicDEVS):
    def __init__(self, name="ControladorBomba"):
        AtomicDEVS.__init__(self, name)
        self.ordenMedica = self.addInPort("ordenMedica")
        self.sensorFlujo = self.addInPort("sensorFlujo")
        self.finBolsa = self.addInPort("finBolsa")
        self.confirmacionEnfermero = self.addInPort(
            "confirmacionEnfermero"
        )

        self.ajustarCaudal = self.addOutPort("ajustarCaudal")
        self.detenerBomba = self.addOutPort("detenerBomba")
        self.alarma = self.addOutPort("alarma")
        self.registrarEvento = self.addOutPort("registrarEvento")

        self.state = {
            "caudalObjetivo": 0.0,
            "caudalReal": 0.0,
            "fase": FASE_OCIOSO,
            "contadorMedia": 0,
            "sigma": INFINITY,
            "t_desvio": INFINITY,
            "t_bolsa": INFINITY,
        }

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        s = self.state
        out = {}
        if s["fase"] == FASE_INFUNDIENDO:
            out[self.ajustarCaudal] = [s["caudalObjetivo"]]
        elif s["fase"] == FASE_ALERTA_BOLSA:
            out[self.alarma] = [ALARMA_BAJA]
        elif s["fase"] == FASE_ALARMA_MEDIA:
            out[self.alarma] = [ALARMA_MEDIA]
        elif s["fase"] == FASE_ALARMA_CRITICA:
            out[self.alarma] = [ALARMA_CRITICA]
            out[self.detenerBomba] = ["signal"]
        if s["fase"] == FASE_OCIOSO and s["caudalObjetivo"] == 0.0:
            out[self.detenerBomba] = ["signal"]
        out[self.registrarEvento] = ["Evento de control ejecutado"]
        return out

    def extTransition(self, inputs):
        s = self.state
        t_desvio = s["t_desvio"] - self.elapsed
        t_bolsa = s["t_bolsa"] - self.elapsed

        if self.ordenMedica in inputs:
            valor = inputs[self.ordenMedica][0]
            nuevo = dict(s)
            nuevo["caudalObjetivo"] = valor
            nuevo["t_desvio"] = t_desvio
            nuevo["t_bolsa"] = t_bolsa
            if valor > 0.0:
                nuevo["fase"] = FASE_INFUNDIENDO
                nuevo["sigma"] = 0.0
            else:
                nuevo["fase"] = FASE_OCIOSO
                nuevo["sigma"] = 0.0
            return nuevo

        if self.sensorFlujo in inputs:
            valor = inputs[self.sensorFlujo][0]
            hay_desvio = (
                s["caudalObjetivo"] > 0
                and abs(valor - s["caudalObjetivo"])
                > 0.1 * s["caudalObjetivo"]
            )
            if hay_desvio and t_desvio == INFINITY:
                nuevo = dict(s)
                nuevo["caudalReal"] = valor
                nuevo["sigma"] = 5.0
                nuevo["t_desvio"] = 5.0
                nuevo["t_bolsa"] = t_bolsa
                return nuevo
            if hay_desvio and t_desvio != INFINITY:
                nuevo = dict(s)
                nuevo["caudalReal"] = valor
                nuevo["sigma"] = min(
                    s["sigma"] - self.elapsed, t_desvio
                )
                nuevo["t_desvio"] = t_desvio
                nuevo["t_bolsa"] = t_bolsa
                return nuevo
            if not hay_desvio:
                nuevo = dict(s)
                nuevo["caudalReal"] = valor
                nuevo["sigma"] = s["sigma"] - self.elapsed
                nuevo["t_desvio"] = INFINITY
                nuevo["t_bolsa"] = t_bolsa
                return nuevo

        if self.finBolsa in inputs:
            nuevo = dict(s)
            nuevo["fase"] = FASE_ALERTA_BOLSA
            nuevo["sigma"] = 0.0
            nuevo["t_bolsa"] = 60.0
            return nuevo

        if self.confirmacionEnfermero in inputs:
            if s["fase"] == FASE_ALARMA_CRITICA:
                nuevo = dict(s)
                nuevo["fase"] = FASE_OCIOSO
                nuevo["contadorMedia"] = 0
                nuevo["sigma"] = 0.0
                nuevo["t_desvio"] = t_desvio
                nuevo["t_bolsa"] = t_bolsa
                return nuevo

        print(
            f"WARNING: ControladorBomba - evento no manejado: {list(inputs.keys())}"
        )
        return s

    def intTransition(self):
        s = self.state

        if s["t_desvio"] <= 0.0:
            if s["contadorMedia"] <= 1:
                nuevo = dict(s)
                nuevo["fase"] = FASE_ALARMA_MEDIA
                nuevo["contadorMedia"] = s["contadorMedia"] + 1
                nuevo["sigma"] = 0.0
                nuevo["t_desvio"] = INFINITY
                return nuevo
            else:
                nuevo = dict(s)
                nuevo["fase"] = FASE_ALARMA_CRITICA
                nuevo["contadorMedia"] = 3
                nuevo["sigma"] = 0.0
                nuevo["t_desvio"] = INFINITY
                return nuevo

        if s["t_bolsa"] <= 0.0:
            nuevo = dict(s)
            nuevo["caudalObjetivo"] = 0.0
            nuevo["fase"] = FASE_OCIOSO
            nuevo["sigma"] = 0.0
            nuevo["t_bolsa"] = INFINITY
            return nuevo

        if s["fase"] == FASE_ALARMA_MEDIA:
            nuevo = dict(s)
            nuevo["fase"] = FASE_INFUNDIENDO
            nuevo["sigma"] = min(s["t_desvio"], s["t_bolsa"])
            return nuevo

        if s["fase"] == FASE_ALERTA_BOLSA:
            nuevo = dict(s)
            nuevo["fase"] = FASE_INFUNDIENDO
            nuevo["sigma"] = min(s["t_desvio"], s["t_bolsa"])
            return nuevo

        if (
            s["fase"] == FASE_INFUNDIENDO
            and s["t_bolsa"] > 0.0
            and s["t_desvio"] > 0
        ):
            nuevo = dict(s)
            nuevo["sigma"] = min(s["t_desvio"], s["t_bolsa"])
            return nuevo

        if (
            s["fase"] in (FASE_ALARMA_CRITICA, FASE_OCIOSO)
            and s["t_desvio"] > 0
        ):
            nuevo = dict(s)
            nuevo["sigma"] = INFINITY
            return nuevo

        return s
