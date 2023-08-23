from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from itertools import chain

from agents import Cinta, Estante, EstacionCarga, Celda, Robot, Paquete
import networkx as nx

class Almacen(Model):

    DIR_POSIBLES = [
            [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
            [0, 1, 6, 6, 6, 6, 10, 6, 6, 6, 6, 6, 6, 6, 4, 0],
            [2, 5, 7, 7, 7, 7, 7, 9, 9, 7, 7, 7, 7, 9, 8, 4],
            [2, 5, 8, 0, 0, 0, 0, 5, 8, 0, 0, 0, 0, 5, 8, 4],
            [2, 5, 11, 6, 6, 6, 6, 12, 8, 6, 6, 6, 6, 12, 8, 4],
            [0, 5, 11, 7, 7, 7, 7, 5, 11, 7, 7, 7, 7, 12, 8, 0],
            [2, 12, 8, 0, 0, 0, 0, 5, 8, 0, 0, 0, 0, 5, 11, 4],
            [0, 5, 11, 6, 6, 6, 6, 12, 8, 6, 6, 6, 6, 12, 8, 0],
            [0, 5, 11, 7, 7, 7, 7, 5, 11, 7, 7, 7, 7, 12, 8, 0],
            [2, 12, 8, 0, 0, 0, 0, 5, 8, 0, 0, 0, 0, 5, 11, 4],
            [0, 5, 11, 6, 6, 6, 6, 12, 8, 6, 6, 6, 6, 12, 8, 0],
            [2, 5, 11, 7, 7, 7, 7, 5, 11, 7, 7, 7, 7, 12, 8, 4],
            [2, 5, 8, 0, 0, 0, 0, 5, 8, 0, 0, 0, 0, 5, 8, 4],
            [0, 5, 10, 6, 6, 6, 6, 10, 10, 6, 6, 6, 6, 12, 8, 0],
            [0, 2, 7, 7, 7, 7, 7, 7, 7, 9, 7, 7, 7, 7, 3, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0]
        ]
    
    def __init__(self, M: int, N: int,
                 num_agentes: int = 5,
                 tasa_entrada: int = 10,
                 tasa_salida: int = 30
        ):
    
        self.tasa_entrada = tasa_entrada
        self.tasa_saluda = tasa_salida
        self.cont_entrada = tasa_entrada
        self.cont_salida = tasa_salida

        self.num_agentes = num_agentes
        self.num_paquetes = 0

        self.solicitudes = []


        self.graph = self.creaGrafo()
        self.grid = MultiGrid(M, N,False)
        self.schedule = RandomActivation(self)

        #posiciones disponibles del grid
        posiciones_disponibles = [pos for _, pos in self.grid.coord_iter()]

        #posiciones para las cintas
        celdas_cinta = [(i, 15) for i in range(9)] + [(i, 0) for i in range(7, 16)] 
        self.celdas_cinta = celdas_cinta
        for id, pos in enumerate(celdas_cinta):
            cinta = Cinta(int(f"{num_agentes}0{id}") + 1, self)
            self.grid.place_agent(cinta, pos)
            posiciones_disponibles.remove(pos)
        

        #posiciones para los estantes
        celdas_estantes = [(i, j) for i in chain(range(3, 7), range(9, 13)) for j in range(3, 13, 3)]
        for id, pos in enumerate(celdas_estantes):
            estante = Estante(int(f"{num_agentes}1{id}") + 1, self)
            self.grid.place_agent(estante, pos)
            posiciones_disponibles.remove(pos)

        #posiciones para las estaciones de carga
        celdas_cargas = [(0, 6), (0, 9), (15, 6), (15, 9)]
        for id, pos in enumerate(celdas_cargas):
            estacion = EstacionCarga(int(f"{num_agentes}2{id}") + 1, self)
            self.grid.place_agent(estacion, pos)
            posiciones_disponibles.remove(pos)

        #posiciones de las celdas
        for id, pos in enumerate(posiciones_disponibles):
            celda = Celda(int(f"{num_agentes}{id}") + 1, self)
            dirs = self.DIR_POSIBLES[pos[1]][pos[0]]
            if dirs == 1:
                celda.directions = ["up"]
            elif dirs == 2:
                celda.directions = ["right"]
            elif dirs == 3:
                celda.directions = ["down"]
            elif dirs == 4:
                celda.directions = ["left"]
            elif dirs == 5:
                celda.directions = ["right", "up"]
            elif dirs == 6:
                celda.directions = ["left", "up"]
            elif dirs == 7:
                celda.directions = ["right", "down"]
            elif dirs == 8:
                celda.directions = ["left", "down"]
            elif dirs == 9:
                celda.directions = ["right", "down", "up"]
            elif dirs == 10:
                celda.directions = ["left", "down", "up"]
            elif dirs == 11:
                celda.directions = ["left", "right", "down"]
            elif dirs == 12:
                celda.directions = ["left", "right", "up"]
            elif dirs == 13:
                celda.directions = ["left", "right", "up", "down"]
            self.grid.place_agent(celda, pos)
            
        #posiciones de los robots
        pos_robots = [(0, 2), (15, 2), (0, 3), (15, 3), (0, 4), (15, 4), (0, 11), (15, 11), (0, 12), (15, 12)]
        pos_robots = pos_robots[:num_agentes]
        for id, pos in enumerate(pos_robots):
            robot = Robot(int(f"{num_agentes}3{id}") + 1, self)
            self.grid.place_agent(robot, pos)
            self.schedule.add(robot)

      

        #self.solicitudes = []

        #self.datacollector = DataCollector(
        #    model_reporters={"Grid": get_grid, "Cargas": get_cargas,
        #                     "CeldasSucias": get_sucias,
        #                     "Tiempo": "tiempo",
        #                     "Movimiento": "movimiento",
        #                     "Carga": "cantidadCarga"})
        

    def step(self):
        self.cont_entrada -= 1
        if self.cont_entrada == 0:
            self.instantiatePackage()
            self.cont_entrada = self.tasa_entrada

        #self.datacollector.collect(self)
        self.schedule.step()
        self.realizarSolicitudes()
        
        #if not self.todoLimpio():
        #    sucias = self.celdasSucias()
        #    sucias_sel = self.random.sample(sucias, k=min(len(sucias), self.num_agentes))
        #    for celda in sucias_sel:
        #        self.pedirAyuda(celda, 1)   

        #    self.realizarSolicitudes()
         #   self.tiempo += 1

    def instantiatePackage(self):
        #crear paquete si la cinta no está llena
        should_create = True
        contents = self.grid.get_cell_list_contents((15, 0))
        for content in contents:
            if isinstance(content, Paquete):
                should_create = False
        #crear paquete
        if should_create:
            paquete = Paquete(int(f"{self.num_agentes}4{self.num_paquetes}")+1, self)
            self.num_paquetes += 1
            self.grid.place_agent(paquete, (15, 0))
            self.schedule.add(paquete)
        #crear solicitud a los robots para recoger el paquete
        solicitud = {
            "priority": 5,
            "position": (6, 0),
            "action": "RETRIEVE"
        }
        self.pedirAyuda(solicitud)


    #calcula distancia entre 2 puntos
    def distancia_manhattan(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    #crea una solicitud de ayuda
    def pedirAyuda(self, solicitud):
        self.solicitudes.append(solicitud)

    #realiza cada una de las solicitudes a los robots
    def realizarSolicitudes(self):
        self.solicitudes = sorted(self.solicitudes, key=lambda solicitud: solicitud["priority"], reverse = True)
        agentes = self.getAgentes()

        for solicitud in self.solicitudes:
            agentes = sorted(agentes, key=lambda agente: self.distancia_manhattan(solicitud["position"], agente[1]))
            for agente in agentes:
                result = agente[0].procesar_solicitud(solicitud)
                if result:
                    break
                
        self.solicitudes = []

    #obtiene los robots de limpieza del grid
    def getAgentes(self):
        agentes = []
        for (content, pos) in self.grid.coord_iter():
            for obj in content:
                if isinstance(obj, Robot):
                    agentes.append((obj, pos))
        return agentes
    
    #creamos grafo del almacen
    def creaGrafo(self):
        G = nx.DiGraph()
        for i in range(16):
            for j in range(16):
                dirs = self.DIR_POSIBLES[i][j]
                if dirs == 1:
                    G.add_edge((j, i), (j, i+1))
                elif dirs == 2:
                    G.add_edge((j, i), (j+1, i))
                elif dirs == 3:
                    G.add_edge((j, i), (j, i-1))
                elif dirs == 4:
                    G.add_edge((j, i), (j-1, i))
                elif dirs == 5:
                    G.add_edge((j, i), (j+1, i))
                    G.add_edge((j, i), (j, i+1))
                elif dirs == 6:
                    G.add_edge((j, i), (j-1, i))
                    G.add_edge((j, i), (j, i+1))
                elif dirs == 7:
                    G.add_edge((j, i), (j+1, i))
                    G.add_edge((j, i), (j, i-1))
                elif dirs == 8:
                    G.add_edge((j, i), (j-1, i))
                    G.add_edge((j, i), (j, i-1))
                elif dirs == 9:
                    G.add_edge((j, i), (j+1, i))
                    G.add_edge((j, i), (j, i-1))
                    G.add_edge((j, i), (j, i+1))
                elif dirs == 10:
                    G.add_edge((j, i), (j-1, i))
                    G.add_edge((j, i), (j, i-1))
                    G.add_edge((j, i), (j, i+1))
                elif dirs == 11:
                    G.add_edge((j, i), (j-1, i))
                    G.add_edge((j, i), (j+1, i))
                    G.add_edge((j, i), (j, i-1))
                elif dirs == 12:
                    G.add_edge((j, i), (j-1, i))
                    G.add_edge((j, i), (j+1, i))
                    G.add_edge((j, i), (j, i+1))
                elif dirs == 13:
                    G.add_edge((j, i), (j-1, i))
                    G.add_edge((j, i), (j+1, i))
                    G.add_edge((j, i), (j, i+1))
                    G.add_edge((j, i), (j, i-1))
        print(G.edges)
        nx.set_edge_attributes(G, {e: 1 for e in G.edges()}, "cost")
        return G

    '''
    #determina si todas las celdas estan limpias
    def todoLimpio(self):
        for (content, pos) in self.grid.coord_iter():
            for obj in content:
                if isinstance(obj, Celda) and obj.sucia:
                    return False
        return True 
    
    #determinar las celdas sucias
    def celdasSucias(self):
        celdas_sucias = []
        for(content, pos) in self.grid.coord_iter():
            for obj in content:
                if isinstance(obj, Celda) and obj.sucia:
                    celdas_sucias.append(pos)
        return celdas_sucias
    
    #obtiene los robots de limpieza del grid
    def getAgentes(self):
        agentes = []
        for (content, pos) in self.grid.coord_iter():
            for obj in content:
                if isinstance(obj, RobotLimpieza):
                    agentes.append((obj, pos))
        return agentes

    #obtiene las estaciones de carga del grid
    def getEstaciones(self):
        estaciones = []
        for (content, pos) in self.grid.coord_iter():
            for obj in content:
                if isinstance(obj, EstacionCarga):
                    estaciones.append(pos)
        return estaciones


def get_grid(model: Model) -> np.ndarray:
    """
    Método para la obtención de la grid y representarla en un notebook
    :param model: Modelo (entorno)
    :return: grid
    """
    grid = np.zeros((model.grid.width, model.grid.height))
    for cell in model.grid.coord_iter():
        cell_content, pos = cell
        x, y = pos
        for obj in cell_content:
            if isinstance(obj, RobotLimpieza):
                grid[x][y] = 2
            elif isinstance(obj, Celda):
                grid[x][y] = int(obj.sucia)
    return grid


def get_cargas(model: Model):
    return [(agent.unique_id, agent.carga) for agent in model.schedule.agents]


def get_sucias(model: Model) -> int:
    """
    Método para determinar el número total de celdas sucias
    :param model: Modelo Mesa
    :return: número de celdas sucias
    """
    sum_sucias = 0
    for cell in model.grid.coord_iter():
        cell_content, pos = cell
        for obj in cell_content:
            if isinstance(obj, Celda) and obj.sucia:
                sum_sucias += 1
    return sum_sucias / model.num_celdas_sucias


def get_movimientos(agent: Agent) -> dict:
    if isinstance(agent, RobotLimpieza):
        return {agent.unique_id: agent.movimientos}
    # else:
    #    return 0
'''