import os
import hashlib
import json
import requests
from collections import OrderedDict

from printable import Printable
import merkle_tree
import hash_table
from hash_util import hash_block, hash_string_256
from block import Block 
from data import Data
from verification import Verification
from wallet import Wallet


class Blockchain(Printable):
    def __init__(self, public_key, node_id):
        #create genesis block which will be overwritten if we load from a file
        genesis_block = Block(0, '', '', '', '', '', 0, 0, 0, 0, [], 100)
        #initializing the empty blockchain
        self.chain = [genesis_block]
        #files not mined yet
        self.open_data = []
        self.hosting_node = node_id
        self.public_key = public_key
        self.root_node = ''
        self.file_name = ''
        self.file_size = 0
        self.file_owner = ''
        self.chunk_number = 0
        self.chunk_size = 0
        self.last_chunk_size = 0
        # self.load_data()


    # def load_data(self):
    #     """Loads the current blockchain and open data that is not mined yet to a text file"""
    #     try:
    #         with open('blockchain-{}.txt'.format(self.hosting_node), mode='r') as f:
    #             file_content = f.readlines()
    #             blockchain = json.loads(file_content[0][:-1])
    #             updated_blockchain = []
    #             for block in blockchain:
    #                 converted_data = [Data(ft['id'], ft['hash'], ft['path'], ft['miner'], ft['miner_public_key'], ft['signature']) for ft in block['data']]
    #                 updated_block = Block(block['index'], block['root_node'], block['previous_hash'], block['creator'], block['miner'], block['file_name'], block['file_size'], block['chunk_number'], block['chunk_size'], block['last_chunk_size'], converted_data, block['proof'], block['timestamp'])
    #                 updated_blockchain.append(updated_block)
    #             self.chain = updated_blockchain
    #             open_data = json.loads(file_content[1])
    #             updated_open_data = [] 
    #             for dt in open_data:
    #                 updated_data = Data(dt['id'], dt['hash'], dt['path'], dt['miner'], dt['miner_public_key'], dt['signature'])
    #                 updated_open_data.append(updated_data)
    #             self.open_data = updated_open_data
    #             self.open_data.sort(key=lambda data: data.id, reverse=True)
    #     except IOError:
    #         print('Handled exception')


    # def save_data(self):
    #     """Saves the current blockchain and open data that is not mined yet to a text file"""
    #     try:
    #         with open('blockchain-{}.txt'.format(self.file_name), mode='w') as f:
    #             savable_chain = [block.__dict__ for block in [Block(block_el.index, block_el.root_node, block_el.previous_hash, block_el.creator, block_el.miner, block_el.file_name, block_el.file_size, block_el.chunk_number, block_el.chunk_size, block_el.last_chunk_size, [dt.__dict__ for dt in block_el.data], block_el.proof, block_el.timestamp) for block_el in self.chain]]
    #             f.write(json.dumps(savable_chain))
    #             f.write('\n')
    #             savable_data = [dt.__dict__ for dt in self.open_data]
    #             f.write(json.dumps(savable_data))
    #     except (IOError, IndexError) :
    #         print('Saving Failed')


    def proof_of_work(self, valid_open_data):
        last_block = self.chain[-1]
        last_hash = hash_block(last_block)
        proof = 0
        while not Verification.valid_proof(valid_open_data, last_hash, proof):
            proof += 1
        return proof


    #return the last value of the blockchain
    def get_last_blockchain_value(self):
        if len(self.chain) < 1:
            return None
        return self.chain[-1]


    #clear useless open_data
    def clear_open_data(self, valid_open_data):
        cleaned_data = [data for data in self.open_data if data not in valid_open_data]
        self.open_data = cleaned_data
                    

    #add the chunks to the open_data as transactions
    def add_chunks(self, chunk_id, chunk_hash, chunk_name, chunk_path, miner, miner_public_key, signature):
        """Add new 'Chunks' to the block

            Arguments:
                :chunk_id: the hash of the chunk
                :chunk_hash: the hash of the chunk
                :chunk_name: name of the chunk
                :chunk_path: the chunk path to local file
                :miner: the node who posseses the chunk
                :signature: signature of the miner
        """
        #ordered dictionary of data so it doesn't change
        data = Data(chunk_id, chunk_hash, chunk_path, miner, miner_public_key, signature)
        if not Wallet.verify_data(data):
            print('failing wallet')
            return False
        if len(self.open_data) > 0:
            for openData in self.open_data:
                if openData.id == data.id:
                    return False
        self.open_data.append(data)
        print('added data to open_data')
        print(data)
        self.open_data.sort(key=lambda data: data.id, reverse=True)
        # self.save_data()
        return True
        


    def mine_block(self):
        """Mine a new block in the blockchain

            Parameters:
                :chunk_number: The number of chunks
                :file_name: The name of the file
                :root_node: root node from merkle tree
                :file_size: The size of the file
        """
        if self.public_key == None:
            return False
        miner = self.hosting_node
        #get only valid open_data
        print('length of open data')
        print(len(self.open_data))
        #valid_open_data.sort(key=lambda data: data.id, reverse=True)
        last_block = self.chain[-1]
        hashed_block = hash_block(last_block)
        proof = self.proof_of_work(self.open_data)
        print('printing valid data')
        #print(valid_open_data)

        # response = {
        #     'chain': dict_chain,
        #     'file_name': current_blockchain.file_name,
        #     'file_size': current_blockchain.file_size,
        #     'file_owner': current_blockchain.file_owner,
        #     'chunk_number': current_blockchain.chunk_number,
        #     'chunk_size': current_blockchain.chunk_size,
        #     'last_chunk_size': current_blockchain.last_chunk_size
        # }

        url = 'http://localhost:5000/get-blockchain'
        print(url)
        try:
            response = requests.post(url, json={'file_name': self.file_name})
            response_data = json.loads(response.text)
            temp_blockchain = Blockchain('', '')
            temp_blockchain.chain = response_data['chain']
            chain_snapshot = self.chain
            dict_chain = [block.__dict__.copy() for block in chain_snapshot]
            for dict_block in dict_chain:
                dict_block['data'] = [dt.__dict__ for dt in dict_block['data']]
            print('printing the raw response data')
            print(response_data)
            print('########################')
            print('printing chain from response data')
            print(temp_blockchain.chain)
            print('printing chain from current blockchain')
            print(dict_chain)

            if temp_blockchain.chain == dict_chain:
                print('this worked')
            # temp_blockchain.file_name = blockchain_data['file_name']
            # temp_blockchain.file_size = blockchain_data['file_size']
            # temp_blockchain.file_owner = blockchain_data['file_owner']
            # temp_blockchain.chunk_number = blockchain_data['chunk_number']
            # temp_blockchain.chunk_size = blockchain_data['chunk_size']
            # temp_blockchain.last_chunk_size = blockchain_data['last_chunk_size']



            block = Block(len(self.chain), self.root_node, hashed_block, self.file_owner, miner, self.file_name, self.file_size, self.chunk_number, self.chunk_size, self.last_chunk_size, self.open_data, proof)
            for dt in block.data:
                if not Wallet.verify_data(dt):
                    return None
            #check if this file exists in blockchain(later to be changed to a hash)
            for blck in self.chain:
                if blck.index != 0 and block.file_name in blck.file_name:
                    print('This file already exists in the blockchain')
                    return None
            if last_block.previous_hash == block.previous_hash:
                print('This file already exists in the blockchain')
                return None
            self.chain.append(block)
            # self.save_data()
            print('**********************************************************')
            print('printing chain from response data')
            print(response_data)
            chain_snapshot = self.chain
            dict_chain = [block.__dict__.copy() for block in chain_snapshot]
            for dict_block in dict_chain:
                dict_block['data'] = [dt.__dict__ for dt in dict_block['data']]
            print('printing chain from current blockchain')
            print(dict_chain)
            return block
            
        except requests.exceptions.ConnectionError:
            print('connection exception handled')
        


    #print the blockchain
    def print_open_data(self):
        print('*********************printing open_data************************')
        for elem in self.open_data:
            print(elem)

     #print the blockchain
    def print_blockchain(self):
        print('*********************printing blockchain************************')
        for block in self.chain:
            print(block)


    







        
    

