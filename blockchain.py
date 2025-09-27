import hashlib
import json
import time
from uuid import uuid4

# --- Blockchain Implementation ---

class Blockchain:
    """
    A simple, decentralized, immutable ledger system.
    Stores transactions in blocks and validates chain integrity.
    """
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        # Create the genesis block
        self.create_block(previous_hash='1', proof=100)

    def create_block(self, proof, previous_hash=None):
        """
        Creates a new Block and adds it to the chain.
        :param proof: The proof given by the Proof of Work algorithm.
        :param previous_hash: Hash of previous Block.
        :return: New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]) if self.chain else '1',
        }
        # Reset the current list of transactions
        self.current_transactions = []
        # Calculate the hash of the new block and add it to the block dictionary
        block['hash'] = self.hash(block) 
        self.chain.append(block)
        return block

    def add_transaction(self, transaction):
        """
        Adds a new transaction to the list of transactions to be mined.
        :param transaction: <dict> New transaction data.
        """
        self.current_transactions.append(transaction)
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block.
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        """Returns the last block in the chain."""
        return self.chain[-1]


# --- Ticket Status Calculation ---

def get_ticket_status(blockchain, event_name=None):
    """
    Calculates the real-time status of all tickets based on the immutable ledger.
    
    Returns:
        total_purchased (int): Total tickets ever sold for the event.
        total_scanned (int): Total tickets scanned (checked in).
        total_remaining (int): Remaining tickets (capacity - total_purchased + scanned).
        ticket_details (dict): Status map {ticket_id: {qty, scanned}}.
        purchased_tickets_cache (dict): Customer data map {ticket_id: {name, email, phone}}.
    """
    
    # Initialize the ledger state trackers
    ticket_details = {}  # {ticket_id: {'qty': N, 'scanned': M}}
    purchased_tickets_cache = {} # {ticket_id: {'name': S, 'email': E, 'phone_number': P}}
    
    # Default initial capacity (assuming a large number if not filtered by event)
    # NOTE: In a real app, capacity would come from a configuration file per event.
    MAX_CAPACITY = 500 
    
    # Iterate through every block and every transaction to build the current state
    for block in blockchain.chain:
        for txn in block["transactions"]:
            
            # If an event filter is applied, skip transactions for other events
            if event_name and txn.get("event") != event_name:
                continue
                
            txn_type = txn.get("type")
            ticket_id = txn.get("ticket_id")
            
            if not ticket_id:
                continue

            if txn_type == "PURCHASE":
                # Record initial purchase data
                qty = txn.get("quantity", 0)
                ticket_details[ticket_id] = {
                    'qty': qty, 
                    'scanned': 0
                }
                # Cache customer data for verification/auditing later
                purchased_tickets_cache[ticket_id] = {
                    'name': txn.get("holder"),
                    'email': txn.get("email"),
                    'phone_number': txn.get("phone_number")
                }
                
            elif txn_type == "VERIFY":
                # Update the check-in count for the ticket_id
                num_entering = txn.get("num_entering", 0)
                if ticket_id in ticket_details:
                    ticket_details[ticket_id]['scanned'] += num_entering

    # --- Final calculations based on the built state ---
    
    total_purchased = sum(td['qty'] for td in ticket_details.values())
    total_scanned = sum(td['scanned'] for td in ticket_details.values())
    
    # Calculate remaining capacity based on a hardcoded max capacity for demo purposes
    total_remaining = MAX_CAPACITY - total_purchased
    
    return total_purchased, total_scanned, total_remaining, ticket_details, purchased_tickets_cache
