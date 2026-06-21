"""
graficos/graficar_resultados.py

Genera gráficos a partir del EventLogger de una simulación:
  - Subplot 1: Caudal objetivo vs caudal real en el tiempo
  - Subplot 2: Estado de la bomba (fases del controlador)
  - Subplot 3: Timeline de eventos (órdenes, alarmas, etc.)
"""

import os
import warnings
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from logger.event_logger import EventLogger
from verificacion.reporte_resultados import generar_reporte, _reconstruir_estados


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitizar(nombre: str) -> str:
    """Convierte un nombre de escenario en un slug válido para filename."""
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ñ": "n", " ": "_", "(": "", ")": "", "ˇ": "",
    }
    for old, new in replacements.items():
        nombre = nombre.replace(old, new)
    return nombre.lower().strip("_")


def _escalon(eventos, tiempo_max, valor_inicial=0.0):
    """
    Convierte eventos (tiempo, valor) en vectores (x, y) para
    dibujar una función escalón con plt.plot(drawstyle='steps-post').
    """
    x = [0.0]
    y = [valor_inicial]
    for e in eventos:
        x.append(e.tiempo)
        y.append(y[-1])
        x.append(e.tiempo)
        y.append(e.valor)
    x.append(tiempo_max)
    y.append(y[-1])
    return x, y


# ---------------------------------------------------------------------------
# Subplot 1: Caudal
# ---------------------------------------------------------------------------

def _graficar_caudal(ax, logger, tiempo_max):
    ordenes = sorted(logger.filtrar_puerto("ordenMedica"),
                     key=lambda e: e.tiempo)
    ajustes = sorted(logger.filtrar_puerto("ajustarCaudal"),
                     key=lambda e: e.tiempo)
    caudales = sorted(logger.filtrar_puerto("caudalActual"),
                      key=lambda e: e.tiempo)
    criticas = sorted(logger.filtrar_puerto("notificacionAlarma"),
                      key=lambda e: e.tiempo)

    x_ord, y_ord = _escalon([e for e in ordenes if e.valor >= 0],
                            tiempo_max)
    x_aj, y_aj = _escalon([e for e in ajustes if e.valor >= 0],
                          tiempo_max)
    x_caud, y_caud = _escalon([e for e in caudales if e.valor >= 0],
                              tiempo_max)

    ax.plot(x_ord, y_ord, drawstyle='steps-post',
            label="Orden médica", color="#2196F3", linewidth=2.0)
    ax.plot(x_aj, y_aj, drawstyle='steps-post',
            label="Ajuste caudal", color="#4CAF50", linewidth=1.5,
            linestyle="--")
    ax.plot(x_caud, y_caud, drawstyle='steps-post',
            label="Caudal real", color="#F44336", linewidth=1.5)

    # Líneas verticales para alarmas críticas
    for e in criticas:
        if "CRITICA" in str(e.valor):
            ax.axvline(x=e.tiempo, color="#F44336", linestyle=":",
                       alpha=0.5, linewidth=1.0)

    ax.set_ylabel("Caudal (ml/h)")
    ax.set_xlim(0, tiempo_max)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_title("Caudal objetivo vs caudal real", fontsize=12)


# ---------------------------------------------------------------------------
# Subplot 2: Estado de la bomba
# ---------------------------------------------------------------------------

def _graficar_estado(ax, logger, tiempo_max):
    colores = {
        "OCIOSO":       "#9E9E9E",
        "INFUNDIENDO":  "#4CAF50",
        "ALERTA_BOLSA": "#FFEB3B",
        "MEDIA":        "#FF9800",
        "CRITICA":      "#F44336",
        "PARADA":       "#B71C1C",
    }
    orden = ["OCIOSO", "INFUNDIENDO", "ALERTA_BOLSA",
             "MEDIA", "CRITICA", "PARADA"]

    fases, timeline = _reconstruir_estados(logger, tiempo_max)

    x = [0.0]
    y = [fases["OCIOSO"]]
    for t, fase in timeline:
        x.append(t)
        y.append(y[-1])
        x.append(t)
        y.append(fases[fase])
    x.append(tiempo_max)
    y.append(y[-1])

    colores_linea = [colores.get(orden[int(v)], "#999") for v in set(y)]
    ax.plot(x, y, drawstyle='steps-post', color="#333", linewidth=2.0)

    for i in range(len(x) - 1):
        if x[i+1] > x[i]:
            ax.axvspan(x[i], x[i+1], alpha=0.15,
                       color=colores[orden[int(y[i])]])

    ax.set_ylabel("Estado")
    ax.set_xlim(0, tiempo_max)
    ax.set_ylim(-0.5, len(orden) - 0.5)
    ax.set_yticks(range(len(orden)))
    ax.set_yticklabels(orden, fontsize=8)
    ax.grid(True, axis="x", alpha=0.3)
    ax.set_title("Estado de la bomba", fontsize=12)


# ---------------------------------------------------------------------------
# Subplot 3: Timeline de eventos
# ---------------------------------------------------------------------------

def _graficar_timeline(ax, logger, tiempo_max):
    filas = {
        "ordenMedica":       (0, "#2196F3", "o",  "Orden médica"),
        "ajustarCaudal":     (1, "#4CAF50", "s",  "Ajuste caudal"),
        "alarma_baja":       (2, "#FFEB3B", "^",  "Alarma baja"),
        "alarma_media":      (3, "#FF9800", "^",  "Alarma media"),
        "alarma_critica":    (4, "#F44336", "v",  "Alarma crítica"),
        "confirmacionEnfermero": (5, "#8BC34A", "D", "Confirmación"),
        "finBolsa":          (6, "#9C27B0", "*",  "Fin bolsa"),
        "detenerBomba":      (7, "#B71C1C", "x",  "Detener bomba"),
    }

    for evento in logger.todos():
        puerto = evento.puerto
        tiempo = evento.tiempo

        if puerto in ("ordenMedica", "ajustarCaudal", "detenerBomba",
                      "confirmacionEnfermero", "finBolsa"):
            tipo = puerto
        elif puerto == "alarma":
            if evento.valor == "baja":
                tipo = "alarma_baja"
            elif evento.valor == "media":
                tipo = "alarma_media"
            elif evento.valor == "critica":
                tipo = "alarma_critica"
            else:
                continue
        elif puerto == "notificacionAlarma":
            if "BAJA" in str(evento.valor):
                tipo = "alarma_baja"
            elif "MEDIA" in str(evento.valor):
                tipo = "alarma_media"
            elif "CRITICA" in str(evento.valor):
                tipo = "alarma_critica"
            else:
                continue
        else:
            continue

        fila, color, marker, _ = filas[tipo]
        kwargs = dict(s=60, zorder=5)
        if marker != "x":
            kwargs["edgecolors"] = "black"
            kwargs["linewidths"] = 0.3
        ax.scatter(tiempo, fila, marker=marker, color=color, **kwargs)

    # Ejes
    ax.set_xlim(0, tiempo_max)
    ax.set_ylim(-0.5, len(filas) - 0.5)
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Tipo de evento")
    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels([v[3] for v in filas.values()], fontsize=8)
    ax.grid(True, axis="x", alpha=0.3)
    ax.set_title("Timeline de eventos", fontsize=12)


# ---------------------------------------------------------------------------
# Descripción textual del escenario
# ---------------------------------------------------------------------------

def _describir_escenario(config, resultados=None):
    lineas = []
    act = config.get("actuador", {})
    sns = config.get("sensor", {})
    ord = config.get("ordenes", {})
    fin = config.get("fin_bolsa", {})
    con = config.get("confirmacion", {})

    if act.get("factor_falla", 1.0) < 1.0:
        pct = (1 - act["factor_falla"]) * 100
        lineas.append(f"Actuador: {pct:.0f}% de desvío permanente")
    else:
        lineas.append("Actuador: sin falla")

    if sns.get("ruido_std", 0) > 0:
        lineas.append(f"Sensor: ruido gaussiano σ={sns['ruido_std']}")
    else:
        lineas.append("Sensor: sin ruido")

    if ord.get("modo") == "deterministico":
        if ord.get("caudal_fijo", 100) == 0:
            lineas.append("Órdenes: caudal=0 (detención programada)")
        else:
            gap = ord.get("interarribo_fijo", "?")
            lineas.append(f"Órdenes determinísticas cada {gap}s")
    elif ord.get("modo") == "estocastico":
        lineas.append("Órdenes estocásticas")

    if fin.get("tiempo_fijo", float("inf")) != float("inf"):
        lineas.append(f"Fin de bolsa en t={fin['tiempo_fijo']}s")
    elif fin.get("modo") == "estocastico":
        lineas.append("Fin de bolsa estocástico")

    if con.get("tiempo_fijo", float("inf")) != float("inf"):
        lineas.append(f"Confirmación en t={con['tiempo_fijo']}s")
    elif con.get("modo") == "estocastico":
        lineas.append("Confirmación estocástica")
    elif con.get("max_confirmaciones", 0) == 0:
        lineas.append("Sin confirmación")

    if config.get("violar_seguridad"):
        lineas.append("⚠ VIOLACIÓN: se ignoran alarmas críticas")

    texto = " | ".join(lineas)

    if resultados:
        fallos = [r for r in resultados if not r.cumplida]
        aciertos = [r for r in resultados if r.cumplida]
        if fallos:
            detalle = "; ".join(f"{r.propiedad}: {r.detalle}" for r in fallos)
            texto += f"\n✗ Violaciones ({len(fallos)}): {detalle}"
            texto += f" | ✓ {len(aciertos)} propiedades cumplidas"
        else:
            texto += f"\n✓ Verificación: {len(resultados)}/10 propiedades cumplidas"

    return texto


# ---------------------------------------------------------------------------
# Función pública
# ---------------------------------------------------------------------------

def graficar_escenario(logger, num_escenario, nombre, tiempo_sim,
                       config=None, resultados=None,
                       dir_salida="graficos", mostrar=True):
    """
    Genera figura con 3 subplots (caudal + estado + timeline) + descripción
    textual y la guarda en ``dir_salida/escenario_{num}_{slug}.png``.

    Parámetros:
        logger — EventLogger con los datos de la simulación
        num_escenario — int, número de escenario
        nombre — str, nombre descriptivo del escenario
        tiempo_sim — float, duración de la simulación
        config — dict, configuración del escenario (para la descripción)
        resultados — list[ResultadoVerificacion], resultados de verificación
        dir_salida — str, directorio donde guardar PNGs
        mostrar — bool, si además mostrar la figura en pantalla
    """
    if not isinstance(logger, EventLogger):
        raise TypeError("logger debe ser un EventLogger")

    if not logger.todos():
        print(f"  [graficos] Escenario {num_escenario}: sin datos, saltando")
        return

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10),
                                         sharex=False)
    fig.suptitle(f"Escenario {num_escenario}: {nombre}",
                 fontsize=14, fontweight="bold")

    _graficar_caudal(ax1, logger, tiempo_sim)
    _graficar_estado(ax2, logger, tiempo_sim)
    _graficar_timeline(ax3, logger, tiempo_sim)
    ax3.set_xlabel("Tiempo (s)")

    # Reporte de métricas
    reporte = generar_reporte(logger, config, tiempo_sim) if config else None

    # Texto descriptivo al pie de la figura
    if config:
        desc = _describir_escenario(config, resultados)
        if reporte and reporte.get("resumen"):
            desc += "\n" + " | ".join(reporte["resumen"])
        fig.text(0.5, 0.005, desc, ha="center", va="bottom",
                 fontsize=6.5, family="monospace",
                 bbox=dict(boxstyle="round,pad=0.4",
                           facecolor="lightyellow", alpha=0.85))

    plt.tight_layout(rect=[0, 0.08, 1, 0.96])

    # Guardar PNG
    os.makedirs(dir_salida, exist_ok=True)
    slug = _sanitizar(nombre)
    ruta = os.path.join(dir_salida, f"escenario_{num_escenario}_{slug}.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    print(f"  [graficos] Guardado: {ruta}")

    if mostrar:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            plt.show()
    else:
        plt.close(fig)
