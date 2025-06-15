#!/usr/bin/env python3
"""Test the SDK fixes for proper hint usage."""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from etrap_sdk import ETRAPClient, S3Config, VerificationHints, TimeRange

# Track method calls
calls_log = []

async def test_fixed_sdk():
    client = ETRAPClient(
        organization_id="acme",
        network="testnet",
        s3_config=S3Config(region="us-west-2")
    )
    
    transaction_data = {
        "id": 109,
        "account_id": "ACC999",
        "amount": 999.99,
        "type": "C",
        "created_at": "2025-06-14 07:10:55.461133",
        "reference": "TEST-VERIFY"
    }
    
    # Patch methods to track calls
    original_get_batch = client.get_batch
    original_get_recent_batches = client._get_recent_batches
    original_get_batches_by_table = client._get_batches_by_table
    original_get_batches_by_database = client._get_batches_by_database
    original_get_batches_by_time_range = client._get_batches_by_time_range
    original_verify_in_batch = client._verify_in_batch
    
    async def tracked_get_batch(batch_id):
        calls_log.append(f"get_batch('{batch_id}')")
        return await original_get_batch(batch_id)
    
    async def tracked_get_recent_batches(limit):
        calls_log.append(f"_get_recent_batches(limit={limit})")
        return await original_get_recent_batches(limit)
    
    async def tracked_get_batches_by_table(table_name, limit):
        calls_log.append(f"_get_batches_by_table(table='{table_name}', limit={limit})")
        return await original_get_batches_by_table(table_name, limit)
    
    async def tracked_get_batches_by_database(database_name, limit=100):
        calls_log.append(f"_get_batches_by_database(database='{database_name}', limit={limit})")
        return await original_get_batches_by_database(database_name, limit)
    
    async def tracked_get_batches_by_time_range(start, end, database=None, limit=100):
        calls_log.append(f"_get_batches_by_time_range(start={start.strftime('%Y-%m-%d')}, end={end.strftime('%Y-%m-%d')}, database={database}, limit={limit})")
        return await original_get_batches_by_time_range(start, end, database, limit)
    
    async def tracked_verify_in_batch(tx_hash, batch):
        calls_log.append(f"_verify_in_batch(batch={batch.batch_id})")
        result = await original_verify_in_batch(tx_hash, batch)
        if result and result.verified:
            calls_log.append(f"  ✓ FOUND in {batch.batch_id}")
        return result
    
    client.get_batch = tracked_get_batch
    client._get_recent_batches = tracked_get_recent_batches
    client._get_batches_by_table = tracked_get_batches_by_table
    client._get_batches_by_database = tracked_get_batches_by_database
    client._get_batches_by_time_range = tracked_get_batches_by_time_range
    client._verify_in_batch = tracked_verify_in_batch
    
    # Test 1: Batch hint (should NOT search recent batches)
    print("\n=== Test 1: BATCH HINT (Fixed) ===")
    calls_log.clear()
    hints = VerificationHints(batch_id="BATCH-2025-06-14-978b1710")
    result = await client.verify_transaction(transaction_data, hints=hints)
    print(f"Verified: {result.verified}")
    print("Calls:")
    for call in calls_log:
        print(f"  {call}")
    print("✅ Should only call get_batch and _verify_in_batch")
    
    # Test 2: Database hint (should use database search)
    print("\n=== Test 2: DATABASE HINT (Fixed) ===")
    calls_log.clear()
    hints = VerificationHints(database_name="etrapdb")
    result = await client.verify_transaction(transaction_data, hints=hints)
    print(f"Verified: {result.verified}")
    print("Calls:")
    for call in calls_log:
        print(f"  {call}")
    print("✅ Should use _get_batches_by_database")
    
    # Test 3: Time range hint (should use time range search)
    print("\n=== Test 3: TIME RANGE HINT (Fixed) ===")
    calls_log.clear()
    hints = VerificationHints(
        time_range=TimeRange(
            start=datetime(2025, 6, 14, 0, 0, 0),
            end=datetime(2025, 6, 14, 23, 59, 59)
        )
    )
    result = await client.verify_transaction(transaction_data, hints=hints)
    print(f"Verified: {result.verified}")
    print("Calls:")
    for call in calls_log:
        print(f"  {call}")
    print("✅ Should use _get_batches_by_time_range")
    
    # Test 4: Combined hints (should use most specific)
    print("\n=== Test 4: TIME RANGE + DATABASE HINT ===")
    calls_log.clear()
    hints = VerificationHints(
        database_name="etrapdb",
        time_range=TimeRange(
            start=datetime(2025, 6, 14, 0, 0, 0),
            end=datetime(2025, 6, 14, 23, 59, 59)
        )
    )
    result = await client.verify_transaction(transaction_data, hints=hints)
    print(f"Verified: {result.verified}")
    print("Calls:")
    for call in calls_log:
        print(f"  {call}")
    print("✅ Should use _get_batches_by_time_range with database parameter")

if __name__ == "__main__":
    asyncio.run(test_fixed_sdk())