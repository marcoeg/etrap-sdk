#!/usr/bin/env python3
"""
Simple Test Script for Batch Verification Fix

This script tests the batch verification fix by directly using the SDK
to verify what the MCP server should be doing.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Add the SDK to the path
import sys
import os
sys.path.insert(0, '/home/marco/Development/mglabs/etrap/near/etrap-sdk/src')

from etrap_sdk import ETRAPClient, S3Config, VerificationHints, TimeRange


class BatchVerificationTester:
    """Test the batch verification fix."""
    
    def __init__(self):
        self.client = ETRAPClient(
            organization_id="lunaris",
            network="testnet",
            s3_config=S3Config(region="us-west-2")
        )
    
    def get_test_transactions(self) -> List[Dict[str, Any]]:
        """Get the 4 test transactions we inserted."""
        return [
            {
                "id": 145,
                "account_id": "TEST800", 
                "amount": "8000.00",
                "type": "C",
                "created_at": "2025-07-01 16:54:07.289142",
                "reference": "Batch test transaction 1"
            },
            {
                "id": 146,
                "account_id": "TEST801",
                "amount": "8100.50", 
                "type": "D",
                "created_at": "2025-07-01 16:54:07.289142",
                "reference": "Batch test transaction 2"
            },
            {
                "id": 147,
                "account_id": "TEST802",
                "amount": "8200.75",
                "type": "C", 
                "created_at": "2025-07-01 16:54:07.289142",
                "reference": "Batch test transaction 3"
            },
            {
                "id": 148,
                "account_id": "TEST803",
                "amount": "8300.25",
                "type": "D",
                "created_at": "2025-07-01 16:54:07.289142", 
                "reference": "Batch test transaction 4"
            }
        ]
    
    async def test_no_hints(self) -> Dict[str, Any]:
        """Test batch verification with no hints - should find all 4 transactions."""
        print("\n🧪 Test 1: No Hints (Should find all 4 transactions)")
        
        transactions = self.get_test_transactions()
        
        start_time = time.time()
        result = await self.client.verify_batch(
            transactions=transactions,
            hints=None  # This is the key fix - None should work like individual verification
        )
        end_time = time.time()
        
        # Analyze results
        total = result.total
        verified = result.verified
        failed = result.failed
        processing_time = int((end_time - start_time) * 1000)
        
        print(f"   📊 Results: {verified}/{total} verified, {failed} failed")
        print(f"   ⏱️  Processing time: {processing_time}ms")
        
        # Check individual results
        for i, tx_result in enumerate(result.results):
            tx_id = transactions[i]["id"]
            verified_status = "✅" if tx_result.verified else "❌"
            batch_id = tx_result.batch_id or "None"
            operation_type = tx_result.operation_type or "None"
            error = tx_result.error or ""
            
            print(f"   {verified_status} TX {tx_id}: Batch {batch_id}, Op: {operation_type}")
            if error:
                print(f"      Error: {error}")
        
        return {
            "total": total,
            "verified": verified,
            "failed": failed,
            "processing_time_ms": processing_time,
            "results": result.results
        }
    
    async def test_individual_verifications(self) -> List[Dict[str, Any]]:
        """Test individual transaction verifications for comparison."""
        print("\n🔍 Individual Transaction Verification (Comparison)")
        
        transactions = self.get_test_transactions()
        results = []
        
        for tx in transactions:
            print(f"   Testing TX {tx['id']}...")
            
            start_time = time.time()
            result = await self.client.verify_transaction(tx)
            end_time = time.time()
            
            verified = result.verified
            batch_id = result.batch_id or "None"
            operation_type = result.operation_type or "None"
            processing_time = int((end_time - start_time) * 1000)
            
            status = "✅" if verified else "❌"
            print(f"   {status} TX {tx['id']}: Batch {batch_id}, Op: {operation_type} ({processing_time}ms)")
            
            results.append({
                "verified": verified,
                "batch_id": batch_id,
                "operation_type": operation_type,
                "processing_time_ms": processing_time,
                "error": result.error
            })
        
        return results
    
    async def test_direct_batch_hints(self) -> Dict[str, Any]:
        """Test with direct batch ID hints."""
        print("\n🧪 Test 2: Direct Batch ID Hints")
        
        transactions = self.get_test_transactions()
        test_results = {}
        
        # Test 1: Batch with 3 transactions
        print("   Testing batch BATCH-2025-07-01-c9de5968 (should find 3/4)...")
        hints = VerificationHints(batch_id="BATCH-2025-07-01-c9de5968")
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["multi_batch"] = {"verified": result.verified, "time": processing_time}
        
        # Test 2: Batch with 1 transaction
        print("   Testing batch BATCH-2025-07-01-56a143c8 (should find 1/4)...")
        hints = VerificationHints(batch_id="BATCH-2025-07-01-56a143c8")
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["single_batch"] = {"verified": result.verified, "time": processing_time}
        
        # Test 3: Non-existent batch
        print("   Testing non-existent batch (should find 0/4)...")
        hints = VerificationHints(batch_id="BATCH-2025-01-01-nonexistent")
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["nonexistent_batch"] = {"verified": result.verified, "time": processing_time}
        
        return test_results
    
    async def test_database_table_hints(self) -> Dict[str, Any]:
        """Test with database and table hints."""
        print("\n🧪 Test 3: Database/Table Hints")
        
        transactions = self.get_test_transactions()
        test_results = {}
        
        # Test 1: Database hint only
        print("   Testing database hint 'etrapdb'...")
        hints = VerificationHints(database_name="etrapdb")
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["database_only"] = {"verified": result.verified, "time": processing_time}
        
        # Test 2: Table hint only
        print("   Testing table hint 'financial_transactions'...")
        hints = VerificationHints(table_name="financial_transactions")
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["table_only"] = {"verified": result.verified, "time": processing_time}
        
        # Test 3: Database + Table combined
        print("   Testing database + table hints combined...")
        hints = VerificationHints(database_name="etrapdb", table_name="financial_transactions")
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["database_table"] = {"verified": result.verified, "time": processing_time}
        
        return test_results
    
    async def test_operation_filtering(self) -> Dict[str, Any]:
        """Test operation type filtering."""
        print("\n🧪 Test 4: Operation Type Filtering")
        
        transactions = self.get_test_transactions()
        test_results = {}
        
        # Test 1: INSERT operations (should find all 4)
        print("   Testing INSERT operation filter...")
        hints = VerificationHints(
            expected_operation="INSERT",
            time_range=TimeRange(
                start=datetime.fromisoformat("2025-07-01T09:54:00"),
                end=datetime.fromisoformat("2025-07-01T09:55:00")
            )
        )
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        
        # Check operation types in results
        insert_ops = sum(1 for r in result.results if r.verified and r.operation_type == "INSERT")
        print(f"   🔍 Operation types verified as INSERT: {insert_ops}")
        test_results["insert_filter"] = {"verified": result.verified, "insert_ops": insert_ops, "time": processing_time}
        
        # Test 2: DELETE operations (should find 0 since these are INSERTs)
        print("   Testing DELETE operation filter...")
        hints = VerificationHints(
            expected_operation="DELETE",
            time_range=TimeRange(
                start=datetime.fromisoformat("2025-07-01T09:54:00"),
                end=datetime.fromisoformat("2025-07-01T09:55:00")
            )
        )
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["delete_filter"] = {"verified": result.verified, "time": processing_time}
        
        # Test 3: UPDATE operations (should find 0)
        print("   Testing UPDATE operation filter...")
        hints = VerificationHints(
            expected_operation="UPDATE",
            time_range=TimeRange(
                start=datetime.fromisoformat("2025-07-01T09:54:00"),
                end=datetime.fromisoformat("2025-07-01T09:55:00")
            )
        )
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["update_filter"] = {"verified": result.verified, "time": processing_time}
        
        return test_results
    
    async def test_time_range_variations(self) -> Dict[str, Any]:
        """Test various time range configurations."""
        print("\n🧪 Test 5: Time Range Variations")
        
        transactions = self.get_test_transactions()
        test_results = {}
        
        # Test 1: Correct narrow range (around actual blockchain time)
        print("   Testing correct narrow time range (09:54:00 - 09:56:00 UTC)...")
        hints = VerificationHints(
            time_range=TimeRange(
                start=datetime.fromisoformat("2025-07-01T09:54:00"),
                end=datetime.fromisoformat("2025-07-01T09:56:00")
            )
        )
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["narrow_range"] = {"verified": result.verified, "time": processing_time}
        
        # Test 2: Broad range around blockchain time
        print("   Testing broad time range (09:00:00 - 11:00:00 UTC)...")
        hints = VerificationHints(
            time_range=TimeRange(
                start=datetime.fromisoformat("2025-07-01T09:00:00"),
                end=datetime.fromisoformat("2025-07-01T11:00:00")
            )
        )
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["broad_range"] = {"verified": result.verified, "time": processing_time}
        
        # Test 3: Wrong timezone (using database time as UTC)
        print("   Testing wrong timezone (database time as UTC: 16:54:00)...")
        hints = VerificationHints(
            time_range=TimeRange(
                start=datetime.fromisoformat("2025-07-01T16:54:00"),  # Database time
                end=datetime.fromisoformat("2025-07-01T16:55:00")
            )
        )
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["wrong_timezone"] = {"verified": result.verified, "time": processing_time}
        
        # Test 4: Future time range (should find 0)
        print("   Testing future time range...")
        hints = VerificationHints(
            time_range=TimeRange(
                start=datetime.fromisoformat("2025-12-01T00:00:00"),
                end=datetime.fromisoformat("2025-12-31T23:59:59")
            )
        )
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["future_range"] = {"verified": result.verified, "time": processing_time}
        
        return test_results
    
    async def test_combined_hints(self) -> Dict[str, Any]:
        """Test combinations of different hint types."""
        print("\n🧪 Test 6: Combined Hints")
        
        transactions = self.get_test_transactions()
        test_results = {}
        
        # Test 1: Operation + Time range
        print("   Testing operation + time range hints...")
        hints = VerificationHints(
            expected_operation="INSERT",
            time_range=TimeRange(
                start=datetime.fromisoformat("2025-07-01T09:54:00"),
                end=datetime.fromisoformat("2025-07-01T09:56:00")
            )
        )
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["operation_time"] = {"verified": result.verified, "time": processing_time}
        
        # Test 2: Database + Table + Time + Operation (comprehensive)
        print("   Testing comprehensive hints (all types)...")
        hints = VerificationHints(
            database_name="etrapdb",
            table_name="financial_transactions",
            expected_operation="INSERT",
            time_range=TimeRange(
                start=datetime.fromisoformat("2025-07-01T09:54:00"),
                end=datetime.fromisoformat("2025-07-01T09:56:00")
            )
        )
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["comprehensive"] = {"verified": result.verified, "time": processing_time}
        
        # Test 3: Batch ID + Operation (validation test)
        print("   Testing batch ID + operation validation...")
        hints = VerificationHints(
            batch_id="BATCH-2025-07-01-c9de5968",
            expected_operation="INSERT"
        )
        start_time = time.time()
        result = await self.client.verify_batch(transactions=transactions, hints=hints)
        end_time = time.time()
        
        processing_time = int((end_time - start_time) * 1000)
        print(f"   📊 Results: {result.verified}/{result.total} verified ({processing_time}ms)")
        test_results["batch_operation"] = {"verified": result.verified, "time": processing_time}
        
        return test_results
    
    async def test_performance_comparison(self) -> Dict[str, Any]:
        """Compare performance of different hint strategies."""
        print("\n🧪 Test 7: Performance Comparison")
        
        transactions = self.get_test_transactions()
        performance_results = {}
        
        # Test scenarios with timing
        scenarios = [
            ("No hints", None),
            ("Direct batch", VerificationHints(batch_id="BATCH-2025-07-01-c9de5968")),
            ("Time range", VerificationHints(
                time_range=TimeRange(
                    start=datetime.fromisoformat("2025-07-01T09:54:00"),
                    end=datetime.fromisoformat("2025-07-01T09:56:00")
                )
            )),
            ("Database hint", VerificationHints(database_name="etrapdb")),
            ("Comprehensive", VerificationHints(
                database_name="etrapdb",
                table_name="financial_transactions",
                expected_operation="INSERT",
                time_range=TimeRange(
                    start=datetime.fromisoformat("2025-07-01T09:54:00"),
                    end=datetime.fromisoformat("2025-07-01T09:56:00")
                )
            ))
        ]
        
        for scenario_name, hints in scenarios:
            print(f"   Testing {scenario_name}...")
            
            # Run test 3 times for average
            times = []
            verified_counts = []
            
            for i in range(3):
                start_time = time.time()
                result = await self.client.verify_batch(transactions=transactions, hints=hints)
                end_time = time.time()
                
                processing_time = int((end_time - start_time) * 1000)
                times.append(processing_time)
                verified_counts.append(result.verified)
            
            avg_time = sum(times) // len(times)
            avg_verified = sum(verified_counts) / len(verified_counts)
            
            print(f"   📊 {scenario_name}: {avg_verified:.1f}/4 verified, {avg_time}ms average")
            performance_results[scenario_name.lower().replace(" ", "_")] = {
                "avg_verified": avg_verified,
                "avg_time_ms": avg_time,
                "times": times
            }
        
        return performance_results
    
    async def run_comprehensive_test(self):
        """Run all test cases and provide summary."""
        print("🔬 ETRAP SDK Batch Verification Comprehensive Test Suite")
        print("=" * 70)
        
        try:
            # Store all test results
            all_results = {}
            
            # Test 1: No hints (main fix validation)
            all_results["no_hints"] = await self.test_no_hints()
            
            # Test 2: Individual verifications for comparison  
            individual_results = await self.test_individual_verifications()
            
            # Test 3: Direct batch hints
            all_results["batch_hints"] = await self.test_direct_batch_hints()
            
            # Test 4: Database/Table hints
            all_results["db_table_hints"] = await self.test_database_table_hints()
            
            # Test 5: Operation filtering
            all_results["operation_hints"] = await self.test_operation_filtering()
            
            # Test 6: Time range variations
            all_results["time_variations"] = await self.test_time_range_variations()
            
            # Test 7: Combined hints
            all_results["combined_hints"] = await self.test_combined_hints()
            
            # Test 8: Performance comparison
            all_results["performance"] = await self.test_performance_comparison()
            
            # Comprehensive Summary
            print("\n📊 COMPREHENSIVE TEST SUMMARY")
            print("=" * 70)
            
            no_hints_verified = all_results["no_hints"]["verified"]
            individual_verified = sum(1 for r in individual_results if r["verified"])
            
            print(f"🎯 CORE FUNCTIONALITY:")
            print(f"   ✅ Batch (No Hints): {no_hints_verified}/4 transactions verified")
            print(f"   👤 Individual Tests: {individual_verified}/4 transactions verified")
            
            # Batch hint results
            batch_results = all_results["batch_hints"]
            print(f"\n🎯 DIRECT BATCH HINTS:")
            print(f"   📦 Multi-batch (3 txs): {batch_results['multi_batch']['verified']}/4 verified")
            print(f"   📦 Single-batch (1 tx): {batch_results['single_batch']['verified']}/4 verified")
            print(f"   📦 Non-existent batch: {batch_results['nonexistent_batch']['verified']}/4 verified")
            
            # Database/Table hints
            db_results = all_results["db_table_hints"]
            print(f"\n🎯 DATABASE/TABLE HINTS:")
            print(f"   🗄️  Database only: {db_results['database_only']['verified']}/4 verified")
            print(f"   📋 Table only: {db_results['table_only']['verified']}/4 verified")
            print(f"   🗄️📋 Database + Table: {db_results['database_table']['verified']}/4 verified")
            
            # Operation filtering
            op_results = all_results["operation_hints"]
            print(f"\n🎯 OPERATION FILTERING:")
            print(f"   ➕ INSERT filter: {op_results['insert_filter']['verified']}/4 verified ({op_results['insert_filter'].get('insert_ops', 0)} INSERT ops)")
            print(f"   ➖ DELETE filter: {op_results['delete_filter']['verified']}/4 verified")
            print(f"   🔄 UPDATE filter: {op_results['update_filter']['verified']}/4 verified")
            
            # Time range variations
            time_results = all_results["time_variations"]
            print(f"\n🎯 TIME RANGE TESTING:")
            print(f"   ⏱️  Narrow range (300ms): {time_results['narrow_range']['verified']}/4 verified")
            print(f"   📅 Broad range (full day): {time_results['broad_range']['verified']}/4 verified")
            print(f"   🌍 Wrong timezone: {time_results['wrong_timezone']['verified']}/4 verified")
            print(f"   🔮 Future range: {time_results['future_range']['verified']}/4 verified")
            
            # Combined hints
            combined_results = all_results["combined_hints"]
            print(f"\n🎯 COMBINED HINTS:")
            print(f"   ⏰➕ Operation + Time: {combined_results['operation_time']['verified']}/4 verified")
            print(f"   🎛️  Comprehensive: {combined_results['comprehensive']['verified']}/4 verified")
            print(f"   📦➕ Batch + Operation: {combined_results['batch_operation']['verified']}/4 verified")
            
            # Performance summary
            perf_results = all_results["performance"]
            print(f"\n🎯 PERFORMANCE COMPARISON:")
            for test_name, results in perf_results.items():
                verified = results['avg_verified']
                time_ms = results['avg_time_ms']
                print(f"   🚀 {test_name.replace('_', ' ').title()}: {verified:.1f}/4 verified, {time_ms}ms avg")
            
            # Key validation
            print(f"\n🎯 KEY VALIDATIONS:")
            if no_hints_verified == individual_verified:
                print("✅ PASS: Batch (no hints) matches individual verification!")
            else:
                print("❌ FAIL: Batch (no hints) doesn't match individual verification!")
            
            if no_hints_verified == 4:
                print("✅ PASS: All 4 transactions found without hints!")
            else:
                print(f"❌ FAIL: Only {no_hints_verified}/4 transactions found without hints!")
            
            # Operation disambiguation validation
            if op_results['insert_filter']['verified'] > 0:
                print("✅ PASS: Operation filtering works!")
            else:
                print("❌ FAIL: Operation filtering not working!")
            
            # Performance validation
            direct_batch_time = perf_results.get('direct_batch', {}).get('avg_time_ms', 0)
            no_hints_time = perf_results.get('no_hints', {}).get('avg_time_ms', 0)
            if direct_batch_time > 0 and direct_batch_time < no_hints_time:
                print("✅ PASS: Direct batch hints improve performance!")
            else:
                print("⚠️  NOTE: Performance improvement not clearly demonstrated")
            
            print(f"\n🎉 COMPREHENSIVE TESTING COMPLETE!")
            print("=" * 70)
        
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main entry point."""
    tester = BatchVerificationTester()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())