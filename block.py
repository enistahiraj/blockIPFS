from time import time
from printable import Printable

class Block(Printable):
    def __init__(self, index, root_node, previous_hash, creator, miner, file_name, file_size, chunk_number, chunk_size, last_chunk_size, data, proof, time=time()):
         self.index = index
         self.root_node = root_node
         self.previous_hash = previous_hash
         self.creator = creator
         self.miner = miner
         self.file_name = file_name
         self.file_size = file_size
         self.chunk_number = chunk_number
         self.chunk_size = chunk_size
         self.last_chunk_size = last_chunk_size
         self.data = data
         self.proof = proof
         self.timestamp = time
