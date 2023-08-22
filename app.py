# Servicio de flask 

# usar pip install flask
# usar pip install flask_cors
from flask import Flask, jsonify, request,json

app = Flask(__name__)



# Testing Route
@app.route('/')
def api_root():
    return 'Prueba de funcionamiento'



# Gets
@app.route('/robots', methods=['GET'])
def numRobots():
    return jsonify(robots),200

@app.route('/paquetes', methods=['GET'])
def numRobots():
    return jsonify(paquetes),200

@app.route('/coordenadas', methods=['GET'])
def numRobots():
    return jsonify(coordenadas),200

#post

@app.route('/numRobots', methods=['POST'])
def post_example():
    data = request.json  # Assuming JSON data is being sent
    return jsonify(data), 201  # HTTP status code 201 Created

@app.route('/tasaPaquetes', methods=['POST'])
def post_example():
    data = request.json  # Assuming JSON data is being sent
    return jsonify(data), 201  # HTTP status code 201 Created

@app.route('/pararSimulacion', methods=['POST'])
def post_example():
    data = request.json  # Assuming JSON data is being sent
    return jsonify(data), 201  # HTTP status code 201 Created

if __name__ == '__main__':
    app.run(debug=True) # opcionales , port=4000,host="0.0.0.0"