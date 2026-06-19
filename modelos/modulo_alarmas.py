"""
modelos/modulo_alarmas.py

Modelo atómico ModuloAlarmas.
Gestiona notificaciones y mantiene el ciclo de retransmisión
para alarmas críticas no confirmadas.
"""

from pypdevs.DEVS import AtomicDEVS
from pypdevs.infinity import INFINITY
from config import TIEMPO_CONF_CRITICA, PERIODO_REP_CRITICA

# Tipos de Alarma
NINGUNA = "NINGUNA"
BAJA    = "BAJA"
MEDIA   = "MEDIA"
CRITICA = "CRITICA"

# Fases Internas
OCIOSO         = "OCIOSO"
NOTIFICANDO    = "NOTIFICANDO"
ESPERANDO_CONF = "ESPERANDO_CONF"
REPETIENDO     = "REPETIENDO"


class ModuloAlarmas(AtomicDEVS):
    """
    Emite notificaciones y repite alarmas críticas hasta confirmación.

    Puertos de entrada:
        alarma                 — str: "baja" | "media" | "critica"
        confirmacionEnfermero  — signal (True)

    Puertos de salida:
        notificacionAlarma — str (mensaje de alerta)
    """

    def __init__(self, name: str = "ModuloAlarmas"):
        super().__init__(name)

        # Puertos De Entradas
        self.alarma = self.addInPort("alarma")
        self.confirmacionEnfermero = self.addInPort("confirmacionEnfermero")
        # Puertos De Salidas
        self.notificacionAlarma    = self.addOutPort("notificacionAlarma")

        # Estado inicial: ocioso
        self.state = {
            "tipoAlarma": NINGUNA,
            "fase":       OCIOSO,
            "sigma":      INFINITY,
        }

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        msg = f"ALERTA: {self.state['tipoAlarma']}"
        return {self.notificacionAlarma: msg}

    def extTransition(self, inputs):
        
        e = self.elapsed
        sigma = max(0.0, self.state["sigma"] - e)
        tipo  = self.state["tipoAlarma"]

        # Confirmación del enfermero: detiene el ciclo de crítica
        if self.confirmacionEnfermero in inputs:
            return {"tipoAlarma": NINGUNA, "fase": OCIOSO, "sigma": INFINITY}

        # Nueva alarma: fuerza notificación inmediata (sigma = 0)
        if self.alarma in inputs:
            
            valor = inputs[self.alarma]
            tipo_nuevo = {
                "baja":   BAJA,
                "media":  MEDIA,
                "critica": CRITICA,
            }.get(valor, NINGUNA)

        # Si ya estamos en CRITICA y llega algo menor, lo ignoramos.
        if tipo == CRITICA and tipo_nuevo in (BAJA, MEDIA):
            return dict(self.state) | {"sigma": sigma}
        
        # Si ya estamos en MEDIA y llega una BAJA, lo ignoramos.
        if tipo == MEDIA and tipo_nuevo == BAJA:
            return dict(self.state) | {"sigma": sigma}
        
        # Si pasa los filtros, fuerza notificacion inmediata (sigma = 0.0)
        return {"tipoAlarma": tipo_nuevo, "fase": NOTIFICANDO, "sigma": 0.0}

        # Sin eventos relevantes: mantener cronograma
        return dict(self.state) | {"sigma": sigma}

    def intTransition(self):
        
        tipo  = self.state["tipoAlarma"]
        fase  = self.state["fase"]

        # Primera notificación de alarma crítica → esperar confirmación
        if tipo == CRITICA and fase == NOTIFICANDO:
            return {"tipoAlarma": tipo, "fase": ESPERANDO_CONF,
                    "sigma": TIEMPO_CONF_CRITICA}

        # Timeout de espera o ciclo de repetición → repetir
        if tipo == CRITICA and fase in (ESPERANDO_CONF, REPETIENDO):
            return {"tipoAlarma": tipo, "fase": REPETIENDO,
                    "sigma": PERIODO_REP_CRITICA}

        # Alarma no crítica (BAJA o MEDIA) → notificación única, volver a OCIOSO
        if tipo in (BAJA, MEDIA):
            return {"tipoAlarma": NINGUNA, "fase": OCIOSO, "sigma": INFINITY}

        # Caso defensivo
        return {"tipoAlarma": NINGUNA, "fase": OCIOSO, "sigma": INFINITY}

    