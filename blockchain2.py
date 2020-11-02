# https://towardsdatascience.com/build-your-own-blockchain-protocol-for-a-distributed-ledger-54e0a92e1f10
import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request

class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()
        self.new_block(previous_hash = '1', proof = 100) # create genesis block

    def register_node(self, address): # register a new node on the network
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):  # iterate through the blockchain, calling valid_proof() to verify
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}]')
            print(f'{block}')
            print("\n-----------\n")

            if block['previous_hash'] != self.hash(last_block): # check hash
                return False

            if not self.valid_proof(last_block['proof'], block['proof']): # check Proof of Work
                return False

            last_block = block
            current_index += 1

        return True # always returns True?
    
    def new_block(self, proof, previous_hash): # create a new block in the blockchain, copy transactions, clear the set
        block = {
            'index' : len(self.chain) + 1,
            'timestamp' : time(),
            'transactions' : self.current_transactions,
            'proof': proof,
            'previous_hash' : previous_hash or self.hash(self.chain[-1]), # ?
            }

        self.current_transactions = []  # reset list of transactions to empty
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount): # add a new transaction to the list
        self.current_transactions.append({
            'sender' : sender,
            'recipient' : recipient,
            'amount' : amount,
            })
        return self.last_block['index'] + 1
    
    @property
    def last_block(self): # return the last block in the chain
        return self.chain[-1]

    @staticmethod
    def hash(block): # "orders the dictionary"?
        block_string = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(block_string.hexdigest()

    def proof_of_work(self, last_proof): # check that mining has yielded correct proof, call valid_proof()
    # here: find p' st hash (pp') contains leading 4 zeroes
    # let p = previous  p' (proof), and p' = new proof
        proof = 0
                              
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof
                              
    @staticmethod
    def valid_proof(last_proof, proof): # check that block's "solution" solves the proble 
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] = "0000"
