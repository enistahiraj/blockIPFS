class Chunk:
    def __init__(self, id, name, path, data, chunk_hash, stored=False, miner=''):
        self.id = id
        self.name = name
        self.path = path
        self.data = data
        self.hash = chunk_hash
        self.stored = stored
        self.miner = miner
