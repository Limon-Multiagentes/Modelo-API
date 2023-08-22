from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from itertools import chain

from agents import Cinta, Estante, EstacionCarga, Celda, Robot

class Almacen(Model):
    def __init__(self, M: int, N: int,
                 num_agentes: int = 5,
                 tasa_entrada: int = 0.2,
                 tasa_salida: int = 0.1
        ):
    
        self.num_agentes = num_agentes
        self.grid = MultiGrid(M, N,False)
        self.schedule = RandomActivation(self)

        #posiciones disponibles del grid
        posiciones_disponibles = [pos for _, pos in self.grid.coord_iter()]

        #posiciones para las cintas
        celdas_cinta = [(i, 0) for i in range(9)] + [(i, 15) for i in range(7, 16)] 
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
            self.grid.place_agent(celda, pos)
            
        #posiciones de los robots
        pos_robots = [(0, 2), (15, 2), (0, 3), (15, 3), (0, 4), (15, 4), (0, 11), (15, 11), (0, 12), (15, 12)]
        for id, pos in enumerate(pos_robots):
            robot = Robot(int(f"{num_agentes}3{id}") + 1, self)
            self.grid.place_agent(robot, pos)



        
        '''

        self.solicitudes = []

        # Posicionamiento de agentes robot
        if modo_pos_inicial == 'Aleatoria':
            pos_inicial_robots = self.random.sample(posiciones_disponibles, k=num_agentes)
        else:  # 'Fija'
            pos_inicial_robots = [(1, 1)] * num_agentes

        for id in range(num_agentes):
            robot = RobotLimpieza(id, self)
            self.grid.place_agent(robot, pos_inicial_robots[id])
            self.schedule.add(robot)

        self.datacollector = DataCollector(
            model_reporters={"Grid": get_grid, "Cargas": get_cargas,
                             "CeldasSucias": get_sucias,
                             "Tiempo": "tiempo",
                             "Movimiento": "movimiento",
                             "Carga": "cantidadCarga"})
        

    def step(self):
        self.datacollector.collect(self)
        
        if not self.todoLimpio():
            self.schedule.step()

            sucias = self.celdasSucias()
            sucias_sel = self.random.sample(sucias, k=min(len(sucias), self.num_agentes))
            for celda in sucias_sel:
                self.pedirAyuda(celda, 1)   

            self.realizarSolicitudes()
            self.tiempo += 1


    #calcula distancia entre dos puntos
    def distancia_euclidiana(self, pos1, pos2):
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

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
    
    #crea una solicitud de ayuda
    def pedirAyuda(self, pos, num_sucias):
        self.solicitudes.append((num_sucias, pos))

    #realiza cada una de las solicitudes a los robots
    def realizarSolicitudes(self):
        self.solicitudes = sorted(self.solicitudes, key=lambda solicitud: solicitud[0], reverse = True)
        agentes = self.getAgentes()

        for solicitud in self.solicitudes:
            agentes = sorted(agentes, key=lambda agente: self.distancia_euclidiana(solicitud[1], agente[1]))
            for agente in agentes:
                result = agente[0].procesar_solicitud(solicitud[1])
                if result:
                    break
                
        self.solicitudes = []


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