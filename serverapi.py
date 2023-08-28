# Servicio de flask 

# usar pip install flask
# usar pip install flask_cors
from flask import Flask, jsonify, request

app = Flask(__name__)

from model import Almacen

modelAlmacen = Almacen(16, 16)


# Gets
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

#post

# iniciar modelo
@app.route('/init', methods=["POST"])
def init_model():
    global modelAlmacen
    data = request.json  # Assuming JSON data is being sent
    modelAlmacen = Almacen(16, 16, data["numRobots"], data["tasaEntrada"], data["tasaSalida"])
    return jsonify({"response": "OK"})

# avanzar un paso
@app.route('/step', methods=['POST'])
def step_simulation():
    global modelAlmacen
    modelAlmacen.step()
    return jsonify({"response": "OK"})

# cambiar numero de robots
@app.route('/params', methods=['POST'])
def post_params():
    global modelAlmacen
    data = request.json  # Assuming JSON data is being sent
    modelAlmacen.reset(data["numRobots"], data["tasaEntrada"], data["tasaSalida"])
    return jsonify({"response": "OK"})  # HTTP status code 201 Created

# detener el modelo
@app.route('/stop', methods=['POST'])
def stop_simulation():
    global modelAlmacen
    modelAlmacen.parar_modelo()
    return jsonify({"response": "OK"}) # HTTP status code 201 Created

# reanudar el modelo
@app.route('/continue', methods=['POST'])
def continue_simulation():
    global modelAlmacen
    modelAlmacen.reanudar_modelo()
    return jsonify({"response": "OK"}) # HTTP status code 201 Created

if __name__ == '__main__':
    app.run(debug=True, port=4000) # opcionales , port=4000,host="0.0.0.0"