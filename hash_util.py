import hashlib
import json


def hash_string_256(string):
    return hashlib.sha256(string).hexdigest()


def hash_block(block):
    """Hashes a block and returns a string representation of it.

        Parameters:
            :block: The block being hashed
    """
    hashable_block = block.__dict__.copy()
    hashable_block['data'] = [data.to_ordered_dict() for data in hashable_block['data']]
    return  hash_string_256(json.dumps(hashable_block, sort_keys=True).encode())