"""
config.py — Parametrización del Sistema de Bomba de Infusión

Sección 1: Constantes del sistema (del enunciado, nunca cambian)
Sección 2: Parámetros de distribuciones estocásticas
Sección 3: Escenarios (determinísticos y estocásticos)
"""

from pypdevs.infinity import INFINITY

# =============================================================================
# SECCIÓN 1 — Constantes del sistema (requisitos del enunciado)
# =============================================================================

PERIODO_SENSOR = 1.0  # s — período de muestreo del SensorFlujo
LATENCIA_ACTUADOR = 0.5  # s — latencia física del ActuadorBomba
DESVIO_MAX_PERMITIDO = 0.10  # 10 % de desvío máximo tolerado
TIEMPO_MAX_DESVIO = (
    5.0  # s — tiempo máximo con desvío antes de alarma
)
TIEMPO_CONF_CRITICA = (
    30.0  # s — ventana para confirmar alarma crítica
)
PERIODO_REP_CRITICA = (
    10.0  # s — período de repetición de alarma crítica
)
TIEMPO_MAX_FIN_BOLSA = 60.0  # s — tiempo máximo tras fin de bolsa
CAUDAL_MIN = 0.0  # ml/h
CAUDAL_MAX = 200.0  # ml/h
TIEMPO_INICIO_INFUSION = (
    3.0  # s — tiempo máx para iniciar infusión tras orden
)
TASA_DERIVA_SENSOR = (
    0.02  # 2% del caudal por segundo desde la última corrección
)

# =============================================================================
# SECCIÓN 2 — Parámetros de distribuciones estocásticas
# =============================================================================

# GeneradorFinBolsa — distribución Normal
MEDIA_FIN_BOLSA = 30.0  # s — tiempo esperado de agotamiento
DESVIO_FIN_BOLSA = 2.0  # s — desviación estándar

# GeneradorConfirmacion — distribución Log-Normal
MU_CONFIRMACION = 2.5  # parámetro mu de la Log-Normal
SIGMA_LN_CONFIRMACION = 0.8  # parámetro sigma de la Log-Normal
MAX_CONFIRMACIONES = 3  # cuántas veces puede confirmar el enfermero

# Parámetros estocásticos para GeneradorOrdenes
INTERARRIBO_ORDENES = (
    20.0  # s — tiempo entre órdenes médicas (determinístico)
)
MEDIA_CAUDAL_ORDENES = 100.0  # ml/h - media de la distribución Normal
DESVIO_CAUDAL_ORDENES = 15.0  # ml/h - desvío estándar
MEDIA_TIEMPO_ORDENES = (
    10.0  # s - media de la distribución Exponencial para interarribos
)

# =============================================================================
# SECCIÓN 3 — Escenarios
# =============================================================================

# ---------------------------------------------------------------------------
# ESCENARIO 1 — Operación normal (sin fin de bolsa, sin desvío)
# ---------------------------------------------------------------------------
ESCENARIO_1_NORMAL = {
    "ordenes": {
        "modo": "deterministico",
        "caudal_fijo": 100.0,
        "interarribo_fijo": INTERARRIBO_ORDENES,
    },
    "fin_bolsa": {
        "modo": "deterministico",
        "tiempo_fijo": INFINITY,  # nunca ocurre
    },
    "confirmacion": {
        "modo": "deterministico",
        "tiempo_fijo": INFINITY,  # no hay alarma crítica
        "max_confirmaciones": 0,
    },
    "actuador": {
        "factor_falla": 1.0,  # sin falla
    },
    "sensor": {
        "ruido_std": 0.0,  # sin ruido
    },
}

# ---------------------------------------------------------------------------
# ESCENARIO 2 — Cambio de orden médica (caudal distinto)
# ---------------------------------------------------------------------------
ESCENARIO_2_CAMBIO_ORDEN = {
    "ordenes": {
        "modo": "estocastico",
        "semilla": 42,
        "media_caudal": MEDIA_CAUDAL_ORDENES,
        "desvio_caudal": DESVIO_CAUDAL_ORDENES,
        "media_tiempo": MEDIA_TIEMPO_ORDENES,
    },
    "fin_bolsa": {
        "modo": "deterministico",
        "tiempo_fijo": INFINITY,
    },
    "confirmacion": {
        "modo": "deterministico",
        "tiempo_fijo": INFINITY,
        "max_confirmaciones": 0,
    },
    "actuador": {
        "factor_falla": 1.0,
    },
    "sensor": {
        "ruido_std": 0.0,
    },
}

# ---------------------------------------------------------------------------
# ESCENARIO 3 — Orden con caudal = 0 (detener bomba)
# ---------------------------------------------------------------------------
ESCENARIO_3_ORDEN_CERO = {
    "ordenes": {
        "modo": "deterministico",
        "caudal_fijo": 0.0,
        "interarribo_fijo": 5.0,
    },
    "fin_bolsa": {
        "modo": "deterministico",
        "tiempo_fijo": INFINITY,
    },
    "confirmacion": {
        "modo": "deterministico",
        "tiempo_fijo": INFINITY,
        "max_confirmaciones": 0,
    },
    "actuador": {
        "factor_falla": 1.0,
    },
    "sensor": {
        "ruido_std": 0.0,
    },
}

# ---------------------------------------------------------------------------
# ESCENARIO 4 — Desvío leve (< 5 s, no dispara alarma media)
# ---------------------------------------------------------------------------
ESCENARIO_4_DESVIO_LEVE = {
    "ordenes": {
        "modo": "deterministico",
        "caudal_fijo": 100.0,
        "interarribo_fijo": INTERARRIBO_ORDENES,
    },
    "fin_bolsa": {
        "modo": "deterministico",
        "tiempo_fijo": INFINITY,
    },
    "confirmacion": {
        "modo": "deterministico",
        "tiempo_fijo": INFINITY,
        "max_confirmaciones": 0,
    },
    "actuador": {
        "factor_falla": 0.85,  # entrega el 85 % → desvío del 15 %, pero dura < 5 s
    },
    "sensor": {
        "ruido_std": 0.0,
    },
}

# ---------------------------------------------------------------------------
# ESCENARIO 5 — Desvío grave (> 5 s, dispara alarma media → crítica)
# ---------------------------------------------------------------------------
ESCENARIO_5_DESVIO_GRAVE = {
    "ordenes": {
        "modo": "deterministico",
        "caudal_fijo": 100.0,
        "interarribo_fijo": INTERARRIBO_ORDENES,
    },
    "fin_bolsa": {
        "modo": "deterministico",
        "tiempo_fijo": INFINITY,
    },
    "confirmacion": {
        "modo": "deterministico",
        "tiempo_fijo": INFINITY,  # sin confirmación → escala a crítica
        "max_confirmaciones": 0,
    },
    "actuador": {
        "factor_falla": 0.80,  # 20 % de desvío sostenido
    },
    "sensor": {
        "ruido_std": 0.0,
    },
}

# ---------------------------------------------------------------------------
# ESCENARIO 6 — Fin de bolsa (determinístico)
# ---------------------------------------------------------------------------
ESCENARIO_6_FIN_BOLSA = {
    "ordenes": {
        "modo": "deterministico",
        "caudal_fijo": 100.0,
        "interarribo_fijo": INTERARRIBO_ORDENES,
    },
    "fin_bolsa": {
        "modo": "deterministico",
        "tiempo_fijo": 30.0,  # bolsa se agota a t=30 s exacto
    },
    "confirmacion": {
        "modo": "deterministico",
        "tiempo_fijo": 20.0,  # enfermero confirma 20 s después del evento
        "max_confirmaciones": 1,
    },
    "actuador": {
        "factor_falla": 1.0,
    },
    "sensor": {
        "ruido_std": 0.0,
    },
}

# Versión estocástica del mismo escenario (para comparación)
ESCENARIO_6_FIN_BOLSA_ESTOCASTICO = {
    "ordenes": {
        "modo": "deterministico",
        "caudal_fijo": 100.0,
        "interarribo_fijo": INTERARRIBO_ORDENES,
    },
    "fin_bolsa": {
        "modo": "estocastico",
        "semilla": 42,
        "media": MEDIA_FIN_BOLSA,
        "desvio_std": DESVIO_FIN_BOLSA,
    },
    "confirmacion": {
        "modo": "estocastico",
        "semilla": 42,
        "mu": MU_CONFIRMACION,
        "sigma_ln": SIGMA_LN_CONFIRMACION,
        "max_confirmaciones": 1,
    },
    "actuador": {
        "factor_falla": 1.0,
    },
    "sensor": {
        "ruido_std": 0.5,
    },
}

# ---------------------------------------------------------------------------
# ESCENARIO 7 — Alarma crítica sin confirmación (repetición indefinida)
# ---------------------------------------------------------------------------
ESCENARIO_7_ALARMA_CRITICA = {
    "ordenes": {
        "modo": "deterministico",
        "caudal_fijo": 100.0,
        "interarribo_fijo": INFINITY,
    },
    "fin_bolsa": {
        "modo": "deterministico",
        "tiempo_fijo": INFINITY,  # no hay fin de bolsa
    },
    "confirmacion": {
        "modo": "deterministico",
        "tiempo_fijo": INFINITY,  # nadie confirma
        "max_confirmaciones": 0,
    },
    "actuador": {
        "factor_falla": 1.0,
    },
    "sensor": {
        "ruido_std": 0.0,
    },
}

# ---------------------------------------------------------------------------
# ESCENARIO 8 — Órdenes médicas estocásticas (Resto del sistema normal)
# ---------------------------------------------------------------------------
ESCENARIO_8_ORDENES_ESTOCASTICO = {
    "ordenes": {
        "modo": "estocastico",
        "semilla": 42,
        "media_caudal": MEDIA_CAUDAL_ORDENES,
        "desvio_caudal": DESVIO_CAUDAL_ORDENES,
        "media_tiempo": MEDIA_TIEMPO_ORDENES,
    },
    "fin_bolsa": {
        "modo": "deterministico",
        "tiempo_fijo": INFINITY,
    },
    "confirmacion": {
        "modo": "deterministico",
        "tiempo_fijo": INFINITY,
        "max_confirmaciones": 0,
    },
    "actuador": {
        "factor_falla": 1.0,
    },
    "sensor": {
        "ruido_std": 0.0,
    },
}

# ---------------------------------------------------------------------------
# ESCENARIO 9 — Caos total (Todos los modelos en modo estocástico)
# ---------------------------------------------------------------------------
ESCENARIO_9_ESTOCASTICO_COMPLETO = {
    "ordenes": {
        "modo": "estocastico",
        "semilla": 42,
        "media_caudal": MEDIA_CAUDAL_ORDENES,
        "desvio_caudal": DESVIO_CAUDAL_ORDENES,
        "media_tiempo": MEDIA_TIEMPO_ORDENES,
    },
    "fin_bolsa": {
        "modo": "estocastico",
        "semilla": 42,
        "media": MEDIA_FIN_BOLSA,
        "desvio_std": DESVIO_FIN_BOLSA,
    },
    "confirmacion": {
        "modo": "estocastico",
        "semilla": 42,
        "mu": MU_CONFIRMACION,
        "sigma_ln": SIGMA_LN_CONFIRMACION,
        "max_confirmaciones": MAX_CONFIRMACIONES,
    },
    "actuador": {
        "factor_falla": 1.0,
    },
    "sensor": {
        "ruido_std": 0.5,  # El sensor mete un poco de ruido en la lectura
    },
}

# ---------------------------------------------------------------------------
# Lista de todos los escenarios determinísticos (para parametrize en pytest)
# ---------------------------------------------------------------------------
TODOS_ESCENARIOS_DETERMINISTICOS = [
    ("normal", ESCENARIO_1_NORMAL),
    ("cambio_orden", ESCENARIO_2_CAMBIO_ORDEN),
    ("orden_cero", ESCENARIO_3_ORDEN_CERO),
    ("desvio_leve", ESCENARIO_4_DESVIO_LEVE),
    ("desvio_grave", ESCENARIO_5_DESVIO_GRAVE),
    ("fin_bolsa", ESCENARIO_6_FIN_BOLSA),
    ("alarma_critica", ESCENARIO_7_ALARMA_CRITICA),
]

# ---------------------------------------------------------------------------
# Lista de todos los escenarios estocásticos
# ---------------------------------------------------------------------------
TODOS_ESCENARIOS_ESTOCASTICOS = [
    ("fin_bolsa_estocastico", ESCENARIO_6_FIN_BOLSA_ESTOCASTICO),
    ("ordenes_estocastico", ESCENARIO_8_ORDENES_ESTOCASTICO),
    ("caos_total", ESCENARIO_9_ESTOCASTICO_COMPLETO),
]
