# Controlador Simplificado de Bomba de Infusión

Este proyecto utiliza la herramienta **PythonPDEVS** para la simulación de eventos discretos. A continuación, se detallan los pasos necesarios para configurar el entorno virtual de Python e instalar las dependencias con sus versiones exactas en entornos Linux.

## 🚀 Requisitos Previos

* **Python 3.12** o superior

---

## 🛠️ Guía de Instalación y Configuración

Siga estos pasos en la terminal desde la raíz del proyecto para crear un entorno aislado y ejecutar la simulación:

### 1. Clonar el repositorio (si aún no lo ha hecho)
```bash
git clone https://github.com/Jhonatan-calle/Controlador-Simplificado-de-Bomba-de-Infusi-n.git
cd Controlador-Simplificado-de-Bomba-de-Infusi-n
```

### 2. Crear el entorno virtual
Cree un entorno virtual de Python para evitar conflictos con librerías globales:
```bash
python3 -m venv venv
```

### 3. Activar el entorno virtual
Active el entorno en su sesión de terminal actual:
```bash
source venv/bin/activate
```
*(Notará el prefijo `(venv)` al inicio de su línea de comandos).*

### 4. Instalar las dependencias
Instale `setuptools` (requerido para la compatibilidad del instalador de PyDEVS con Python moderno) junto con el módulo local de la herramienta de forma automática:
```bash
pip install -r requirements.txt
```

---

## 🧪 Ejecución de la Simulación

Una vez que el entorno esté configurado y activo, puede ejecutar el script principal del controlador de la bomba de infusión mediante el siguiente comando:

```bash
python3 main.py
```

## 🛑 Desactivar el Entorno

Cuando finalice la revisión del proyecto, puede salir del entorno virtual ejecutando simplemente:
```bash
deactivate
```
