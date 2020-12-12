class HashTable:
    def __init__(self,public_key, name, path):
        self.public_key = public_key
        self.private_key = None
        self.name = name
        self.path = path
        self.fat = []
        self.MAX = 100
        self.files = [[] for i in range(self.MAX)]


    def get_hash(self, key):
        hash = 0
        for char in key:
            hash += ord(char)
        return hash % self.MAX


    def __getitem__(self, key):
        h = self.get_hash(key)
        for element in self.files[h]:
            if element[0] == key:
                return element[1]


    def __setitem__(self, key, val):
        h = self.get_hash(key)
        found = False
        for idx, element, in enumerate(self.files[h]):
            if len(element) == 2 and element[0] == key:
                self.files[h][idx] = (key, val)
                found = True
                break
        if not found:
            self.files[h].append((key,val))


    def __delitem__(self, key):
        h = self.get_hash(key)
        for index, element in enumerate(self.files[h]):
            if element[0] == key:
                del self.files[h][index]


#t = HashTable()
#t['march 6'] = 120
#t['february 4'] = 44
#del t['march 6']
#print(t.files)
