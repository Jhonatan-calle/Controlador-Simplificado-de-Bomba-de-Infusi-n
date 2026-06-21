# Simulador DEVS de Bomba de Infusión Intravenosa

Simulador de eventos discretos basado en el formalismo **DEVS** (Discrete Event System Specification) que modela el control y monitoreo de una bomba de infusión intravenosa. Utiliza **PythonPDEVS** como motor de simulación.

## Requisitos

- **Python 3.12+** (probado en Python 3.14)
- **pip** y **venv** (incluidos en la instalación estándar de Python)
- **Git** (para clonar el repositorio)

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/Jhonatan-calle/Controlador-Simplificado-de-Bomba-de-Infusi-n.git proyecto
cd proyecto

# 2. Crear y activar el entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

## Estructura del proyecto

```
proyecto/
├── main.py                          # Punto de entrada
├── config.py                        # Constantes y configuración de escenarios
├── requirements.txt                 # Dependencias
├── README.md
├── modelos/
│   ├── controlador_bomba.py         # Lógica central del controlador
│   ├── actuador_bomba.py            # Interfaz física con latencia 0.5s
│   ├── sensor_flujo.py              # Muestreo cada 1s con deriva y ruido
│   ├── modulo_alarmas.py            # Gestión y repetición de alarmas
│   ├── generador_ordenes.py         # Generación autónoma de órdenes
│   ├── generador_fin_bolsa.py       # Evento de fin de bolsa (one-shot)
│   └── generador_confirmacion.py    # Confirmación del enfermero
├── sistema/
│   └── sistema_bomba.py             # Modelo acoplado (CoupledDEVS)
├── logger/
│   └── event_logger.py              # Captura de eventos de simulación
├── verificacion/
│   └── verificador_propiedades.py   # 10 verificaciones (P1-P10)
├── graficos/
│   └── graficar_resultados.py       # Generación de gráficos (matplotlib)
├── tests/
│   ├── conftest.py                  # Fixtures de pytest
│   ├── test_confirmacion.py
│   ├── test_fin_bolsa.py
│   ├── test_integracion.py
│   └── test_modulo_alarmas.py
├── graficos/                        # PNGs generados (output)
└── PythonPDEVS/src/pypdevs/         # Motor de simulación (dependencia local)
```

## Uso

### Ejecución básica

```bash
# Escenario por defecto (operación normal, 100s)
python main.py

# Escenario específico
python main.py --escenario 5
```

### Escenarios disponibles

| #  | Nombre                         | Descripción                                |
|----|--------------------------------|--------------------------------------------|
| 1  | Operación normal               | Órdenes determinísticas, sin fallas        |
| 2  | Cambio de orden médica         | Órdenes estocásticas con cambios           |
| 3  | Orden con caudal = 0           | Detención programada                       |
| 4  | Desvío leve (< 5 s)            | Desvío corregido antes de la alarma        |
| 5  | Desvío grave (> 5 s)           | Desvío persistente → alarma crítica        |
| 6  | Fin de bolsa (determinístico)  | Fin de bolsa en tiempo fijo                |
| 7  | Alarma crítica sin confirmación| Alarma crítica que se repite cada 10s      |
| 8  | Fin de bolsa (estocástico)     | Fin de bolsa con tiempo aleatorio          |
| 9  | Violación deliberada           | Desvío grave ignorando alarma crítica      |

### Flags

```bash
# Verificar propiedades de seguridad y liveness
python main.py --escenario 5 --verificar

# Mostrar eventos en tiempo real
python main.py --escenario 5 --verbose

# Generar gráficos (PNG en graficos/)
python main.py --escenario 5 --graficos

# Combinar flags
python main.py --escenario 5 --verificar --graficos

# Duración personalizada
python main.py --tiempo 200
```

### Verificaciones (P1-P10)

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| P1 | Safety | Caudal cero: última orden no debe ser caudal cero |
| P2 | Safety | Caudal máximo: ningún caudal supera 200 ml/h |
| P3 | Safety | Crítica sin confirmación: no hay ajustes tras crítica |
| P4 | Liveness | Orden produce acción: toda orden > 0 genera un ajuste |
| P5 | Liveness | Crítica se repite: críticas sin confirmación se retransmiten |
| P6 | Liveness | Fin de bolsa detiene: fin de bolsa seguido de detención |
| P7 | Temporal | Inicio de infusión: ajuste < 3s tras la orden |
| P8 | Temporal | Alarma media en 5s: tiempo correcto de alarma por desvío |
| P9 | Temporal | Fin de bolsa 60s: detención dentro del tiempo límite |
| P10 | Temporal | Crítica repite cada 10s: período correcto de retransmisión |

## Arquitectura

### Modelo acoplado

```
GeneradorOrdenes ──ordenMedica──→ ControladorBomba ──ajustarCaudal──→ ActuadorBomba
                                      ↑                               │
                                      │                          caudalActual
                                      │                               ↓
GeneradorFinBolsa ──finBolsa──────→ ControladorBomba ←─sensorFlujo── SensorFlujo
                                      │
GeneradorConfirmacion ──confirmacion→ ControladorBomba
                                      │
                                      └──alarma──→ ModuloAlarmas
```

### Componentes

- **ControladorBomba**: Cerebro del sistema. Gestiona estados (`OCIOSO`, `INFUNDIENDO`, `ALARMA_MEDIA`, `ALARMA_CRITICA`, `PARADA_POR_BOLSA`) y temporizadores de desvío (5s) y fin de bolsa (60s).
- **ActuadorBomba**: Interfaz física con latencia de 0.5s y factor de falla configurable.
- **SensorFlujo**: Muestrea cada 1s con deriva (2%/s) y ruido gaussiano opcional.
- **ModuloAlarmas**: Repite alarmas críticas no confirmadas (30s luego 10s).
- **Generadores**: Autónomos, sin entradas. Emiten órdenes, fin de bolsa, y confirmaciones.

## Desactivar entorno

```bash
deactivate
```
