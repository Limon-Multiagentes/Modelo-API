from mesa.model import Model
from mesa.agent import Agent
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

import numpy as np
import networkx as nx
import copy


class Celda(Agent):
    DIRECTIONS = ['right', 'down', 'left', 'up']

    def __init__(self, unique_id, model, directions=[]):
        super().__init__(unique_id, model)
        self.directions = directions

class Estante(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class EstacionCarga(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class Paquete(Agent):
    def __init__(self, unique_id, model, peso):
        super().__init__(unique_id, model)
        self.peso = peso
        
    def step(self):
        if(self.pos in self.model.celdas_cinta):
            self.sig_pos = (self.pos[0]-1, self.pos[1])
            should_move = True
            contents = self.model.grid.get_cell_list_contents(self.sig_pos)
            for content in contents:
                if isinstance(content, Paquete):
                    should_move = False
            if should_move:
                if self.sig_pos[0] >= 0:
                    self.model.grid.move_agent(self, self.sig_pos)
                else:
                    self.model.grid.remove_agent(self)
                    self.model.schedulePaquetes.remove(self)
            else:
                self.sig_pos = self.pos
        else:
            if self.sig_pos != self.pos:
                self.model.grid.move_agent(self, self.sig_pos)


class Cinta(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class Robot(Agent):    

    dirMovs = {
        "right": (1, 0),
        "left": (-1, 0),
        "down": (0, -1),
        "up": (0, 1), 
    }

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.sig_pos = None
        self.movimientos = 0
        self.peso_carga = 0
        self.carga = 100
        self.target = None
        self.action = "WANDER"

        self.path = []
        self.updated_graph = False

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
                agents = [agent for agent in cell_contents if isinstance(agent, Robot)]
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

    #avanza hacia un objetivo
    def ve_a_objetivo(self):      
        if self.action in ["STORE", "CHARGE", "PICKUP"]:
            if not self.updated_graph:
                self.graph = self.actualizar_grafo(self.model.graph, self.target, self.action)
            self.path = nx.astar_path(self.graph, self.pos, self.target, heuristic=self.distancia_manhattan, weight="cost")
        else:
            self.path = nx.astar_path(self.model.graph, self.pos, self.target, heuristic=self.distancia_manhattan, weight="cost")

        #si no hay celdas disponibles se queda en la misma posicion
        if(len(self.path) == 0):
          self.sig_pos = self.pos
          return
        
        self.path.pop(0)
        self.sig_pos = self.path[0]

    #actualiza grafo para acceder a estaciones de carga
    def actualizar_grafo(self, graph, target, action):
        G = copy.deepcopy(graph)
        if action in ["STORE", "PICKUP"]:
            G.add_edge((target[0], target[1]-1), target)
            G.add_edge((target[0], target[1]+1), target)
        else:
            if target[0] == 0:
                G.add_edge((target[0]+1, target[1]), target)
            else:
                G.add_edge((target[0]-1, target[1]), target)
        nx.set_edge_attributes(G, {e: 1 for e in G.edges()}, "cost")
        self.updated_graph = True
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

    #recoge un paquete de un estante
    def recoge_paquete(self):
        contents = self.model.grid.get_cell_list_contents(self.pos)
        for content in contents:
            if isinstance(content, Paquete):
                self.peso_carga = content.peso
                self.target = (9, 15)
                self.action = "SEND"
                break

    #envia un paquete por la cinta transportadora
    def envia_paquete(self):
        contents = self.model.grid.get_cell_list_contents(self.pos)
        for content in contents:
            if isinstance(content, Paquete):
                content.sig_pos = (self.pos[0]-1, self.pos[1])
                self.peso_carga = 0
                self.action = "WANDER"

    #calcula distancia entre 2 puntos
    def distancia_manhattan(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    #procesa solicitud de ayuda
    def procesar_solicitud(self, solicitud):
        if self.target or self.action in ["RECEIVE", "STORE", "CHARGE", "SEND"] or self.carga_baja():
            return False
        else:
            self.target = solicitud["position"]
            self.action = solicitud["action"]
            return True
    
    #solicitar un espacio para guardar un paquete
    def solicitar_espacio_guardar(self):
        self.action = "STORE"
        self.target = self.model.get_espacio_disponible()

    #mueve el paquete a su siguiente posicion
    def mover_paquete(self):
        contents = self.model.grid.get_cell_list_contents(self.pos)
        for content in contents:
            if isinstance(content, Paquete):
                content.sig_pos = self.sig_pos


    #seleccionar la estacion mas carga y colocarla como objetivo del robot
    def selecciona_estacion_carga(self):
        celdas_carga = self.model.celdas_cargas
        celdas_ord = sorted(celdas_carga, key=lambda celda: self.distancia_manhattan(self.pos, celda))
        celda_mas_cercana = celdas_ord[0]
        self.target = celda_mas_cercana

    #regresa si la carga está baja
    def carga_baja(self):
        return self.carga <= 25

    #regresa si el robot está cargando
    def esta_cargando(self):
        return self.carga < 100 and self.pos in self.model.celdas_cargas
        
    #carga al robot
    def cargar(self):
        self.carga += (100/15)
        self.carga = round( min(self.carga, 100), 2)

    def step(self):
        #si ha llegado al target eliminarlo
        #cuando esta guardando, eliminar la carga
        if self.pos == self.target:
            self.target = None
            self.updated_graph = False

        if self.target:
            self.ve_a_objetivo()
            if self.action in ["STORE", "SEND"]:
                self.mover_paquete()
        elif self.action == "RETRIEVE":
            self.espera_paquete()
        elif self.action == "STORE":
            self.guardar_paquete()
        elif self.action == "PICKUP":
            self.recoge_paquete()
        elif self.action == "SEND":
            self.envia_paquete()
        elif self.esta_cargando():
            self.cargar()
            if self.carga == 100:
                self.action = "WANDER"
        elif self.carga_baja() and self.action not in ["STORE", "RECEIVE", "PICKUP", "SEND"]:
            self.selecciona_estacion_carga()
            self.action = "CHARGE"
            self.ve_a_objetivo()
        else:
            self.seleccionar_nueva_pos()

        self.advance()
                
    def advance(self):
        if self.pos != self.sig_pos:
            self.movimientos += 1
            if self.carga > 0:
                descarga = (0.1 + self.peso_carga * 0.1)*2
                self.carga = round(self.carga - descarga, 2)
                self.model.grid.move_agent(self, self.sig_pos)
                if self.carga < 0:
                    self.carga = 0

