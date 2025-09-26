from typing import List, Dict, Any
import time
import hashlib
import json

class Blockchain:
    """A simple blockchain to track ticket purchases and verification logs."""

    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self.pending_transactions: List[Dict[str, Any]] = []
        self.create_block(previous_hash="0") # Create the genesis block

    def create_block(self, previous_hash: str):
        """Mines a new block and adds it to the chain."""
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "transactions": self.pending_transactions,
            "previous_hash": previous_hash,
            "hash": ""
        }
        # Calculate hash before appending
        block["hash"] = self.hash_block(block)
        self.pending_transactions = []
        self.chain.append(block)
        return block

    def add_transaction(self, transaction: dict):
        """Adds a new transaction (purchase or verification) to the list of pending transactions."""
        self.pending_transactions.append(transaction)
        return self.last_block["index"] + 1

    @property
    def last_block(self):
        """Returns the last block in the chain."""
        return self.chain[-1]

    @staticmethod
    def hash_block(block: Dict[str, Any]) -> str:
        """Creates a SHA-256 hash of a Block. Uses sort_keys=True for deterministic hashing."""
        temp = block.copy()
        temp.pop("hash", None) # Remove 'hash' key before hashing
        # The FIX: Use json.dumps with sort_keys=True for deterministic string representation
        block_string = json.dumps(temp, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
