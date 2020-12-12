from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
import requests
from collections import OrderedDict
from munch import Munch, munchify, unmunchify



from wallet import Wallet
from blockchain import Blockchain
from file import File
from dht import DHT
from hash_table import HashTable
from hash_util import hash_string_256
from merkle_tree import MerkleTreeHash

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def get_ui():
    return 'This works!!!'


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_snapshot = blockchain.chain
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]
    for dict_block in dict_chain:
        dict_block['data'] = [dt.__dict__ for dt in dict_block['data']]
    return jsonify(dict_chain), 200

@app.route('/get-hashtable', methods=['GET'])
def get_hashtable():
    response = {
        'files': hash_table.files
    }
    return jsonify(response), 201

# @app.route('/print-blockchains', methods=['GET'])
# def print_blockchains():
#     print(blockchains)
#     response = {
#         'blockchains': b
#     }
#     return jsonify(response), 201



@app.route('/mine', methods=['POST'])
def mine():
    block = blockchain.mine_block()
    if block != None:
        for blockchain_ls in blockchains:
            if block.root_node == blockchain_ls.root_node:
                blockchain_ls = block
                broadcast = True
                broadcast_blochchain_list(broadcast)
        dict_block = block.__dict__.copy()
        dict_block['data'] = [dt.__dict__ for dt in dict_block['data']]
        respone = {
            'message': 'Block added successfully',
            'block': dict_block
        }
        return jsonify(respone), 201
    else:
        response = {
            'message': 'Mining the Block failed.'
        }
        return jsonify(response), 500


@app.route('/node', methods=['POST'])
def add_node():
    """Follow this format
        "public_key": "id",
        "name": "name",
        "path": "path"

    """
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data attached'
        }
        return jsonify(response), 400
    if 'public_key' not in values or 'name' not in values or 'path' not in values:
        response = {
            'message': 'No nodes data found'
        }
        return jsonify(response), 400

    public_key = values['public_key']
    name = values['name']
    path = values['path']

    if not os.path.isdir(path):
        response = {
            'message': 'Not a valid path to local directory'
        }
        return jsonify(response), 400

    node = HashTable(public_key, name, path)
    dht.add_peer_nodes(node)
    response = {
        'message': 'Node added successfully',
        'all_nodes': dht.get_peer_nodes()
    }
    return jsonify(response), 201


@app.route('/node/<node_url>', methods=['DELETE'])
def remove_node(node_url):
    if node_url == '' or node_url == None:
        response = {
            'message': 'No node found'
        }
        return jsonify(response), 400
    dht.remove_peer_node(node_url)
    response = {
        'message': 'Node removes',
        'all_nodes': dht.get_peer_nodes()
    }
    return jsonify(response), 200


@app.route('/update-dht', methods=['POST'])
def update_dht():
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data found'
        }
        return jsonify(response), 400
    required = ['file_name', 'file_path', 'file_size', 'file_owner', 'chunk_id', 'chunk_name', 'chunk_size',
                'chunk_number', 'chunk_path', 'chunk_data', 'chunk_hash', 'chunk_owner', 'peer_key', 'peer_id']
    if not all(key in values for key in required):
        response = {
            'message': 'Some data is missing'
        }
        return jsonify(response), 400
    if values['file_owner'] != '5000':
        response = {
            'message': 'port incorrect, make the request in port 5000'
        }
        return jsonify(response), 400
    encoded_data = values['chunk_data'].encode("utf-8")
    data_hash = str(hash_string_256(encoded_data))
    dht.peer_nodes[values['peer_id']][data_hash] = values['chunk_path'] + values['chunk_name']
    response = {
        'message': 'DHT updated successfully'
    }
    return jsonify(response), 201
    


@app.route('/nodes', methods=['GET'])
def get_nodes():
    nodes = dht.get_peer_nodes()
    response = {
        'all_nodes': nodes
    }
    return jsonify(response), 200


@app.route('/get-dht-size', methods=['GET'])
def get_dht_size():
    response = {
        'dht_size': len(dht.peer_nodes)
    }
    return jsonify(response), 201


@app.route('/get-peer', methods=['POST'])
def get_peer():
    val = request.get_json()
    if not val:
        response = {
            'message': 'no value'
        }
    noode_to_store = val['node_to_store']
    response = {
        'peer_key': dht.peer_nodes[int(noode_to_store)].public_key,
        'peer_name': dht.peer_nodes[int(noode_to_store)].name,
        'peer_path': dht.peer_nodes[int(noode_to_store)].path
    }
    return jsonify(response), 201

# def convert_to_dict():
#     chain_snapshot = current_blockchain.chain
#     dict_chain = [block.__dict__.copy() for block in chain_snapshot]
#     for dict_block in dict_chain:
#         dict_block['data'] = [dt.__dict__ for dt in dict_block['data']]

    




def broadcast_blochchain_list(root_node):
    blockchain_list = blockchains[:]
    for b_chain in blockchain_list:
        chain_snapshot = b_chain.chain
        dict_chain = [block.__dict__.copy() for block in chain_snapshot]
        for dict_block in dict_chain:
            dict_block['data'] = [dt.__dict__ for dt in dict_block['data']]
        b_chain.chain = dict_chain
        open_data_snapshot = b_chain.open_data
        dict_open_data = [block.__dict__.copy() for block in open_data_snapshot]
        for dict_block in dict_open_data:
            dict_block['data'] = [dt.__dict__ for dt in dict_block['data']]
        b_chain.open_data = dict_open_data
    
    if not root_node:
        for iter_blockchain in blockchain_list:
            for peer in dht.peer_nodes:
                url = 'http://localhost:{}/updated-blockchains'.format(peer.name)
                try:
                    response = requests.post(url, json={'chain': iter_blockchain.chain,
                                                        'open_data': iter_blockchain.open_data,
                                                        'hosting_node': iter_blockchain.hosting_node,
                                                        'public_key': iter_blockchain.public_key,
                                                        'root_node': iter_blockchain.root_node,
                                                        'file_name': iter_blockchain.file_name,
                                                        'file_size': iter_blockchain.file_size,
                                                        'file_owner': iter_blockchain.file_owner,
                                                        'chunk_number': iter_blockchain.chunk_number,
                                                        'chunk_size': iter_blockchain.chunk_size,
                                                        'last_chunk_size': iter_blockchain.last_chunk_size})
                    print(response.status_code)
                    if response.status_code == 400 or response.status_code == 500:
                        res = {
                            'message': 'Couldnt send updated blockchains'
                        }
                        return jsonify(res), 400
                except requests.exceptions.ConnectionError:
                    print('There was a connection error')
    else:
        url = 'http://localhost:5000/updated-blockchains'
        try:
            response = requests.post(url, json={'chain': iter_blockchain.chain,
                                                'open_data': iter_blockchain.open_data,
                                                'hosting_node': iter_blockchain.hosting_node,
                                                'public_key': iter_blockchain.public_key,
                                                'root_node': iter_blockchain.root_node,
                                                'file_name': iter_blockchain.file_name,
                                                'file_size': iter_blockchain.file_size,
                                                'file_owner': iter_blockchain.file_owner,
                                                'chunk_number': iter_blockchain.chunk_number,
                                                'chunk_size': iter_blockchain.chunk_size,
                                                'last_chunk_size': iter_blockchain.last_chunk_size})
            print(response.status_code)
            if response.status_code == 400 or response.status_code == 500:
                res = {
                    'message': 'Couldnt send updated blockchains'
                }
                return jsonify(res), 400
        except requests.exceptions.ConnectionError:
            print('There was a connection error')



@app.route('/updated-blockchains', methods=['POST'])
def updated_blockchain():
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data found'
        }
    required_content = ['chain', 'open_data', 'hosting_node', 'public_key', 'root_node', 'file_name', 'file_size', 'file_owner', 'chunk_number', 'chunk_size', 'last_chunk_size']
    if not all(key in values for key in required_content):
        response = {
            'message': 'Missing some values'
        }
    print('munching***************************************************************************************')
    chain = Munch(values['chain'])
    print(chain)
    print('munching***************************************************************************************')
    new_blockchain = Blockchain('', '')
    new_blockchain.chain = values['chain']
    new_blockchain.open_data = values['open_data']
    new_blockchain.hosting_node = values['hosting_node']
    new_blockchain.public_key = values['public_key']
    new_blockchain.root_node = values['root_node']
    new_blockchain.file_name = values['file_name']
    new_blockchain.file_size = int(values['file_size'])
    new_blockchain.file_name = values['file_owner']
    new_blockchain.chunk_number = int(values['chunk_number'])
    new_blockchain.chunk_size = int(values['chunk_size'])
    new_blockchain.last_chunk_size = int(values['last_chunk_size'])
    
    if len(blockchains) == 0:
        blockchains.append(new_blockchain)
    else:
        for block in blockchains:
            if block.file_name == new_blockchain.file_name:
                block = new_blockchain
    response = {
        'message': 'Success'    
        }
    return jsonify(response), 201




    
@app.route('/new_file', methods=['POST'])
def new_file():
    """Follow this body style
        {
            "name": "helloworld.txt",
            "path": "/Users/enistahiraj/Desktop/College/Fall_2020/blockIPFS/files/",
            "chunk_size": "10"
        }
    """
    if port != '5000':
        values = request.get_json()
        if not values:
            response = {
                'message': 'No data found'
            }
            return jsonify(response), 400
        if 'name' not in values or 'path' not in values or 'chunk_size' not in values:
            response = {
                'message': 'Name, path or chunk size was not found'
            }
            return jsonify(response), 400
        
        #get the information to create a new file object
        name = values['name']
        path = values['path']
        chunk_size = values['chunk_size']

        #reset the file object
        file.chunks = []
        file.fat = []
        file.file_size = 0
        file.name = name
        file.path = path
        file.chunk_size = int(chunk_size)
        file.owner = str(port)
        if file.isFile():
            fat_file = {
                'file_name': file.name,
                'file_owner': file.owner,
                'fat': []
            }
            hash_table.fat.append(fat_file)

            #split the file into chunks of data to distribute between peers
            chunk_hashes = file.split_to_chunks()

            MT = MerkleTreeHash()
            root_hash = MT.find_merkle_hash(chunk_hashes)

            #make a new blockchain for the file that was crreated
            new_blockchain = Blockchain('', '')

            #update some of its properties 
            new_blockchain.file_name = file.name
            new_blockchain.file_size = file.file_size
            new_blockchain.chunk_number = len(file.chunks)
            new_blockchain.last_chunk_size = file.file_size%int(chunk_size)
            new_blockchain.root_node = root_hash


            url = 'http://localhost:5000/new-file'
            try:
                response = requests.post(url, json={
                                                    'file_name': new_blockchain.file_name,
                                                    'file_size': new_blockchain.file_size,
                                                    'chunk_number': new_blockchain.chunk_number,
                                                    'last_chunk_size': new_blockchain.last_chunk_size,
                                                    'root_node': new_blockchain.root_node})
                if response.status_code == 400 or response.status_code == 500:
                        print('Sending files declined')
                        return False
            except requests.exceptions.ConnectionError:
                print('connection exception handled')
                return False
        

        url = 'http://localhost:5000/get-dht-size'
        value = requests.get(url)
        json_value = value.json()
        dht_size = json_value['dht_size']
        file.distribute_chunks(int(dht_size))



        #update blockchain files with the new information
        

        
        response = {
            'message': 'File added successfully',
            'file_name': file.name,
            'file_size': file.file_size,
            'file_path': path + name,
            'number_of_chunks': len(file.chunks),
            'chunks': file.print_chunks(),
            'chunk_size': chunk_size,
            'last_chunk_size': file.file_size%int(chunk_size),
            'file_creator': 'localhost:' + str(port)
        }
        return jsonify(response), 201
    response = {
        'message': 'Something went wrong'
    }
    return jsonify(response), 400


@app.route('/new-file', methods=['POST'])
def new_file_main():
    val = request.get_json()
    if not val:
        response = {
            'message': 'Data missing'
        }
    req = ['file_name', 'file_size', 'chunk_number', 'last_chunk_size', 'root_node']
    if not all(field in val for field in req):
        response = {
            'message': 'some data missing'
        }
    #make a new blockchain for the file that was crreated
    new_blockchain = Blockchain('', '')

    #update some of its properties 
    new_blockchain.file_name = val['file_name']
    new_blockchain.file_size = int(val['file_size'])
    new_blockchain.chunk_number = int(val['chunk_number'])
    new_blockchain.last_chunk_size = int(val['last_chunk_size'])
    new_blockchain.root_node = val['root_node']
    #check if this file exists in the blockchain list
    for bc in blockchains:
        if new_blockchain.root_node == bc.root_node:
            response = {
                'message': 'This file exists already'
            }
            return jsonify(response), 400
    blockchains.append(new_blockchain)
    print('calling broadcast')
    broadcast = False
    broadcast_blochchain_list(broadcast)
    response = {
        'message': 'Created new file/blockchain successfully, added to the list and broadcasted it'
    }
    return jsonify(response), 201


@app.route('/get-fat', methods=['GET'])
def get_fat():
    if blockchain.hosting_node == '5000':
        response = {
            'message': 'The hosting node doesnt have a fat'
        }
        return jsonify(response), 400
    response = {
        'FAT': hash_table.fat
    }
    return jsonify(response), 201


@app.route('/update-fat', methods=['POST'])
def update_fat():
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data found'
        }
        return jsonify(response), 400
    required = ['file_name', 'file_path', 'file_size', 'file_owner', 'chunk_id', 'chunk_name', 'chunk_size',
                'chunk_number', 'chunk_path', 'chunk_data', 'chunk_hash', 'chunk_owner', 'peer_key', 'peer_id']
    if not all(key in values for key in required):
        response = {
            'message': 'Some data is missing'
        }
        return jsonify(response), 400
    if values['chunk_owner'] == '5000':
        response = {
            'message': 'port 5000,  make the call in a different port'
        }
        return jsonify(response), 400
    for index, fat in enumerate(hash_table.fat):
        if fat['file_name'] == values['file_name']:
            temp_fat = {
                'chunk_name': values['chunk_name'],
                'chunk_id': values['chunk_id'],
                'chunk_owner': values['chunk_owner'],
                'chunk_path': values['chunk_path'],
                'owner_key': values['peer_key']
            }
            hash_table.fat[index]['fat'].append(temp_fat)
    response = {
        'message': 'Fat Updated Successfully'
    }
    return jsonify(response), 201


# @app.route('/blockchain', methods=['GET', 'POST'])
# def set_blockchain():
#     if request.method == 'POST':
#         values = request.get_json()
#         if not values:
#             response = {
#                 'message': 'No data found'
#             }
#             return jsonify(response), 400
#         required_fields = ['file_name', 'file_path', 'file_size', 'file_owner', 'chunk_id', 'chunk_name', 'chunk_size',
#                         'chunk_number', 'chunk_path', 'chunk_data', 'chunk_hash', 'chunk_owner', 'peer_key', 'peer_id']
#         if not all(field in values for field in required_fields):
#             response = {
#                 'message': 'Some data is missing'
#             }
#             return jsonify(response), 400

        # self.chain = [genesis_block]
        # self.hosting_node = node_id
        # self.public_key = public_key
        # self.root_node = ''
        # self.file_name = ''
        # self.file_size = 0
        # self.file_owner = ''
        # self.chunk_number = 0
        # self.chunk_size = 0
        # self.last_chunk_size = 0

@app.route('/get-blockchain', methods=['POST'])
def get_blockchain():

    values = request.get_json()
    if not values:
        response = {
            'message': 'No data found'
        }
        return jsonify(response), 400
    blockchain_name = values['file_name']
    current_blockchain = Blockchain('', '')
    for temp_blockchain in blockchains:
        if temp_blockchain.file_name == blockchain_name:
            current_blockchain = temp_blockchain
            break

    # chain_snapshot = current_blockchain.chain
    # dict_chain = [block.__dict__.copy() for block in chain_snapshot]
    # for dict_block in dict_chain:
    #     dict_block['data'] = [dt.__dict__ for dt in dict_block['data']]
    response = {
        'chain': current_blockchain.chain,
        'file_name': current_blockchain.file_name,
        'file_size': current_blockchain.file_size,
        'file_owner': current_blockchain.file_owner,
        'chunk_number': current_blockchain.chunk_number,
        'chunk_size': current_blockchain.chunk_size,
        'last_chunk_size': current_blockchain.last_chunk_size
    }
    return jsonify(response), 201



@app.route('/add-chunks', methods=['POST'])
def add_chunks():
    if wallet.public_key == None:
        response = {
            'message': 'No public key'
        }
        return jsonify(response), 400
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data found'
        }
        return jsonify(response), 400
    required_fields = ['file_name', 'file_path', 'file_size', 'file_owner', 'chunk_id', 'chunk_name', 'chunk_size',
                        'chunk_number', 'chunk_path', 'chunk_data', 'chunk_hash', 'chunk_owner', 'peer_key', 'peer_id']
    if not all(field in values for field in required_fields):
        response = {
            'message': 'Missing some data'
        }
        return jsonify(response), 400
    chunk_data = values['chunk_data'].encode("utf-8")
    chunk_hash = hash_string_256(chunk_data)
    signature = wallet.sign_data(values['chunk_id'], chunk_hash, values['chunk_path'], values['peer_key'])
    success = blockchain.add_chunks(values['chunk_id'], chunk_hash, values['chunk_name'], values['chunk_path'], values['chunk_owner'], values['peer_key'], signature)
    if success:
        for chain in blockchains:
            if chain.file_name == values['file_name']:
                chain = blockchain
        broadcast_blochchain_list(False)
        response = {
            'message': 'Successcully added data'
        }
        return jsonify(response), 201
    response = {
        'message': 'Failed to add the data'
    }
    return jsonify(response), 400




@app.route('/send-files', methods=['POST'])
def distribute_file_chunks():
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data found'
        }
        return jsonify(response), 400
    required = ['file_name', 'file_path', 'file_size', 'file_owner', 'chunk_id', 'chunk_name', 'chunk_size',
                'chunk_number', 'chunk_path', 'chunk_data', 'chunk_hash', 'chunk_owner', 'peer_key', 'peer_id']
    if not all(key in values for key in required):
        response = {
            'message': 'Some data is missing'
        }
        return jsonify(response), 400
    if values['chunk_owner'] == '5000':
        response = {
            'message': 'port 5000,  make the call in a different port'
        }
        return jsonify(response), 400
    
    blockchain.file_name = values['file_name']
    blockchain.file_size = values['file_size']
    blockchain.file_owner = values['file_owner']
    blockchain.chunk_number = values['chunk_number']
    blockchain.chunk_size = values['chunk_size']
    blockchain.last_chunk_size = int(values['file_size']) % blockchain.chunk_size
    success = file.write_chunks(values['chunk_id'], values['chunk_path'], values['chunk_name'], values['chunk_data'])
    if success:
        for data in blockchain.open_data:
            if data.id == values['chunk_id']:
                data.miner = values['chunk_owner']
        response = {
            'message': 'File saved successfully'
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
    parser.add_argument('-p', '--port', type=int, default=5000)
    args = parser.parse_args()
    port = args.port
    if port == 5000:
        file = File('', '', 0, '')
        dht = DHT()
        wallet = Wallet(port)
        wallet.create_keys()
        blockchain = Blockchain(wallet.public_key, port)
        blockchains = []
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        path = '/Users/enistahiraj/Desktop/College/Fall_2020/blockIPFScopy/files/{}/'.format(str(port))
        file = File('', '', 0, '')
        wallet = Wallet(port)
        wallet.create_keys()
        blockchain = Blockchain(wallet.public_key, port)
        hash_table = HashTable(blockchain.public_key, str(port), path)
        blockchains = []
        url = 'http://localhost:5000/node'
        try:
            response = requests.post(url, json={'public_key': hash_table.public_key, 'name': hash_table.name, 'path': path})
            if response.status_code == 400 or response.status_code == 500:
                print('Sending files declined')
        except requests.exceptions.ConnectionError:
            print('connection error')

        print(blockchain.public_key)
        app.run(host='0.0.0.0', port=port, debug=True)