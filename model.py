from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from itertools import chain
from agents import Cinta, Estante, EstacionCarga, Celda, Robot, Paquete
import networkx as nx
import random
       
# Creacion del modelo a utilizar
class Almacen(Model):
    # Aqui definimos todas las posiciones del almacen que pueden hacer , es decir, subir o bajar o moverse de izquierda o derecha
    DIR_POSIBLES = [
            [0, 1, 6, 6, 6, 6, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
            [0, 1, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 4, 0],
            [2, 5, 7, 7, 7, 7, 7, 9, 9, 7, 7, 7, 7, 9, 8, 4],
            [2, 5, 8, 14, 14, 14, 14, 5, 8, 14, 14, 14, 14, 5, 8, 4],
            [2, 5, 11, 6, 6, 6, 6, 12, 8, 6, 6, 6, 6, 12, 8, 4],
            [2, 5, 11, 7, 7, 7, 7, 5, 11, 7, 7, 7, 7, 12, 8, 4],
            [9, 5, 8, 14, 14, 14, 14, 5, 8, 14, 14, 14, 14, 5, 8, 10],
            [5, 5, 11, 6, 6, 6, 6, 12, 8, 6, 6, 6, 6, 12, 8, 6],
            [7, 5, 11, 7, 7, 7, 7, 5, 11, 7, 7, 7, 7, 12, 8, 8],
            [9, 5, 8, 14, 14, 14, 14, 5, 8, 14, 14, 14, 14, 5, 8, 10],
            [2, 5, 11, 6, 6, 6, 6, 12, 8, 6, 6, 6, 6, 12, 8, 4],
            [2, 5, 11, 7, 7, 7, 7, 5, 11, 7, 7, 7, 7, 12, 8, 4],
            [2, 5, 8, 14, 14, 14, 14, 5, 8, 14, 14, 14, 14, 5, 8, 4],
            [0, 5, 10, 6, 6, 6, 6, 10, 10, 6, 6, 6, 6, 12, 8, 0],
            [0, 2, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 3, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 3, 0]
        ]
    # Aqui definimos la cantidad de filas y columnas
    FILAS_ESTANTES = 4
    COLUMNAS_ESTANTES = 8

    # Aqui definimos el contrusctor del modelo y le damos parametros de entrada
    def __init__(self, M: int, N: int,
                 num_agentes: int = 4,
                 tasa_entrada: int = 10,
                 tasa_salida: int = 30
        ):
        self.width = M
        self.height = N
        self.reset(num_agentes, tasa_entrada, tasa_salida)
    
    # Reset es el encargado de reiniciarlizar el modelo en caso de que se reinicie
    def reset(self, num_agentes, tasa_entrada, tasa_salida):
        #tasas y contadores de entrada y salida
        self.tasa_entrada = tasa_entrada
        self.tasa_salida = tasa_salida
        self.cont_entrada = tasa_entrada
        self.cont_salida = tasa_salida

        #cantidad de robots y paquetes
        self.num_agentes = num_agentes
        self.num_paquetes = 0
        self.ordenes = 0

        #espacios de los estantes en el almacen
        #0 indica que esta vacio
        #1 indica que la posicion ya se asigno a un robot para dejar un paquete
        #e2 indica que esta ocupado
        self.espacios_almacen = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0]
        ]

        #variables a analizar
        self.movimientos = 0
        self.paquetes_recibidos = 0
        self.paquetes_enviados = 0
        self.ciclos_carga = 0

        #solicitudes a los robots
        self.solicitudes = []

        #grafo para busqueda de trayectorias optimas
        self.graph = self.creaGrafo()

        self.grid = MultiGrid(self.width, self.height,False)
        self.scheduleRobots = RandomActivation(self)
        self.schedulePaquetes = RandomActivation(self)

        #posiciones disponibles del grid
        self.posiciones_disponibles = [pos for _, pos in self.grid.coord_iter()]

        self.colocar_cintas()
        self.colocar_estantes()
        self.colocar_celdas_carga()
        self.colocar_celdas()
        self.colocar_robots()

        self.running = True

        # Esto lo que hace es pasarle toda la informacion que necesitamos para hacer las graficas
        self.datacollector = DataCollector(
            model_reporters={"Movimientos": "movimientos",
                             "PaquetesRecibidos": "paquetes_recibidos",
                             "PaquetesEnviados": "paquetes_enviados",
                             "CiclosCarga": "ciclos_carga"})
        
    # Colocamos la cintas en determinadas posciones
    def colocar_cintas(self):
        #posiciones para las cintas
        self.celdas_cinta = [(i, 15) for i in range(9)] + [(i, 0) for i in range(7, 16)] 
        for id, pos in enumerate(self.celdas_cinta):
            cinta = Cinta(int(f"{self.num_agentes}0{id}") + 1, self)
            self.grid.place_agent(cinta, pos)
            self.posiciones_disponibles.remove(pos)

    # Aqui definimos una funcion para colocar los estantes 
    def colocar_estantes(self):
         #posiciones para los estantes
        self.celdas_estantes = [(i, j) for j in range(3, 13, 3) for i in chain(range(3, 7), range(9, 13))]
        for id, pos in enumerate(self.celdas_estantes):
            estante = Estante(int(f"{self.num_agentes}1{id}") + 1, self)
            self.grid.place_agent(estante, pos)

    # Colocamos las celdas en determinadas posciones
    def colocar_celdas_carga(self):
        #posiciones para las estaciones de carga
        self.celdas_cargas = [(0, 6), (0, 9), (15, 6), (15, 9)]
        for id, pos in enumerate(self.celdas_cargas):
            estacion = EstacionCarga(int(f"{self.num_agentes}2{id}") + 1, self)
            self.grid.place_agent(estacion, pos)

    # Definimos en que posicion se puede mover la celda
    def colocar_celdas(self): 
        #posiciones de las celdas
        for id, pos in enumerate(self.posiciones_disponibles):
            celda = Celda(int(f"{self.num_agentes}{id}") + 1, self)
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
            elif dirs == 14:
                celda.directions = ["up", "down"]
            self.grid.place_agent(celda, pos)

    #Colocamos los robots en determinadas posiciones
    def colocar_robots(self):
        #posiciones de los robots
        pos_robots = [(0, 2), (15, 2), (0, 3), (15, 3), (0, 4), (15, 4), (0, 11), (15, 11), (0, 12), (15, 12)]
        pos_robots = pos_robots[:self.num_agentes]
        for id, pos in enumerate(pos_robots):
            robot = Robot(int(f"{self.num_agentes}3{id}") + 1, self)
            self.grid.place_agent(robot, pos)
            self.scheduleRobots.add(robot)

    # aqui vemos si el modelo esta corriendo 
    def step(self):
        if self.running:
            #instanciar paquetes despues de una cuenta
            self.cont_entrada -= 1
            if self.cont_entrada == 0:
                self.instantiatePackage()
                self.cont_entrada = self.tasa_entrada

            #solicitar pedidos despues de una cuenta
            self.cont_salida -= 1
            if self.cont_salida == 0:
                self.realizar_pedido()
                self.cont_salida = self.tasa_salida

            self.realizarSolicitudes()
            self.scheduleRobots.step()
            self.schedulePaquetes.step()
            self.datacollector.collect(self)
            
    # Checamos si el almacen esta lleno
    def instantiatePackage(self):
        #no ingresar paquetes si el almacen esta lleno
        if self.todo_lleno():
            return

        #crear paquete si la cinta no está llena
        should_create = True
        contents = self.grid.get_cell_list_contents((15, 0))
        for content in contents:
            if isinstance(content, Paquete):
                should_create = False
        #crear paquete
        if should_create:
            peso = round(random.uniform(1, 10), 2)
            paquete = Paquete(int(f"{self.num_agentes}4{self.num_paquetes}")+1, self, peso)
            self.num_paquetes += 1
            self.grid.place_agent(paquete, (15, 0))
            self.schedulePaquetes.add(paquete)
        #crear solicitud a los robots para recoger el paquete
        solicitud = {
            "priority": 5,
            "id": self.num_paquetes-1,
            "position": (6, 0),
            "action": "RETRIEVE"
        }
        self.pedirAyuda(solicitud)

    #mandar a recoger un paquete
    def realizar_pedido(self):
        #no hacer pedidos si el almacen esta vacio
        if self.todo_vacio():
            return
        
        ocupadas = []

        #seleccionar un estante de los que estan ocupados aleatoritamente
        for i in range(self.FILAS_ESTANTES):
            for j in range(self.COLUMNAS_ESTANTES):
                if self.espacios_almacen[i][j] == 2:
                    ocupadas.append((i, j))

        if len(ocupadas) == 0:
            return

        random_estante = random.choice(ocupadas)

        #obtener su posicion
        index = random_estante[0] * self.COLUMNAS_ESTANTES + random_estante[1]
        selected = self.celdas_estantes[index]

        #crear la solicitud
        solicitud = {
            "priority": 4,
            "id": self.ordenes,
            "position": selected,
            "action": "PICKUP"
        }
        self.ordenes += 1
        self.pedirAyuda(solicitud)

    #retorna si todos los estantes estan llenos
    def todo_lleno(self):
        for i in range(self.FILAS_ESTANTES):
            for j in range(self.COLUMNAS_ESTANTES):
                if self.espacios_almacen[i][j] == 0:
                    return False
        return True
    
    #retorna si todos los estantes estan vacios
    def todo_vacio(self):
        for i in range(self.FILAS_ESTANTES):
            for j in range(self.COLUMNAS_ESTANTES):
                if self.espacios_almacen[i][j] != 0:
                    return False
        return True
    
    #libera un espacio del almacen
    def liberar_espacio(self, pos):
        index = self.celdas_estantes.index(pos)
        i = index // self.COLUMNAS_ESTANTES
        j = index % self.COLUMNAS_ESTANTES
        self.espacios_almacen[i][j] = 0

    #ocupa un espacio del almacen
    def ocupar_espacio(self, pos):
        index = self.celdas_estantes.index(pos)
        i = index // self.COLUMNAS_ESTANTES
        j = index % self.COLUMNAS_ESTANTES
        self.espacios_almacen[i][j] = 2

    #calcula distancia entre 2 puntos
    def distancia_manhattan(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    #crea una solicitud de ayuda
    def pedirAyuda(self, solicitud):
        if solicitud:
            self.solicitudes.append(solicitud)

    def es_optimo(self, solicitud, dist):
        if(solicitud == None):
            return True
        agentes = self.getAgentes()
        disponibles = [agente for agente in agentes if agente[0].puede_hacer_tarea(solicitud)]
        for agente in disponibles:
            if self.distancia_manhattan(agente[1], solicitud["position"]) < dist:
                self.pedirAyuda(solicitud) 
                return False
        return True


    #realiza cada una de las solicitudes a los robots
    def realizarSolicitudes(self):
        self.solicitudes = sorted(self.solicitudes, key=lambda solicitud: (-solicitud["priority"], solicitud["id"]))
        agentes = self.getAgentes()

        restantes = []

        for solicitud in self.solicitudes:
            agentes = sorted(agentes, key=lambda agente: self.distancia_manhattan(solicitud["position"], agente[1]))
            accepted = False
            for agente in agentes:
                result = agente[0].procesar_solicitud(solicitud)
                if result:
                    accepted = True
                    break
            if not accepted:
                restantes.append(solicitud)
                
        self.solicitudes = restantes

    #obtiene los robots de limpieza del grid
    def getAgentes(self):
        agentes = []
        for (content, pos) in self.grid.coord_iter():
            for obj in content:
                if isinstance(obj, Robot):
                    agentes.append((obj, pos))
        return agentes
    
    #retorna el siguiente espacio disponible en el almacen y lo marca como ocupado
    def get_espacio_disponible(self):
        for i in range(self.FILAS_ESTANTES):
            for j in range(self.COLUMNAS_ESTANTES):
                if self.espacios_almacen[i][j] == 0:
                    self.espacios_almacen[i][j] = 1
                    index = i * self.COLUMNAS_ESTANTES + j
                    return self.celdas_estantes[index]
    
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
                elif dirs == 14:
                    G.add_edge((j, i), (j, i+1))
                    G.add_edge((j, i), (j, i-1))

        nx.set_edge_attributes(G, {e: 1 for e in G.edges()}, "cost")
        return G
    
    # Se ha parado el modelo
    def parar_modelo(self):
        self.running = False

    # Se ha reanudo el modelo
    def reanudar_modelo(self):
        self.running = True