# ETRAP SDK Examples

This directory contains example scripts demonstrating how to use the ETRAP SDK for various transaction verification and audit trail operations.

## Examples Overview

### Basic Examples

- **basic_usage.py** - Simple transaction verification example
- **list_batches.py** - List recent batches from the blockchain
- **debug_batch.py** - Debug and inspect batch metadata
- **hash_computation.py** - Demonstrate transaction hash computation
- **data_models.py** - Show how to work with SDK data models
- **with_logging.py** - Configure SDK logging for debugging

### Verification Tools

- **verify.py** - Full-featured command-line tool demonstrating all SDK capabilities
- **etrap_verify_sdk.py** - Drop-in replacement for etrap_verify.py using the SDK

## The Verification Tool (verify.py)

The `verify.py` script is a comprehensive command-line tool that demonstrates all capabilities of the ETRAP SDK. It provides functionality similar to the core `etrap_verify.py` tool but uses the SDK for all operations.

### Features

- **Transaction Verification** - Verify individual transactions against blockchain records
- **Batch Management** - List, search, and analyze batches
- **Transaction Search** - Find transactions by hash across multiple batches
- **Contract Statistics** - View usage statistics and contract information
- **Transaction History** - Query historical transaction data with filters
- **Multiple Output Formats** - Human-readable or JSON output

### Installation

Make sure you have the ETRAP SDK installed:

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

### Basic Usage

```bash
# Verify a transaction
python verify.py verify --data '{"id": 123, "amount": 100.50, ...}'

# Search for a transaction by hash
python verify.py search --hash abc123...

# List recent batches
python verify.py list-batches --limit 10

# Get contract statistics
python verify.py stats --period 24h
```

### Command Reference

#### Global Options

- `-o, --organization` - Organization ID (default: acme)
- `-n, --network` - NEAR network: testnet, mainnet, or localnet (default: testnet)
- `--json` - Output results in JSON format instead of human-readable format

#### verify - Verify a Transaction

Verifies a single transaction against blockchain records.

```bash
python verify.py verify --data '<JSON_DATA>' [OPTIONS]
```

**Options:**
- `--data` (required) - Transaction data as JSON string
- `--batch-id` - Specific batch ID to check (optimization hint)
- `--table` - Table name hint for faster verification

**Example:**

```bash
# Verify a financial transaction
python verify.py verify --data '{
  "id": 109,
  "account_id": "ACC999",
  "amount": 999.99,
  "type": "C",
  "created_at": "2025-06-14 07:10:55.461133",
  "reference": "TEST-VERIFY"
}'

# Output:
🔐 ETRAP Transaction Verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Organization: acme
   Contract: acme.testnet
   Network: testnet

📊 Transaction Summary:
   ID: 109 | Account: ACC999 | Amount: $999.99 | Type: C
   Hash: 147236710593a5eb2f386b7fa1508bf5...

✅ TRANSACTION VERIFIED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Batch ID: BATCH-2025-06-14-978b1710
   Blockchain Time: 2025-06-14 00:10:55.463000
   Merkle Root: 147236710593a5eb2f386b7fa1508bf5...
   Database: etrapdb
   Table(s): financial_transactions
```

**JSON Output:**

```bash
python verify.py --json verify --data '{"id": 109, ...}'

# Output:
{
  "verified": true,
  "transaction_hash": "147236710593a5eb2f386b7fa1508bf5...",
  "batch_id": "BATCH-2025-06-14-978b1710",
  "blockchain_timestamp": "2025-06-14 00:10:55.463000",
  "merkle_proof": {
    "leaf_hash": "147236710593a5eb2f386b7fa1508bf5...",
    "proof_path": [],
    "root": "147236710593a5eb2f386b7fa1508bf5...",
    "valid": true
  },
  "batch_info": {
    "database": "etrapdb",
    "tables": ["financial_transactions"],
    "transaction_count": 1,
    "timestamp": "2025-06-14 00:10:55.463000"
  }
}
```

#### search - Search by Transaction Hash

Find a transaction by its hash across recent batches.

```bash
python verify.py search --hash <TRANSACTION_HASH> [OPTIONS]
```

**Options:**
- `--hash` (required) - Transaction hash to search for
- `--depth` - Number of batches to search (default: 500)

**Example:**

```bash
python verify.py search --hash 147236710593a5eb2f386b7fa1508bf5...

# Output:
🔍 Searching for transaction: 147236710593a5eb2f386b7fa1508bf5...
✓ Found in batch: BATCH-2025-06-14-978b1710
  Position: 0
  Merkle proof: 0 nodes
  Root: 147236710593a5eb2f386b7fa1508bf5...
```

#### list-batches - List Recent Batches

Display recent batches with optional filtering.

```bash
python verify.py list-batches [OPTIONS]
```

**Options:**
- `--limit` - Number of batches to show (default: 20)
- `--database` - Filter by database name
- `--table` - Filter by table name
- `--start-date` - Start date filter (YYYY-MM-DD)
- `--end-date` - End date filter (YYYY-MM-DD)

**Example:**

```bash
python verify.py list-batches --limit 5 --database etrapdb

# Output:
📦 Recent Batches (showing 5 of 27)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Batch ID                       Time                 DB        Txns  Size
────────────────────────────────────────────────────────────────────────
BATCH-2025-06-14-978b1710      2025-06-14 00:10:55  etrapdb   1     1.9KB
BATCH-2025-06-14-d86e6e52      2025-06-14 00:01:29  etrapdb   1     1.9KB
BATCH-2025-06-14-5da8b7f9      2025-06-13 23:54:27  etrapdb   1     1.9KB
```

#### analyze-batch - Analyze a Specific Batch

Get detailed information about a batch including Merkle tree and S3 data.

```bash
python verify.py analyze-batch --batch-id <BATCH_ID>
```

**Options:**
- `--batch-id` (required) - Batch ID to analyze

**Example:**

```bash
python verify.py analyze-batch --batch-id BATCH-2025-06-14-978b1710

# Output:
🔬 Analyzing batch: BATCH-2025-06-14-978b1710
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Batch Information:
   Database: etrapdb
   Tables: financial_transactions
   Transactions: 1
   Timestamp: 2025-06-14 00:10:55.463000
   Merkle Root: 147236710593a5eb2f386b7fa1508bf5...
   S3 Location: s3://etrap-acme/etrapdb/financial_transactions/BATCH-2025-06-14-978b1710/

🌳 Merkle Tree:
   Algorithm: sha256
   Height: 1
   Root: 147236710593a5eb2f386b7fa1508bf5...

📑 Indices Available:
   By timestamp: 1 entries
   By operation: INSERT
   By date: 1 dates
```

#### stats - Get Contract Statistics

View contract usage statistics for different time periods.

```bash
python verify.py stats [OPTIONS]
```

**Options:**
- `--period` - Time period: 1h, 24h, 7d, 30d, or all (default: 24h)

**Example:**

```bash
python verify.py stats --period 7d

# Output:
📊 Contract Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Overall Statistics:
   Contract: acme.testnet
   Total Batches: 27
   Total Transactions: 57
   Date Range: 2024-12-12 to 2025-06-14
   Databases: etrapdb, test_db, unknown
   Tables: 4 unique tables

📊 Period Statistics (7d):
   Batches Created: 26
   Transactions: 53
   Active Tables: 3
   Active Databases: 2
```

#### search-batches - Search Batches

Search for batches using various criteria.

```bash
python verify.py search-batches [OPTIONS]
```

**Options:**
- `--tx-hash` - Transaction hash to find
- `--merkle-root` - Merkle root to find
- `--start-date` - Start date (YYYY-MM-DD)
- `--end-date` - End date (YYYY-MM-DD)
- `--max-results` - Maximum results (default: 100)

**Example:**

```bash
python verify.py search-batches --start-date 2025-06-13 --end-date 2025-06-14

# Output:
🔍 Searching Batches
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Found 10 batches in 890ms

Matching Batches:
 1. BATCH-2025-06-14-978b1710 - 2025-06-14 00:10:55 (1 txns)
 2. BATCH-2025-06-14-d86e6e52 - 2025-06-14 00:01:29 (1 txns)
 3. BATCH-2025-06-14-5da8b7f9 - 2025-06-13 23:54:27 (1 txns)
    ... and 7 more
```

#### history - Get Transaction History

Query historical transaction data with filters.

```bash
python verify.py history [OPTIONS]
```

**Options:**
- `--operations` - Filter by operation types: INSERT, UPDATE, DELETE
- `--start-time` - Start time (ISO format)
- `--end-time` - End time (ISO format)
- `--limit` - Maximum results (default: 100)

**Example:**

```bash
python verify.py history --operations INSERT --limit 10

# Output:
📜 Transaction History
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Found 10 transactions
Time range: 2025-06-13 22:03:09 to 2025-06-14 00:10:55

Recent Transactions:
Time                 Operation  Table                    Hash
──────────────────────────────────────────────────────────────────
2025-06-14 00:10:55  INSERT     financial_transactions   147236710593a5eb...
2025-06-14 00:01:29  INSERT     financial_transactions   ba5ba542b41eaa22...
2025-06-13 23:54:27  INSERT     financial_transactions   4d1c3c7d0db0e74d...
```

### Advanced Usage Examples

#### Verify with Optimization Hints

Speed up verification by providing hints:

```bash
# If you know the batch ID
python verify.py verify --data '{"id": 123, ...}' --batch-id BATCH-2025-06-14-978b1710

# If you know the table name
python verify.py verify --data '{"id": 123, ...}' --table financial_transactions
```

#### Time Range Search Optimization

The ETRAP Verify SDK tool supports time range hints for efficient verification when you know the approximate time when a transaction was recorded:

```bash
# Search within a specific day
./etrap_verify_sdk.py -o acme --data '{"id": 109, ...}' \
  --hint-time-start 2025-06-14 \
  --hint-time-end 2025-06-14

# Search within specific hours 
./etrap_verify_sdk.py -o acme --data '{"id": 109, ...}' \
  --hint-time-start "2025-06-14 06:00:00" \
  --hint-time-end "2025-06-14 08:00:00"

# Combine time range with database hint for maximum efficiency
./etrap_verify_sdk.py -o acme --data '{"id": 109, ...}' \
  --hint-time-start 2025-06-14 \
  --hint-time-end 2025-06-14 \
  --hint-database etrapdb

# Multi-day range search
./etrap_verify_sdk.py -o acme --data '{"id": 109, ...}' \
  --hint-time-start "2025-06-13 00:00:00" \
  --hint-time-end "2025-06-15 23:59:59"
```

**Time Format Options:**
- **Date only**: `YYYY-MM-DD` (automatically extends end time to 23:59:59)
- **Full timestamp**: `YYYY-MM-DD HH:MM:SS` for precise time ranges

**Performance Benefits:**
- Uses smart contract's `get_batches_by_time_range()` method
- Searches only batches within the specified time range
- Can reduce search from hundreds of batches to just a few
- Combines efficiently with database and table hints

**Example Output with Time Range:**
```bash
./etrap_verify_sdk.py -o acme --data '{"id": 109, ...}' \
  --hint-time-start 2025-06-14 --hint-time-end 2025-06-14

🔐 ETRAP Transaction Verification Tool
   Contract: acme.testnet
   Network: testnet

📊 Transaction Hash: 147236710593a5eb2f386b7fa1508bf563a11b73b3d580219db2b59c2e135fc8

🔎 Searching recent batches...
   Found 29 recent batches to check
   Found in batch 3 of 29

✅ TRANSACTION VERIFIED
```

**Hint Priority Order:**
1. **Batch hint** (`--hint-batch`) - Most specific, direct lookup
2. **Time range hint** (`--hint-time-start` + `--hint-time-end`) - Time-based search
3. **Database hint** (`--hint-database`) - Database-specific search  
4. **Table hint** (`--hint-table`) - Table-specific search
5. **No hints** - Searches recent batches sequentially

#### Filter Batches by Date Range

```bash
python verify.py list-batches \
  --start-date 2025-06-01 \
  --end-date 2025-06-14 \
  --database etrapdb \
  --limit 50
```

#### Search for Specific Transaction Types

```bash
python verify.py history \
  --operations INSERT UPDATE \
  --start-time "2025-06-13T00:00:00" \
  --end-time "2025-06-14T23:59:59" \
  --limit 100
```

#### Export Results as JSON

All commands support JSON output for programmatic use:

```bash
# Verify and get JSON result
python verify.py --json verify --data '{"id": 123, ...}' > verification_result.json

# List batches as JSON
python verify.py --json list-batches --limit 100 > batches.json

# Get stats as JSON
python verify.py --json stats --period all > contract_stats.json
```

### Error Handling

The tool provides clear error messages:

- **Transaction Not Found**: Returns exit code 1
- **Network Errors**: Shows connection issues
- **Invalid Data**: Reports JSON parsing errors
- **S3 Access Issues**: Indicates when batch data is not available

### Integration Examples

#### Bash Script Integration

```bash
#!/bin/bash
# Verify a transaction and check result

TX_DATA='{"id": 123, "amount": 100.50, ...}'

if python verify.py --json verify --data "$TX_DATA" > result.json; then
    echo "Transaction verified!"
    BATCH_ID=$(jq -r '.batch_id' result.json)
    echo "Found in batch: $BATCH_ID"
else
    echo "Verification failed!"
    exit 1
fi
```

#### Python Integration

```python
import subprocess
import json

# Run verification
result = subprocess.run([
    'python', 'verify.py', '--json', 'verify',
    '--data', json.dumps(transaction_data)
], capture_output=True, text=True)

if result.returncode == 0:
    verification = json.loads(result.stdout)
    print(f"Verified: {verification['verified']}")
    print(f"Batch: {verification['batch_id']}")
```

### Performance Tips

1. **Use Hints**: Provide batch ID or table name hints when available
2. **Limit Search Depth**: Use reasonable limits for batch searches
3. **Cache Results**: The SDK caches data for 5 minutes by default
4. **Batch Operations**: Use the SDK directly for bulk verifications

### Troubleshooting

**"Transaction not found"**
- Ensure the transaction data matches exactly what was recorded
- Check if the batch has been created (may take a few seconds)
- Increase search depth with `--depth` parameter

**"S3 Access Error"**
- Verify AWS credentials are configured
- Check if the batch data has been uploaded by the CDC agent
- The tool can still verify using blockchain data only

**"Contract Error"**
- Ensure the organization ID is correct
- Verify the NEAR network (testnet/mainnet) matches your setup
- Check if the contract is deployed and accessible

### SDK Methods Demonstrated

The verify.py tool showcases all major SDK capabilities:

- `verify_transaction()` - Core verification with Merkle proofs
- `find_transaction()` - Search by transaction hash
- `list_batches()` - List and filter batches
- `get_batch()` & `get_batch_data()` - Access batch information
- `search_batches()` - Advanced batch search
- `get_transaction_history()` - Query historical data
- `get_contract_info()` & `get_contract_stats()` - Contract analytics
- `compute_transaction_hash()` - Hash computation
- `get_merkle_proof()` - Merkle proof retrieval

## ETRAP Verify SDK Tool (etrap_verify_sdk.py)

A complete clone of the original `etrap_verify.py` tool that uses the ETRAP SDK for all operations. This tool provides identical functionality with a cleaner interface using organization IDs instead of contract IDs.

### Key Differences from Original

- Uses `-o/--organization` instead of `-c/--contract` (though `--contract` is supported for backward compatibility)
- Automatically derives the contract ID from organization ID and network
- Leverages the SDK for all verification operations

### Usage

```bash
# Verify a transaction from JSON string
./etrap_verify_sdk.py -o acme --data '{"id":123,"account_id":"ACC500","amount":10000}'

# Verify from a file
./etrap_verify_sdk.py -o acme --data-file transaction.json

# Verify from stdin
echo '{"id":123,...}' | ./etrap_verify_sdk.py -o acme --data -

# Provide hints for faster search
./etrap_verify_sdk.py -o acme --data-file tx.json --hint-table financial_transactions
./etrap_verify_sdk.py -o acme --data-file tx.json --hint-batch BATCH-2025-06-14-abc123
./etrap_verify_sdk.py -o acme --data-file tx.json --hint-database production
./etrap_verify_sdk.py -o acme --data-file tx.json --hint-time-start 2025-06-14 --hint-time-end 2025-06-14

# JSON output
./etrap_verify_sdk.py -o acme --data '{...}' --json

# Quiet mode (minimal output)
./etrap_verify_sdk.py -o acme --data '{...}' --quiet
```

### Command-Line Options

- `-o, --organization` - Organization ID (e.g., 'acme')
- `-c, --contract` - NEAR contract ID (deprecated, use --organization)
- `--data` - Transaction data as JSON string (use "-" for stdin)
- `--data-file` - Path to file containing transaction JSON
- `--hint-table` - Table name hint for faster search
- `--hint-batch` - Specific batch ID to check
- `--hint-database` - Database name hint
- `--hint-time-start` - Start time for time range search (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
- `--hint-time-end` - End time for time range search (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
- `-n, --network` - NEAR network: testnet, mainnet, or localnet (default: testnet)
- `--json` - Output result as JSON
- `-q, --quiet` - Minimal output (just verification status)

### Output Formats

#### Standard Output

```
🔐 ETRAP Transaction Verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Organization: acme
   Contract: acme.testnet
   Network: testnet

📊 Transaction Summary:
   ID: 123 | Account: ACC500 | Amount: $10,000.00
   Hash: 8684c656d2addf8a0c5040ba3863c0fb...

✅ TRANSACTION VERIFIED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Batch ID: BATCH-2025-06-14-abc123
   Blockchain Time: 2025-06-14 12:34:56
   Merkle Root: def456...
   Database: production
   Table(s): financial_transactions
```

#### JSON Output

```json
{
  "verified": true,
  "transaction_hash": "8684c656d2addf8a0c5040ba3863c0fb...",
  "batch_id": "BATCH-2025-06-14-abc123",
  "blockchain_timestamp": "2025-06-14 12:34:56",
  "merkle_proof": {
    "leaf_hash": "8684c656d2addf8a0c5040ba3863c0fb...",
    "proof_path": [...],
    "merkle_root": "def456...",
    "is_valid": true
  },
  "batch_info": {
    "database": "production",
    "tables": ["financial_transactions"],
    "transaction_count": 100,
    "timestamp": "2025-06-14 12:34:56"
  }
}
```

#### Quiet Mode Output

```
✓ VERIFIED
```

or

```
✗ NOT VERIFIED
```

### Exit Codes

- `0` - Transaction verified successfully
- `1` - Verification failed or error occurred

### Migration from etrap_verify.py

To migrate from the original tool:

1. Replace `-c contract.testnet` with `-o organization`
2. All other options remain the same
3. The tool will automatically derive the correct contract ID

Example migration:
```bash
# Old:
etrap_verify.py -c acme.testnet --data '{...}'

# New:
etrap_verify_sdk.py -o acme --data '{...}'
```

## Other Examples

### basic_usage.py

Simple transaction verification:

```python
result = await client.verify_transaction({
    "id": 109,
    "account_id": "ACC999",
    "amount": 999.99,
    "type": "C",
    "created_at": "2025-06-14 07:10:55.461133"
})
```

### list_batches.py

List recent batches with filtering:

```python
batch_list = await client.list_batches(
    filter=BatchFilter(database_name="etrapdb"),
    limit=10
)
```

### debug_batch.py

Debug batch metadata:

```bash
python debug_batch.py BATCH-2025-06-14-978b1710
```

### with_logging.py

Enable debug logging:

```python
logging.getLogger('etrap_sdk').setLevel(logging.DEBUG)
```

## Requirements

- Python 3.8+
- ETRAP SDK installed
- NEAR account access (for blockchain queries)
- AWS credentials (optional, for S3 access)

## Support

For issues or questions:
- Check the main SDK documentation
- Review error messages for specific guidance
- Enable debug logging with `with_logging.py` example