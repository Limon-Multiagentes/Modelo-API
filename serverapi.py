# Servicio de flask 

# usar pip install flask
# usar pip install flask_cors
# Importamos las librerias que vamos a usar
from flask import Flask, jsonify, request
from model import Almacen

# Aqui declaramos que vamos a usar flask 
app = Flask(__name__)
# cramos el modelado del almacen
modelAlmacen = Almacen(16, 16)


# ----------------------------------- GETS ------------------------------#
# retornar una lista con los datos de los robots 
@app.route('/robots', methods=['GET'])
def numRobots():
    global modelAlmacen
    robots = [{'id': agent.unique_id, 'x': agent.pos[0], 'y': agent.pos[1], "action": agent.action, "carga": agent.carga} for agent in modelAlmacen.scheduleRobots.agents]
    return jsonify(robots)

# retornar una lista con los datos de los paquetes
@app.route('/paquetes', methods=['GET'])
def numPaquetes():
    global modelAlmacen
    paquetes = [{'id': agent.unique_id, 'x': agent.pos[0], 'y': agent.pos[1], "peso": agent.peso} for agent in modelAlmacen.schedulePaquetes.agents]
    return jsonify(paquetes)

#retornar los datos para las graficas
@app.route('/data', methods=['GET'])
def data():
    global modelAlmacen
    dict = modelAlmacen.datacollector.get_model_vars_dataframe().to_dict()
    return jsonify(dict)

#---------------------------- POST --+----------------------------#

# Este metodo es el constructor del modelo se utiliza el metodo post porque el usuario puede definir los parametros
@app.route('/init', methods=["POST"])
def init_model():
    global modelAlmacen
    data = request.json  # Assuming JSON data is being sent
    modelAlmacen = Almacen(16, 16, data["numRobots"], data["tasaEntrada"], data["tasaSalida"])
    return jsonify({"response": "OK"})

# Este metodo es para avanzar paso a paso en el modelo 
@app.route('/step', methods=['POST'])
def step_simulation():
    global modelAlmacen
    modelAlmacen.step()
    return jsonify({"response": "OK"})

# Cambiar numero de robots
@app.route('/params', methods=['POST'])
def post_params():
    global modelAlmacen
    data = request.json  # Assuming JSON data is being sent
    modelAlmacen.reset(data["numRobots"], data["tasaEntrada"], data["tasaSalida"])
    return jsonify({"response": "OK"})  # HTTP status code 201 Created

# Detener el modelo
@app.route('/stop', methods=['POST'])
def stop_simulation():
    global modelAlmacen
    modelAlmacen.parar_modelo()
    return jsonify({"response": "OK"}) # HTTP status code 201 Created

# Reanudar el modelo
@app.route('/continue', methods=['POST'])
def continue_simulation():
    global modelAlmacen
    modelAlmacen.reanudar_modelo()
    return jsonify({"response": "OK"}) # HTTP status code 201 Created

# Aqui inicializamos el modelo por eos se llama main cabe resaltar que usamos el puerto 4000
if __name__ == '__main__':
    app.run(debug=True, port=4000) # opcionales , port=4000,host="0.0.0.0"