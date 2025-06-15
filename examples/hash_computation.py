#!/usr/bin/env python3
"""
Example showing transaction hash computation and normalization.

This demonstrates how the SDK normalizes transaction data to ensure
consistent hashing between the database format and CDC agent format.
"""

from etrap_sdk import normalize_transaction_data, compute_transaction_hash


def main():
    # Transaction as returned from database
    db_transaction = {
        "id": 109,
        "account_id": "ACC999",
        "amount": 999.99,
        "type": "C",
        "created_at": "2025-06-14 07:10:55.461133",  # Space separator
        "reference": "TEST-VERIFY"
    }
    
    print("Original transaction from database:")
    for key, value in db_transaction.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    # Normalize the transaction
    normalized = normalize_transaction_data(db_transaction)
    
    print("\nNormalized transaction:")
    for key, value in normalized.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    # Compute hash
    hash_with_norm = compute_transaction_hash(db_transaction, normalize=True)
    hash_without_norm = compute_transaction_hash(db_transaction, normalize=False)
    
    print(f"\nHash with normalization: {hash_with_norm}")
    print(f"Hash without normalization: {hash_without_norm}")
    
    # Show that different formats produce same hash when normalized
    alt_transaction = {
        "id": "109",  # String instead of int
        "account_id": "ACC999",
        "amount": "999.99",  # String instead of float
        "type": "C",
        "created_at": "2025-06-14T07:10:55.461",  # T separator, 3 decimals
        "reference": "TEST-VERIFY"
    }
    
    alt_hash = compute_transaction_hash(alt_transaction, normalize=True)
    print(f"\nAlternative format hash: {alt_hash}")
    print(f"Hashes match: {hash_with_norm == alt_hash}")
    
    # Show null value handling
    tx_with_null = db_transaction.copy()
    tx_with_null["optional_field"] = None
    
    hash_with_null = compute_transaction_hash(tx_with_null, normalize=True)
    print(f"\nHash with null field: {hash_with_null}")
    print(f"Null fields ignored: {hash_with_norm == hash_with_null}")


if __name__ == "__main__":
    main()