from mesa.model import Model
from mesa.agent import Agent
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

import numpy as np


class Celda(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class Estante(Agent):
    def __init__(self, unique_id, model, ocupado=False):
        super().__init__(unique_id, model)

class EstacionCarga(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class Paquete(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class Cinta(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class Robot(Agent):
    DIRECTIONS = ['right', 'down', 'left', 'up']
    
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.sig_pos = None
        self.movimientos = 0
        self.carga = 100
        self.target = None
        

    #busca_celdas_disponibles
    def busca_celdas_disponibles(self, incluir, remove_agents=True):
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
        celdas = []
        for neighbor in neighbors:
            if isinstance(neighbor, incluir):
                celdas.append(neighbor)
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
        celdas = self.busca_celdas_disponibles((Celda))
        if(len(celdas) == 0):
          self.sig_pos = self.pos
          return
        self.sig_pos = self.random.choice(celdas).pos

    #selecciona una celda a limpiar
    def limpiar_una_celda(self, lista_de_celdas_sucias):
        if(len(lista_de_celdas_sucias) == 0):
          self.sig_pos = self.pos
          return
        celda_a_limpiar = self.random.choice(lista_de_celdas_sucias)
        celda_a_limpiar.sucia = False
        self.num_celdas_sucias -= 1
        self.sig_pos = celda_a_limpiar.pos

    #calcula distancia entre 2 puntos
    def distancia_euclidiana(self, pos1, pos2):
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

    #seleccionar la estacion mas carga y colocarla como objetivo del robot
    def seleccionar_estacion_carga(self, lista_celdas_carga):
        celda_mas_cercana = lista_celdas_carga[0]
        min_distancia = float("inf") #celda[0], celda[1] coordenadas estacion
        for celda in lista_celdas_carga: #self.pos.x, self.pos.y coordenadas robot 
            distancia = self.distancia_euclidiana(celda, self.pos)  
            if distancia < min_distancia:
                min_distancia = distancia
                celda_mas_cercana = celda
        self.target = celda_mas_cercana

    #avanza hacia un objetivo
    def ve_a_objetivo(self):      
        if self.target in self.model.posiciones_estaciones:
            celdas = self.busca_celdas_disponibles((Celda, EstacionCarga))
        else:
            celdas = self.busca_celdas_disponibles((Celda))
        if(len(celdas) == 0):
          self.sig_pos = self.pos
          return
        celdas = sorted(celdas, key=lambda neighbor: self.distancia_euclidiana(self.target, neighbor.pos))
        self.sig_pos = celdas[0].pos
        #si va a avanzar a una celda sucia, la limpia
        contents = self.model.grid.get_cell_list_contents(self.sig_pos)
        for obj in contents:
            if isinstance(obj, Celda) and obj.sucia:
                obj.sucia = False

    #regresa si la carga está baja
    def carga_baja(self):
        return self.carga <= 25

    #regresa si el robot está cargando
    def esta_cargando(self):
        return self.carga < 100 and self.pos in self.model.posiciones_estaciones 
        
    #carga al robot
    def cargar(self):
        if self.carga < 100:
            self.carga += 25
            self.carga = min(self.carga, 100)
            self.sig_pos = self.pos
            if self.carga == 100:
                self.model.cantidadCarga += 1

    #procesa solicitud de ayuda
    def procesar_solicitud(self, pos):
        if self.num_celdas_sucias > 0 or self.target:
            return False
        else:
            self.target = pos
            return True

    #buscar una celda sucia
    def buscar_celdas_sucia(self):
        celdas = self.busca_celdas_disponibles((Celda))
        celdas_sucias = []
        for vecino in celdas:
            if vecino.sucia:
                celdas_sucias.append(vecino)
        return celdas_sucias
    
    #Dirreccciones
    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction):
        self._direction = direction
        if self._direction == 'up':
            self.dx, self.dy = -1, 0
        elif self._direction == 'down':
            self.dx, self.dy = 1, 0
        if self._direction == 'right':
            self.dx, self.dy = 0, 1
        elif self._direction == 'left':
            self.dx, self.dy = 0, -1

    def step(self):
        
        #si llego al target, borrar el target
        if self.pos == self.target:
            self.target = None

        if self.esta_cargando():
            self.cargar()
        elif self.target: 
            self.ve_a_objetivo()
        elif self.carga_baja():
            self.seleccionar_estacion_carga(self.model.getEstaciones())
            self.ve_a_objetivo()
        else:
            celdas_sucias = self.buscar_celdas_sucia()
            self.num_celdas_sucias = len(celdas_sucias)
            if len(celdas_sucias) == 0:
                self.seleccionar_nueva_pos()
            else:
                if self.num_celdas_sucias >= 3:
                    self.model.pedirAyuda(self.pos, self.num_celdas_sucias)
                self.limpiar_una_celda(celdas_sucias)

        self.advance()
                

    def advance(self):
        if self.pos != self.sig_pos:
            self.movimientos += 1
            self.model.movimiento += 1
            if self.carga > 0:
                self.carga -= 1
                self.model.grid.move_agent(self, self.sig_pos)
