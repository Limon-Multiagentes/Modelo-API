import mesa

from model import Almacen
from agents import Cinta, Estante, EstacionCarga, Robot, Paquete

MAX_NUMBER_ROBOTS = 10


def agent_portrayal(agent):
    if isinstance(agent, Cinta):
        return {"Shape": "rect", "Filled": "true", "Color": "gray", "Layer": 0, "w": 0.9, "h": 0.9}
    elif isinstance(agent, Estante):
        return {"Shape": "rect", "Filled": "true", "Color": "maroon", "Layer": 0, "w": 0.9, "h": 0.9}
    elif isinstance(agent, EstacionCarga):
        return {"Shape": "rect", "Filled": "true", "Color": "yellow", "Layer": 0, "w": 0.9, "h": 0.9}
    elif isinstance(agent, Robot):
        return {"Shape": "circle", "Filled": "true", "Color": "blue", "Layer": 1, "r": 0.8}
    elif isinstance(agent, Paquete):
        return {"Shape": "rect", "Filled": "true", "Color": "green", "Layer": 1, "w": 0.7, "h": 0.7}


grid = mesa.visualization.CanvasGrid(
    agent_portrayal, 16, 16, 400, 400)

"""
chart_celdas = mesa.visualization.ChartModule(
    [{"Label": "CeldasSucias", "Color": '#36A2EB', "label": "Celdas Sucias"}],
    50, 200,
    data_collector_name="datacollector"
)
chart_carga = mesa.visualization.ChartModule(
    [{"Label": "Carga", "Color": '#8D6BD5', "label": "Carga"}],
    50, 200,
    data_collector_name="datacollector"
)
chart_tiempo = mesa.visualization.ChartModule(
    [{"Label": "Tiempo", "Color": '#34BA89', "label": "Tiempo"}],
    50, 200,
    data_collector_name="datacollector"
)
chart_movimientos = mesa.visualization.ChartModule(
    [{"Label": "Movimiento", "Color": '#F59F3D', "label": "Movimiento"}],
    50, 200,
    data_collector_name="datacollector"
)
"""

model_params = {
    "num_agentes": mesa.visualization.Slider(
        "Número de Robots",
        1,
        1,
        MAX_NUMBER_ROBOTS,
        1,
        description="Escoge cuántos robots deseas implementar en el modelo",
    ),
    'M': 16,
    'N': 16

}



server = mesa.visualization.ModularServer(
    Almacen, [grid],
    "botCleaner", model_params, 8521
)
