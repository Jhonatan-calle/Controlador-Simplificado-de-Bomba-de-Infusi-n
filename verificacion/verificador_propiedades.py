"""
verificacion/verificador_propiedades.py

Verifica propiedades de safety, liveness y temporalidad
contra el log de eventos de una simulación.
"""

from dataclasses import dataclass, field
from logger.event_logger import Evento, EventLogger
from config import (
    CAUDAL_MAX,
    TIEMPO_INICIO_INFUSION,
    TIEMPO_MAX_DESVIO,
    DESVIO_MAX_PERMITIDO,
    TIEMPO_MAX_FIN_BOLSA,
    TIEMPO_CONF_CRITICA,
    PERIODO_REP_CRITICA,
)


@dataclass
class ResultadoVerificacion:
    propiedad: str
    cumplida:  bool
    detalle:   str = ""
    evidencia: list[Evento] = field(default_factory=list)


T = 0.1  # tolerancia en segundos


class VerificadorPropiedades:

    def __init__(self, log: EventLogger, config: dict):
        self.log = log
        self.config = config

    def verificar_todo(self) -> list[ResultadoVerificacion]:
        return [
            self.p_safety_caudal_cero(),
            self.p_safety_caudal_maximo(),
            self.p_safety_critica_sin_confirmacion(),
            self.p_liveness_orden_produce_accion(),
            self.p_liveness_critica_se_repite(),
            self.p_liveness_fin_bolsa_detiene(),
            self.p_temporal_inicio_infusion(),
            self.p_temporal_alarma_media_en_5s(),
            self.p_temporal_fin_bolsa_60s(),
            self.p_temporal_critica_repite_10s(),
        ]

    # ------------------------------------------------------------------
    # Safety
    # ------------------------------------------------------------------

    def p_safety_caudal_cero(self) -> ResultadoVerificacion:
        """
        Si la última ordenMedica es 0, no debe haber ajustarCaudal > 0 después.
        """
        ordenes = self.log.filtrar_puerto("ordenMedica")
        ajustes = self.log.filtrar_puerto("ajustarCaudal")

        if not ordenes:
            return ResultadoVerificacion(
                "P1: Safety — caudal cero",
                True, "No hubo órdenes médicas"
            )

        ultima_orden = ordenes[-1]
        if ultima_orden.valor != 0:
            return ResultadoVerificacion(
                "P1: Safety — caudal cero",
                True, "Última orden no es caudal cero"
            )

        violaciones = [e for e in ajustes
                       if e.tiempo >= ultima_orden.tiempo and e.valor > 0]
        if violaciones:
            return ResultadoVerificacion(
                "P1: Safety — caudal cero",
                False,
                f"Se ajustó caudal > 0 después de orden=0 en t={violaciones[0].tiempo}",
                violaciones,
            )
        return ResultadoVerificacion(
            "P1: Safety — caudal cero",
            True, "No hubo ajustes tras orden=0"
        )

    def p_safety_caudal_maximo(self) -> ResultadoVerificacion:
        """
        Ningún ajustarCaudal supera CAUDAL_MAX.
        """
        ajustes = self.log.filtrar_puerto("ajustarCaudal")
        violaciones = [e for e in ajustes if e.valor > CAUDAL_MAX]
        if violaciones:
            return ResultadoVerificacion(
                "P2: Safety — caudal máximo",
                False,
                f"Se superó {CAUDAL_MAX} ml/h en t={violaciones[0].tiempo}",
                violaciones,
            )
        return ResultadoVerificacion(
            "P2: Safety — caudal máximo",
            True, "Todos los caudales dentro del límite"
        )

    def p_safety_critica_sin_confirmacion(self) -> ResultadoVerificacion:
        """
        Tras alarmaCritica, no debe haber ajustarCaudal
        hasta que llegue confirmacionEnfermero o nueva orden.
        """
        criticas = [e for e in self.log.filtrar_puerto("alarma")
                    if e.valor == "critica"]
        if not criticas:
            return ResultadoVerificacion(
                "P3: Safety — crítica sin confirmación",
                True, "No hubo alarma crítica"
            )

        confirmaciones = self.log.tiempos_de("confirmacionEnfermero")
        ordenes = self.log.tiempos_de("ordenMedica")

        for critica in criticas:
            t_critica = critica.tiempo
            ajustes_post = [e for e in self.log.filtrar_puerto("ajustarCaudal")
                            if e.tiempo > t_critica]

            reanudacion = [t for t in confirmaciones if t >= t_critica]
            reanudacion += [t for t in ordenes if t >= t_critica]

            if not reanudacion:
                if ajustes_post:
                    return ResultadoVerificacion(
                        "P3: Safety — crítica sin confirmación",
                        False,
                        f"Ajuste post-crítica sin confirmación en t={ajustes_post[0].tiempo}",
                        ajustes_post,
                    )
            else:
                t_reanudacion = min(reanudacion)
                violaciones = [e for e in ajustes_post
                               if e.tiempo < t_reanudacion]
                if violaciones:
                    return ResultadoVerificacion(
                        "P3: Safety — crítica sin confirmación",
                        False,
                        f"Ajuste antes de reanudación en t={violaciones[0].tiempo}",
                        violaciones,
                    )

        return ResultadoVerificacion(
            "P3: Safety — crítica sin confirmación",
            True, "No hay ajustes ilegales tras crítica"
        )

    # ------------------------------------------------------------------
    # Liveness
    # ------------------------------------------------------------------

    def p_liveness_orden_produce_accion(self) -> ResultadoVerificacion:
        """
        Toda ordenMedica debe producir ajustarCaudal o detenerBomba.
        """
        ordenes = self.log.filtrar_puerto("ordenMedica")
        for orden in ordenes:
            t = orden.tiempo
            acciones = [e for e in self.log.todos()
                        if e.puerto in ("ajustarCaudal", "detenerBomba")
                        and e.tiempo - t <= TIEMPO_INICIO_INFUSION]
            if not acciones:
                return ResultadoVerificacion(
                    "P4: Liveness — orden produce acción",
                    False,
                    f"Orden en t={t} sin acción asociada",
                    [orden],
                )
        return ResultadoVerificacion(
            "P4: Liveness — orden produce acción",
            True, "Todas las órdenes produjeron acción"
        )

    def p_liveness_critica_se_repite(self) -> ResultadoVerificacion:
        """
        Toda alarma crítica sin confirmación debe repetirse eventualmente.
        """
        criticas = [e for e in self.log.filtrar_puerto("notificacionAlarma")
                    if e.valor.startswith("ALERTA: CRITICA")]
        if not criticas:
            return ResultadoVerificacion(
                "P5: Liveness — crítica se repite",
                True, "No hubo alarma crítica"
            )

        confirmaciones = self.log.tiempos_de("confirmacionEnfermero")

        # No exigir repetición para la última crítica (simulación termina antes)
        for i, critica in enumerate(criticas[:-1]):
            t = critica.tiempo
            conf_post = [c for c in confirmaciones if c >= t]
            if conf_post:
                continue

            siguientes = [c for c in criticas[i+1:]
                          if c.tiempo > t + T]
            if not siguientes:
                return ResultadoVerificacion(
                    "P5: Liveness — crítica se repite",
                    False,
                    f"Crítica en t={t} sin confirmación ni repetición",
                    [critica],
                )

        return ResultadoVerificacion(
            "P5: Liveness — crítica se repite",
            True, "Todas las críticas sin confirmación se repiten"
        )

    def p_liveness_fin_bolsa_detiene(self) -> ResultadoVerificacion:
        """
        Tras finBolsa, eventualmente debe ocurrir detenerBomba.
        """
        fines = self.log.tiempos_de("finBolsa")
        if not fines:
            return ResultadoVerificacion(
                "P6: Liveness — fin de bolsa detiene",
                True, "No hubo evento fin de bolsa"
            )

        detenciones = self.log.tiempos_de("detenerBomba")
        for t_fin in fines:
            det_post = [d for d in detenciones if d >= t_fin]
            if not det_post:
                return ResultadoVerificacion(
                    "P6: Liveness — fin de bolsa detiene",
                    False,
                    f"Fin de bolsa en t={t_fin} sin detenerBomba posterior",
                )

        return ResultadoVerificacion(
            "P6: Liveness — fin de bolsa detiene",
            True, "Todo fin de bolsa fue seguido de detención"
        )

    # ------------------------------------------------------------------
    # Temporal
    # ------------------------------------------------------------------

    def p_temporal_inicio_infusion(self) -> ResultadoVerificacion:
        """
        ordenMedica > 0 → ajustarCaudal debe ocurrir en < TIEMPO_INICIO_INFUSION s.
        """
        ordenes = self.log.filtrar_puerto("ordenMedica")
        max_time = max(e.tiempo for e in self.log.todos()) if self.log.todos() else 0.0
        for orden in ordenes:
            if orden.valor <= 0:
                continue
            if orden.tiempo + TIEMPO_INICIO_INFUSION > max_time:
                continue
            ajustes = [e for e in self.log.filtrar_puerto("ajustarCaudal")
                       if e.tiempo >= orden.tiempo]
            if not ajustes:
                return ResultadoVerificacion(
                    "P7: Temporal — inicio de infusión",
                    False,
                    f"Orden en t={orden.tiempo} sin ajuste posterior",
                    [orden],
                )
            demora = ajustes[0].tiempo - orden.tiempo
            if demora > TIEMPO_INICIO_INFUSION + T:
                return ResultadoVerificacion(
                    "P7: Temporal — inicio de infusión",
                    False,
                    f"Demora de {demora:.2f}s supera límite de {TIEMPO_INICIO_INFUSION}s",
                    [orden, ajustes[0]],
                )
        return ResultadoVerificacion(
            "P7: Temporal — inicio de infusión",
            True, "Todas las infusiones iniciaron a tiempo"
        )

    def p_temporal_alarma_media_en_5s(self) -> ResultadoVerificacion:
        """
        Desvío > 10% por más de TIEMPO_MAX_DESVIO s → debe disparar alarmaMedia.
        """
        medias = self.log.filtrar_puerto("alarma")
        medias = [e for e in medias if e.valor == "media"]
        if not medias:
            return ResultadoVerificacion(
                "P8: Temporal — alarma media en 5s",
                True, "No hubo alarma media"
            )

        ajustes = self.log.filtrar_puerto("ajustarCaudal")
        for media in medias:
            t_media = media.tiempo
            ajuste_previo = [a for a in ajustes
                             if a.tiempo < t_media and a.tiempo > t_media - TIEMPO_MAX_DESVIO - T]
            if not ajuste_previo:
                return ResultadoVerificacion(
                    "P8: Temporal — alarma media en 5s",
                    False,
                    f"Alarma media en t={t_media} sin desvío previo detectable",
                    [media],
                )

        return ResultadoVerificacion(
            "P8: Temporal — alarma media en 5s",
            True, "Alarmas medias ocurrieron dentro del tiempo esperado"
        )

    def p_temporal_fin_bolsa_60s(self) -> ResultadoVerificacion:
        """
        finBolsa → detenerBomba debe ocurrir en ≤ TIEMPO_MAX_FIN_BOLSA s.
        """
        fines = self.log.tiempos_de("finBolsa")
        if not fines:
            return ResultadoVerificacion(
                "P9: Temporal — fin de bolsa 60s",
                True, "No hubo evento fin de bolsa"
            )

        detenciones = self.log.tiempos_de("detenerBomba")
        for t_fin in fines:
            det_post = [d for d in detenciones if d >= t_fin]
            if not det_post:
                return ResultadoVerificacion(
                    "P9: Temporal — fin de bolsa 60s",
                    False,
                    f"Fin de bolsa en t={t_fin} sin detenerBomba posterior",
                )
            demora = det_post[0] - t_fin
            if demora > TIEMPO_MAX_FIN_BOLSA + T:
                return ResultadoVerificacion(
                    "P9: Temporal — fin de bolsa 60s",
                    False,
                    f"Demora de {demora:.2f}s supera límite de {TIEMPO_MAX_FIN_BOLSA}s",
                )

        return ResultadoVerificacion(
            "P9: Temporal — fin de bolsa 60s",
            True, "Todas las detenciones ocurrieron dentro del plazo"
        )

    def p_temporal_critica_repite_10s(self) -> ResultadoVerificacion:
        """
        Si una alarma crítica no es confirmada dentro de TIEMPO_CONF_CRITICA s,
        debe repetirse cada PERIODO_REP_CRITICA s.
        """
        criticas = self.log.filtrar_puerto("notificacionAlarma")
        criticas = [e for e in criticas if e.valor == "ALERTA: CRITICA"]

        if len(criticas) < 2:
            return ResultadoVerificacion(
                "P10: Temporal — crítica repite cada 10s",
                True, "No hubo repeticiones de crítica"
            )

        confirmaciones = self.log.tiempos_de("confirmacionEnfermero")

        primera = criticas[0]
        seguidas = criticas[1:]

        conf_entre = [t for t in confirmaciones
                      if primera.tiempo < t <= seguidas[0].tiempo]

        if conf_entre:
            return ResultadoVerificacion(
                "P10: Temporal — crítica repite cada 10s",
                True, "Crítica confirmada antes de necesitar repetición"
            )

        gap1 = seguidas[0].tiempo - primera.tiempo
        if abs(gap1 - TIEMPO_CONF_CRITICA) > T:
            return ResultadoVerificacion(
                "P10: Temporal — crítica repite cada 10s",
                False,
                f"Primera repetición en {gap1:.2f}s, esperada en {TIEMPO_CONF_CRITICA}s",
                [primera, seguidas[0]],
            )

        for i in range(1, len(seguidas)):
            gap = seguidas[i].tiempo - seguidas[i-1].tiempo
            if abs(gap - PERIODO_REP_CRITICA) > T:
                return ResultadoVerificacion(
                    "P10: Temporal — crítica repite cada 10s",
                    False,
                    f"Repetición {i+1} en {gap:.2f}s, esperada en {PERIODO_REP_CRITICA}s",
                    [seguidas[i-1], seguidas[i]],
                )

        return ResultadoVerificacion(
            "P10: Temporal — crítica repite cada 10s",
            True,
            f"{len(criticas)} notificaciones, gaps correctos "
            f"(1er gap={gap1:.1f}s, resto≈{PERIODO_REP_CRITICA}s)"
        )
