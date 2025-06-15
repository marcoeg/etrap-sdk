# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the ETRAP SDK codebase.

## Project Overview

The ETRAP SDK is a Python library for verifying database transactions against blockchain records stored on the NEAR blockchain. It provides a clean, async interface for interacting with the ETRAP (Enterprise Transaction Recording and Audit Platform) system.

## Architecture

### Core Components

#### ETRAPClient (`src/etrap_sdk/client.py`)
- Main SDK entry point providing all verification and query functionality
- Handles NEAR blockchain interactions through py-near library
- Manages S3 access for detailed batch data retrieval
- Implements intelligent search optimization using various hints
- Supports both single transaction verification and batch operations

#### Models (`src/etrap_sdk/models.py`)
- Comprehensive data models using Pydantic for validation
- Key models: `VerificationResult`, `BatchInfo`, `VerificationHints`, `TimeRange`
- Structured representation of blockchain data and verification results

#### Utilities (`src/etrap_sdk/utils.py`)
- Transaction hash computation and normalization
- Merkle proof validation algorithms
- Data formatting and parsing utilities

#### Exceptions (`src/etrap_sdk/exceptions.py`)
- Custom exception hierarchy for different error types
- Proper error handling patterns throughout the SDK

### Data Flow

1. **Transaction Input** → SDK normalizes and computes hash
2. **Search Strategy** → Uses optimization hints to select best search method
3. **Blockchain Query** → Queries NEAR smart contract for batches
4. **S3 Verification** → Downloads detailed batch data for Merkle proof verification
5. **Result Assembly** → Returns comprehensive verification result with proof

## Key Features

### Smart Contract Integration
- Organization-based architecture: `{org_id}.{network}` contract addresses
- Leverages all available smart contract search methods:
  - `nft_token` - Direct batch lookup
  - `get_recent_batches` - Recent batches with limit
  - `get_batches_by_table` - Table-specific searches
  - `get_batches_by_database` - Database-specific searches  
  - `get_batches_by_time_range` - Time-based searches
  - `get_batch_summary` - Enhanced batch metadata

### Optimization Hints System
- **Batch Hint**: Direct lookup by batch ID (most efficient)
- **Time Range Hint**: Search within specific time bounds
- **Database Hint**: Limit search to specific database
- **Table Hint**: Focus on specific table batches
- **Hint Combination**: Multiple hints work together for maximum efficiency

### Verification Methods
- **Single-transaction batches**: Hash equals Merkle root (no S3 needed)
- **Multi-transaction batches**: Full Merkle proof verification via S3
- **Fallback verification**: Works even when S3 data unavailable

## Development Guidelines

### Code Style
- Use async/await throughout for all I/O operations
- Follow Python type hints consistently
- Use Pydantic models for all data structures
- Implement proper exception handling (don't use logger.error + return None)

### Error Handling Patterns
```python
# GOOD: Raise exceptions for unexpected errors
try:
    result = await some_operation()
    if not result:
        return None  # Expected "not found" case
except SpecificError:
    # Handle expected error types appropriately
    logger.debug("Expected error occurred")
    return None
except Exception as e:
    # Unexpected errors should bubble up
    raise SDKError(f"Unexpected error: {e}")

# BAD: Logging errors and returning None
try:
    result = await some_operation()
except Exception as e:
    logger.error(f"Error: {e}")  # Don't do this
    return None
```

### Testing Strategy
- Mock NEAR blockchain calls for unit tests
- Use pytest with async support
- Test both success and failure scenarios
- Include integration tests with actual blockchain (when possible)

## Environment and Dependencies

### Core Dependencies
- `py-near` - NEAR blockchain interaction
- `boto3` - AWS S3 access for batch data
- `pydantic` - Data validation and models
- `asyncio` - Async/await support

### Environment Variables
The SDK reads AWS credentials from environment or AWS config:
- `AWS_ACCESS_KEY_ID` - AWS access key (optional)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key (optional) 
- `AWS_DEFAULT_REGION` - AWS region (optional, defaults to us-west-2)

Note: The SDK does NOT read any ETRAP-specific environment variables.

### Python Version
- Requires Python 3.8+
- Uses modern async/await patterns
- Type hints compatible with Python 3.8+

## Examples and Tools

### Examples Directory (`examples/`)
- `basic_usage.py` - Simple verification example
- `verify.py` - Comprehensive CLI tool demonstrating all SDK features
- `etrap_verify_sdk.py` - Drop-in replacement for original etrap_verify.py
- `list_batches.py` - Batch listing and filtering
- `debug_batch.py` - Batch inspection and debugging

### Key Example: etrap_verify_sdk.py
- Production-ready verification tool
- Supports all optimization hints including time ranges
- Clean error handling and user experience
- JSON and human-readable output formats
- Direct replacement for legacy verification tools

## Common Operations

### Basic Verification
```python
client = ETRAPClient(organization_id="acme", network="testnet")
result = await client.verify_transaction(transaction_data)
```

### Optimized Verification with Hints
```python
hints = VerificationHints(
    batch_id="BATCH-2025-06-14-abc123",  # Most specific
    time_range=TimeRange(start=datetime(...), end=datetime(...)),
    database_name="production",
    table_name="financial_transactions"
)
result = await client.verify_transaction(transaction_data, hints=hints)
```

### Batch Operations
```python
# List recent batches
batches = await client.list_batches(limit=50)

# Get specific batch
batch = await client.get_batch("BATCH-2025-06-14-abc123")

# Search by criteria
results = await client.search_batches(
    SearchCriteria(transaction_hash="abc123...")
)
```

## Performance Considerations

### Search Optimization
- Always use the most specific hint available
- Batch ID hint is fastest (direct lookup)
- Time range hints dramatically reduce search scope
- Combined hints (time + database) are very efficient

### Caching
- SDK caches batch data for 5 minutes by default
- Contract calls are not cached (always fresh)
- S3 data is cached per batch ID

### Error Handling
- S3 access errors during batch search are expected and handled gracefully
- Network errors are retried with exponential backoff
- Blockchain errors bubble up as appropriate exceptions

## Deployment Patterns

### Organization-Based Setup
```python
# Development
client = ETRAPClient(organization_id="acme", network="testnet")

# Production  
client = ETRAPClient(organization_id="acme", network="mainnet")
```

### S3 Configuration
```python
# With explicit S3 config
s3_config = S3Config(
    bucket_name="custom-bucket",
    region="us-east-1",
    access_key_id="...",
    secret_access_key="..."
)
client = ETRAPClient(organization_id="acme", s3_config=s3_config)

# With default S3 config (uses etrap-{org_id} bucket)
client = ETRAPClient(organization_id="acme", s3_config=S3Config(region="us-west-2"))
```

## Troubleshooting

### Common Issues

**"Transaction not found"**
- Verify transaction data matches exactly what was recorded
- Check if transaction has been batched yet (CDC agent may be processing)
- Try broader search hints or no hints at all

**S3 Access Errors**
- Verify AWS credentials are configured correctly
- Check bucket permissions and region settings
- SDK can verify using blockchain data only if S3 fails

**Contract Errors**
- Ensure organization ID maps to correct contract address
- Verify network setting (testnet vs mainnet)
- Check NEAR RPC endpoint accessibility

### Debug Logging
```python
import logging
logging.getLogger('etrap_sdk').setLevel(logging.DEBUG)
```

## Integration Patterns

### CLI Tool Integration
```bash
# Direct command-line usage
python etrap_verify_sdk.py -o acme --data '{"id": 123, ...}' --hint-time-start 2025-06-14

# Programmatic usage
result = subprocess.run([...], capture_output=True)
verification = json.loads(result.stdout)
```

### Library Integration
```python
# As imported library
from etrap_sdk import ETRAPClient, VerificationHints, TimeRange

async def verify_my_transaction(tx_data):
    client = ETRAPClient(organization_id="myorg")
    result = await client.verify_transaction(tx_data)
    return result.verified
```

## Testing Commands

### Run All Tests
```bash
# Using pytest
pytest tests/

# With coverage
pytest --cov=etrap_sdk tests/

# With async support
pytest -v tests/
```

### Example Tests
```bash
# Run basic verification example
python examples/basic_usage.py

# Test verification tool
python examples/etrap_verify_sdk.py -o acme --data '{"id": 123, "amount": 100}'

# List recent batches
python examples/list_batches.py
```

### Manual Testing
```bash
# Verify a transaction with time hint
python examples/etrap_verify_sdk.py -o acme \
  --data '{"id": 109, "account_id": "ACC999", "amount": 999.99}' \
  --hint-time-start 2025-06-14 --hint-time-end 2025-06-14

# Check specific batch
python examples/debug_batch.py BATCH-2025-06-14-abc123
```

## Project Structure

```
etrap-sdk/
├── src/etrap_sdk/           # Main SDK package
│   ├── __init__.py         # Public API exports
│   ├── client.py           # ETRAPClient main class
│   ├── models.py           # Pydantic data models
│   ├── utils.py            # Utility functions
│   ├── exceptions.py       # Exception classes
│   └── py.typed           # Type hint marker
├── examples/               # Usage examples and tools
│   ├── verify.py          # Comprehensive CLI tool
│   ├── etrap_verify_sdk.py # Production verification tool
│   ├── basic_usage.py     # Simple examples
│   └── ...
├── tests/                  # Unit and integration tests
├── pyproject.toml         # Project configuration
├── uv.lock               # Dependency lock file
└── README.md             # Project documentation
```

## Release Process

### Version Management
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Update version in `pyproject.toml`
- Tag releases in git
- Generate changelog from commit messages

### Publishing
```bash
# Build package
uv build

# Publish to PyPI  
uv publish

# Install from PyPI
pip install etrap-sdk
```

## Important Notes

### Blockchain Integration
- The SDK is designed for the NEAR blockchain specifically
- Smart contract addresses follow `{organization}.{network}` pattern
- NFT-based batch storage with Merkle root verification

### Security Considerations
- Transaction data is hashed and normalized before verification
- Merkle proofs provide cryptographic verification
- Original transaction data is not stored on blockchain (privacy by design)
- S3 batch data should be treated as sensitive information

### Performance Characteristics
- Direct batch lookup: ~100ms
- Time range search: ~500ms for 1-day range
- Full recent batch search: ~2-5s for 100 batches
- S3 batch data retrieval: ~200-500ms per batch