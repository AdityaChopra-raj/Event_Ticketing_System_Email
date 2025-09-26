from typing import List, Dict, Any
import time
import hashlib

class Blockchain:
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self.pending_transactions: List[Dict[str, Any]] = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = {
            "index": 0,
            "timestamp": time.time(),
            "transactions": [],
            "previous_hash": "0",
            "hash": "0"
        }
        self.chain.append(genesis_block)

    def add_transaction(self, **transaction_data):
        self.pending_transactions.append(transaction_data)

    def mine_block(self):
        previous_block = self.chain[-1]
        block = {
            "index": len(self.chain),
            "timestamp": time.time(),
            "transactions": self.pending_transactions.copy(),
            "previous_hash": previous_block["hash"]
        }
        block["hash"] = self.hash_block(block)
        self.chain.append(block)
        self.pending_transactions = []

    def hash_block(self, block: Dict[str, Any]) -> str:
        block_str = f"{block['index']}{block['timestamp']}{block['transactions']}{block['previous_hash']}"
        return hashlib.sha256(block_str.encode()).hexdigest()
