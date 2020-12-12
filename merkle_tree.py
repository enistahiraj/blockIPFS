import hashlib
import json
PATH = '/Users/enistahiraj/Desktop/College/Fall_2020/blockIPFS/files/'

class MerkleTreeHash(object):
    def __init__(self):
        pass


    def find_merkle_hash(self, file_hashes):
        #print('file hashes are')
        #print(file_hashes)
        blocks = []

        if not file_hashes:
            raise ValueError('Missing required file hashes for computing the merkle tree hash')

        
        for m in file_hashes:
            blocks.append(m)
            #print(m)
        #sorting the hashes
        file_hashes.sort()
        block_length = len(blocks)

        #make sure there are even nr. of leafs
        while block_length % 2 != 0:
            blocks.append(blocks[-1])
            block_length = len(blocks)

        hashed_merkle = []
        for k in [blocks[x:x+2] for x in range(0, len(blocks), 2)]:
            hasher = hashlib.sha256()
            hasher.update((k[0]+k[1]).encode())
            hashed_merkle.append(hasher.hexdigest())

        if len(hashed_merkle) == 1:
            return hashed_merkle[0][0:64]
        else:
            return self.find_merkle_hash(hashed_merkle)


            
    
    #cls = MerkleTreeHash()
    #print(file_hashes)
    #mk = cls.find_merkle_hash(file_hashes)

    #print('file hashes are')
    #print(file_hashes)
    #print('merkle tree root hash is')
    #print(mk)
