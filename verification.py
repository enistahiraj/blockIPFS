from hash_util import hash_string_256, hash_block

class Verification:

    @staticmethod
    def valid_proof( valid_open_data, last_hash, proof):
        guess = (str([vdata.to_ordered_dict() for vdata in valid_open_data]) + str(last_hash) + str(proof)).encode()
        guess_hash = hash_string_256(guess)
        return guess_hash[0:2] == '00'

    @classmethod
    def verify_chain(cls, blockchain):
        """Verify the blockchain and return TRUE if its valid, else return FALSE
        """
        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != hash_block(blockchain[index - 1]):
                return False
            if not cls.valid_proof(block.data, block.previous_hash, block.proof):
                print('Proof of work not valid')
                return False
        return True

    