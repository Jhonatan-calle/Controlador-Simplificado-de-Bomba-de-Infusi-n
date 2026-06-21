"""
sistema/sistema_bomba.py

Modelo acoplado del Sistema de Bomba de Infusión.
Conecta todos los modelos atómicos según el diagrama del proyecto.
"""

from pypdevs.DEVS import CoupledDEVS

from modelos.generador_ordenes      import GeneradorOrdenes
from modelos.sensor_flujo           import SensorFlujo
from modelos.actuador_bomba         import ActuadorBomba
from modelos.controlador_bomba      import ControladorBomba
from modelos.modulo_alarmas         import ModuloAlarmas
from modelos.generador_confirmacion import GeneradorConfirmacion
from modelos.generador_fin_bolsa    import GeneradorFinBolsa


class SistemaBomba(CoupledDEVS):
    """
    Modelo acoplado completo de la bomba de infusión.

    Puertos de salida externos (observables desde el exterior):
        caudalActual       — caudal físico real (del ActuadorBomba)
        registrarEvento    — log de auditoría (del ControladorBomba)
        notificacionAlarma — mensajes de alarma (del ModuloAlarmas)
    """

    def __init__(self, config: dict, name: str = "SistemaBomba"):
        super().__init__(name)

        # ----------------------------------------------------------------
        # Instanciar modelos atómicos
        # ----------------------------------------------------------------
        self.generador_ordenes   = self.addSubModel(GeneradorOrdenes(config))
        self.sensor_flujo        = self.addSubModel(SensorFlujo(config))
        self.actuador_bomba      = self.addSubModel(ActuadorBomba(config))
        self.controlador_bomba   = self.addSubModel(
            ControladorBomba(violar_seguridad=config.get("violar_seguridad", False))
        )
        self.modulo_alarmas      = self.addSubModel(ModuloAlarmas())
        self.generador_confirm   = self.addSubModel(GeneradorConfirmacion(config))
        self.generador_fin_bolsa = self.addSubModel(GeneradorFinBolsa(config))

        # ----------------------------------------------------------------
        # Puertos de salida externos
        # ----------------------------------------------------------------
        self.caudalActual       = self.addOutPort("caudalActual")
        self.registrarEvento    = self.addOutPort("registrarEvento")
        self.notificacionAlarma = self.addOutPort("notificacionAlarma")

        # ----------------------------------------------------------------
        # Conexiones internas
        # ----------------------------------------------------------------

        # GeneradorOrdenes → ControladorBomba
        self.connectPorts(
            self.generador_ordenes.ordenMedica,
            self.controlador_bomba.ordenMedica,
        )

        # ControladorBomba → ActuadorBomba
        self.connectPorts(
            self.controlador_bomba.ajustarCaudal,
            self.actuador_bomba.ajustarCaudal,
        )
        self.connectPorts(
            self.controlador_bomba.detenerBomba,
            self.actuador_bomba.detenerBomba,
        )

        # ActuadorBomba → SensorFlujo
        self.connectPorts(
            self.actuador_bomba.caudalActual,
            self.sensor_flujo.caudalActual,
        )

        # SensorFlujo → ControladorBomba
        self.connectPorts(
            self.sensor_flujo.sensorFlujo,
            self.controlador_bomba.sensorFlujo,
        )

        # GeneradorFinBolsa → ControladorBomba
        self.connectPorts(
            self.generador_fin_bolsa.finBolsa,
            self.controlador_bomba.finBolsa,
        )

        # GeneradorConfirmacion → ControladorBomba y ModuloAlarmas
        self.connectPorts(
            self.generador_confirm.confirmacionEnfermero,
            self.controlador_bomba.confirmacionEnfermero,
        )
        self.connectPorts(
            self.generador_confirm.confirmacionEnfermero,
            self.modulo_alarmas.confirmacionEnfermero,
        )

        # ControladorBomba → ModuloAlarmas
        self.connectPorts(
            self.controlador_bomba.alarma,
            self.modulo_alarmas.alarma,
        )

        # ----------------------------------------------------------------
        # Conexiones hacia puertos externos (observabilidad)
        # ----------------------------------------------------------------
        self.connectPorts(
            self.actuador_bomba.caudalActual,
            self.caudalActual,
        )
        self.connectPorts(
            self.controlador_bomba.registrarEvento,
            self.registrarEvento,
        )
        self.connectPorts(
            self.modulo_alarmas.notificacionAlarma,
            self.notificacionAlarma,
        )