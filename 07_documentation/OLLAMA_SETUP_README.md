# 🚀 Ollama Secure Setup for SCRPA Processing

## Overview
This automated setup script configures Ollama for secure local AI processing with your SCRPA report generator. It ensures **localhost-only** operation with no external API dependencies.

## Files Included
- `setup_ollama_secure.py` - Main automated setup script
- `setup_ollama.bat` - Windows batch launcher (run as Administrator)
- `test_ollama_setup.py` - Validation script
- `OLLAMA_SETUP_README.md` - This documentation

## Prerequisites
- **Windows 10/11**
- **Python 3.8+** installed and in PATH
- **Internet connection** for model download
- **Administrator privileges** (recommended)
- **4-8 GB free disk space** for AI models

## Quick Start

### Method 1: Batch File (Recommended)
1. Right-click `setup_ollama.bat`
2. Select "Run as administrator"
3. Follow on-screen prompts

### Method 2: Python Script
```cmd
# Run as Administrator
python setup_ollama_secure.py
```

## What the Script Does

### 🔍 Step 1: Installation Check
- Searches for Ollama in PATH
- Checks common installation directories
- Scans Windows Registry for installation
- Provides download instructions if not found

### 🚀 Step 2: Service Management
- Starts Ollama service automatically
- Configures background operation
- Validates service is responding
- Handles port conflicts and firewall issues

### 📡 Step 3: Connectivity Testing
- Tests socket connection to localhost:11434
- Validates HTTP API responses
- Ensures localhost-only operation
- Provides network troubleshooting

### 📥 Step 4: Model Installation
- Downloads recommended AI model (Llama2 7B by default)
- Shows real-time download progress
- Handles network timeouts and retries
- Validates model integrity

### ✅ Step 5: Model Validation
- Tests model with sample prompt
- Measures response time and performance
- Confirms model is working correctly
- Provides performance metrics

### ⚙️ Step 6: Auto-Start Configuration
- Creates Windows startup entries
- Configures automatic service start
- Sets up registry entries
- Provides manual instructions if needed

## Expected Output

```
============================================================
🔒 SECURE OLLAMA SETUP FOR SCRPA PROCESSING
============================================================

✅ Installation Check: Ollama found in PATH: C:\Users\...\ollama.exe
✅ Service Start: Ollama service started successfully (PID: 1234)
✅ Connectivity Test: API connection successful (0 models available)
📥 Downloading llama2:7b model...
   📊 pulling manifest
   📊 pulling 3b8ca1dce0bb... 100%
✅ Model Download: Successfully downloaded llama2:7b
✅ Model Validation: Model responded: 'SUCCESS'
   📊 Load time: 1500ms, Total time: 2.1s
✅ Auto-start Configuration: Startup script created

============================================================
🎉 OLLAMA SETUP COMPLETE!
============================================================
✅ Setup Summary: 6/6 steps completed successfully
🤖 Model: llama2:7b
🔗 API URL: http://localhost:11434
📍 Ollama Path: C:\Users\...\ollama.exe
```

## Troubleshooting

### ❌ Ollama Not Found
**Problem**: Script reports "Ollama not found on system"

**Solutions**:
1. Install Ollama from https://ollama.ai
2. Use Windows Package Manager: `winget install Ollama.Ollama`
3. Add Ollama to system PATH
4. Run script as Administrator

### ❌ Service Start Failed
**Problem**: "Service started but not responding to API calls"

**Solutions**:
1. Check if port 11434 is available: `netstat -an | findstr 11434`
2. Run as Administrator
3. Check Windows Firewall settings
4. Manually start: `ollama serve`

### ❌ Connection Timeout
**Problem**: "Connection timeout - API not responding"

**Solutions**:
1. Wait longer for service startup (can take 2-3 minutes)
2. Check Task Manager for ollama.exe process
3. Verify localhost connectivity
4. Restart Windows and try again

### ❌ Model Download Failed
**Problem**: "Model download failed"

**Solutions**:
1. Check internet connection
2. Verify disk space (models are 4-7 GB)
3. Try smaller model: `ollama pull llama2:7b`
4. Check firewall/antivirus blocking downloads

### ❌ Model Validation Timeout
**Problem**: "Model validation timeout (>60s)"

**Solutions**:
1. First model load can take 1-2 minutes
2. Check system RAM (need 8GB+ for larger models)
3. Try smaller model if system has limited resources
4. Close other applications to free memory

## Security Features

### 🔒 Localhost-Only Operation
- All connections validated to localhost/127.0.0.1 only
- No external API endpoints configured
- Prevents data leakage to external services

### 🛡️ Secure Configuration
- Service runs with minimal privileges
- No network exposure beyond localhost
- Audit logging of all operations
- Comprehensive error handling

## Integration with SCRPA

Once setup is complete, use with your secure SCRPA generator:

```python
from secure_scrpa_generator import SecureSCRPAGenerator

# Initialize with localhost Ollama
generator = SecureSCRPAGenerator("http://localhost:11434")

# Generate secure report
sanitized_data = your_sanitized_dataframe
report = generator.generate_secure_report(sanitized_data)
```

## Performance Expectations

### Model Download Times
- **Llama2 7B**: 4.1 GB - 15-45 minutes depending on connection
- **Llama3.1 8B**: 4.7 GB - 20-60 minutes depending on connection
- **Mistral 7B**: 4.1 GB - 15-45 minutes depending on connection

### Response Times (after initial load)
- **Simple prompts**: 1-5 seconds
- **SCRPA reports**: 10-30 seconds depending on data size
- **First model load**: 30-120 seconds (one-time)

### System Requirements
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space for models and cache
- **CPU**: Modern multi-core processor recommended

## Files Generated

After successful setup:
- `ollama_setup.log` - Detailed setup log
- `ollama_setup_report.json` - JSON configuration report
- Startup scripts in Windows Startup folder
- Registry entries for auto-start

## Maintenance

### Update Models
```cmd
ollama pull llama2:latest
```

### Check Service Status
```cmd
# Check if running
tasklist | findstr ollama

# Test API
curl http://localhost:11434/api/tags
```

### Restart Service
```cmd
# Stop service
taskkill /im ollama.exe /f

# Start service
ollama serve
```

## Support

If you encounter issues not covered in troubleshooting:

1. Check `ollama_setup.log` for detailed error messages
2. Verify system meets minimum requirements
3. Try manual Ollama installation first
4. Run setup script as Administrator
5. Ensure Windows is up to date

---

**Security Notice**: This setup ensures all AI processing remains on your local machine with no external API calls. Your SCRPA data never leaves your system.