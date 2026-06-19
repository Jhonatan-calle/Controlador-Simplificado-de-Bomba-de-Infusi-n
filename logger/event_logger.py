"""
logger/event_logger.py

Captura y almacena eventos de la simulación para análisis posterior.
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