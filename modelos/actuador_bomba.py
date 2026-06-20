"""
modelos/actuador_bomba.py
 
Modelo atómico ActuadorBomba.
Recibe comandos del controlador y, tras una latencia de 0.5 s,
actualiza el caudal físico y notifica al SensorFlujo.
"""

from pypdevs.DEVS import AtomicDEVS
from pypdevs.infinity import INFINITY
from config import LATENCIA_ACTUADOR

class ActuadorBomba(AtomicDEVS):
    
    """
    Interfaz física de la bomba con latencia de respuesta.
 
    Puertos de entrada:
        ajustarCaudal — float (nuevo caudal objetivo desde el Controlador)
        detenerBomba  — signal (parada de emergencia desde el Controlador)
 
    Puertos de salida:
        caudalActual — float (caudal físico notificado al SensorFlujo)
    """
 
    def __init__(self, config: dict, name: str = "ActuadorBomba"):
        super().__init__(name)
 
        # Puertos De Entrada
        self.ajustarCaudal = self.addInPort("ajustarCaudal")
        self.detenerBomba  = self.addInPort("detenerBomba")
        # Puertos De Salida
        self.caudalActual  = self.addOutPort("caudalActual")
 
        cfg = config["actuador"]
        self._factor_falla = cfg["factor_falla"]

        # Estado inicial: pasivo, sin caudal
        self.state = {
            "caudalFisico": 0.0,
            "caudalObjetivo": 0.0,
            "sigma": INFINITY,
        }

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        # El caudal real que llega al paciente aplica el factor de falla
        caudal_real = self.state["caudalObjetivo"] * self._factor_falla
        return {self.caudalActual: caudal_real}

    def extTransition(self, inputs):
        """Recibe una orden y programa la actualizacion tras la latencia."""
        nuevo_estado = dict(self.state)
        
        if self.detenerBomba in inputs:

            nuevo_estado["caudalObjetivo"] = 0.0
            nuevo_estado["sigma"] = LATENCIA_ACTUADOR
        
        elif self.ajustarCaudal in inputs:
            
            nuevo_estado["caudalObjetivo"] = inputs[self.ajustarCaudal]
            nuevo_estado["sigma"] = LATENCIA_ACTUADOR
 
        return nuevo_estado

    def intTransition(self):
        """Cumplida la latencia, el caudal fisico alcanza al objetivo."""
        return { 
            "caudalFisico": self.state["caudalObjetivo"] * self._factor_falla,
            "caudalObjetivo": self.state["caudalObjetivo"],
            "sigma": INFINITY,
        }
        
            
