# ETRAP SDK Hint Usage Analysis

## Summary of Findings

### 1. Batch Hint (--hint-batch)
- **Status**: ✅ WORKING (but inefficient)
- **Behavior**: Correctly prioritizes direct batch lookup
- **Issue**: `get_batch()` method searches through 100 recent batches before trying direct NFT lookup
- **Smart Contract Method Used**: `get_recent_batches` then `nft_token`
- **Should Use**: `nft_token` directly first

### 2. Table Hint (--hint-table)
- **Status**: ✅ PARTIALLY WORKING
- **Behavior**: Attempts to use table-specific search
- **Smart Contract Method Used**: `get_batches_by_table`
- **Issue**: Falls back to searching all recent batches after table search

### 3. Database Hint (--hint-database)
- **Status**: ❌ NOT IMPLEMENTED
- **Behavior**: Ignored - just reduces search limit from 100 to 50
- **Smart Contract Method Available**: `get_batches_by_database`
- **Should Use**: `get_batches_by_database` for database-specific search

### 4. Time Range Hint (time_range)
- **Status**: ❌ NOT IMPLEMENTED
- **Behavior**: Ignored - just reduces search limit from 100 to 50
- **Smart Contract Method Available**: `get_batches_by_time_range`
- **Should Use**: `get_batches_by_time_range` for time-based search

## Unused Smart Contract Methods

The SDK is not leveraging these available optimized search methods:

1. **`get_batches_by_database`** - Could be used with database hint
2. **`get_batches_by_time_range`** - Could be used with time range hint
3. **`get_batch_summary`** - Could be used for direct batch info retrieval

## Test Results

### No Hints
- Searches through 100 recent batches sequentially
- Found transaction in batch #3

### Batch Hint
- Uses batch hint for direct lookup
- Still calls `get_recent_batches(100)` unnecessarily

### Table Hint
- Calls `get_batches_by_table` correctly
- But then falls back to full search pattern

### Database Hint
- **NOT USED** - just reduces limit to 50
- Should call `get_batches_by_database`

### Time Range Hint
- **NOT USED** - just reduces limit to 50
- Should call `get_batches_by_time_range`

## Recommendations

1. **Fix `get_batch()` method**:
   - Try `nft_token` first for direct lookup
   - Only use `get_recent_batches` as fallback

2. **Implement database hint**:
   - Use `get_batches_by_database` when database hint provided

3. **Implement time range hint**:
   - Use `get_batches_by_time_range` when time range provided

4. **Optimize search order**:
   - Batch hint: Direct lookup only
   - Table hint: Use table search, don't fall back to general search
   - Database hint: Use database search
   - Time range: Use time range search
   - Combine hints: Use most specific method first