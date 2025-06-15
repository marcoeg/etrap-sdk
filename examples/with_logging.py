#!/usr/bin/env python3
"""
Example showing how to configure logging for the ETRAP SDK.

This demonstrates how to enable debug logging to see what the SDK is doing.
"""

import asyncio
import logging
from etrap_sdk import ETRAPClient, S3Config


def setup_logging():
    """Configure logging for the SDK and application."""
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Enable debug logging for ETRAP SDK
    logging.getLogger('etrap_sdk').setLevel(logging.DEBUG)
    
    # Optionally, configure specific modules
    logging.getLogger('etrap_sdk.client').setLevel(logging.DEBUG)
    logging.getLogger('etrap_sdk.utils').setLevel(logging.INFO)


async def main():
    # Setup logging
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting ETRAP SDK example with logging")
    
    # Initialize client
    client = ETRAPClient(
        organization_id="acme",
        network="testnet",
        s3_config=S3Config(
            region="us-west-2"
        )
    )
    
    # Example transaction
    transaction = {
        "id": 109,
        "account_id": "ACC999",
        "amount": 999.99,
        "type": "C",
        "created_at": "2025-06-14 07:10:55.461133",
        "reference": "TEST-VERIFY"
    }
    
    logger.info("Verifying transaction %s", transaction['id'])
    
    try:
        # This will show debug logs from the SDK
        result = await client.verify_transaction(transaction)
        
        if result.verified:
            logger.info("Transaction verified successfully")
            logger.info("Batch ID: %s", result.batch_id)
            logger.info("Transaction hash: %s", result.transaction_hash)
        else:
            logger.warning("Verification failed: %s", result.error)
            
    except Exception as e:
        logger.error("Error during verification", exc_info=True)
    
    # Update client configuration
    logger.info("Updating client configuration")
    client.update_config({
        "cache_ttl": 600,
        "max_retries": 5
    })
    
    config = client.get_config()
    logger.info("New configuration: cache_ttl=%d, max_retries=%d", 
                config.cache_ttl, config.max_retries)


if __name__ == "__main__":
    asyncio.run(main())