# Test script to validate Ollama setup functionality
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from setup_ollama_secure import OllamaSetupManager, SetupStatus
    print("[OK] Successfully imported OllamaSetupManager")
    
    # Test initialization
    manager = OllamaSetupManager()
    print("[OK] Successfully initialized OllamaSetupManager")
    
    # Test step logging
    manager._log_step("Test Step", "success", "Testing step logging functionality")
    print("[OK] Step logging works correctly")
    
    # Test connectivity check (will fail if Ollama not running, but tests structure)
    print("\n[TEST] Testing setup structure (will show expected failures if Ollama not installed):")
    
    # Just test the installation check method
    try:
        result = manager._check_ollama_installation()
        if result:
            print("[OK] Ollama installation detected")
        else:
            print("[INFO] Ollama not detected (expected if not installed)")
    except Exception as e:
        print(f"[ERROR] Error in installation check: {e}")
    
    print("\n[COMPLETE] Structure validation complete!")
    print("Run 'python setup_ollama_secure.py' or 'setup_ollama.bat' for full setup.")
    
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    sys.exit(1)