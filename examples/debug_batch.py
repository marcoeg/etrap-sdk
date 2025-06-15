#!/usr/bin/env python3
"""
Debug batch metadata from NEAR contract.
"""

import asyncio
import json
import sys
from etrap_sdk import ETRAPClient


async def main():
    # Initialize client
    client = ETRAPClient(
        organization_id="acme",
        network="testnet"
    )
    
    batch_id = sys.argv[1] if len(sys.argv) > 1 else "BATCH-2025-06-14-b6d61bf9"
    
    print(f"Fetching batch: {batch_id}\n")
    
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