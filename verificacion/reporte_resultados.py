"""
verificacion/reporte_resultados.py

Reporte estructurado de resultados de simulación.
"""

from logger.event_logger import EventLogger
from config import DESVIO_MAX_PERMITIDO


def _porcentaje_infusion_correcta(logger, tiempo_sim):
    ordenes = sorted(logger.filtrar_puerto("ordenMedica"),
                     key=lambda e: e.tiempo)
    caudales = sorted(logger.filtrar_puerto("caudalActual"),
                      key=lambda e: e.tiempo)

    if not ordenes or not caudales:
        return 0.0

    eventos = []
    for e in ordenes:
        eventos.append((e.tiempo, "orden", e.valor))
    for e in caudales:
        eventos.append((e.tiempo, "caudal", e.valor))
    eventos.sort(key=lambda x: x[0])

    target = 0.0
    real = 0.0
    t_correcto = 0.0
    ultimo_t = 0.0
    primera_orden = ordenes[0].tiempo

    for t, tipo, valor in eventos:
        if t > ultimo_t and target > 0:
            diff = abs(real - target) / target
            if diff <= DESVIO_MAX_PERMITIDO:
                t_correcto += t - ultimo_t

        if tipo == "orden":
            target = valor
        else:
            real = valor
        ultimo_t = t

    if ultimo_t < tiempo_sim and target > 0:
        diff = abs(real - target) / target
        if diff <= DESVIO_MAX_PERMITIDO:
            t_correcto += tiempo_sim - ultimo_t

    total = tiempo_sim - primera_orden
    return (t_correcto / total * 100) if total > 0 else 0.0


def _reconstruir_estados(logger, tiempo_sim):
    """Reconstruye la fase del controlador en el tiempo desde eventos."""
    eventos = []

    for e in logger.filtrar_puerto("alarma"):
        eventos.append((e.tiempo, e.valor.upper()))

    for e in logger.filtrar_puerto("detenerBomba"):
        eventos.append((e.tiempo, "DETENER"))

    for e in logger.filtrar_puerto("ajustarCaudal"):
        if e.valor > 0:
            eventos.append((e.tiempo, "INFUNDIENDO"))

    for e in logger.filtrar_puerto("finBolsa"):
        eventos.append((e.tiempo, "ALERTA_BOLSA"))

    for e in logger.filtrar_puerto("registrarEvento"):
        val = e.valor
        if "CRITICA" in val:
            eventos.append((e.tiempo, "CRITICA"))
        elif "MEDIA" in val:
            eventos.append((e.tiempo, "MEDIA"))
        elif "fin de bolsa" in val.lower() or "limite tras" in val:
            eventos.append((e.tiempo, "PARADA"))
        elif "caudal=0" in val:
            eventos.append((e.tiempo, "OCIOSO"))

    eventos.sort(key=lambda x: x[0])

    fases = {"OCIOSO": 0, "INFUNDIENDO": 1, "ALERTA_BOLSA": 2,
             "MEDIA": 3, "CRITICA": 4, "PARADA": 5}
    fase_actual = "OCIOSO"
    timeline = [(0.0, fase_actual)]

    for t, ev in eventos:
        if ev == "INFUNDIENDO" and fase_actual not in ("CRITICA", "PARADA"):
            fase_actual = "INFUNDIENDO"
        elif ev == "baja" or ev == "ALERTA_BOLSA":
            fase_actual = "ALERTA_BOLSA"
        elif ev == "media" or ev == "MEDIA":
            fase_actual = "MEDIA"
        elif ev == "critica" or ev == "CRITICA":
            fase_actual = "CRITICA"
        elif ev == "DETENER":
            if fase_actual == "CRITICA":
                pass
            elif fase_actual == "PARADA":
                pass
            else:
                fase_actual = "OCIOSO"
        elif ev == "PARADA":
            fase_actual = "PARADA"
        elif ev == "OCIOSO":
            fase_actual = "OCIOSO"
        timeline.append((t, fase_actual))

    return fases, timeline


def generar_reporte(logger, config, tiempo_sim):
    ordenes = logger.filtrar_puerto("ordenMedica")
    ajustes = logger.filtrar_puerto("ajustarCaudal")
    caudales = logger.filtrar_puerto("caudalActual")

    # Alarmas generadas
    alarmas = {"baja": 0, "media": 0, "critica": 0}
    for e in logger.filtrar_puerto("alarma"):
        if e.valor in alarmas:
            alarmas[e.valor] += 1

    # Tiempo de respuesta ante desvíos
    medias = [e for e in logger.filtrar_puerto("alarma") if e.valor == "media"]
    tiempos_desvio = []
    for m in medias:
        prev = [a for a in ajustes
                if a.tiempo < m.tiempo and a.tiempo > m.tiempo - 10]
        if prev:
            tiempos_desvio.append(round(m.tiempo - prev[0].tiempo, 2))

    # Tiempo de respuesta ante fin de bolsa
    fines = logger.tiempos_de("finBolsa")
    detenciones = logger.tiempos_de("detenerBomba")
    tiempos_fin = []
    for f in fines:
        post = [d for d in detenciones if d >= f]
        if post:
            tiempos_fin.append(round(post[0] - f, 2))

    # Cantidad de detenciones preventivas
    total_detenciones = len(detenciones)

    # Porcentaje de tiempo con infusión correcta
    pct_correcto = round(
        _porcentaje_infusion_correcta(logger, tiempo_sim), 1)

    # Resumen textual
    resumen = []
    total_alarmas = sum(alarmas.values())
    resumen.append(f"Alarmas: {total_alarmas} total "
                   f"(baja={alarmas['baja']}, media={alarmas['media']}, "
                   f"critica={alarmas['critica']})")

    if tiempos_desvio:
        prom = sum(tiempos_desvio) / len(tiempos_desvio)
        resumen.append(f"Respuesta a desvío: {prom:.2f}s (promedio de "
                       f"{len(tiempos_desvio)} eventos)")

    if tiempos_fin:
        resumen.append(f"Respuesta a fin de bolsa: "
                       f"{tiempos_fin[0]:.2f}s")

    resumen.append(f"Detenciones: {total_detenciones}")
    resumen.append(f"Infusión correcta: {pct_correcto:.1f}% del tiempo")

    return {
        "alarmas": alarmas,
        "tiempo_respuesta_desvio": tiempos_desvio,
        "tiempo_respuesta_fin_bolsa": tiempos_fin,
        "detenciones": total_detenciones,
        "porcentaje_correcto": pct_correcto,
        "resumen": resumen,
    }
