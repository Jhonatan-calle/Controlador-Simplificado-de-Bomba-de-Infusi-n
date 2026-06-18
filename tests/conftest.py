# tests/conftest.py
import pytest
import sys
import os

# Asegurar que pytest encuentre tus módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import ESCENARIO_1_NORMAL, ESCENARIO_6_FIN_BOLSA

@pytest.fixture
def config_normal():
    return ESCENARIO_1_NORMAL

@pytest.fixture
def config_fin_bolsa():
    return ESCENARIO_6_FIN_BOLSA

# Fixture avanzado que pide tu .md: corre la simulación y devuelve el logger
@pytest.fixture
def run_simulation():
    def _run(config_escenario, tiempo_fin=100.0):
        from sistema.sistema_bomba import SistemaBomba
        from pypdevs.simulator import Simulator
        
        modelo = SistemaBomba("SistemaTest", config_escenario)
        sim = Simulator(modelo)
        sim.setClassicDEVS()
        sim.setTerminationTime(tiempo_fin)
        sim.simulate()
        
        # Asumiendo que tenés una forma de obtener la traza de tu logger
        # return logger.get_eventos() 
        pass
    return _run
