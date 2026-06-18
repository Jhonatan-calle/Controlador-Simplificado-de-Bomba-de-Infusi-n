from pypdevs.infinity import INFINITY

# =============================================================================
# SECCIÓN 1: Constantes del sistema (Tabla 1 del enunciado)
# =============================================================================
CAUDAL_MIN = 0.0                       # ml/h
CAUDAL_MAX = 200.0                     # ml/h
TIEMPO_MAX_INICIO_INFUSION = 3.0       # s
PERIODO_MUESTREO_SENSOR = 1.0          # s
LATENCIA_ACTUADOR = 0.5                # s
DESVIO_MAX_PORCENTAJE = 0.10           # 10%
TIEMPO_MAX_DESVIO = 5.0                # s
TIEMPO_CONFIRMACION_CRITICA = 30.0     # s
PERIODO_REPETICION_CRITICA = 10.0      # s
TIEMPO_MAX_FIN_BOLSA = 60.0            # s

# Criterio de escalado
ALARMAS_MEDIA_ANTES_DE_CRITICA = 3     # nº de alarmaMedia toleradas antes de escalar

# =============================================================================
# SECCIÓN 2: Parámetros de distribuciones estocásticas
# =============================================================================
MEDIA_FIN_BOLSA = 30.0          # s, tiempo esperado de agotamiento
DESVIO_FIN_BOLSA = 2.0          # s, desviación estándar

MU_CONFIRMACION = 2.5           # parámetro mu de la Log-Normal
SIGMA_LN_CONFIRMACION = 0.8     # parámetro sigma de la Log-Normal
MAX_CONFIRMACIONES = 5          # límite para no ciclar infinito en estocástico

# =============================================================================
# SECCIÓN 3: Escenarios de simulación
# =============================================================================

ESCENARIO_1_NORMAL = {
    "ordenes":      {"eventos": [(0.0, 100.0)]},
    "fin_bolsa":     {"modo": "deterministico", "tiempo_fijo": INFINITY},
    "confirmacion":  {"modo": "deterministico", "tiempos_fijos": [], "max_confirmaciones": 0},
    "actuador":      {"factor_falla": 1.0},
    "sensor":        {"ruido_std": 0.0, "seed": 1},
}

ESCENARIO_2_CAMBIO_ORDEN = {
    "ordenes":      {"eventos": [(0.0, 50.0), (30.0, 80.0)]},
    "fin_bolsa":     {"modo": "deterministico", "tiempo_fijo": INFINITY},
    "confirmacion":  {"modo": "deterministico", "tiempos_fijos": [], "max_confirmaciones": 0},
    "actuador":      {"factor_falla": 1.0},
    "sensor":        {"ruido_std": 0.0, "seed": 1},
}

ESCENARIO_3_ORDEN_CERO = {
    "ordenes":      {"eventos": [(0.0, 100.0), (20.0, 0.0)]},
    "fin_bolsa":     {"modo": "deterministico", "tiempo_fijo": INFINITY},
    "confirmacion":  {"modo": "deterministico", "tiempos_fijos": [], "max_confirmaciones": 0},
    "actuador":      {"factor_falla": 1.0},
    "sensor":        {"ruido_std": 0.0, "seed": 1},
}

ESCENARIO_4_DESVIO_LEVE = {
    "ordenes":      {"eventos": [(0.0, 100.0)]},
    "fin_bolsa":     {"modo": "deterministico", "tiempo_fijo": INFINITY},
    "confirmacion":  {"modo": "deterministico", "tiempos_fijos": [], "max_confirmaciones": 0},
    "actuador":      {"factor_falla": 0.95}, # 5% de desvío
    "sensor":        {"ruido_std": 0.0, "seed": 1},
}

ESCENARIO_5_DESVIO_GRAVE = {
    "ordenes":      {"eventos": [(0.0, 100.0)]},
    "fin_bolsa":     {"modo": "deterministico", "tiempo_fijo": INFINITY},
    "confirmacion":  {"modo": "deterministico", "tiempos_fijos": [], "max_confirmaciones": 0},
    "actuador":      {"factor_falla": 0.85}, # 15% de desvío
    "sensor":        {"ruido_std": 0.0, "seed": 1},
}

ESCENARIO_6_FIN_BOLSA = {
    "ordenes":      {"eventos": [(0.0, 100.0)]},
    "fin_bolsa":     {"modo": "deterministico", "tiempo_fijo": 30.0},
    "confirmacion":  {"modo": "deterministico", "tiempos_fijos": [50.0], "max_confirmaciones": 1},
    "actuador":      {"factor_falla": 1.0},
    "sensor":        {"ruido_std": 0.0, "seed": 1},
}

ESCENARIO_6_FIN_BOLSA_ESTOCASTICO = {
    "ordenes":      {"eventos": [(0.0, 100.0)]},
    "fin_bolsa":     {"modo": "estocastico", "media": MEDIA_FIN_BOLSA, "desvio_std": DESVIO_FIN_BOLSA, "seed": 42},
    "confirmacion":  {"modo": "estocastico", "mu": MU_CONFIRMACION, "sigma_ln": SIGMA_LN_CONFIRMACION, "max_confirmaciones": 1, "seed": 43},
    "actuador":      {"factor_falla": 1.0},
    "sensor":        {"ruido_std": 0.5, "seed": 44},
}

ESCENARIO_7_ALARMA_CRITICA = {
    "ordenes":      {"eventos": [(0.0, 100.0)]},
    "fin_bolsa":     {"modo": "deterministico", "tiempo_fijo": INFINITY},
    "confirmacion":  {"modo": "deterministico", "tiempos_fijos": [], "max_confirmaciones": 0},
    "actuador":      {"factor_falla": 0.85},
    "sensor":        {"ruido_std": 0.0, "seed": 1},
}