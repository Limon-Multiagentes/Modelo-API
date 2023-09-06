# Importacion de librerias a utilizat
from mesa.model import Model
from mesa.agent import Agent
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import networkx as nx
import copy
import random

# Aqui declaramos la celda y que direcciones puede tener
class Celda(Agent):
    DIRECTIONS = ['right', 'down', 'left', 'up']

    def __init__(self, unique_id, model, directions=[]):
        super().__init__(unique_id, model)
        self.directions = directions
        
# Clase estante donde se guardar las cajas
class Estante(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

# Clase estacion de carga en esta estacion es donde se carga la pila de los robots
class EstacionCarga(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

# Definimos una clase paquete que nos va a indicar que peso tiene el paquete y paquetes_recibidos nos sirve para conocer la cantidad de paquetes recibidos y mostrarlos de forma grafica  
class Paquete(Agent):
    def __init__(self, unique_id, model, peso):
        super().__init__(unique_id, model)
        self.peso = peso
        self.surface = "Cinta" #superficie en que esta el paquete, usada por Unity
        self.model.paquetes_recibidos += 1
        self.robotId = None
    
    def step(self):
        if(self.pos in self.model.celdas_cinta): #si esta sobre una cinta

            self.sig_pos = (self.pos[0]-1, self.pos[1]) #la siguiente posicion 

            if self.sig_pos[0] < 0: #si sale de la escena eliminar el paquete
                self.model.paquetes_enviados += 1
                self.model.grid.remove_agent(self)
                self.model.schedulePaquetes.remove(self)

            should_move = True

            #condiciones para no moverse
            #si hay un paquete en la siguiente celda no moverse
            contents = self.model.grid.get_cell_list_contents(self.sig_pos) 
            for content in contents:
                if isinstance(content, Paquete):
                    should_move = False

            #si no se debe mover retornar
            if not should_move:
                self.sig_pos = self.pos
                return

            if self.sig_pos not in self.model.celdas_cinta: #si deja la cinta si no hay un robot esperando en la siguiente celda no moverse
                contents = self.model.grid.get_cell_list_contents(self.sig_pos)
                is_robot_waiting = False
                for content in contents:
                    if isinstance(content, Robot):
                        is_robot_waiting = True
                if not is_robot_waiting:
                    should_move = False
                else: # actualizar la superficie si se debe mover
                    self.surface = "Robot" 

            if should_move: #si se puede mover actualizar la posicion
                self.model.grid.move_agent(self, self.sig_pos)
            else:
                self.sig_pos = self.pos
        else: #si no esta sobre una cinta se puede mover si su posicion cambia
            if self.sig_pos != self.pos:

                #revisar el contenido de la siguiente celda para actualizar la superificie
                contents = self.model.grid.get_cell_list_contents(self.sig_pos)
                for content in contents:
                    if isinstance(content, Robot):
                        self.surface = "Robot"
                    elif isinstance(content, Estante):
                        self.surface = "Estante"
                        break
                    elif isinstance(content, Cinta):
                        self.surface = "Cinta"
                        self.robotId = None

                self.model.grid.move_agent(self, self.sig_pos)


# Aqui definimos la clase cinta
class Cinta(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

# Aqui definimos la clase Robot
class Robot(Agent):    
    #Aqui son los posibles movimientos que puede hacer los robots
    dirMovs = {
        "right": (1, 0),
        "left": (-1, 0),
        "down": (0, -1),
        "up": (0, 1), 
    }

    actions = {
        "RETRIEVE": 7,
        "CHARGE": 6,
        "STORE": 5,
        "SEND": 4,
        "PICKUP": 3,
        "WANDER": 2,
        "HALT": 1
    }

    # Constructor de la clase Robor le entregamos su siguiente posicion que peso lleva, su carga de bateria, que objetivo tiene, que accion lleva es decir si va divagando o tiene algo fijo , camino recorrido y grafo actualizado
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.sig_pos = None
        self.peso_carga = 0
        self.carga = 100
        self.solicitud = None #solcitud a procesar
        self.target = None
        self.action = "HALT" # El robot no se mueve al incio
        self.cont_wander = 0 #Cuantos steps estará en wander
        self.path = []
        self.updated_graph = False
        self.isFast = False #el robot va rapido o lento

    #busca_celdas_disponibles
    def busca_celdas_disponibles(self, incluir, inicio, remove_agents=True):
        celdas = []
        directions = []
        #Obtener las direcciones a las que se puede mover desde la celda actual
        contents = self.model.grid.get_cell_list_contents(inicio)
        for content in contents:
            if isinstance(content, Celda):
                directions = content.directions
        #Agregar los elementos de las celdas adyacentes a las que se puede mover
        for dir in directions:
            newPosition = (self.pos[0] + self.dirMovs[dir][0], self.pos[1] + self.dirMovs[dir][1]) 
            contents = self.model.grid.get_cell_list_contents(newPosition)
            for content in contents:
                if isinstance(content, incluir):
                    celdas.append(content)
        #Remover las que tienen robots en el sitio
        disponibles = []
        if remove_agents:
            for celda in celdas:
                cell_contents = self.model.grid.get_cell_list_contents(celda.pos)
                agents = [agent for agent in cell_contents if isinstance(agent, (Robot, Estante, EstacionCarga))]
                if not agents:
                    disponibles.append(celda)
        else:
            disponibles = celdas
        return disponibles
    
     #selecciona nueva posición a avanzar
    def seleccionar_nueva_pos(self):
        celdas = self.busca_celdas_disponibles((Celda), self.pos)
        #si no hay celdas disponibles se queda en la misma posicion
        if(len(celdas) == 0):
          self.sig_pos = self.pos
          return
        #seleccionar una de las celdas disponibles
        self.sig_pos = self.random.choice(celdas).pos

        if self.action == "WANDER":
            #disminuye la cantidad de steps en wander
            self.cont_wander -=1
            #se pide al robot esperar si el contador llega a 0
            if(self.cont_wander == 0): 
                self.action = "HALT" #detenerse
            #no va a velocidad doble
        self.isFast = False


    #avanza hacia un objetivo
    def ve_a_objetivo(self):      
        #actualizar el grafo con los caminos adicionales correspondientes y buscar el camino

        if self.action in ["RETRIEVE", "STORE", "CHARGE", "PICKUP", "SEND"]:
            if not self.updated_graph:
                self.graph = self.actualizar_grafo(self.model.graph, self.target, self.action)
            try:
                graph = self.elimina_obstaculos(self.graph, self.pos, self.action)
                if self.sig_pos != self.pos: #si debe apartarse retornar
                    return
                self.path = nx.astar_path(graph, self.pos, self.target, heuristic=self.distancia_manhattan, weight="cost")
            except Exception as e:
                self.sig_pos = self.pos
                return
        else:
            try:
                graph = self.elimina_obstaculos(self.model.graph, self.pos, self.action)
                if self.sig_pos != self.pos: #si debe apartarse retornar
                    return
                self.path = nx.astar_path(graph, self.pos, self.target, heuristic=self.distancia_manhattan, weight="cost")
            except:
                self.sig_pos = self.pos
                return

        #eliminar la primera celda del camino, dado que es la celda actual
        self.path.pop(0)

        #si no hay celdas disponibles se queda en la misma posicion
        if(len(self.path) == 0):
          self.sig_pos = self.pos
          return

        avanza = self.num_avanzar(self.pos, self.path)
        # Aqui checamos la posicion del robot para ver si puedes avanzar 2 celdas
        if(avanza == 1):
            self.sig_pos = self.path[0]
            self.path.pop(0)
            self.isFast = False
        else:
            self.sig_pos = self.path[1]
            self.path.pop(0)
            self.path.pop(0)
            self.isFast = True
        
               
    #regresa si hay un robot en una celda
    def robotInCell(self,celda):
        cell_contents = self.model.grid.get_cell_list_contents(celda)
        agents = [agent for agent in cell_contents if isinstance(agent, Robot)]
        return len(agents)>0
        
    #regresa la cantidad de celdas que el robot puede avanzar
    def num_avanzar(self, pos, path):
        if len(path) < 2: #si el camino no tiene al menos 2 celdas solo se desplaza una
            return 1
        
        #analizamos la celda actual y las dos siguientes
        #si no comparten fila ni comparten columna se desplaza una sola celda
        coincide_x = pos[0] == path[0][0] and path[0][0] == path[1][0]
        coincide_y = pos[1] == path[0][1] and path[0][1] == path[1][1]

        if not (coincide_x or coincide_y):
            return 1
        
        if(self.robotInCell(path[1])): #si hay un robot en la segunda celda se desplaza una
            return 1
        
        #si hay robots en las celdas a los laterales de la primera celda, solo se puede desplazar una
        if coincide_y:
            if path[0][1] == 0:
                if self.robotInCell((path[0][0], path[0][1]+1)): #si estamos en la primera linea solo checar la superior
                    return 1
            elif path[0][1] == 15:
                if self.robotInCell((path[0][0], path[0][1]-1)): #si estamos en la ultima linea solo checar la inferior
                    return 1
            else:
                if self.robotInCell((path[0][0], path[0][1]+1)) or self.robotInCell((path[0][0], path[0][1]-1)): #si no checar a ambos lados
                    return 1
        if coincide_x:
            if path[0][0] == 0:
                if self.robotInCell((path[0][0]+1, path[0][1])): #si estamos en la primera columna solo checar a la derecha
                    return 1
            elif path[0][0] == 15: 
                if self.robotInCell((path[0][0]-1, path[0][1])): #si estamos en la ultima columna solo checar a la izquierda
                    return 1
            else:
                if (self.robotInCell((path[0][0]+1, path[0][1])) or self.robotInCell((path[0][0]-1, path[0][1]))): #si no checar a ambos lados
                    return 1
            
        return 2    #si no se desplaza 2
    
    #actualiza grafo para acceder a estaciones de carga
    def actualizar_grafo(self, graph, target, action):
        G = copy.deepcopy(graph)
        if action in ["STORE", "PICKUP"]:
            G.add_edge((target[0], target[1]-1), target)
            G.add_edge((target[0], target[1]+1), target)
        elif action == "RETRIEVE":
            G.add_edge((target[0], target[1]+1), target)
        elif action == "SEND":
            G.add_edge((target[0], target[1]-1), target)
        else:
            if target[0] == 0:
                G.add_edge((target[0]+1, target[1]), target)
            else:
                G.add_edge((target[0]-1, target[1]), target)
        nx.set_edge_attributes(G, {e: 1 for e in G.edges()}, "cost")
        self.updated_graph = True
        return G
    
    #elimina del grafo las aristas que llevan a celdas ocupadas por otros robots
    def elimina_obstaculos(self, graph, pos, action):
        G = copy.deepcopy(graph)
        #obtener las direcciones de la celda actual
        contents = self.model.grid.get_cell_list_contents(pos)
        directions = []
        for content in contents:
            if isinstance(content, Celda):
                directions = content.directions

        #agregar las direcciones necesarias dependiendo de la accion del robot
        if action in ["STORE", "PICKUP"] and abs(self.target[1] - pos[1]) == 1 and self.target[0] - pos[0] == 0:
            if self.target[1] > pos[1]: #target arriba
                directions.append("up")
            else: #target abajo
                directions.append("down")
        elif action == "CHARGE" and abs(self.target[0] - pos[0]) == 1 and self.target[1] - pos[1] == 0:
            if self.target[0] > pos[0]: #target a la derecha
                directions.append("right") 
            else: #target a la izquierda
                directions.append("left")
            
        #para cada una de las celdas a las que puede ir eliminar las aristas que llevan  a otros robots
        for dir in directions:
            newPosition = (pos[0] + self.dirMovs[dir][0], pos[1] + self.dirMovs[dir][1])
            contents = self.model.grid.get_cell_list_contents(newPosition)
            for content in contents:
                if isinstance(content, Robot): #si hay un robot en la celda remover la arista, enviar la negociacion
                    prioridad = content.compara_prioridad(self.action)
                    if prioridad == 1: #si este robot tiene mayor prioridad pedir al otro que se mueva
                        content.apartarse()
                    elif prioridad == -1: #si este robot tiene menor prioridad moverse
                        self.apartarse()
                    else:
                        robot = random.choice([self, content])
                        robot.apartarse()

                    if G.has_edge(pos, newPosition):
                        G.remove_edge(pos, newPosition)

        return G

    #espera hasta que el paquete llegue a la zona de recoleccion
    def espera_paquete(self):
        contents = self.model.grid.get_cell_list_contents(self.pos)
        for content in contents:
            if isinstance(content, Paquete):
                self.peso_carga = content.peso
                self.solicitar_espacio_guardar()
                break

    #guardar el paquete en el estante
    def guardar_paquete(self):
        self.peso_carga = 0
        self.action = "WANDER"
        self.cont_wander = 5
        contents = self.model.grid.get_cell_list_contents(self.pos)
        for content in contents:
            if isinstance(content, Paquete):
                self.model.ocupar_espacio(self.pos)
                content.robotId = None
                

    #recoge un paquete de un estante
    def recoge_paquete(self):
        contents = self.model.grid.get_cell_list_contents(self.pos)
        for content in contents:
            if isinstance(content, Paquete):
                self.peso_carga = content.peso
                self.target = (9, 15)
                self.action = "SEND"
                self.model.liberar_espacio(self.pos)
                self.solicitud = None
                break

    #envia un paquete por la cinta transportadora
    def envia_paquete(self):
        contents = self.model.grid.get_cell_list_contents(self.pos)
        for content in contents:
            if isinstance(content, Paquete):
                content.sig_pos = (self.pos[0]-1, self.pos[1])
                self.peso_carga = 0
                self.action = "WANDER"
                self.cont_wander = 5

    #calcula distancia entre 2 puntos
    def distancia_manhattan(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    #procesa solicitud de ayuda
    def procesar_solicitud(self, solicitud):
        if self.puede_hacer_tarea(solicitud):
            self.solicitud = copy.deepcopy(solicitud)
            self.target = solicitud["position"]
            self.action = solicitud["action"]
            return True
        
    def puede_hacer_tarea(self, solicitud):
        if self.action in ["RETRIEVE", "STORE", "CHARGE", "SEND", "PICKUP"] or self.carga_baja():
            return False
        if solicitud["action"] == "RETRIEVE" and not self.puede_guardar():
            return False
        return True
        
    #indica reasignar una tarea que el robot habia aceptado previamente
    def reasigna_tarea(self):
        self.model.pedirAyuda(copy.deepcopy(self.solicitud))
        self.action = "HALT"
        self.target = None
        self.solicitud = None
        self.updated_graph = False
        
    #regresa si un robot puede guardar un paquete
    def puede_guardar(self):
        return not self.model.todo_lleno()
    
    #solicitar un espacio para guardar un paquete
    def solicitar_espacio_guardar(self):
        self.action = "STORE"
        self.solicitud = None
        self.target = self.model.get_espacio_disponible()

    #mueve el paquete a su siguiente posicion
    def mover_paquete(self):
        contents = self.model.grid.get_cell_list_contents(self.pos)
        for content in contents:
            if isinstance(content, Paquete):
                content.sig_pos = self.sig_pos
                content.robotId = self.unique_id

    #seleccionar la estacion mas carga y colocarla como objetivo del robot
    def selecciona_estacion_carga(self):
        celdas_carga = self.model.celdas_cargas
        celdas_ord = sorted(celdas_carga, key=lambda celda: self.distancia_manhattan(self.pos, celda))
        libres = []
        for celda in celdas_ord:
            if not self.robotInCell(celda):
                libres.append(celda)
        if len(libres) == 0:
            self.sig_pos = self.pos
        else:
            celda_mas_cercana = libres[0]
            self.target = celda_mas_cercana

    #regresa si la carga está baja
    def carga_baja(self):
        return self.carga <= 50

    #regresa si el robot está cargando
    def esta_cargando(self):
        return self.carga < 100 and self.pos in self.model.celdas_cargas
        
    #carga al robot
    def cargar(self):
        self.carga += (100/15)
        self.carga = round( min(self.carga, 100), 2)

    #comparar prioridad
    #si el otro robot tiene mas prioridad regresa uno, si tiene menos regresa -1, si es igual regresa 0
    def compara_prioridad(self, other_action):
        if self.actions[other_action] > self.actions[self.action]:
            return 1
        elif self.actions[other_action] == self.actions[self.action]:
            return 0
        else:
            return -1
        
    #apartarse fuera del camino de otro robot
    def apartarse(self):
        self.seleccionar_nueva_pos()

    def step(self):

        if self.sig_pos and (self.pos != self.sig_pos): #si ya tiene una posicion asignada moverse, esto ocurrira cuando se aparte del camino de otro robot
            if self.action in ["STORE", "SEND"]: #si va a guardar o enviar un paquete mover al paquete
                self.mover_paquete()
            self.advance()
            return

        #si ha llegado al target eliminarlo
        if self.pos == self.target:
            self.target = None
            self.updated_graph = False

        if self.target: #si hay un target ir al objetivo
            if self.action == "RETRIEVE":
                if self.puede_guardar():
                    self.ve_a_objetivo()
                else:
                    self.reasigna_tarea()
            else:
                self.ve_a_objetivo()
            if self.action in ["STORE", "SEND"]: #si va a guardar o enviar un paquete mover al paquete
                self.mover_paquete()
        elif self.action == "RETRIEVE": #esperar un paquete en la cinta transportadora
            self.espera_paquete()
        elif self.action == "STORE": #guardar un paquete en un estante
            self.guardar_paquete()
        elif self.action == "PICKUP": #recoger un paquete de un estante
            self.recoge_paquete()
        elif self.action == "SEND": #enviar un paquete por la cinta transportadora de salida
            self.envia_paquete()
        elif self.esta_cargando(): #cargar 
            self.cargar()
            if self.carga == 100: #si ya se termino de cargar comienza a divagar
                self.model.ciclos_carga +=1
                self.action = "WANDER"
                self.cont_wander = 5
        elif self.carga_baja() and self.action not in ["STORE", "RETRIEVE", "PICKUP", "SEND"]: #si tiene carga y no esta ocupado seleccionar una estacion de carga
            self.selecciona_estacion_carga()
            self.action = "CHARGE"
            self.ve_a_objetivo()
        elif self.action == "WANDER": #seleccionar una posicion
            self.seleccionar_nueva_pos()
        else: #esta en modo halt y debe esperar
            self.sig_pos = self.pos

        #avanzar
        self.advance()
        #evaluar si es el optimo para realizar una tarea
        self.evaluar_optimo()
                
    def advance(self):
        if self.pos != self.sig_pos and self.carga > 0 and not self.esta_cargando(): #si se va a mover y tiene carga
            descarga = (0.1 + self.peso_carga * 0.1) #cantidad a descargar
            if self.isFast:
                descarga += 0.1
            self.carga = round(self.carga - descarga, 2) #redondear bateria a 2 decimales
            self.model.movimientos += 1 
            self.model.grid.move_agent(self, self.sig_pos) #mover al agente
            if self.carga < 0:
                self.carga = 0
    
    #evalua si el agente es optimo para realizar la tarea que esta haciendo
    def evaluar_optimo(self):
        if self.target and self.action in ["RETRIEVE", "PICKUP"]: #pedir al modelo si se debe reasignar la tarea para eficientar
            dist = self.distancia_manhattan(self.pos, self.target)
            res = self.model.es_optimo(copy.deepcopy(self.solicitud), dist)
            #si no es optimo dejara de hacerla y esta se pasara a otro agente
            if not res: 
                self.action = "HALT"
                self.target = None
                self.solicitud = None
                self.updated_graph = False


