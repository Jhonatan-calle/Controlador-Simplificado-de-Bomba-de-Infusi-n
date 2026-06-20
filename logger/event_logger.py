"""
logger/event_logger.py

Captura y almacena eventos de la simulación para análisis posterior.
Contiene TracerEventLogger para integrarse con PythonPDEVS.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Evento:
    tiempo:  float
    modelo:  str
    puerto:  str
    valor:   Any


class EventLogger:
    """
    Registra todos los eventos emitidos durante una simulación.
    Permite filtrar por puerto para hacer assertions en tests.
    """

    def __init__(self):
        self._log: list[Evento] = []

    def registrar(self, tiempo: float, modelo: str, puerto: str, valor: Any) -> None:
        self._log.append(Evento(tiempo=tiempo, modelo=modelo,
                                puerto=puerto, valor=valor))

    def todos(self) -> list[Evento]:
        return list(self._log)

    def filtrar_puerto(self, puerto: str) -> list[Evento]:
        return [e for e in self._log if e.puerto == puerto]

    def tiempos_de(self, puerto: str) -> list[float]:
        return [e.tiempo for e in self.filtrar_puerto(puerto)]

    def valores_de(self, puerto: str) -> list[Any]:
        return [e.valor for e in self.filtrar_puerto(puerto)]

    def conteo(self, puerto: str) -> int:
        return len(self.filtrar_puerto(puerto))

    def primer_evento(self, puerto: str) -> "Evento | None":
        eventos = self.filtrar_puerto(puerto)
        return eventos[0] if eventos else None

    def __repr__(self) -> str:
        lines = [f"  t={e.tiempo:.3f}  [{e.modelo}] {e.puerto} = {e.valor}"
                 for e in self._log]
        return "EventLog:\n" + "\n".join(lines)


class TracerEventLogger:
    """
    Tracer de pypdevs que captura eventos en un EventLogger.
    Se conecta usando sim.setCustomTracer().
    """

    def __init__(self, uid, server, event_logger, verbose=False):
        self.uid = uid
        self.server = server
        self.logger = event_logger
        self.verbose = verbose
        self._ultimo_tiempo = -1.0

    def startTracer(self, recover):
        pass

    def stopTracer(self):
        pass

    def _separador(self, tiempo):
        if self.verbose and tiempo != self._ultimo_tiempo:
            print(f"\n{'-'*55}")
            print(f"  t = {tiempo:.2f} s")
            print(f"{'-'*55}")
            self._ultimo_tiempo = tiempo

    def traceInit(self, aDEVS, t):
        tiempo = float(t[0])
        modelo = aDEVS.getModelFullName()
        estado = dict(aDEVS.state) if aDEVS.state else None
        self.logger.registrar(tiempo, modelo, "STATE_INIT", estado)
        if self.verbose:
            print(f"  [INIT] {modelo} → {estado}")

    def _log_output(self, aDEVS):
        if aDEVS.my_output is None:
            return
        tiempo = aDEVS.time_last[0]
        modelo = aDEVS.getModelFullName()
        self._separador(tiempo)
        for port, valores in aDEVS.my_output.items():
            nombre_puerto = port.getPortName()
            for valor in valores:
                self.logger.registrar(tiempo, modelo, nombre_puerto, valor)
                if self.verbose:
                    print(f"  [{modelo}] → {nombre_puerto} = {valor}")

    def _log_input(self, aDEVS):
        if aDEVS.my_input is None:
            return
        tiempo = aDEVS.time_last[0]
        modelo = aDEVS.getModelFullName()
        self._separador(tiempo)
        for port, valores in aDEVS.my_input.items():
            nombre_puerto = port.getPortName()
            for valor in valores:
                self.logger.registrar(tiempo, modelo, f"IN_{nombre_puerto}", valor)
                if self.verbose:
                    print(f"  [{modelo}] ← {nombre_puerto} = {valor}")

    def traceInternal(self, aDEVS):
        self._log_output(aDEVS)

    def traceExternal(self, aDEVS):
        self._log_input(aDEVS)

    def traceConfluent(self, aDEVS):
        self._log_input(aDEVS)
        self._log_output(aDEVS)