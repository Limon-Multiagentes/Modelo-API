from mesa.model import Model
from mesa.agent import Agent
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

import numpy as np


class Celda(Agent):
    DIRECTIONS = ['right', 'down', 'left', 'up']

    def __init__(self, unique_id, model, directions=[]):
        super().__init__(unique_id, model)
        self.directions = directions

class Estante(Agent):
    def __init__(self, unique_id, model, ocupado=False):
        super().__init__(unique_id, model)

class EstacionCarga(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class Paquete(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        
    def step(self):
        if(self.pos in self.model.celdas_cinta):
            self.sig_pos = (self.pos[0]-1, self.pos[1])
            should_move = True
            contents = self.model.grid.get_cell_list_contents(self.sig_pos)
            for content in contents:
                if isinstance(content, Paquete):
                    should_move = False
            if should_move:
                self.model.grid.move_agent(self, self.sig_pos)
            else:
                self.sig_pos = self.pos


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
        self.carga = 100
        self.target = None
        self.action = None

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
        #if self.target in self.model.posiciones_estaciones:
        #    celdas = self.busca_celdas_disponibles((Celda, EstacionCarga))
        #else:
        celdas = self.busca_celdas_disponibles((Celda), self.pos)
        #si no hay celdas disponibles se queda en la misma posicion
        celdas_ut = self.celdas_utiles(celdas, self.pos, self.target, 2)

        if(len(celdas_ut) == 0):
          self.sig_pos = self.pos
          return
        
        celdas_ut = sorted(celdas_ut, key=lambda neighbor: self.distancia_manhattan(self.target, neighbor.pos))
        self.sig_pos = celdas_ut[0].pos

    #las celdas utiles para un objetivo son aquellas cuyas direcciones permiten acercarse al objetivo
    def celdas_utiles(self, celdas, pos, target, it):
        #detectar las direcciones que debe seguir
        best_dirs = []
        if pos[0] > target[0]:
            best_dirs.append("left")
        else:
            best_dirs.append("right")
        if pos[1] > target[1]:
            best_dirs.append("down")
        else:
            best_dirs.append("up")

        it -= 1
        best_celdas = []

        #iterar sobre las celdas para encontrar las celdas utiles
        for celda in celdas:
            for dir in best_dirs:
                #si la celda tiene una direccion util o es el target
                if dir in celda.directions or celda.pos == target:
                    #si la accion no es store es necesario verificar que la direccion no lleve a un estante
                    if self.action != "STORE":
                        next_pos = (celda.pos[0] + self.dirMovs[dir][0], celda.pos[1] + self.dirMovs[dir][1])
                        is_available = True
                        for content in self.model.grid.get_cell_list_contents(next_pos):
                            if isinstance(content, Estante):
                                is_available = False
                        if is_available:
                            best_celdas.append(celda)
                            break
                    else:
                        best_celdas.append(celda)
                        break  
        
        #si el target esta en las celdas seleccionadas o se acabaron las iteraciones se termina el procesamiento
        for celda in best_celdas:
            if celda.pos == target:
                return best_celdas
            
        if it == 0:
            return best_celdas
        
        #calcular si a partir de las celdas seleccionadas se puede desplazar a nuevas celdas utiles
        best_celdas_d = []

        for celda in best_celdas:
            adyacentes = self.busca_celdas_disponibles((Celda), celda.pos)
            celdas_ut = self.celdas_utiles(adyacentes, celda.pos, self.target, it)
            if celdas_ut:
                best_celdas_d.append(celda)
        return best_celdas_d


    #espera hasta que el paquete llegue a la zona de recoleccion
    def espera_paquete(self):
        contents = self.model.grid.get_cell_list_contents(self.pos)
        for content in contents:
            if isinstance(content, Paquete):
                self.action = "STORE"
                break

    #calcula distancia entre 2 puntos
    def distancia_manhattan(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    #procesa solicitud de ayuda
    def procesar_solicitud(self, solicitud):
        if self.target:
            return False
        else:
            self.target = solicitud["position"]
            self.action = solicitud["action"]
            print(self.target, self.action)
            return True

    """
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

    #buscar una celda sucia
    def buscar_celdas_sucia(self):
        celdas = self.busca_celdas_disponibles((Celda))
        celdas_sucias = []
        for vecino in celdas:
            if vecino.sucia:
                celdas_sucias.append(vecino)
        return celdas_sucias
    """

    def step(self):

        print(self.pos, self.target)

        if self.pos == self.target:
            self.target = None

        if self.target:
            self.ve_a_objetivo()
        elif self.action == "RETRIEVE":
            self.espera_paquete()
        else:
            self.seleccionar_nueva_pos()

        self.advance()

        
        #si llego al target, borrar el target
        #if self.pos == self.target:
        #    self.target = None

        #if self.esta_cargando():
        #    self.cargar()
        #elif self.target: 
        #    self.ve_a_objetivo()
        #elif self.carga_baja():
        #    self.seleccionar_estacion_carga(self.model.getEstaciones())
        #    self.ve_a_objetivo()
        #else:
        #    celdas_sucias = self.buscar_celdas_sucia()
        #    self.num_celdas_sucias = len(celdas_sucias)
        #    if len(celdas_sucias) == 0:
        #        self.seleccionar_nueva_pos()
        #    else:
        #        if self.num_celdas_sucias >= 3:
        #            self.model.pedirAyuda(self.pos, self.num_celdas_sucias)
        #        self.limpiar_una_celda(celdas_sucias)

        #self.advance()
                
    def advance(self):
        if self.pos != self.sig_pos:
            self.movimientos += 1
            self.model.grid.move_agent(self, self.sig_pos)
            #if self.carga > 0:
            #    self.carga -= 1
            #    self.model.grid.move_agent(self, self.sig_pos)

