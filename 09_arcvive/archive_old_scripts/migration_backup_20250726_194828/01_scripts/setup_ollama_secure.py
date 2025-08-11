# 🚀 Automated Ollama Setup Script for Windows
# Author: Claude Code (Anthropic)
# Purpose: Secure, automated Ollama installation and configuration for SCRPA processing
# Features: Installation check, service management, model download, validation, troubleshooting

import subprocess
import requests
import time
import json
import os
import sys
import socket
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime
import winreg
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ollama_setup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SetupStatus:
    """Track setup progress and status."""
    step: str
    status: str  # 'pending', 'running', 'success', 'failed', 'skipped'
    message: str
    timestamp: datetime
    details: Optional[Dict] = None

class OllamaSetupManager:
    """Comprehensive Ollama setup and configuration manager for Windows."""
    
    def __init__(self):
        """Initialize the setup manager."""
        self.setup_steps: List[SetupStatus] = []
        self.ollama_url = "http://localhost:11434"
        self.recommended_models = ["llama2:7b", "llama3.1:8b", "mistral:7b"]
        self.selected_model = "llama2:7b"  # Default model
        self.ollama_exe_path = None
        
        logger.info("🚀 Ollama Setup Manager initialized")
        
    def run_complete_setup(self) -> bool:
        """Run the complete Ollama setup process."""
        
        print("=" * 60)
        print("🔒 SECURE OLLAMA SETUP FOR SCRPA PROCESSING")
        print("=" * 60)
        print("This script will set up Ollama for secure local AI processing.")
        print("No external APIs will be configured - localhost only!\n")
        
        # Step 1: Check if Ollama is installed
        if not self._check_ollama_installation():
            return False
        
        # Step 2: Start Ollama service
        if not self._start_ollama_service():
            return False
        
        # Step 3: Test connectivity
        if not self._test_connectivity():
            return False
        
        # Step 4: Download and install model
        if not self._setup_model():
            return False
        
        # Step 5: Validate model functionality
        if not self._validate_model():
            return False
        
        # Step 6: Configure auto-start
        if not self._configure_autostart():
            return False
        
        # Step 7: Generate final report
        self._generate_setup_report()
        
        return True
    
    def _log_step(self, step: str, status: str, message: str, details: Optional[Dict] = None):
        """Log a setup step with status."""
        step_status = SetupStatus(
            step=step,
            status=status,
            message=message,
            timestamp=datetime.now(),
            details=details
        )
        self.setup_steps.append(step_status)
        
        # Format status for display
        status_icon = {
            'pending': '⏳',
            'running': '🔄',
            'success': '✅',
            'failed': '❌',
            'skipped': '⏭️'
        }.get(status, '❓')
        
        print(f"{status_icon} {step}: {message}")
        
        if status == 'failed':
            logger.error(f"FAILED - {step}: {message}")
        else:
            logger.info(f"{status.upper()} - {step}: {message}")
    
    def _check_ollama_installation(self) -> bool:
        """Check if Ollama is installed on the system."""
        
        self._log_step("Installation Check", "running", "Checking for Ollama installation...")
        
        # Method 1: Check if ollama.exe is in PATH
        ollama_path = shutil.which("ollama")
        if ollama_path:
            self.ollama_exe_path = ollama_path
            self._log_step("Installation Check", "success", 
                          f"Ollama found in PATH: {ollama_path}")
            return True
        
        # Method 2: Check common installation directories
        common_paths = [
            os.path.expanduser("~\\AppData\\Local\\Programs\\Ollama\\ollama.exe"),
            "C:\\Program Files\\Ollama\\ollama.exe",
            "C:\\Program Files (x86)\\Ollama\\ollama.exe",
            os.path.expanduser("~\\ollama\\ollama.exe")
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                self.ollama_exe_path = path
                self._log_step("Installation Check", "success", 
                              f"Ollama found at: {path}")
                return True
        
        # Method 3: Check Windows Registry
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall") as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if "ollama" in display_name.lower():
                                    install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                    ollama_exe = os.path.join(install_location, "ollama.exe")
                                    if os.path.exists(ollama_exe):
                                        self.ollama_exe_path = ollama_exe
                                        self._log_step("Installation Check", "success", 
                                                      f"Ollama found via registry: {ollama_exe}")
                                        return True
                            except FileNotFoundError:
                                pass
                        i += 1
                    except OSError:
                        break
        except Exception as e:
            logger.debug(f"Registry check failed: {e}")
        
        # Ollama not found - provide installation guidance
        self._log_step("Installation Check", "failed", 
                      "Ollama not found on system")
        
        print("\n🚨 OLLAMA NOT INSTALLED")
        print("Please install Ollama before running this script:")
        print("1. Go to https://ollama.ai")
        print("2. Download Ollama for Windows")
        print("3. Run the installer")
        print("4. Restart this script")
        print("\nAlternatively, you can install via command line:")
        print("  winget install Ollama.Ollama")
        
        return False
    
    def _start_ollama_service(self) -> bool:
        """Start the Ollama service."""
        
        self._log_step("Service Start", "running", "Starting Ollama service...")
        
        try:
            # Check if Ollama is already running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self._log_step("Service Start", "success", 
                              "Ollama service already running")
                return True
        except requests.exceptions.RequestException:
            pass  # Service not running yet
        
        # Start Ollama service
        try:
            if sys.platform == "win32":
                # Start Ollama in background on Windows
                startup_info = subprocess.STARTUPINFO()
                startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startup_info.wShowWindow = subprocess.SW_HIDE
                
                process = subprocess.Popen(
                    [self.ollama_exe_path, "serve"],
                    startupinfo=startup_info,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Give service time to start
                time.sleep(10)
                
                # Verify service started
                for attempt in range(12):  # 60 seconds total
                    try:
                        response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                        if response.status_code == 200:
                            self._log_step("Service Start", "success", 
                                          f"Ollama service started successfully (PID: {process.pid})")
                            return True
                    except requests.exceptions.RequestException:
                        pass
                    
                    time.sleep(5)
                    print(f"   ⏳ Waiting for service to start... ({attempt + 1}/12)")
                
                self._log_step("Service Start", "failed", 
                              "Service started but not responding to API calls")
                return False
                
        except Exception as e:
            self._log_step("Service Start", "failed", 
                          f"Error starting service: {str(e)}")
            
            print("\n🔧 TROUBLESHOOTING - Service Start Failed:")
            print("1. Try running as Administrator")
            print("2. Check if port 11434 is available:")
            print("   netstat -an | findstr 11434")
            print("3. Manually start Ollama:")
            print(f"   {self.ollama_exe_path} serve")
            print("4. Check firewall settings")
            
            return False
    
    def _test_connectivity(self) -> bool:
        """Test connectivity to Ollama API."""
        
        self._log_step("Connectivity Test", "running", 
                      f"Testing connection to {self.ollama_url}...")
        
        # Test 1: Basic socket connection
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', 11434))
            sock.close()
            
            if result != 0:
                self._log_step("Connectivity Test", "failed", 
                              "Cannot connect to localhost:11434")
                print("\n🔧 TROUBLESHOOTING - Connection Failed:")
                print("1. Check if Ollama service is running:")
                print("   tasklist | findstr ollama")
                print("2. Verify port 11434 is listening:")
                print("   netstat -an | findstr 11434")
                print("3. Check for port conflicts")
                return False
                
        except Exception as e:
            self._log_step("Connectivity Test", "failed", 
                          f"Socket connection error: {str(e)}")
            return False
        
        # Test 2: HTTP API connectivity
        max_retries = 6
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    f"{self.ollama_url}/api/tags",
                    timeout=10,
                    headers={'Accept': 'application/json'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    model_count = len(data.get('models', []))
                    
                    self._log_step("Connectivity Test", "success", 
                                  f"API connection successful ({model_count} models available)")
                    return True
                else:
                    self._log_step("Connectivity Test", "failed", 
                                  f"API returned status code: {response.status_code}")
                    return False
                    
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    self._log_step("Connectivity Test", "failed", 
                                  "Connection timeout - API not responding")
                    return False
                else:
                    print(f"   ⏳ Connection timeout, retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(5)
                    
            except requests.exceptions.RequestException as e:
                self._log_step("Connectivity Test", "failed", 
                              f"API request error: {str(e)}")
                return False
        
        return False
    
    def _setup_model(self) -> bool:
        """Download and set up the AI model."""
        
        # First, check what models are available
        self._log_step("Model Setup", "running", "Checking available models...")
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                available_models = [model['name'] for model in data.get('models', [])]
                
                # Check if a recommended model is already installed
                for model in self.recommended_models:
                    if model in available_models:
                        self.selected_model = model
                        self._log_step("Model Setup", "success", 
                                      f"Model {model} already installed")
                        return True
                
                if available_models:
                    self._log_step("Model Setup", "success", 
                                  f"Found {len(available_models)} existing models: {', '.join(available_models[:3])}")
                    # Use first available model
                    self.selected_model = available_models[0]
                    return True
        
        except Exception as e:
            logger.warning(f"Could not check existing models: {e}")
        
        # Download recommended model
        print(f"\n📥 Downloading {self.selected_model} model...")
        print("This may take several minutes depending on your internet connection.")
        
        self._log_step("Model Download", "running", 
                      f"Downloading {self.selected_model}...")
        
        try:
            # Use subprocess to run ollama pull with real-time output
            process = subprocess.Popen(
                [self.ollama_exe_path, "pull", self.selected_model],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Monitor download progress
            last_progress = ""
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                
                if output:
                    output = output.strip()
                    if "pulling" in output.lower() or "%" in output:
                        if output != last_progress:
                            print(f"   📊 {output}")
                            last_progress = output
            
            return_code = process.poll()
            
            if return_code == 0:
                self._log_step("Model Download", "success", 
                              f"Successfully downloaded {self.selected_model}")
                return True
            else:
                self._log_step("Model Download", "failed", 
                              f"Model download failed with code {return_code}")
                
                print("\n🔧 TROUBLESHOOTING - Model Download Failed:")
                print("1. Check internet connection")
                print("2. Try a smaller model: ollama pull llama2:7b")
                print("3. Check disk space (models can be 4-7GB)")
                print("4. Try manual download:")
                print(f"   {self.ollama_exe_path} pull {self.selected_model}")
                
                return False
                
        except Exception as e:
            self._log_step("Model Download", "failed", 
                          f"Error during download: {str(e)}")
            return False
    
    def _validate_model(self) -> bool:
        """Validate that the model is working correctly."""
        
        self._log_step("Model Validation", "running", 
                      f"Testing {self.selected_model} with sample prompt...")
        
        test_prompt = "Hello, please respond with just the word 'SUCCESS' to confirm you are working."
        
        try:
            # Make generation request
            payload = {
                "model": self.selected_model,
                "prompt": test_prompt,
                "stream": False,
                "options": {
                    "num_predict": 10,
                    "temperature": 0.1
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60  # Generous timeout for model loading
            )
            
            if response.status_code == 200:
                data = response.json()
                model_response = data.get('response', '').strip()
                
                if model_response:
                    self._log_step("Model Validation", "success", 
                                  f"Model responded: '{model_response[:50]}...'")
                    
                    # Additional validation info
                    load_duration = data.get('load_duration', 0) / 1_000_000  # Convert to ms
                    total_duration = data.get('total_duration', 0) / 1_000_000_000  # Convert to seconds
                    
                    print(f"   📊 Load time: {load_duration:.0f}ms, Total time: {total_duration:.1f}s")
                    return True
                else:
                    self._log_step("Model Validation", "failed", 
                                  "Model returned empty response")
                    return False
            else:
                self._log_step("Model Validation", "failed", 
                              f"API error: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            self._log_step("Model Validation", "failed", 
                          "Model validation timeout (>60s)")
            
            print("\n🔧 TROUBLESHOOTING - Model Validation Timeout:")
            print("1. Model may be loading for first time (can take 1-2 minutes)")
            print("2. Try with smaller model if system has limited RAM")
            print("3. Check system resources:")
            print("   Task Manager > Performance > Memory")
            
            return False
            
        except Exception as e:
            self._log_step("Model Validation", "failed", 
                          f"Validation error: {str(e)}")
            return False
    
    def _configure_autostart(self) -> bool:
        """Configure Ollama to start automatically."""
        
        self._log_step("Auto-start Configuration", "running", 
                      "Setting up automatic startup...")
        
        try:
            # Method 1: Add to Windows Startup folder
            startup_folder = os.path.join(
                os.path.expanduser("~"),
                "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", 
                "Programs", "Startup"
            )
            
            if os.path.exists(startup_folder):
                batch_file_path = os.path.join(startup_folder, "start_ollama.bat")
                
                batch_content = f'''@echo off
REM Auto-start Ollama for SCRPA processing
"{self.ollama_exe_path}" serve
'''
                
                try:
                    with open(batch_file_path, 'w') as f:
                        f.write(batch_content)
                    
                    self._log_step("Auto-start Configuration", "success", 
                                  f"Startup script created: {batch_file_path}")
                    return True
                    
                except Exception as e:
                    logger.warning(f"Could not create startup script: {e}")
            
            # Method 2: Windows Registry startup entry
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                    0, winreg.KEY_WRITE
                )
                
                winreg.SetValueEx(
                    key, "OllamaService", 0, winreg.REG_SZ, 
                    f'"{self.ollama_exe_path}" serve'
                )
                winreg.CloseKey(key)
                
                self._log_step("Auto-start Configuration", "success", 
                              "Registry startup entry created")
                return True
                
            except Exception as e:
                logger.warning(f"Could not create registry entry: {e}")
            
            # Fallback: Manual instructions
            self._log_step("Auto-start Configuration", "skipped", 
                          "Auto-configuration failed, manual setup required")
            
            print("\n📋 MANUAL AUTO-START SETUP:")
            print("To start Ollama automatically on Windows startup:")
            print("1. Press Win+R, type 'shell:startup', press Enter")
            print("2. Create a new text file called 'start_ollama.bat'")
            print("3. Add this content:")
            print(f'   "{self.ollama_exe_path}" serve')
            print("4. Save the file")
            
            return True  # Don't fail setup for this
            
        except Exception as e:
            self._log_step("Auto-start Configuration", "failed", 
                          f"Configuration error: {str(e)}")
            return True  # Don't fail setup for this
    
    def _generate_setup_report(self):
        """Generate final setup report."""
        
        print("\n" + "=" * 60)
        print("🎉 OLLAMA SETUP COMPLETE!")
        print("=" * 60)
        
        # Summary
        successful_steps = len([s for s in self.setup_steps if s.status == 'success'])
        total_steps = len([s for s in self.setup_steps if s.status in ['success', 'failed']])
        
        print(f"✅ Setup Summary: {successful_steps}/{total_steps} steps completed successfully")
        print(f"🤖 Model: {self.selected_model}")
        print(f"🔗 API URL: {self.ollama_url}")
        print(f"📍 Ollama Path: {self.ollama_exe_path}")
        
        # Configuration details
        print(f"\n📋 Configuration Details:")
        for step in self.setup_steps:
            status_icon = {
                'success': '✅',
                'failed': '❌',
                'skipped': '⏭️'
            }.get(step.status, '❓')
            print(f"   {status_icon} {step.step}: {step.message}")
        
        # Usage instructions
        print(f"\n🚀 Ready for SCRPA Processing!")
        print("You can now use Ollama in your secure SCRPA generator:")
        print()
        print("```python")
        print("from secure_scrpa_generator import SecureSCRPAGenerator")
        print("generator = SecureSCRPAGenerator()")
        print("report = generator.generate_secure_report(your_data)")
        print("```")
        
        # Save detailed report
        report_path = "ollama_setup_report.json"
        report_data = {
            'setup_timestamp': datetime.now().isoformat(),
            'summary': {
                'successful_steps': successful_steps,
                'total_steps': total_steps,
                'model': self.selected_model,
                'api_url': self.ollama_url,
                'ollama_path': self.ollama_exe_path
            },
            'steps': [
                {
                    'step': s.step,
                    'status': s.status,
                    'message': s.message,
                    'timestamp': s.timestamp.isoformat(),
                    'details': s.details
                }
                for s in self.setup_steps
            ]
        }
        
        try:
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"\n📄 Detailed report saved: {report_path}")
        except Exception as e:
            logger.warning(f"Could not save report: {e}")

def main():
    """Main setup function."""
    
    try:
        setup_manager = OllamaSetupManager()
        success = setup_manager.run_complete_setup()
        
        if success:
            print("\n🎯 Setup completed successfully!")
            print("Your system is ready for secure local AI processing.")
            return 0
        else:
            print("\n⚠️ Setup completed with some issues.")
            print("Check the troubleshooting guidance above.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup cancelled by user.")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {str(e)}")
        logger.exception("Unexpected error in main setup")
        return 1

if __name__ == "__main__":
    sys.exit(main())