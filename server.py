import mesa
from model import Almacen
from agents import Cinta, Estante, EstacionCarga, Robot, Paquete

# Aqui simulamos la grafico del funcionamiento de los robots
# NOTA: No es la solucion final solo nos sirve para ver como se comporta el modelo multiagente 
MAX_NUMBER_ROBOTS = 10


def agent_portrayal(agent):
    if isinstance(agent, Cinta):
        return {"Shape": "rect", "Filled": "true", "Color": "gray", "Layer": 0, "w": 0.9, "h": 0.9}
    elif isinstance(agent, Estante):
        return {"Shape": "rect", "Filled": "true", "Color": "maroon", "Layer": 0, "w": 0.9, "h": 0.9}
    elif isinstance(agent, EstacionCarga):
        return {"Shape": "rect", "Filled": "true", "Color": "yellow", "Layer": 0, "w": 0.9, "h": 0.9}
    elif isinstance(agent, Robot):
        return {"Shape": "circle", "Filled": "true", "Color": "blue", "Layer": 1, "r": 0.9, "text": f"{agent.action}", "text_color": "white"}
    elif isinstance(agent, Paquete):
        return {"Shape": "rect", "Filled": "true", "Color": "green", "Layer": 2, "w": 0.5, "h": 0.5, "text": f"{agent.peso}", "text_color": "white"}


grid = mesa.visualization.CanvasGrid(
    agent_portrayal, 16, 16, 400, 400)

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
    "almacenRobots", model_params, 8521
)
