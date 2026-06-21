"""
modelos/controlador_bomba.py
 
Modelo atómico ControladorBomba.
Componente central: recibe órdenes médicas y mediciones del sensor,
detecta desvíos, gestiona alarmas y coordina el actuador.
"""

from pypdevs.DEVS import AtomicDEVS
from pypdevs.infinity import INFINITY
from config import (
    DESVIO_MAX_PERMITIDO,
    TIEMPO_MAX_DESVIO,
    TIEMPO_MAX_FIN_BOLSA,
    CAUDAL_MAX,
)


# Fases del controlador
OCIOSO        = "OCIOSO"
INFUNDIENDO   = "INFUNDIENDO"
ALERTA_BOLSA  = "ALERTA_BOLSA"
ALARMA_MEDIA  = "ALARMA_MEDIA"
ALARMA_CRITICA = "ALARMA_CRITICA"
PARADA_POR_BOLSA = "PARADA_POR_BOLSA"  #Fase Para Gestionar la Detencion De Fin De Bolsa


class ControladorBomba(AtomicDEVS):
    """
    Controlador central de la bomba de infusión.
 
    Puertos de entrada:
        ordenMedica            — float (caudal objetivo)
        sensorFlujo            — float (caudal real medido)
        finBolsa               — signal (bolsa casi vacía)
        confirmacionEnfermero  — signal
 
    Puertos de salida:
        ajustarCaudal  — float (comando al ActuadorBomba)
        detenerBomba   — signal (parada de emergencia)
        alarma         — str: "baja" | "media" | "critica"
        registrarEvento — str (log de auditoría)
    """

    def __init__(self, name: str = "ControladorBomba"):
        super().__init__(name)
 
        # Puertos de Entrada
        self.ordenMedica = self.addInPort("ordenMedica")
        self.sensorFlujo = self.addInPort("sensorFlujo")
        self.finBolsa = self.addInPort("finBolsa")
        self.confirmacionEnfermero = self.addInPort("confirmacionEnfermero")
 
        # Puertos de Salida
        self.ajustarCaudal = self.addOutPort("ajustarCaudal")
        self.detenerBomba = self.addOutPort("detenerBomba")
        self.alarma = self.addOutPort("alarma")
        self.registrarEvento = self.addOutPort("registrarEvento")
 
        # Estado inicial
        self.state = {
            "caudalObjetivo": 0.0,
            "caudalReal": 0.0,
            "fase": OCIOSO,
            "contadorMedia": 0,
            "sigma": INFINITY,
            "t_desvio": INFINITY,
            "t_bolsa": INFINITY,
        }

    def timeAdvance(self):
        return self.state["sigma"]

    def outputFnc(self):
        s = self.state
        salidas = {}
 
        if s["fase"] == INFUNDIENDO:
            
            salidas[self.ajustarCaudal]   = _clamp_caudal(s["caudalObjetivo"])
            salidas[self.registrarEvento] = f"Ajustando caudal a {s['caudalObjetivo']:.1f} ml/h"
 
        elif s["fase"] == ALERTA_BOLSA:
            
            salidas[self.alarma]          = "baja"
            salidas[self.registrarEvento] = "Fin de bolsa detectado — alarma BAJA emitida"
 
        elif s["fase"] == ALARMA_MEDIA:
            
            salidas[self.alarma]          = "media"
            salidas[self.registrarEvento] = "Desvío sostenido — alarma MEDIA emitida"
 
        elif s["fase"] == ALARMA_CRITICA:
            
            salidas[self.alarma]          = "critica"
            salidas[self.detenerBomba]    = True
            salidas[self.registrarEvento] = "Alarma CRITICA — bomba detenida"

        elif s["fase"] == PARADA_POR_BOLSA:

            salidas[self.detenerBomba]    = True
            salidas[self.registrarEvento] = f"Tiempo limite tras fin de bolsa ({TIEMPO_MAX_FIN_BOLSA}s) - bomba detenida"
 
        elif s["fase"] == OCIOSO and s["caudalObjetivo"] == 0.0:
            
            salidas[self.detenerBomba]    = True
            salidas[self.registrarEvento] = "Orden de caudal=0 — bomba detenida"
 
        return salidas

    def extTransition(self, inputs):
        
        e = self.elapsed
        s = self.state
        nuevo = dict(s)
 
        # tiempo acumulado en desvio 
        if s["t_desvio"] != INFINITY:
            
            nuevo["t_desvio"] = max(0.0, s["t_desvio"] - e)
        
        # tiempo acumulado desde que se 
        # anuncio el finde bolsa
        if s["t_bolsa"] != INFINITY:
            
            nuevo["t_bolsa"] = max(0.0, s["t_bolsa"] - e)
        
        sigma_restante = max(0.0, s["sigma"] - e) if s["sigma"] != INFINITY else INFINITY
 
        # --- Orden médica ---
        if self.ordenMedica in inputs:
            valor = inputs[self.ordenMedica]
            
            if valor > 0.0:
                
                nuevo["caudalObjetivo"] = _clamp_caudal(valor)
                nuevo["fase"] = INFUNDIENDO
                nuevo["sigma"] = 0.0           # emitir ajustarCaudal inmediatamente
            
            else:
                
                nuevo["caudalObjetivo"] = 0.0
                nuevo["fase"] = OCIOSO
                nuevo["sigma"] = 0.0           # emitir detenerBomba
            
            return nuevo
 
        # --- Lectura del sensor ---
        if self.sensorFlujo in inputs:
            
            caudal_leido = inputs[self.sensorFlujo]
            nuevo["caudalReal"] = caudal_leido
 
            desvio = abs(caudal_leido - s["caudalObjetivo"])
            umbral = DESVIO_MAX_PERMITIDO * s["caudalObjetivo"]
 
            if desvio > umbral:
                
                # Desvío detectado
                if s["t_desvio"] == INFINITY:
                    
                    # Iniciar temporizador de desvío
                    nuevo["t_desvio"] = TIEMPO_MAX_DESVIO
                
                # Si ya estaba corriendo, continúa sin reiniciarse
                nuevo["sigma"] = _sigma_min(nuevo["t_desvio"], nuevo["t_bolsa"])
            
            else:
                
                # Desvío corregido: resetear temporizador y contador
                nuevo["t_desvio"] = INFINITY
                nuevo["contadorMedia"] = 0
                nuevo["sigma"] = _sigma_min(nuevo["t_desvio"], nuevo["t_bolsa"])
            
            return nuevo
 
        # --- Fin de bolsa ---
        if self.finBolsa in inputs:
            
            nuevo["fase"] = ALERTA_BOLSA
            nuevo["t_bolsa"] = TIEMPO_MAX_FIN_BOLSA
            nuevo["sigma"] = 0.0    # emitir alarma baja inmediatamente
            return nuevo
 
        # --- Confirmación del enfermero ---
        if self.confirmacionEnfermero in inputs:
            
            if s["fase"] == ALARMA_CRITICA:
                
                nuevo["fase"] = OCIOSO
                nuevo["sigma"] = 0.0
                nuevo["contadorMedia"] = 0
            
            # Si no hay alarma crítica activa: ignorar
            else:
                
                nuevo["sigma"] = sigma_restante
            
            return nuevo
 
        # Sin evento relevante
        nuevo["sigma"] = sigma_restante
        
        return nuevo

    def intTransition(self) -> dict:
        
        s = self.state
        nuevo = dict(s)

        if nuevo["t_bolsa"] != INFINITY:
            
            nuevo["t_bolsa"] = max(0.0, nuevo["t_bolsa"] - s["sigma"])
        
        if nuevo["t_desvio"] != INFINITY:
            
            nuevo["t_desvio"] = max(0.0, nuevo["t_desvio"] - s["sigma"])
 
        """MAXIMA PRIORIDAD"""

        # 1. Timeout de fin de bolsa → detener todo
        if nuevo["t_bolsa"] != INFINITY and nuevo["t_bolsa"] <= 0.0:
            
            nuevo["caudalObjetivo"] = 0.0
            nuevo["fase"]          = PARADA_POR_BOLSA
            nuevo["t_bolsa"]       = INFINITY
            nuevo["sigma"]         = 0.0
            return nuevo

        # 2. Timeout de desvío → escalar alarma
        if nuevo["t_desvio"] != INFINITY and nuevo["t_desvio"] <= 0.0:
            
            if s["contadorMedia"] < 2:
                
                nuevo["contadorMedia"] = s["contadorMedia"] + 1
                nuevo["fase"]          = ALARMA_MEDIA
                nuevo["t_desvio"]      = INFINITY
                nuevo["sigma"]         = 0.0
            
            else:
                
                nuevo["contadorMedia"] = 3
                nuevo["fase"]          = ALARMA_CRITICA
                nuevo["t_desvio"]      = INFINITY
                nuevo["sigma"]         = 0.0
            
            return nuevo
 
        # 3. Tras emitir PARADA_POR_BOLSA → volver a OCIOSO
        if s["fase"] == PARADA_POR_BOLSA:

            nuevo["fase"] = OCIOSO
            nuevo["sigma"] = INFINITY
            return nuevo 

        # 4. Tras emitir ALARMA_MEDIA → volver a INFUNDIENDO
        if s["fase"] == ALARMA_MEDIA:
            
            nuevo["fase"]  = INFUNDIENDO
            nuevo["sigma"] = _sigma_min(nuevo["t_desvio"], nuevo["t_bolsa"])
            return nuevo
 
        # 5. Tras emitir ALERTA_BOLSA → seguir en INFUNDIENDO con timer bolsa activo
        if s["fase"] == ALERTA_BOLSA:
            
            nuevo["fase"]  = INFUNDIENDO
            nuevo["sigma"] = _sigma_min(nuevo["t_desvio"], nuevo["t_bolsa"])
            return nuevo
 
        # 6. Tras emitir en INFUNDIENDO (ajustar caudal al inicio)
        if s["fase"] == INFUNDIENDO:
            
            nuevo["sigma"] = _sigma_min(nuevo["t_desvio"], nuevo["t_bolsa"])
            return nuevo
 
        # 7. ALARMA_CRITICA o OCIOSO sin timers → pasivo
        nuevo["sigma"] = INFINITY
        return nuevo

##########################################################################################

def _sigma_min(t_desvio: float, t_bolsa: float) -> float:
    """Devuelve el mínimo de los timers activos (ignora INFINITY)."""
    candidatos = [t for t in (t_desvio, t_bolsa) if t != INFINITY and t >= 0.0]
    return min(candidatos) if candidatos else INFINITY

def _clamp_caudal(valor: float) -> float:
    return max(0.0, min(CAUDAL_MAX, valor))

