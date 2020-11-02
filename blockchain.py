"""
Albert
September 2020
based on: https://hackernoon.com/learn-blockchains-by-building-one-117428612f46
"""

import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
import requests
from flask import Flask, jsonify, request

class Blockchain:
    def __init__(self):
        self.chain =[]
        self.currentTransactions = []
        self.nodes = set()

        self.newBlock(previousHash = '1', proof = 100)
        # create a genesis block

    def registerNode(self, address):
        """
        adds a new node to the list of nodes
        arguments:
            address - str, address of node
        returns:
            None
        """
        parsedUrl = urlparse(address)
        if parsedUrl.netloc:
            self.nodes.add(parsedUrl.netloc)
        elif parsedUrl.path:
            self.nodes.add(parsedUrl.path)
            # acccepts a URL without "scheme" i.e. no http:// -
        else:
            raise ValueError('Invalid URL')

    def validChain(self, chain):
        """
        determine if a version of the blockchain is valid
        arguments:
            chain - Blockchain, a blockchain
        returns:
            boolean for validity
        """

        lastBlock = chain[0]
        currentIndex = 1

        while currentIndex < len(chain):
            block = chain[currentIndex]
            print(f'{lastBlock}')
            print(f'{block}')
            print("\n___________\n")

            lastBlockHash = self.hash(lastBlock)
            if block['previousHash'] != lastBlockHash:
                return False
            # checking if the hash of the last block is correct

            if not self.validProof(lastBlock['proof'], block['proof'], lastBlockHash):
                return False
            # checking if the PoW is correct

            lastBlock = block
            currentIndex += 1

        return True

    def resolveConflicts(self):
        """
        consensus algorithm, replacing conflicting chain versions with the longest available
        arguments:
            self?
        returns:
            boolean, was the chain replaced?
        """
        
        neighbours = self.nodes
        newChain = None
        maxLength = len(self.chain)

        for nodes in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.statusCode == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > maxLength and self.validChain(chain):
                    maxLength = length
                    newChain = chain

        if newChain:
            self.chain = newChain
            return True
        
        return False
    
    def newBlock(self, proof, previousHash):
        # initializes new block, appends it to the chain
        # each block has an index, timestamp, list of transactions, proof, and hash of the previous block
        # proof (int, given by PoW), previousHash (optional, str, hash of previous block), returns a new block (dict)
        # consider organizing arguments / parameters and returns in 'docstrings'

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.currentTransactions,
            'proof': proof,
            'previousHash': previousHash or self.hash(self.chain[-1]) 
        }

        self.currentTransactions = []
        # resets the list of transactions

        self.chain.append(block)
        return block

    def newTransaction(self, sender, recipient, amount):
        # appends a transaction to the list of transations - will enter the next block
        # sender (str, address of sender), recipient (str, address of recipient), amount (int, amount), returns index of transaction block (int)
        self.currentTransactions.append(
            {
                'sender': sender,
                'recipient': recipient,
                'amount': amount,
            }
        )
        return self.lastBlock['index'] + 1
    
    @staticmethod
    # like a class level method; doesn't access Blockchain class properties - but makes sense that it belongs here
    def hash(block):
        # hashes a block (SHA-256)
        # block (dict, block), returns hash (str)

        blockString = json.dumps(block, sort_keys = True).encode()
        # here, we're ordering the dictionary to ensure consistency of hashes

        return hashlib.sha256(blockString).hexdigest()


    @property
    # adds special functionality to last_block() method
    def lastBlock(self):
        # returns the last block in the chain
        return self.chain[-1]

    def PoW(self, lastProof):
        """
        PoW in a nutshell: find a numerical solution to a prolem that's hard to solve but easy to verify
        in Bitcoin, the PoW algorithm is called "HashCash"
        here: find a number p such that when hashed with the previous block's solution, a hash with four leading zeroes is produced
        """
        
        proof = 0
        while self.validProof(lastProof, proof) is False:
            proof += 1
        
        return proof

    @staticmethod
    def validProof(lastProof, proof):
        """
        validates the proof i.e. does hash(lastProof, proof) contain four leading zeroes
        arguments:
            lastProof - int, previous proof
            proof - int, current proof
        returns:
            a boolean indicating validity
        """

        attempt = f'{lastProof}{proof}'.encode()
        attemptHash = hashlib.sha256(attempt).hexdigest()
        
        return attemptHash[:4] == "0000"
        # modulate difficulty by adding zeroes, or other character patterns

    # setting up our blockchain like an API, for interaction via HTTP

app = Flask(__name__)
# "instantiates our node"

nodeIdentifier = str(uuid4()).replace('-', '')
# generates a globally unique address for this node

blockchain = Blockchain()
# instatiates a blockchain

@app.route("/mine", methods = ['GET'])
# we call these endpoints, here we have a GET request
def mine():
    lastBlock = blockchain.lastBlock
    lastProof = lastBlock['proof']
    proof = blockchain.PoW(lastProof)
    # run the PoW algo to find the next proof

    blockchain.newTransaction(
        sender = '0',
        recipient = nodeIdentifier,
        amount = 1,
    )
    # a reward of one coin is mined, we'll designate the sender as '0'
    
    previousHash = blockchain.hash(lastBlock)
    block = blockchain.newBlock(proof, previousHash)
    # forging a new block and adding it to the chain
    
    response = {
        'message': 'New block forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previousHash': block['previousHash']
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods = ['POST'])
def newTransaction():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    # checking that all required fields are in the POST'ed data

    index = blockchain.newTransaction(values['sender'], values['recipient'], values['amount'])
    # creating a new transaction

    reponse = {'message': f'Adding transaction to block {index}...'}
    return jsonify(response), 201

@app.route('/chain', methods = ['GET'])
# endpoint returning the full blockchain
def fullChain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)
# server run on port 5000
