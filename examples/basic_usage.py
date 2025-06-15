#!/usr/bin/env python3
"""
Basic usage example for ETRAP SDK.

This example demonstrates how to use the SDK to verify transactions.
"""

import asyncio
from etrap_sdk import ETRAPClient, S3Config, VerificationHints


async def main():
    # Initialize the client
    client = ETRAPClient(
        organization_id="acme",  # Your organization ID
        network="testnet",
        s3_config=S3Config(
            # bucket_name is automatically derived as "etrap-acme"
            # contract_id is automatically set to "acme.testnet"
            region="us-west-2"
        )
    )
    
    # Example transaction data (as returned from database)
    transaction = {
        "id": 109,
        "account_id": "ACC999",
        "amount": 999.99,
        "type": "C",
        "created_at": "2025-06-14 07:10:55.461133",
        "reference": "TEST-VERIFY"
    }
    
    # Show computed hash
    tx_hash = client.compute_transaction_hash(transaction)
    print(f"Transaction hash: {tx_hash}")
    
    print("\nVerifying transaction...")
    print(f"  ID: {transaction['id']}")
    print(f"  Account: {transaction['account_id']}")
    print(f"  Amount: {transaction['amount']}")
    
    try:
        # Verify the transaction
        result = await client.verify_transaction(transaction)
        
        if result.verified:
            print(f"\n✓ Transaction verified!")
            print(f"  Batch ID: {result.batch_id}")
            print(f"  Blockchain timestamp: {result.blockchain_timestamp}")
            print(f"  Transaction hash: {result.transaction_hash}")
        else:
            print(f"\n✗ Verification failed: {result.error}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
    
    # Example with optimization hints
    print("\n\nVerifying with hints...")
    
    hints = VerificationHints(
        table_name="financial_transactions",
        database_name="production"
    )
    
    try:
        result = await client.verify_transaction(transaction, hints=hints)
        
        if result.verified:
            print(f"\n✓ Transaction verified with hints!")
            print(f"  Batch ID: {result.batch_id}")
        else:
            print(f"\n✗ Verification failed: {result.error}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())