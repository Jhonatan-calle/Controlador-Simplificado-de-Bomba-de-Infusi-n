"""
graficos/graficar_resultados.py

Genera gráficos a partir del EventLogger de una simulación:
  - Subplot 1: Caudal objetivo vs caudal real en el tiempo
  - Subplot 2: Timeline de eventos (órdenes, alarmas, etc.)
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from logger.event_logger import EventLogger


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
# Subplot 2: Timeline de eventos
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
        ax.scatter(tiempo, fila, marker=marker, color=color,
                   s=60, zorder=5, edgecolors="black", linewidths=0.3)

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
# Función pública
# ---------------------------------------------------------------------------

def graficar_escenario(logger, num_escenario, nombre, tiempo_sim,
                       dir_salida="graficos", mostrar=True):
    """
    Genera figura con 2 subplots (caudal + timeline) y la guarda en
    ``dir_salida/escenario_{num}_{slug}.png``.

    Parámetros:
        logger — EventLogger con los datos de la simulación
        num_escenario — int, número de escenario
        nombre — str, nombre descriptivo del escenario
        tiempo_sim — float, duración de la simulación
        dir_salida — str, directorio donde guardar PNGs
        mostrar — bool, si además mostrar la figura en pantalla
    """
    if not isinstance(logger, EventLogger):
        raise TypeError("logger debe ser un EventLogger")

    if not logger.todos():
        print(f"  [graficos] Escenario {num_escenario}: sin datos, saltando")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=False)
    fig.suptitle(f"Escenario {num_escenario}: {nombre}",
                 fontsize=14, fontweight="bold")

    _graficar_caudal(ax1, logger, tiempo_sim)
    _graficar_timeline(ax2, logger, tiempo_sim)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Guardar PNG
    os.makedirs(dir_salida, exist_ok=True)
    slug = _sanitizar(nombre)
    ruta = os.path.join(dir_salida, f"escenario_{num_escenario}_{slug}.png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    print(f"  [graficos] Guardado: {ruta}")

    if mostrar:
        plt.show()
    else:
        plt.close(fig)
