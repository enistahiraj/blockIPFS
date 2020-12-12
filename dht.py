import os
import json
import requests
from hash_table import HashTable

class DHT:
    def __init__(self):
        self.peer_nodes = []
        

    def add_peer_nodes(self, node):
        self.peer_nodes.append(node)
    

    def remove_peer_node(self, node):
        self.peer_nodes.remove(node)


    def get_peer_nodes(self):
        dict_list = [ls.__dict__.copy() for ls in self.peer_nodes]
        return dict_list
