import hashlib, json, time
from typing import List, Dict, Any

class Blockchain:
    """Immutable ledger to record ticket PURCHASE and VERIFY transactions."""

    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self.current_transactions: List[Dict[str, Any]] = []
        # Genesis block
        self.create_block(proof=100, previous_hash='1')

    def create_block(self, proof: int, previous_hash: str) -> Dict[str, Any]:
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash
        }
        # Reset the list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block

    @property
    def last_block(self) -> Dict[str, Any]:
        if not self.chain:     # Safe even if chain is empty
            return {}
        return self.chain[-1]

    def add_transaction(self, tx_type: str, event: str,
                        ticket_id: str, email: str, num: int):
        """Add a transaction to the next block to be mined."""
        self.current_transactions.append({
            'type': tx_type,   # PURCHASE or VERIFY
            'event': event,
            'ticket_id': ticket_id,
            'email': email,
            'num': num,
            'timestamp': time.time()
        })

    @staticmethod
    def hash(block: Dict[str, Any]) -> str:
        # Deterministic hash
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

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

    # ---------- Audit / Status ----------
    def get_ticket_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Rebuild real-time status of each ticket ID:
        how many purchased, how many guests checked-in.
        """
        status = {}
        for block in self.chain:
            for tx in block.get('transactions', []):
                tid = tx['ticket_id']
                if tid not in status:
                    status[tid] = {
                        'event': tx['event'],
                        'email': tx['email'],
                        'purchased': 0,
                        'checked_in': 0
                    }
                if tx['type'] == "PURCHASE":
                    status[tid]['purchased'] += tx['num']
                elif tx['type'] == "VERIFY":
                    status[tid]['checked_in'] += tx['num']
        return status
