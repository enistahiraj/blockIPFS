import os
import binascii
import json
import requests

from printable import Printable
from hash_util import hash_string_256
from wallet import Wallet
from chunk import Chunk

class File(Printable):
    def __init__(self, name, path, chunk_size, owner):
        self.name = name
        self.path = path
        self.chunk_size = chunk_size
        self.chunks = []
        self.fat = []
        self.file_size = 0
        self.owner = owner


    #check if this file exists
    def isFile(self):
        """Check if this file exists and return it's size"""
        find_file = self.path + self.name
        print(find_file)
        print(self.file_size)
        if os.path.isfile(find_file):
            self.file_size = os.stat(find_file).st_size
            print(find_file)
            print(self.file_size)
            return True
        else:
            return False


    #update the fat of the file
    def update_fat(self, chunk_name, peer_name, path_to_file):
        data = {
            'file_name': self.name,
            'chunk_name': chunk_name,
            'peer_name': peer_name,
            'path_to_file': path_to_file
        }
        self.fat.append(data)


    def split_to_chunks(self):
        """Split the file into chunks and add it to the list of chunks"""
        file_number = 1
        self.file_size = os.stat(self.path + self.name).st_size
        last_chunk_size = self.file_size % self.chunk_size
        num = 0

        with open(self.path + self.name, 'rb') as infile:
            while True:
                # Read chunk_size(bytes ex. 'chunk_size=10' = '1000bytes') chunks of the file, except for the last chunk
                if num == self.file_size / self.chunk_size:
                    read_chunk = infile.read(last_chunk_size)
                    if not read_chunk:
                        break
                    else:
                        chunk_name = self.name + '_chunk_' + str(file_number)
                        chunk_hash = hash_string_256(read_chunk)
                        chunk = Chunk(file_number, chunk_name, '', read_chunk, chunk_hash)
                        self.chunks.append(chunk)
                else:
                    read_chunk = infile.read(self.chunk_size)
                    if not read_chunk:
                        break
                    else:
                        chunk_name = self.name + '_chunk_' + str(file_number)
                        chunk_hash = hash_string_256(read_chunk)
                        chunk = Chunk(file_number, chunk_name, '', read_chunk, chunk_hash)
                        self.chunks.append(chunk)
                file_number += 1
            chunk_hashes = []
            for chunk in self.chunks:
                chunk_hashes.append(chunk.hash)
            return chunk_hashes


    def write_chunks(self, chunk_id, chunk_path, chunk_name, chunk_data):
        #write the chunks of data into new files
        encoded_data = chunk_data.encode("utf-8")
        chunk_file = open(chunk_path + chunk_name, 'wb+')
        chunk_file.write(encoded_data)
        return True


    def distribute_chunks(self, dht_size):
        number_of_peers = dht_size
        for chunk in self.chunks:
            hash = chunk.hash
            file_number = 0
            for char in hash:
                file_number += ord(char)
            if file_number == 0:
                file_number += 1
            node_to_store = file_number % number_of_peers
            val = requests.post('http://localhost:5000/get-peer', json={'node_to_store': node_to_store})
            readable_value = val.json()
            peer_key = readable_value['peer_key']
            peer_name = readable_value['peer_name']
            peer_path = readable_value['peer_path']
            chunk_data = chunk.data.decode("utf-8")
            chunk_hash = hash_string_256(chunk.data)
            if self.post_request(peer_name, '/send-files', self.name, self.path, self.file_size, self.owner, chunk.id, chunk.name, self.chunk_size, len(self.chunks), peer_path, chunk_data, chunk_hash, peer_name, peer_key, node_to_store):
                print('Files were sent')
                if self.post_request('5000', '/update-dht', self.name, self.path, self.file_size, '5000', chunk.id, chunk.name, self.chunk_size, len(self.chunks), peer_path, chunk_data, chunk_hash, peer_name, peer_key, node_to_store):
                    print('DHT updated')
                if self.post_request(self.owner, '/update-fat', self.name, self.path, self.file_size, self.owner, chunk.id, chunk.name, self.chunk_size, len(self.chunks), peer_path, chunk_data, chunk_hash, peer_name, peer_key, node_to_store):
                    print('FAT updated')
                if self.post_request(peer_name, '/add-chunks', self.name, self.path, self.file_size, self.owner, chunk.id, chunk.name, self.chunk_size, len(self.chunks), peer_path, chunk_data, chunk_hash, peer_name, peer_key, node_to_store):
                    print('added to open data')
        return True
    
    def post_request(self, peer_name, url_extension, file_name, file_path, file_size, file_owner, 
                    chunk_id, chunk_name, chunk_size, chunk_number, chunk_path, chunk_data, chunk_hash, chunk_owner, peer_key, peer_id):
        url = 'http://localhost:{}'.format(peer_name + url_extension)
        print(url)
        try:
            response = requests.post(url, json={'file_name': file_name,
                                                'file_path': file_path,
                                                'file_size': file_size,
                                                'file_owner': file_owner,
                                                'chunk_id': chunk_id, 
                                                'chunk_name': chunk_name,
                                                'chunk_size': chunk_size,
                                                'chunk_number': chunk_number, 
                                                'chunk_path': chunk_path, 
                                                'chunk_data': chunk_data, 
                                                'chunk_hash': chunk_hash,
                                                'chunk_owner': chunk_owner,
                                                'peer_key': peer_key,
                                                'peer_id': peer_id})
            if response.status_code == 400 or response.status_code == 500:
                print('Sending files declined')
                return False
        except requests.exceptions.ConnectionError:
            print('connection exception handled')
            return False
        return True
        





    def print_chunks(self):
        dict_list = [str(ls.__dict__.copy()) for ls in self.chunks]
        return dict_list










        # else:
        #     #make directory if directory doesn't exist
        #     os.mkdir(self.path + folder_name + '/')

        #     #write the chunks of data into new files
        #     chunk_file = open(self.path + folder_name + '/' + self.name + '_chunk_' + str(file_number) + '.txt', 'wb+')
        #     chunk_file.write(chunk)

        #     #hash the chunks to put in merkle tree
        #     hashed_data = hash_string_256(chunk)
        #     file_hashes.append(hashed_data)

        #     #add the hash and path of chunk to the node responsible for it
        #     chunkPath = self.path + folder_name + '/' + self.name + '_chunk_' + str(file_number) + '.txt'
        #     list_nodes[node_to_store].hashTable[hashed_data] = chunkPath

        #     #add to open_data
        #     signature = self.wallet.sign_data(hashed_data, chunkPath, self.wallet.public_key)
        #     self.add_chunks_to_open_data(hashed_data, chunkPath, self.wallet.public_key, signature)
