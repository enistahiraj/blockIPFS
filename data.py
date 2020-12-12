from collections import OrderedDict
from printable import Printable

class Data(Printable):
    def __init__(self, id, hash, path, miner, public_key, signature):
        self.id = id
        self.hash = hash
        self.path = path
        self.miner = miner
        self.miner_public_key = public_key
        self.signature = signature


    def to_ordered_dict(self):
        return OrderedDict([('id', self.id), ('hash', self.hash), ('path', self.path), ('miner', self.miner)])