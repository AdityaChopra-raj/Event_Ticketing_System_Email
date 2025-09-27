import hashlib
import time
from typing import List, Dict, Any

class Blockchain:
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self.current_transactions: List[Dict[str, Any]] = []
        self.create_genesis_block()

    # -----------------------
    # Genesis Block
    # -----------------------
    def create_genesis_block(self):
        genesis_block = {
            'index': 1,
            'timestamp': time.time(),
            'transactions': [],
            'proof': 100,
            'previous_hash': '1'
        }
        self.chain.append(genesis_block)

    # -----------------------
    # Block properties
    # -----------------------
    @property
    def last_block(self):
        return self.chain[-1] if self.chain else None

    # -----------------------
    # Hash a block
    # -----------------------
    @staticmethod
    def hash(block: Dict[str, Any]) -> str:
        """
        Creates a SHA-256 hash of a block
        """
        block_string = str(sorted(block.items())).encode()
        return hashlib.sha256(block_string).hexdigest()

    # -----------------------
    # Proof of Work
    # -----------------------
    def proof_of_work(self, last_proof: int) -> int:
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof: int, proof: int) -> bool:
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    # -----------------------
    # Create new block
    # -----------------------
    def create_block(self, proof: int, previous_hash: str = None) -> Dict[str, Any]:
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.last_block)
        }
        self.current_transactions = []
        self.chain.append(block)
        return block

    # -----------------------
    # Add a transaction
    # -----------------------
    def add_transaction(self, tx_type: str, event: str, ticket_id: str, email: str, num_tickets: int):
        """
        Add a PURCHASE or VERIFY transaction
        """
        transaction = {
            "type": tx_type,            # "PURCHASE" or "VERIFY"
            "event": event,
            "ticket_id": ticket_id,
            "email": email,
            "num_tickets": num_tickets
        }
        self.current_transactions.append(transaction)
        return transaction

    # -----------------------
    # Audit function
    # -----------------------
    def get_ticket_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns a dictionary of all tickets with their current status:
        {
            ticket_id: {
                "event": event_name,
                "email": purchaser_email,
                "purchased": total_tickets_bought,
                "checked_in": total_guests_checked_in
            }
        }
        """
        tickets = {}
        for block in self.chain:
            for tx in block.get("transactions", []):
                tid = tx.get("ticket_id")
                if not tid:
                    continue
                if tid not in tickets:
                    tickets[tid] = {
                        "event": tx.get("event"),
                        "email": tx.get("email"),
                        "purchased": 0,
                        "checked_in": 0
                    }
                if tx["type"] == "PURCHASE":
                    tickets[tid]["purchased"] += tx.get("num_tickets", 0)
                elif tx["type"] == "VERIFY":
                    tickets[tid]["checked_in"] += tx.get("num_tickets", 0)
        return tickets
