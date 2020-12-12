from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
import requests

from dht import DHT
from hash_table import HashTable


app2 = Flask(__name__)
CORS(app2)


@app2.route('/node', methods=['POST'])
def add_nodes():
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data found'
        }
        return jsonify(response), 400
    required = ['node_id', 'node__name', 'node_path']
    if not all(key in values for key in required):
        response = {
            'message': 'Some data is missing'
        }
        return jsonify(response), 400
    success = False
    hash_table = HashTable(values['node_id'], values['node_name'], values['node_path'])
    #hash_table.files = values['node_files']
    print('printing stuff about new dht')
    print(hash_table.name)
    print(hash_table.path)
    print(hash_table.public_key)
    print(hash_table.files)
    if hash_table not in dht.peer_nodes:
        dht.peer_nodes.append(hash_table)
        success = True
    else:
        response = {
            'message': 'Cannot have node duplicates'
        }
        return jsonify(response), 400
    if success:
        response = {
            dht.get_peer_nodes()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'File saving failes'
        }
        return jsonify(response), 500






if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=6000)
    args = parser.parse_args()
    port = args.port
    dht = DHT()
    app2.run(host='0.0.0.0', port=port, debug=True)