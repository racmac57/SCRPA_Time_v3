# Test script to validate migration functionality
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_migration_structure():
    """Test migration script structure and imports."""
    
    try:
        from migrate_to_secure_scrpa import SCRPASecurityMigrator, SecurityFinding, BackupManifest
        print("[OK] Successfully imported migration classes")
        
        # Test initialization
        migrator = SCRPASecurityMigrator()
        print("[OK] Successfully initialized SCRPASecurityMigrator")
        
        # Test step logging
        migrator._log_step("Test Step", "success", "Testing step logging functionality")
        print("[OK] Step logging works correctly")
        
        # Test security finding creation
        finding = SecurityFinding(
            finding_type="test",
            severity="medium",
            file_path="test.py",
            line_number=1,
            content="test content",
            description="test description",
            recommendation="test recommendation"
        )
        print("[OK] SecurityFinding creation works")
        
        # Test backup manifest
        manifest = BackupManifest(
            timestamp="20250725_143022",
            backup_path="/test/path"
        )
        print("[OK] BackupManifest creation works")
        
        print("\n[COMPLETE] Migration structure validation complete!")
        print("Run 'python migrate_to_secure_scrpa.py' for actual migration.")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

def test_file_structure():
    """Test that all required files are present."""
    
    current_dir = Path(__file__).parent
    
    required_files = [
        "migrate_to_secure_scrpa.py",
        "run_migration.bat", 
        "MIGRATION_GUIDE.md",
        "secure_scrpa_generator.py",
        "comprehensive_data_sanitizer.py",
        "setup_ollama_secure.py"
    ]
    
    print("\n[TEST] Checking required files:")
    
    all_present = True
    for filename in required_files:
        file_path = current_dir / filename
        if file_path.exists():
            print(f"[OK] {filename}")
        else:
            print(f"[MISSING] {filename}")
            all_present = False
    
    if all_present:
        print("\n[SUCCESS] All required files are present")
    else:
        print("\n[WARNING] Some files are missing - migration may not work properly")
    
    return all_present

if __name__ == "__main__":
    print("=" * 50)
    print("SCRPA MIGRATION VALIDATION TEST")
    print("=" * 50)
    
    structure_ok = test_migration_structure()
    files_ok = test_file_structure()
    
    if structure_ok and files_ok:
        print("\n[READY] Migration system is ready to use!")
        print("Run 'run_migration.bat' as Administrator to start migration.")
    else:
        print("\n[NOT READY] Fix issues above before running migration.")
        sys.exit(1)