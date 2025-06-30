#!/usr/bin/env python3
"""
Debug batch metadata from NEAR contract.
"""

import asyncio
import json
import sys
from etrap_sdk import ETRAPClient


async def main():
    if len(sys.argv) < 3:
        print("Usage: debug_batch.py <batch_id> <organization_id>")
        print("Example: debug_batch.py BATCH-2025-06-28-1107c8e1 lunaris")
        sys.exit(1)
    
    batch_id = sys.argv[1]
    organization_id = sys.argv[2]
    
    # Initialize client
    client = ETRAPClient(
        organization_id=organization_id,
        network="testnet"
    )
    
    print(f"Fetching batch: {batch_id}")
    print(f"Organization: {organization_id}")
    print(f"Contract: {organization_id}.testnet\n")
    
    try:
        # Get raw response from NEAR
        result = await client.near_account.view_function(
            client.contract_id,
            "nft_token",
            {"token_id": batch_id}
        )
        
        # Handle ViewFunctionResult
        if hasattr(result, 'result'):
            result = result.result
            
        print("Raw NFT data from contract:")
        print(json.dumps(result, indent=2))
        
        # Try to parse it
        batch = await client.get_batch(batch_id)
        if batch:
            print(f"\nParsed batch info:")
            print(f"  Database: {batch.database_name}")
            print(f"  S3 bucket: {batch.s3_location.bucket}")
            print(f"  S3 key: {batch.s3_location.key}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())