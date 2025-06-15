#!/usr/bin/env python3
"""
Comprehensive ETRAP Verification Tool

This example demonstrates all SDK capabilities including:
- Transaction verification with various search strategies
- Batch exploration and analysis
- Contract information and statistics
- Transaction history search
- Merkle proof validation
- S3 data access

Usage:
    # Verify a single transaction
    python comprehensive_verify.py verify --data '{"id": 123, "amount": 100.50, ...}'
    
    # Search for transactions by hash
    python comprehensive_verify.py search --hash abc123...
    
    # List recent batches
    python comprehensive_verify.py list-batches --limit 10
    
    # Get contract statistics
    python comprehensive_verify.py stats --period 7d
    
    # Analyze a specific batch
    python comprehensive_verify.py analyze-batch --batch-id BATCH-2024-01-01-abc123
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from etrap_sdk import (
    ETRAPClient, S3Config, VerificationHints,
    BatchFilter, SearchCriteria, TransactionFilter,
    TimeRange, DateRange
)
from etrap_sdk.utils import format_transaction_summary, parse_timestamp


class ComprehensiveVerifier:
    """Comprehensive verification tool using ETRAP SDK."""
    
    def __init__(self, organization_id: str, network: str = "testnet"):
        """Initialize verifier with organization settings."""
        self.client = ETRAPClient(
            organization_id=organization_id,
            network=network,
            s3_config=S3Config(region="us-west-2")
        )
        self.organization_id = organization_id
        self.network = network
    
    async def verify_transaction(
        self,
        transaction_data: Dict[str, Any],
        hints: Optional[Dict[str, Any]] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """Verify a transaction with comprehensive search strategies."""
        if verbose:
            print("🔐 ETRAP Transaction Verification")
            print("━" * 60)
            print(f"   Organization: {self.organization_id}")
            print(f"   Contract: {self.client.contract_id}")
            print(f"   Network: {self.network}")
            print()
        
        # Compute transaction hash
        tx_hash = self.client.compute_transaction_hash(transaction_data)
        
        if verbose:
            print(f"📊 Transaction Summary:")
            print(f"   {format_transaction_summary(transaction_data)}")
            print(f"   Hash: {tx_hash}")
            print()
        
        # Create verification hints if provided
        verification_hints = None
        if hints:
            verification_hints = VerificationHints(
                batch_id=hints.get('batch_id'),
                table_name=hints.get('table'),
                database_name=hints.get('database'),
                timestamp_hint=parse_timestamp(hints.get('timestamp')) if hints.get('timestamp') else None
            )
        
        # Perform verification
        try:
            result = await self.client.verify_transaction(
                transaction_data,
                hints=verification_hints
            )
            
            if result.verified:
                # Get additional batch information
                batch_info = await self.client.get_batch(result.batch_id)
                
                verification_result = {
                    'verified': True,
                    'transaction_hash': result.transaction_hash,
                    'batch_id': result.batch_id,
                    'blockchain_timestamp': result.blockchain_timestamp,
                    'merkle_proof': {
                        'leaf_hash': result.merkle_proof.leaf_hash,
                        'proof_path': result.merkle_proof.proof_path,
                        'root': result.merkle_proof.merkle_root,
                        'valid': result.merkle_proof.is_valid
                    }
                }
                
                if batch_info:
                    verification_result['batch_info'] = {
                        'database': batch_info.database_name,
                        'tables': batch_info.table_names,
                        'transaction_count': batch_info.transaction_count,
                        'timestamp': batch_info.timestamp
                    }
                
                if verbose:
                    print("✅ TRANSACTION VERIFIED")
                    print("━" * 60)
                    print(f"   Batch ID: {result.batch_id}")
                    print(f"   Blockchain Time: {result.blockchain_timestamp}")
                    print(f"   Merkle Root: {result.merkle_proof.merkle_root}")
                    if batch_info:
                        print(f"   Database: {batch_info.database_name}")
                        print(f"   Table(s): {', '.join(batch_info.table_names)}")
                
                return verification_result
            else:
                if verbose:
                    print(f"❌ Verification failed: {result.error}")
                
                return {
                    'verified': False,
                    'transaction_hash': tx_hash,
                    'error': result.error
                }
                
        except Exception as e:
            if verbose:
                print(f"❌ Error during verification: {e}")
            
            return {
                'verified': False,
                'transaction_hash': tx_hash,
                'error': str(e)
            }
    
    async def search_by_hash(
        self,
        transaction_hash: str,
        max_depth: int = 500,
        verbose: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Search for a transaction by its hash."""
        if verbose:
            print(f"🔍 Searching for transaction: {transaction_hash}")
        
        # First, try to find the transaction
        location = await self.client.find_transaction(
            transaction_hash,
            search_depth=max_depth
        )
        
        if location:
            if verbose:
                print(f"✓ Found in batch: {location.batch_id}")
                print(f"  Position: {location.position}")
            
            # Get the full batch data
            try:
                batch_data = await self.client.get_batch_data(
                    location.batch_id,
                    include_merkle_tree=True
                )
                
                if batch_data:
                    # Get merkle proof
                    proof = await self.client.get_merkle_proof(
                        location.batch_id,
                        transaction_hash
                    )
                    
                    result = {
                        'found': True,
                        'batch_id': location.batch_id,
                        'position': location.position,
                        'batch_info': location.batch_info,
                        'has_merkle_proof': proof is not None
                    }
                    
                    if verbose and proof:
                        print(f"  Merkle proof: {len(proof.proof_path)} nodes")
                        print(f"  Root: {proof.merkle_root}")
                    
                    return result
                    
            except Exception as e:
                if verbose:
                    print(f"  ⚠️  Could not get full batch data: {e}")
                
                return {
                    'found': True,
                    'batch_id': location.batch_id,
                    'position': location.position,
                    'batch_info': location.batch_info,
                    'error': str(e)
                }
        else:
            if verbose:
                print(f"✗ Transaction not found in {max_depth} recent batches")
            
            return None
    
    async def list_batches(
        self,
        limit: int = 20,
        filter_criteria: Optional[Dict[str, Any]] = None,
        verbose: bool = True
    ) -> List[Dict[str, Any]]:
        """List batches with optional filtering."""
        # Create filter
        batch_filter = None
        if filter_criteria:
            time_range = None
            if filter_criteria.get('start_date') or filter_criteria.get('end_date'):
                time_range = TimeRange(
                    start=parse_timestamp(filter_criteria.get('start_date', '2020-01-01')),
                    end=parse_timestamp(filter_criteria.get('end_date', datetime.now().isoformat()))
                )
            
            batch_filter = BatchFilter(
                database_name=filter_criteria.get('database'),
                table_name=filter_criteria.get('table'),
                time_range=time_range,
                min_transactions=filter_criteria.get('min_transactions', 0)
            )
        
        # Get batches
        batch_list = await self.client.list_batches(
            filter=batch_filter,
            limit=limit,
            order_by="timestamp_desc"
        )
        
        if verbose:
            print(f"📦 Recent Batches (showing {len(batch_list.batches)} of {batch_list.total_count})")
            print("━" * 80)
            print(f"{'Batch ID':<30} {'Time':<20} {'DB':<15} {'Txns':<6} {'Size':<10}")
            print("─" * 80)
            
            for batch in batch_list.batches:
                timestamp = batch.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                size = f"{batch.size_bytes / 1024:.1f}KB" if batch.size_bytes else "N/A"
                print(f"{batch.batch_id:<30} {timestamp:<20} {batch.database_name:<15} "
                      f"{batch.transaction_count:<6} {size:<10}")
        
        return [
            {
                'batch_id': b.batch_id,
                'timestamp': b.timestamp,
                'database': b.database_name,
                'tables': b.table_names,
                'transaction_count': b.transaction_count,
                'merkle_root': b.merkle_root,
                'size_bytes': b.size_bytes
            }
            for b in batch_list.batches
        ]
    
    async def analyze_batch(
        self,
        batch_id: str,
        include_merkle_tree: bool = True,
        verbose: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Analyze a specific batch in detail."""
        if verbose:
            print(f"🔬 Analyzing batch: {batch_id}")
            print("━" * 60)
        
        # Get batch info
        batch_info = await self.client.get_batch(batch_id)
        if not batch_info:
            if verbose:
                print("❌ Batch not found")
            return None
        
        result = {
            'batch_id': batch_id,
            'database': batch_info.database_name,
            'tables': batch_info.table_names,
            'transaction_count': batch_info.transaction_count,
            'merkle_root': batch_info.merkle_root,
            'timestamp': batch_info.timestamp,
            's3_location': {
                'bucket': batch_info.s3_location.bucket,
                'key': batch_info.s3_location.key
            }
        }
        
        if verbose:
            print(f"📊 Batch Information:")
            print(f"   Database: {batch_info.database_name}")
            print(f"   Tables: {', '.join(batch_info.table_names)}")
            print(f"   Transactions: {batch_info.transaction_count}")
            print(f"   Timestamp: {batch_info.timestamp}")
            print(f"   Merkle Root: {batch_info.merkle_root}")
            print(f"   S3 Location: s3://{batch_info.s3_location.bucket}/{batch_info.s3_location.key}")
        
        # Try to get full batch data
        try:
            batch_data = await self.client.get_batch_data(
                batch_id,
                include_merkle_tree=include_merkle_tree,
                include_indices=True
            )
            
            if batch_data:
                result['has_s3_data'] = True
                
                if batch_data.merkle_tree:
                    result['merkle_tree'] = {
                        'algorithm': batch_data.merkle_tree.algorithm,
                        'height': batch_data.merkle_tree.height,
                        'root': batch_data.merkle_tree.root
                    }
                    
                    if verbose:
                        print(f"\n🌳 Merkle Tree:")
                        print(f"   Algorithm: {batch_data.merkle_tree.algorithm}")
                        print(f"   Height: {batch_data.merkle_tree.height}")
                        print(f"   Root: {batch_data.merkle_tree.root}")
                
                if batch_data.indices:
                    result['has_indices'] = True
                    if verbose:
                        print(f"\n📑 Indices Available:")
                        print(f"   By timestamp: {len(batch_data.indices.by_timestamp)} entries")
                        print(f"   By operation: {', '.join(batch_data.indices.by_operation.keys())}")
                        print(f"   By date: {len(batch_data.indices.by_date)} dates")
        
        except Exception as e:
            result['has_s3_data'] = False
            result['s3_error'] = str(e)
            
            if verbose:
                print(f"\n⚠️  S3 Data: Not accessible ({e})")
        
        return result
    
    async def get_contract_stats(
        self,
        time_period: str = "24h",
        verbose: bool = True
    ) -> Dict[str, Any]:
        """Get contract statistics and information."""
        if verbose:
            print("📊 Contract Statistics")
            print("━" * 60)
        
        # Get contract info
        contract_info = await self.client.get_contract_info()
        
        # Get stats for period
        stats = await self.client.get_contract_stats(time_period)
        
        result = {
            'contract_id': contract_info.contract_id,
            'total_batches': contract_info.total_batches,
            'total_transactions': contract_info.total_transactions,
            'earliest_batch': contract_info.earliest_batch,
            'latest_batch': contract_info.latest_batch,
            'databases': contract_info.supported_databases,
            'tables': contract_info.supported_tables,
            'period_stats': {
                'period': stats.time_period,
                'batches_created': stats.batches_created,
                'transactions_recorded': stats.transactions_recorded,
                'unique_tables': stats.unique_tables,
                'unique_databases': stats.unique_databases
            }
        }
        
        if verbose:
            print(f"📈 Overall Statistics:")
            print(f"   Contract: {contract_info.contract_id}")
            print(f"   Total Batches: {contract_info.total_batches:,}")
            print(f"   Total Transactions: {contract_info.total_transactions:,}")
            print(f"   Date Range: {contract_info.earliest_batch.date()} to {contract_info.latest_batch.date()}")
            print(f"   Databases: {', '.join(contract_info.supported_databases)}")
            print(f"   Tables: {len(contract_info.supported_tables)} unique tables")
            
            print(f"\n📊 Period Statistics ({stats.time_period}):")
            print(f"   Batches Created: {stats.batches_created}")
            print(f"   Transactions: {stats.transactions_recorded}")
            print(f"   Active Tables: {stats.unique_tables}")
            print(f"   Active Databases: {stats.unique_databases}")
        
        return result
    
    async def search_batches(
        self,
        criteria: Dict[str, Any],
        max_results: int = 100,
        verbose: bool = True
    ) -> List[Dict[str, Any]]:
        """Search batches using various criteria."""
        if verbose:
            print("🔍 Searching Batches")
            print("━" * 60)
        
        # Build search criteria
        date_range = None
        if criteria.get('start_date') or criteria.get('end_date'):
            date_range = DateRange(
                start=criteria.get('start_date', '2020-01-01'),
                end=criteria.get('end_date', datetime.now().strftime('%Y-%m-%d'))
            )
        
        search_criteria = SearchCriteria(
            transaction_hash=criteria.get('transaction_hash'),
            merkle_root=criteria.get('merkle_root'),
            operation_type=criteria.get('operation_types'),
            date_range=date_range
        )
        
        # Perform search
        results = await self.client.search_batches(
            search_criteria,
            max_results=max_results
        )
        
        if verbose:
            print(f"Found {len(results.matching_batches)} batches in {results.search_time_ms}ms")
            
            if results.matching_batches:
                print("\nMatching Batches:")
                for i, batch in enumerate(results.matching_batches[:10], 1):
                    print(f"{i:2d}. {batch.batch_id} - {batch.timestamp} ({batch.transaction_count} txns)")
                
                if len(results.matching_batches) > 10:
                    print(f"    ... and {len(results.matching_batches) - 10} more")
        
        return [
            {
                'batch_id': b.batch_id,
                'timestamp': b.timestamp,
                'database': b.database_name,
                'transaction_count': b.transaction_count
            }
            for b in results.matching_batches
        ]
    
    async def get_transaction_history(
        self,
        filter_params: Dict[str, Any],
        limit: int = 100,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """Get transaction history with filtering."""
        if verbose:
            print("📜 Transaction History")
            print("━" * 60)
        
        # Build filter
        time_range = None
        if filter_params.get('start_time') or filter_params.get('end_time'):
            time_range = TimeRange(
                start=parse_timestamp(filter_params.get('start_time', '2020-01-01')),
                end=parse_timestamp(filter_params.get('end_time', datetime.now().isoformat()))
            )
        
        tx_filter = TransactionFilter(
            time_range=time_range,
            operation_types=filter_params.get('operation_types'),
            account_id=filter_params.get('account_id'),
            min_amount=filter_params.get('min_amount'),
            max_amount=filter_params.get('max_amount')
        )
        
        # Get history
        history = await self.client.get_transaction_history(
            tx_filter,
            limit=limit
        )
        
        result = {
            'total_found': history.total_found,
            'time_range': {
                'start': history.time_range_covered.start,
                'end': history.time_range_covered.end
            },
            'transactions': []
        }
        
        if verbose:
            print(f"Found {history.total_found} transactions")
            print(f"Time range: {history.time_range_covered.start} to {history.time_range_covered.end}")
            
            if history.transactions:
                print("\nRecent Transactions:")
                print(f"{'Time':<20} {'Operation':<10} {'Table':<20} {'Hash':<16}")
                print("─" * 70)
                
                for tx in history.transactions[:10]:
                    timestamp = tx.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    hash_short = tx.transaction_hash
                    print(f"{timestamp:<20} {tx.operation_type:<10} "
                          f"{tx.table_affected:<20} {hash_short:<16}")
        
        for tx in history.transactions:
            result['transactions'].append({
                'transaction_id': tx.transaction_id,
                'timestamp': tx.timestamp,
                'operation_type': tx.operation_type,
                'database': tx.database_name,
                'table': tx.table_affected,
                'hash': tx.transaction_hash
            })
        
        return result


async def main():
    """Main entry point for the verification tool."""
    parser = argparse.ArgumentParser(
        description='Comprehensive ETRAP Verification Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-o', '--organization',
        default='acme',
        help='Organization ID (default: acme)'
    )
    
    parser.add_argument(
        '-n', '--network',
        default='testnet',
        choices=['testnet', 'mainnet', 'localnet'],
        help='NEAR network (default: testnet)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify a transaction')
    verify_parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='Transaction data as JSON string'
    )
    verify_parser.add_argument(
        '--batch-id',
        help='Specific batch ID to check (optimization hint)'
    )
    verify_parser.add_argument(
        '--table',
        help='Table name hint'
    )
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for a transaction by hash')
    search_parser.add_argument(
        '--hash',
        required=True,
        help='Transaction hash to search for'
    )
    search_parser.add_argument(
        '--depth',
        type=int,
        default=500,
        help='Number of batches to search (default: 500)'
    )
    
    # List batches command
    list_parser = subparsers.add_parser('list-batches', help='List recent batches')
    list_parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Number of batches to show (default: 20)'
    )
    list_parser.add_argument(
        '--database',
        help='Filter by database name'
    )
    list_parser.add_argument(
        '--table',
        help='Filter by table name'
    )
    list_parser.add_argument(
        '--start-date',
        help='Start date (YYYY-MM-DD)'
    )
    list_parser.add_argument(
        '--end-date',
        help='End date (YYYY-MM-DD)'
    )
    
    # Analyze batch command
    analyze_parser = subparsers.add_parser('analyze-batch', help='Analyze a specific batch')
    analyze_parser.add_argument(
        '--batch-id',
        required=True,
        help='Batch ID to analyze'
    )
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Get contract statistics')
    stats_parser.add_argument(
        '--period',
        default='24h',
        choices=['1h', '24h', '7d', '30d', 'all'],
        help='Time period for statistics (default: 24h)'
    )
    
    # Search batches command
    search_batches_parser = subparsers.add_parser('search-batches', help='Search batches')
    search_batches_parser.add_argument(
        '--tx-hash',
        help='Transaction hash to find'
    )
    search_batches_parser.add_argument(
        '--merkle-root',
        help='Merkle root to find'
    )
    search_batches_parser.add_argument(
        '--start-date',
        help='Start date (YYYY-MM-DD)'
    )
    search_batches_parser.add_argument(
        '--end-date',
        help='End date (YYYY-MM-DD)'
    )
    search_batches_parser.add_argument(
        '--max-results',
        type=int,
        default=100,
        help='Maximum results (default: 100)'
    )
    
    # Transaction history command
    history_parser = subparsers.add_parser('history', help='Get transaction history')
    history_parser.add_argument(
        '--operations',
        nargs='+',
        choices=['INSERT', 'UPDATE', 'DELETE'],
        help='Filter by operation types'
    )
    history_parser.add_argument(
        '--start-time',
        help='Start time (ISO format)'
    )
    history_parser.add_argument(
        '--end-time',
        help='End time (ISO format)'
    )
    history_parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Maximum results (default: 100)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Create verifier
    verifier = ComprehensiveVerifier(args.organization, args.network)
    verbose = not args.json
    
    try:
        # Execute command
        if args.command == 'verify':
            # Parse transaction data
            try:
                transaction_data = json.loads(args.data)
            except json.JSONDecodeError:
                print("Error: Invalid JSON data", file=sys.stderr)
                return 1
            
            # Create hints
            hints = {}
            if args.batch_id:
                hints['batch_id'] = args.batch_id
            if args.table:
                hints['table'] = args.table
            
            # Verify
            result = await verifier.verify_transaction(
                transaction_data,
                hints=hints,
                verbose=verbose
            )
            
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            
            return 0 if result['verified'] else 1
        
        elif args.command == 'search':
            result = await verifier.search_by_hash(
                args.hash,
                max_depth=args.depth,
                verbose=verbose
            )
            
            if args.json:
                print(json.dumps(result or {'found': False}, indent=2, default=str))
            elif not result:
                return 1
            
            return 0
        
        elif args.command == 'list-batches':
            filter_criteria = {}
            if args.database:
                filter_criteria['database'] = args.database
            if args.table:
                filter_criteria['table'] = args.table
            if args.start_date:
                filter_criteria['start_date'] = args.start_date
            if args.end_date:
                filter_criteria['end_date'] = args.end_date
            
            result = await verifier.list_batches(
                limit=args.limit,
                filter_criteria=filter_criteria if filter_criteria else None,
                verbose=verbose
            )
            
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            
            return 0
        
        elif args.command == 'analyze-batch':
            result = await verifier.analyze_batch(
                args.batch_id,
                verbose=verbose
            )
            
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            elif not result:
                return 1
            
            return 0
        
        elif args.command == 'stats':
            result = await verifier.get_contract_stats(
                time_period=args.period,
                verbose=verbose
            )
            
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            
            return 0
        
        elif args.command == 'search-batches':
            criteria = {}
            if args.tx_hash:
                criteria['transaction_hash'] = args.tx_hash
            if args.merkle_root:
                criteria['merkle_root'] = args.merkle_root
            if args.start_date:
                criteria['start_date'] = args.start_date
            if args.end_date:
                criteria['end_date'] = args.end_date
            
            result = await verifier.search_batches(
                criteria,
                max_results=args.max_results,
                verbose=verbose
            )
            
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            
            return 0
        
        elif args.command == 'history':
            filter_params = {}
            if args.operations:
                filter_params['operation_types'] = args.operations
            if args.start_time:
                filter_params['start_time'] = args.start_time
            if args.end_time:
                filter_params['end_time'] = args.end_time
            
            result = await verifier.get_transaction_history(
                filter_params,
                limit=args.limit,
                verbose=verbose
            )
            
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            
            return 0
    
    except KeyboardInterrupt:
        print("\n\n👋 Verification cancelled", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        if not args.json:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))