import hashlib
import json
import time
from uuid import uuid4

# --- Blockchain Implementation ---

class Blockchain:
    """
    A simple, decentralized, immutable ledger system for ticket management.
    Stores purchase (PURCHASE) and check-in (VERIFY) transactions in blocks
    and validates chain integrity using SHA-256 hashing.
    """
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        # The chain starts with the genesis block (index 1)
        # This is the FIRST and only block when initialized.
        if not self.chain:
            self.create_block(previous_hash='1', proof=100)

    def create_block(self, proof, previous_hash=None):
        """
        Creates a new Block and adds it to the chain.
        
        :param proof: The proof of work value.
        :param previous_hash: Hash of the previous Block.
        :return: The newly created Block dictionary.
        """
        # Determine previous_hash safely. If the chain is not empty, use the hash of the last block.
        # If the chain IS empty (i.e., we are mining the Genesis Block), use '1'.
        if previous_hash is None:
            previous_hash = self.hash(self.chain[-1]) if self.chain else '1'

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash,
        }
        # Reset the current list of transactions after they are included in the block
        self.current_transactions = []
        # Calculate the hash of the new block and add it to the block dictionary
        block['hash'] = self.hash(block)
        self.chain.append(block)
        return block

    def add_transaction(self, transaction):
        """
        Adds a new transaction (PURCHASE or VERIFY) to the list of transactions
        to be included in the next mined block.
        
        :param transaction: <dict> New transaction data.
        :return: The index of the block that will hold this transaction.
        """
        self.current_transactions.append(transaction)
        # Safely determine the next block index. If chain is empty (shouldn't happen after __init__), default to 1.
        return self.last_block['index'] + 1 if self.chain else 1

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block to ensure its immutability.
        """
        # Dictionary must be sorted to ensure consistent hashing across runs
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeros?
        
        :param last_proof: <int> Previous proof
        :param proof: <int> Current proof
        :return: <bool> True if correct, False otherwise.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        # The difficulty target: 4 leading zeros
        return guess_hash[:4] == "0000"

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number (proof) such that when hashed with the previous
           block's proof, it produces a hash with 4 leading zeros.
           
        :param last_proof: <int> The proof from the previous block.
        :return: <int> The new proof of work.
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @property
    def last_block(self):
        """
        Returns the last block in the chain.
        Crucially, it handles the possibility of an empty chain by returning
        the first block if the list is accessed directly before being created,
        or simply returning the last element otherwise.
        """
        # Safety check: if the chain is empty, return an empty dictionary or raise an error.
        # Since the genesis block should always exist after __init__, we ensure it's accessed correctly.
        if self.chain:
            return self.chain[-1]
        
        # If somehow the chain is empty (shouldn't happen), we'll return a minimal placeholder
        # which will likely cause an error downstream, but is safer than IndexError here.
        return {'index': 0, 'proof': 0, 'hash': '0'} 


# --- Ticket Status Calculation Helper ---

def get_ticket_status(blockchain, event_name=None):
    """
    Iterates through the entire blockchain ledger to calculate the current,
    real-time status of all tickets for a given event (or all events if None).
    
    :param blockchain: The Blockchain object instance.
    :param event_name: (Optional) Filter transactions by a specific event name.
    
    :returns: A tuple containing (total_purchased, total_scanned, total_remaining, ticket_details, purchased_tickets_cache)
    """

    # Initialize the ledger state trackers
    # Tracks usage: {ticket_id: {'qty': N, 'scanned': M}}
    ticket_details = {}  
    # Tracks customer data: {ticket_id: {'name': S, 'email': E, 'phone_number': P}}
    purchased_tickets_cache = {} 

    # Hardcoded maximum capacity for demonstration purposes
    MAX_CAPACITY = 500 

    # 1. Iterate through the ledger to build the state
    for block in blockchain.chain:
        for txn in block["transactions"]:

            # Filter transactions if an event name is provided
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
                # Cache customer data (used for verification and auditing)
                purchased_tickets_cache[ticket_id] = {
                    'name': txn.get("holder"),
                    'email': txn.get("email"),
                    'phone_number': txn.get("phone_number")
                }

            elif txn_type == "VERIFY":
                # Update the check-in count for the existing ticket_id
                num_entering = txn.get("num_entering", 0)
                if ticket_id in ticket_details:
                    # Check-in counts accumulate based on VERIFY transactions
                    ticket_details[ticket_id]['scanned'] += num_entering

    # 2. Final calculations based on the built state
    total_purchased = sum(td['qty'] for td in ticket_details.values())
    total_scanned = sum(td['scanned'] for td in ticket_details.values())

    # Calculate remaining capacity 
    total_remaining = MAX_CAPACITY - total_purchased

    return total_purchased, total_scanned, total_remaining, ticket_details, purchased_tickets_cache
