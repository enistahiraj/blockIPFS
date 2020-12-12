import os
from uuid import uuid4

from hash_table import HashTable 
from merkle_tree import MerkleTreeHash
from blockchain import Blockchain
from hash_util import hash_string_256
from data import Data
from verification import Verification
from wallet import Wallet

#GLOBAL VARIABLES
CHUNK_SIZE = 10
PATH = '/Users/enistahiraj/Desktop/College/Fall_2020/blockIPFS/files/'


class Node(object):
    
    def __init__(self):
        self.hashTable = HashTable()
        #self.wallet.public_key = str(uuid4())
        self.wallet = Wallet()
        self.wallet.create_keys()
        self.blockchain = Blockchain(self.wallet.public_key)

    

    #get user choice from the main menu
    def get_user_choice(self):
        user_input = input('Your choice:')
        return user_input


    #print the blockchain
    def print_blockchain_elements(self):
        print('*********************printing blockchain************************')
        for block in self.blockchain.chain:
            print(block)

    #print the blockchain
    def print_open_data_elements(self, open_data):
        print('*********************printing open_data************************')
        for elem in open_data:
            print(elem)


    #add the chunks to the open_data as transactions
    def add_chunks_to_open_data(self, chunk_id, chunk_path, miner, signature):
        """Add new 'Transactions' to the blockchain

            Arguments:
                :chunk_id: the hash of the chunk
                :chunk_path: the chunk path to local file
                :miner: the node who posseses the chunk
        """
        exist = False
        #ordered dictionary of data so it doesn't change
        data = Data(chunk_id, chunk_path, miner, signature)
        if not Wallet.verify_data(data):
            exist = True
        if len(self.blockchain.open_data) > 0:
            for openData in self.blockchain.open_data:
                if openData.id == data.id:
                    exist = True
        if not exist:
            self.blockchain.open_data.append(data)
            self.blockchain.open_data.sort(key=lambda data: data.id, reverse=True)
        self.blockchain.save_data()


    #split the file into chunks and return the number of chunks
    def split_to_chunks(self, file_name, list_nodes):
        """This function splits a file into chunks then returns the number of chunks and a list of hashes of these chunks

            Parameter:
                :file_name: the name of the file to split
        """

        file_hashes = []
        file_number = 1
        file_name = file_name
        file_size = os.stat(PATH + file_name).st_size
        last_chunk_size = file_size % CHUNK_SIZE
        num = 0


        with open(PATH + file_name, 'rb') as infile:
            while True:
                # Read 1000byte chunks of the file, except for the last chunk
                if num == self.blockchain.file_size / CHUNK_SIZE:
                    chunk = infile.read(last_chunk_size)
                    if not chunk: break
                else:
                    chunk = infile.read(CHUNK_SIZE)
                    if not chunk: break

                
                node_to_store = 0 #file_number % len(list_nodes)
                folder_name = self.wallet.public_key[:8]

                if os.path.isdir(PATH + folder_name):
                    #write the chunks of data into new files
                    chunk_file = open(PATH + folder_name + '/' + file_name + '_chunk_' + str(file_number) + '.txt', 'wb+')
                    chunk_file.write(chunk)

                    #hash the chunks to put in merkle tree
                    hashed_data = hash_string_256(chunk)
                    file_hashes.append(hashed_data)

                    #add the hash and path of chunk to the node responsible for it
                    chunkPath = PATH + folder_name + '/' + file_name + '_chunk_' + str(file_number) + '.txt'
                    list_nodes[node_to_store].hashTable[hashed_data] = chunkPath

                    #add to open_data
                    signature = self.wallet.sign_data(hashed_data, chunkPath, self.wallet.public_key)
                    self.add_chunks_to_open_data(hashed_data, chunkPath, self.wallet.public_key, signature)
                    
                else:
                    #make directory if directory doesn't exist
                    os.mkdir(PATH + folder_name + '/')

                    #write the chunks of data into new files
                    chunk_file = open(PATH + folder_name + '/' + file_name + '_chunk_' + str(file_number) + '.txt', 'wb+')
                    chunk_file.write(chunk)

                    #hash the chunks to put in merkle tree
                    hashed_data = hash_string_256(chunk)
                    file_hashes.append(hashed_data)

                    #add the hash and path of chunk to the node responsible for it
                    chunkPath = PATH + folder_name + '/' + file_name + '_chunk_' + str(file_number) + '.txt'
                    list_nodes[node_to_store].hashTable[hashed_data] = chunkPath

                    #add to open_data
                    signature = self.wallet.sign_data(hashed_data, chunkPath, self.wallet.public_key)
                    self.add_chunks_to_open_data(hashed_data, chunkPath, self.wallet.public_key, signature)
                file_number += 1
        return (file_number - 1, file_hashes)

    #get the chunks of files to add to the blockchain
    def get_chunks(self, chunk_id, file_name):
        """Returns the data inside the chunk

            Parameters:
                :chunk_id: the number(id) of the chunk we want to access
                :file_name: the name of the file to which the chunk belongs to
        """
        name_file = file_name + '_chunk_' + str(chunk_id) + '.txt'
        with open(PATH + name_file, 'rb') as infile:
            chunk_data = infile.read(CHUNK_SIZE)
        return chunk_data


    #get the file name from the user
    def get_fileName_fileSize(self):
        """Returns the name of the file and the size of the file being added to the blockchain"""
        #user_input = input('Please enter the name of the file you wish to add to the blockchain:')
        fileName = 'helloworld.txt' #user_input
        if os.path.isfile(PATH + fileName):
            fileSize = os.stat(PATH + fileName).st_size
            return (fileName, 88)
        else:
            return (None, None)

    DHT = HashTable()


    def get_blockchain_info(self, list_nodes):
        self.blockchain.file_name, self.blockchain.file_size = self.get_fileName_fileSize()
        if self.blockchain.file_name == None or self.blockchain.file_size == None:
            print("File doesn't exist. Please choose a different file!")
        else:
            """Get the number of chunks and a list of the hashes of these chunks"""
            self.blockchain.chunk_number, file_hashes = self.split_to_chunks(self.blockchain.file_name, list_nodes)

            """Find the root hash from the given list of chunk hashes"""
            MerkleTree = MerkleTreeHash()
            self.blockchain.root_hash = MerkleTree.find_merkle_hash(file_hashes)


    def listen_for_input(self):
        waiting_for_input = True
        while waiting_for_input:
            print('Please enter:')
            print('1: Add a new file')
            print('m: Mine blocks')
            print('2: Print the blockchain')
            print('3: Print open_data')
            print('4: Create a Wallet')
            print('5: Load a Wallet')
            print('6: Save Wallet')
            print('q: quit')
            user_choice = self.get_user_choice()
            if user_choice == '1':
                self.blockchain.file_name, self.blockchain.file_size = self.get_fileName_fileSize()
                if self.blockchain.file_name == None or self.blockchain.file_size == None:
                    print("File doesn't exist. Please choose a different file!")
                    continue
                else:
                    """Get the number of chunks and a list of the hashes of these chunks"""
                    #self.blockchain.chunk_number, file_hashes = self.split_to_chunks(self.blockchain.file_name)

                    """Find the root hash from the given list of chunk hashes"""
                    MerkleTree = MerkleTreeHash()
                    #self.blockchain.root_hash = MerkleTree.find_merkle_hash(file_hashes)
            elif user_choice == 'm':
                if self.wallet.private_key != Node:
                    if self.blockchain.chunk_number != None or self.blockchain.file_name != None or self.blockchain.root_hash != None or self.blockchain.file_size != None:
                        self.blockchain.mine_block()
                    else:
                        print("Can't mine because missing one of [chunk_number, file_name, root_hash, file_size]")
            elif user_choice == '2':
                self.print_blockchain_elements()
            elif user_choice == '3':
                self.print_open_data_elements(self.blockchain.open_data)
            elif user_choice == '4':
                self.wallet.create_keys()
                self.blockchain = Blockchain(self.wallet.public_key)
            elif user_choice == '5':
                self.wallet.load_keys()
                self.blockchain = Blockchain(self.wallet.public_key)
            elif user_choice == '6':
                self.wallet.save_keys()
            elif user_choice == 'q':
                waiting_for_input = False
            elif user_choice == 'd':
                print(self.blockchain.open_data)
            else:
                print('Input was invalid')
            if not Verification.verify_chain(self.blockchain.chain):
                self.print_blockchain_elements()
                print('Invalid blockchain')
                break 
"""
if __name__ == '__main__':
    node = Node()
    list_nodes = []
    list_nodes.append(node)
    node.listen_for_input()

number_nodes = 5
#Holds list of nodes
list_node = [[] for i in range(0, number_nodes)]

j = 1
for i in range(len(list_node)):
    node = Node('Node{}'.format(str(j)))
    list_node[i] = node
    j += 1

#list_nodes = []
#def add_nodes(number):
    #for i in range(number):
        #node = Node('node{}'.format(str(i)))
        #list_nodes.append(node)
"""

#number = 6
#add_nodes(number)
#for i in range(number):
    #print(list_nodes[i].hashTable.arr)