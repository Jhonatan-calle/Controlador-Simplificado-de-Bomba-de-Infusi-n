# Simulación de Sistema de Tiempo Real: Bomba de Infusión Intravenosa

Este repositorio contiene el desarrollo, modelado y simulación de un sistema automático de administración de medicación intravenosa. El proyecto se enfoca en un **controlador simplificado** que gestiona dosis, sensores de flujo y alarmas críticas, asegurando que las acciones de control cumplan con estrictos requisitos temporales.

## 👥 Colaboradores
*   **Jhoantan Calle**
*   **Hernan Jara**

## 🚀 Descripción del Proyecto
El objetivo es construir un modelo de **simulación de eventos discretos** que represente el comportamiento de una bomba de infusión. El sistema recibe órdenes médicas (caudal objetivo), monitorea el caudal real mediante un sensor y reacciona ante desviaciones o el agotamiento de la bolsa de medicación.

### Requisitos Temporales Clave:
*   **Inicio de infusión:** Menos de 3 segundos tras la orden médica.
*   **Monitoreo:** Muestreo del sensor cada 1 segundo.
*   **Alarma Media:** Activada si el desvío es > 10% durante más de 5 segundos.
*   **Seguridad:** Detención automática a los 60 segundos de detectar "Fin de Bolsa".

## 🛠️ Especificación Formal (DEVS)
El sistema ha sido modelado utilizando el formalismo **DEVS** (Discrete Event System Specification).

### Modelos Atómicos:
1.  **Generador de órdenes:** Emite el caudal objetivo (0-200 ml/h).
2.  **Sensor de flujo:** Mide periódicamente el caudal real.
3.  **Controlador de bomba:** Cerebro del sistema; toma decisiones de ajuste y alarmas.
4.  **Actuador de la bomba:** Mecanismo físico que aplica el ajuste (latencia < 0.5s).
5.  **Módulo de alarmas:** Gestiona notificaciones visuales/sonoras y repeticiones.

### Notación Utilizada
Para la descripción abstracta se utilizó la sintaxis **CML-DEVS** (Conceptual Modeling Language for DEVS), permitiendo una definición matemática y lógica independiente de la plataforma.

## 💻 Implementación y Herramientas
*   **Software de Simulación:** [PowerDEVS](http://sourceforge.net/projects/powerdevs/) (u otra herramienta utilizada).
*   **Lenguaje de Especificación:** CML-DEVS.
*   **Análisis de Datos:** Registro de trazas de simulación para verificar propiedades de seguridad (*safety*) y vivacidad (*liveness*).

## 📊 Escenarios de Simulación
El repositorio incluye la configuración para testear:
*   Funcionamiento normal y cambios de dosis en tiempo real.
*   Escenarios de falla (desvío de caudal > 10% y alarma crítica).
*   Agotamiento de bolsa y confirmación manual de enfermero.

