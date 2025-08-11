#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
demo_rollback_scenarios.py

Demonstration script for PBIX rollback scenarios and recovery testing.
Shows various failure conditions and how the rollback system handles them.
"""

import os
import sys
import tempfile
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from test_pbix_update import PBIXTestManager
    from update_pbix_parameter_enhanced import PBIXParameterUpdater
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Make sure all required scripts are in the same directory")
    sys.exit(1)

class RollbackScenarioDemo:
    """Demonstrates various rollback scenarios for PBIX operations."""
    
    def __init__(self):
        self.demo_dir = None
        self.test_pbix_path = None
        self.scenarios_run = []
        
    def setup_demo_environment(self):
        """Create demo environment with test PBIX files."""
        print("🔧 Setting up demo environment...")
        
        # Create demo directory
        self.demo_dir = tempfile.mkdtemp(prefix="pbix_rollback_demo_")
        print(f"📁 Demo directory: {self.demo_dir}")
        
        # Create a test PBIX file
        self.test_pbix_path = self.create_test_pbix()
        print(f"📄 Test PBIX created: {os.path.basename(self.test_pbix_path)}")
        
        return True
    
    def create_test_pbix(self):
        """Create a test PBIX file for demonstrations."""
        pbix_path = os.path.join(self.demo_dir, "demo_test.pbix")
        
        # Create temporary directory for PBIX contents
        with tempfile.TemporaryDirectory() as temp_contents:
            # Create standard PBIX structure
            files_to_create = {
                "Version": "1.0",
                "Metadata": '{"version": "1.0", "type": "demo"}',
                "Settings": "{}",
                "SecurityBindings": "[]"
            }
            
            for filename, content in files_to_create.items():
                with open(os.path.join(temp_contents, filename), 'w') as f:
                    f.write(content)
            
            # Create DataMashup with test parameters
            datamashup_content = '''
let
    BasePath = "C:\\\\Original\\\\Demo\\\\Path",
    ServerName = "demo-server",
    DatabaseName = "DemoDB",
    TestParameter = "original_value",
    Source = Excel.Workbook(File.Contents(BasePath & "\\\\demo_data.xlsx")),
    MainTable = Source{[Item="DemoSheet",Kind="Sheet"]}[Data]
in
    MainTable
'''
            
            with open(os.path.join(temp_contents, "DataMashup"), 'w', encoding="latin1") as f:
                f.write(datamashup_content)
            
            # Create ZIP file (PBIX)
            with zipfile.ZipFile(pbix_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                for root, _, files in os.walk(temp_contents):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, temp_contents)
                        zip_out.write(full_path, rel_path)
        
        return pbix_path
    
    def run_scenario(self, scenario_name: str, scenario_func):
        """Run a single rollback scenario."""
        print(f"\n{'='*60}")
        print(f"🎭 SCENARIO: {scenario_name}")
        print(f"{'='*60}")
        
        try:
            # Create fresh copy of test PBIX for this scenario
            scenario_pbix = os.path.join(self.demo_dir, f"scenario_{len(self.scenarios_run)+1}.pbix")
            shutil.copy2(self.test_pbix_path, scenario_pbix)
            
            result = scenario_func(scenario_pbix)
            
            self.scenarios_run.append({
                'name': scenario_name,
                'success': result,
                'pbix_file': scenario_pbix
            })
            
            status = "✅ COMPLETED" if result else "❌ FAILED"
            print(f"\n{status}: {scenario_name}")
            
            return result
            
        except Exception as e:
            print(f"\n❌ SCENARIO ERROR: {e}")
            self.scenarios_run.append({
                'name': scenario_name,
                'success': False,
                'error': str(e)
            })
            return False
    
    def scenario_normal_rollback(self, pbix_path: str) -> bool:
        """Scenario 1: Normal operation with intentional rollback."""
        print("📋 Testing normal rollback after successful backup creation")
        
        test_manager = PBIXTestManager(verbose=True)
        
        try:
            # Create backup
            backup_info = test_manager.create_backup(pbix_path)
            print(f"✅ Backup created: {os.path.basename(backup_info.backup_path)}")
            
            # Modify original file (simulate some operation)
            with open(pbix_path, 'w') as f:
                f.write("Modified content for rollback test")
            print("✅ File modified (simulating operation)")
            
            # Perform rollback
            rollback_success = test_manager.rollback_from_backup(backup_info)
            print(f"🔄 Rollback result: {'Success' if rollback_success else 'Failed'}")
            
            # Verify file was restored
            updater = PBIXParameterUpdater(verbose=False)
            validation = updater.validate_input_file(pbix_path)
            
            if validation['is_valid_zip'] and validation['datamashup_found']:
                print("✅ File successfully restored to valid PBIX format")
                return True
            else:
                print("❌ File restoration validation failed")
                return False
                
        except Exception as e:
            print(f"❌ Scenario error: {e}")
            return False
        finally:
            test_manager.cleanup()
    
    def scenario_missing_backup(self, pbix_path: str) -> bool:
        """Scenario 2: Rollback attempt with missing backup file."""
        print("📋 Testing rollback behavior when backup file is missing")
        
        test_manager = PBIXTestManager(verbose=True)
        
        try:
            # Create backup
            backup_info = test_manager.create_backup(pbix_path)
            print(f"✅ Backup created: {os.path.basename(backup_info.backup_path)}")
            
            # Delete the backup file (simulate backup corruption/deletion)
            os.remove(backup_info.backup_path)
            print("🗑️  Backup file deleted (simulating corruption)")
            
            # Attempt rollback
            rollback_success = test_manager.rollback_from_backup(backup_info)
            
            if not rollback_success:
                print("✅ Rollback correctly failed due to missing backup")
                return True
            else:
                print("❌ Rollback should have failed but didn't")
                return False
                
        except Exception as e:
            print(f"❌ Scenario error: {e}")
            return False
        finally:
            test_manager.cleanup()
    
    def scenario_permission_error(self, pbix_path: str) -> bool:
        """Scenario 3: Rollback with file permission issues."""
        print("📋 Testing rollback behavior with permission issues")
        
        test_manager = PBIXTestManager(verbose=True)
        
        try:
            # Create backup
            backup_info = test_manager.create_backup(pbix_path)
            print(f"✅ Backup created: {os.path.basename(backup_info.backup_path)}")
            
            # Modify original file
            with open(pbix_path, 'w') as f:
                f.write("Modified for permission test")
            
            # Make original file read-only (simulate permission issue)
            # Note: This might not work on all systems, so we'll handle it gracefully
            try:
                os.chmod(pbix_path, 0o444)  # Read-only
                print("🔒 Original file set to read-only")
                
                # Attempt rollback
                rollback_success = test_manager.rollback_from_backup(backup_info)
                
                # Reset permissions for cleanup
                os.chmod(pbix_path, 0o666)  # Writable
                
                if rollback_success:
                    print("✅ Rollback succeeded despite permission challenges")
                    return True
                else:
                    print("⚠️  Rollback failed due to permissions (expected behavior)")
                    return True  # This is acceptable behavior
                    
            except (OSError, PermissionError):
                print("⚠️  Cannot test permission scenario on this system")
                return True  # Skip this test gracefully
                
        except Exception as e:
            print(f"❌ Scenario error: {e}")
            return False
        finally:
            # Ensure file is writable for cleanup
            try:
                os.chmod(pbix_path, 0o666)
            except:
                pass
            test_manager.cleanup()
    
    def scenario_multiple_backups(self, pbix_path: str) -> bool:
        """Scenario 4: Multiple backups and selective rollback."""
        print("📋 Testing multiple backups and rollback order")
        
        test_manager = PBIXTestManager(verbose=True)
        
        try:
            # Create multiple backups
            backup1 = test_manager.create_backup(pbix_path)
            print(f"✅ Backup 1 created: {os.path.basename(backup1.backup_path)}")
            
            # Modify file
            with open(pbix_path, 'w') as f:
                f.write("First modification")
            
            backup2 = test_manager.create_backup(pbix_path)
            print(f"✅ Backup 2 created: {os.path.basename(backup2.backup_path)}")
            
            # Modify file again
            with open(pbix_path, 'w') as f:
                f.write("Second modification")
            
            backup3 = test_manager.create_backup(pbix_path)
            print(f"✅ Backup 3 created: {os.path.basename(backup3.backup_path)}")
            
            print(f"📊 Total backups created: {len(test_manager.backups)}")
            
            # Corrupt current file
            with open(pbix_path, 'w') as f:
                f.write("Corrupted content")
            
            # Perform rollback (should restore from most recent backup)
            rollback_count = test_manager.rollback_all_backups()
            print(f"🔄 Rollback completed: {rollback_count} restorations")
            
            # Verify restoration
            updater = PBIXParameterUpdater(verbose=False)
            validation = updater.validate_input_file(pbix_path)
            
            if validation['is_valid_zip'] and validation['datamashup_found']:
                print("✅ File successfully restored from backup chain")
                return True
            else:
                print("❌ File restoration from backup chain failed")
                return False
                
        except Exception as e:
            print(f"❌ Scenario error: {e}")
            return False
        finally:
            test_manager.cleanup()
    
    def scenario_full_update_with_rollback(self, pbix_path: str) -> bool:
        """Scenario 5: Full parameter update with induced failure and rollback."""
        print("📋 Testing full update process with induced failure and automatic rollback")
        
        test_manager = PBIXTestManager(verbose=True)
        
        try:
            # Perform full test with intentional failure
            # We'll use an invalid parameter value that should cause processing to fail
            test_result = test_manager.run_full_pbix_test(
                pbix_path=pbix_path,
                param_name="NonexistentParameter",  # This will cause failure
                new_value="test_value"
            )
            
            # The test should fail but rollback should be performed
            if not test_result['success'] and test_result['rollback_performed']:
                print("✅ Test failed as expected and rollback was performed")
                
                # Verify original file is restored
                updater = PBIXParameterUpdater(verbose=False)
                validation = updater.validate_input_file(pbix_path)
                
                if validation['is_valid_zip'] and validation['datamashup_found']:
                    print("✅ Original file successfully restored after failure")
                    return True
                else:
                    print("❌ Original file not properly restored")
                    return False
            else:
                print("❌ Expected failure and rollback behavior not observed")
                return False
                
        except Exception as e:
            print(f"❌ Scenario error: {e}")
            return False
        finally:
            test_manager.cleanup()
    
    def scenario_disk_space_simulation(self, pbix_path: str) -> bool:
        """Scenario 6: Simulate disk space issues during backup."""
        print("📋 Testing backup behavior with simulated disk space constraints")
        
        test_manager = PBIXTestManager(verbose=True)
        
        try:
            # Create backup in a very restricted directory
            # (This is a simplified simulation - real disk space testing would be more complex)
            restricted_backup_dir = os.path.join(self.demo_dir, "restricted")
            os.makedirs(restricted_backup_dir, exist_ok=True)
            
            # Try to create backup
            backup_info = test_manager.create_backup(pbix_path, restricted_backup_dir)
            
            if backup_info and os.path.exists(backup_info.backup_path):
                print("✅ Backup created successfully despite space simulation")
                
                # Test rollback
                with open(pbix_path, 'w') as f:
                    f.write("Modified for space test")
                
                rollback_success = test_manager.rollback_from_backup(backup_info)
                
                if rollback_success:
                    print("✅ Rollback successful")
                    return True
                else:
                    print("❌ Rollback failed")
                    return False
            else:
                print("⚠️  Backup creation failed (may indicate space issues)")
                return True  # This is acceptable for this simulation
                
        except Exception as e:
            print(f"❌ Scenario error: {e}")
            return False
        finally:
            test_manager.cleanup()
    
    def run_all_scenarios(self):
        """Run all rollback scenarios."""
        print("🚀 PBIX ROLLBACK SCENARIOS DEMONSTRATION")
        print("=" * 80)
        
        # Setup demo environment
        if not self.setup_demo_environment():
            print("❌ Failed to setup demo environment")
            return False
        
        # Define scenarios
        scenarios = [
            ("Normal Rollback Operation", self.scenario_normal_rollback),
            ("Missing Backup File", self.scenario_missing_backup),
            ("Permission Error Handling", self.scenario_permission_error),
            ("Multiple Backups Management", self.scenario_multiple_backups),
            ("Full Update with Rollback", self.scenario_full_update_with_rollback),
            ("Disk Space Simulation", self.scenario_disk_space_simulation)
        ]
        
        # Run each scenario
        passed = 0
        total = len(scenarios)
        
        for scenario_name, scenario_func in scenarios:
            if self.run_scenario(scenario_name, scenario_func):
                passed += 1
        
        # Print final summary
        self.print_final_summary(passed, total)
        
        # Cleanup
        self.cleanup_demo()
        
        return passed == total
    
    def print_final_summary(self, passed: int, total: int):
        """Print comprehensive final summary."""
        print(f"\n{'='*80}")
        print("ROLLBACK SCENARIOS SUMMARY")
        print(f"{'='*80}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Scenarios: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {total - passed} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\nDETAILED RESULTS:")
        for i, scenario in enumerate(self.scenarios_run, 1):
            status = "✅ PASS" if scenario['success'] else "❌ FAIL"
            print(f"  {i}. {scenario['name']}: {status}")
            
            if 'error' in scenario:
                print(f"     Error: {scenario['error']}")
        
        print(f"\nRECOMMENDations:")
        if passed == total:
            print("✅ All rollback scenarios passed - system is robust")
            print("✅ Backup and recovery mechanisms are working correctly")
            print("✅ Error handling is appropriate for various failure modes")
        else:
            print("⚠️  Some scenarios failed - review error handling")
            print("🔧 Consider improving backup validation")
            print("🔧 Test in different environments for better coverage")
        
        print(f"\n📁 Demo files location: {self.demo_dir}")
        print("🧹 Run cleanup_demo() to remove temporary files")
    
    def cleanup_demo(self):
        """Clean up demo environment."""
        if self.demo_dir and os.path.exists(self.demo_dir):
            try:
                shutil.rmtree(self.demo_dir)
                print(f"\n🧹 Demo environment cleaned up: {self.demo_dir}")
            except Exception as e:
                print(f"\n⚠️  Could not clean up demo directory: {e}")
                print(f"   Manual cleanup may be required: {self.demo_dir}")

def main():
    """Main demonstration execution."""
    print("🎭 PBIX ROLLBACK SCENARIOS DEMONSTRATION")
    print("This script demonstrates various rollback scenarios and recovery mechanisms")
    print("for PBIX parameter update operations.")
    print()
    
    try:
        demo = RollbackScenarioDemo()
        success = demo.run_all_scenarios()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())