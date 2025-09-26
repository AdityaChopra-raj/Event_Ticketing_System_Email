from typing import List, Dict, Any
import time
import hashlib
import json
from events_data import events # Import events to calculate capacity

class Blockchain:
    """A single, centralized blockchain to track purchases and verification logs."""

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
        # CRITICAL FIX: Use the deterministic hashing
        block["hash"] = self.hash_block(block)
        self.pending_transactions = []
        self.chain.append(block)
        return block

    def add_transaction(self, transaction: dict):
        """Adds a new transaction (purchase or verification) to the pending list."""
        self.pending_transactions.append(transaction)
        return self.chain[-1]["index"] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash_block(block: Dict[str, Any]) -> str:
        """
        Creates a SHA-256 hash using deterministic JSON serialization.
        This ensures the hash is the same every time, which is mandatory for chain integrity.
        """
        temp = block.copy()
        # Remove hash before calculating it
        temp.pop("hash", None)
        block_string = json.dumps(temp, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

def get_ticket_status(blockchain_instance, event_name):
    """
    Reads the entire blockchain to calculate total purchased, scanned, and remaining capacity.
    This replaces mutable state dictionaries.
    """
    total_capacity = events[event_name]["capacity"]
    total_purchased = 0
    total_scanned = 0
    ticket_details = {} # ticket_id -> {'qty': x, 'scanned': y}
    purchased_tickets_cache = {} # ticket_id -> {details} for quick email/name lookup

    for block in blockchain_instance.chain:
        for txn in block["transactions"]:
            if txn.get("event") == event_name:
                ticket_id = txn.get("ticket_id")
                if not ticket_id: continue

                # PURCHASE Transaction (Sets the initial quantity)
                if txn.get("type") == "PURCHASE":
                    qty = txn["quantity"]
                    total_purchased += qty
                    ticket_details[ticket_id] = {"qty": qty, "scanned": 0}
                    # Update cache with holder details
                    purchased_tickets_cache[ticket_id] = {
                        "event": event_name, 
                        "name": txn.get("holder", "N/A"), 
                        "qty": qty, 
                        "email": txn.get("email", "N/A"),
                        "phone": txn.get("phone_number", "N/A")
                    }

                # VERIFY Transaction (Logs usage against quantity)
                elif txn.get("type") == "VERIFY":
                    num_entering = txn.get("num_entering", 0)
                    if ticket_id in ticket_details:
                        ticket_details[ticket_id]["scanned"] += num_entering
                        total_scanned += num_entering

    remaining_capacity = total_capacity - total_purchased
    
    return total_purchased, total_scanned, remaining_capacity, ticket_details, purchased_tickets_cache
