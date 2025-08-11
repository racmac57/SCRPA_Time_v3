# 🔒 SCRPA Security Testing Suite Guide

## Overview
Comprehensive security validation suite for SCRPA (Strategic Crime Reduction Plan Analysis) system. Ensures all police data processing meets security standards with localhost-only AI processing and complete PII protection.

## 🎯 **Testing Coverage**

### **Network Security Tests**
- ✅ **Localhost-only validation** - Rejects external API URLs
- ✅ **External connection detection** - Real-time network monitoring  
- ✅ **Ollama service availability** - Validates local AI service
- ✅ **Connection timeout handling** - Graceful failure scenarios

### **Data Sanitization Tests**
- ✅ **PII masking effectiveness** - Names, phones, SSNs, emails
- ✅ **License plate redaction** - Vehicle identification protection
- ✅ **Address block-level filtering** - Location privacy protection
- ✅ **Audit function validation** - Detects unsanitized data
- ✅ **Consistent name replacement** - SUBJECT_1, SUBJECT_2 mapping

### **LLM Processing Tests**
- ✅ **Local-only operation** - No external AI service calls
- ✅ **Fallback behavior** - Graceful handling when Ollama offline
- ✅ **Security notices** - Reports include PII protection notices
- ✅ **Processing validation** - Confirms localhost-only generation

### **Configuration Security Tests**
- ✅ **External API detection** - Scans for prohibited configurations
- ✅ **Secure config validation** - Verifies localhost-only settings
- ✅ **Environment variable check** - No external API keys exposed

### **File System Security Tests**
- ✅ **Log file protection** - No sensitive data in logs
- ✅ **Backup security** - Proper backup file permissions
- ✅ **Audit trail integrity** - Complete operation logging

### **Error Handling Tests**
- ✅ **Offline resilience** - System functions when AI unavailable
- ✅ **Invalid data handling** - Graceful processing of malformed input
- ✅ **Security failure modes** - Fails securely, not openly

## 📁 **File Structure**

```
security_validation_suite.py       # Main test orchestrator
├── test_data_generator.py         # Generates realistic test data with PII
├── network_monitor.py             # Real-time network connection monitoring  
├── security_report_generator.py   # Compliance reports (JSON + HTML)
├── run_security_tests.py          # User-friendly test runner
├── run_security_tests.bat         # Windows batch launcher
└── test_security_suite.py         # Component validation tests
```

## 🚀 **Quick Start**

### **Method 1: Batch File (Recommended)**
```cmd
# Right-click and "Run as administrator"
run_security_tests.bat
```

### **Method 2: Python Script**
```cmd
python run_security_tests.py
```

### **Method 3: Component Testing**
```cmd
# Test individual components
python test_security_suite.py

# Generate test data
python test_data_generator.py

# Test network monitoring
python network_monitor.py

# Generate sample report
python security_report_generator.py
```

## 📊 **Expected Output**

### **Test Execution Flow**
```
🔒 SCRPA COMPREHENSIVE SECURITY VALIDATION SUITE
================================================================

✅ [NETWORK] Localhost URL Validation: Valid localhost URL accepted
✅ [NETWORK] External URL Rejection: External URL correctly rejected  
✅ [NETWORK] Ollama Service Availability: Service running on localhost:11434
✅ [NETWORK] External Network Calls: No external connections detected

✅ [SANITIZATION] Data Sanitization Effectiveness: All sensitive data properly sanitized
✅ [SANITIZATION] Address Block-Level Sanitization: Addresses correctly sanitized
✅ [SANITIZATION] Sanitization Audit Function: Audit correctly detected violations

✅ [LLM] Local-Only LLM Processing: Report generated using local processing only
✅ [LLM] LLM Fallback Behavior: Fallback mode activated when Ollama unavailable

✅ [CONFIG] External API Configuration Check: No external API configurations found
✅ [CONFIG] Secure Configuration Validation: All security settings properly configured

✅ [FILESYSTEM] Log File Security Check: No sensitive data found in log files
✅ [FILESYSTEM] Backup File Security: Backup directories properly secured

✅ [ERROR] Ollama Offline Error Handling: Graceful fallback when Ollama offline
✅ [ERROR] Invalid Data Error Handling: Invalid data handled gracefully

🔍 Network monitoring active - watching for external connections...
🔍 Network monitoring stopped: 0 connections, 0 alerts

🎉 SECURITY VALIDATION COMPLETE!
================================================================
⏱️  Execution Time: 127.3 seconds
📊 Tests Executed: 16
✅ Passed: 16
❌ Failed: 0
⚠️  Warnings: 0
🚨 Errors: 0

🔒 COMPLIANCE SUMMARY:
   Status: COMPLIANT
   Score: 100.0%
   Critical Issues: 0

📜 CERTIFICATION: CERTIFIED
   System meets all police data security requirements

📄 REPORTS GENERATED:
   📋 JSON Report: scrpa_security_report_20250725_152345.json
   🌐 HTML Report: scrpa_security_report_20250725_152345.html

🎯 ALL TESTS PASSED - System is secure!
```

### **Failure Scenario Example**
```
❌ [NETWORK] External Network Calls: Detected 2 external connections
   🚨 CRITICAL: Connection to api.openai.com detected
   Process: python.exe (PID: 1234)
   Address: api.openai.com:443

⚠️ [SANITIZATION] Data Sanitization Effectiveness: Found 3 sanitization failures
   - phones found in narrative: Contact at 555-123-4567...
   - ssns found in officer_notes: SSN 123-45-6789 verified...

❌ CRITICAL SECURITY ISSUES FOUND
================================================================
❌ 2 critical security violations detected
❌ System NOT SAFE for police data processing  
❌ Must fix all critical issues before use

🔧 TOP RECOMMENDATIONS:
   1. Block external AI service access immediately
   2. Review and fix sanitization patterns
   3. Verify SCRPA is using localhost-only processing
```

## 📋 **Compliance Checklist**

### **CJIS Security Policy Requirements**
- ✅ **Data Protection (DP)**
  - DP-001: PII sanitized before AI processing
  - DP-002: SSNs masked or redacted  
  - DP-003: Phone/email protection
  - DP-004: Block-level addresses only
  - DP-005: Consistent name masking

- ✅ **Network Security (NS)**  
  - NS-001: Localhost-only AI processing
  - NS-002: No external API connections
  - NS-003: Network monitoring active
  - NS-004: Localhost configuration validated

- ✅ **Access Control (AC)**
  - AC-001: No external API keys stored
  - AC-002: Log files secured
  - AC-003: Backup files protected

- ✅ **Audit Logging (AL)**
  - AL-001: Sanitization operations logged
  - AL-002: Complete audit trail
  - AL-003: Security violations flagged

- ✅ **Error Handling (EH)**
  - EH-001: Secure failure modes
  - EH-002: Invalid data protection
  - EH-003: No sensitive error exposure

## 🔧 **Test Data Specifications**

### **Generated Test Data Contains:**
- **Names**: ~80 realistic police names (officers, victims, suspects)
- **Phone Numbers**: ~60 in various formats (555-123-4567, (555) 123-4567)
- **SSNs**: ~40 test SSNs (invalid ranges for safety)
- **Email Addresses**: ~40 realistic email patterns
- **License Plates**: ~40 various state formats
- **Credit Cards**: ~20 test card numbers
- **Addresses**: ~20 realistic street addresses

### **Edge Cases Tested:**
- Multiple PII formats in single field
- PII without spaces/punctuation  
- Case sensitivity variations
- Names with special characters
- Partially masked data patterns

## 🌐 **Network Monitoring Details**

### **Monitored Connections**
- **Safe Hosts**: localhost, 127.0.0.1, ::1, private networks
- **Suspicious Hosts**: External IPs, non-local domains
- **Dangerous Hosts**: api.openai.com, api.anthropic.com, AI services

### **Security Alerts**
- **Critical**: Connections to AI services (immediate alert)
- **Medium**: Suspicious external connections  
- **Low**: Unexpected local connections

### **Process Monitoring**
- **Python processes**: Monitor for external API calls
- **Ollama processes**: Validate localhost-only operation
- **Network tools**: Detect curl, wget, external requests

## 📊 **Reports Generated**

### **JSON Report (Technical)**
```json
{
  "executive_summary": {
    "overall_status": "COMPLIANT",
    "compliance_score": 100.0,
    "critical_violations": 0,
    "compliant_requirements": 18
  },
  "compliance_statistics": {
    "status_breakdown": {
      "compliant": 18,
      "non_compliant": 0
    }
  },
  "certification_status": {
    "status": "CERTIFIED",
    "message": "System meets all police data security requirements"
  }
}
```

### **HTML Report (Visual)**
- Executive dashboard with compliance score
- Color-coded requirement status
- Category-wise compliance breakdown  
- Critical findings highlighted
- Actionable recommendations
- Certification status with validity

## 🚨 **Common Issues & Solutions**

### **Network Connection Failures**
```
❌ Cannot establish secure connection to Ollama
```
**Solution**: Run `setup_ollama_secure.py` first

### **Data Sanitization Failures**
```
❌ Found 5 sanitization failures
```
**Solution**: Update regex patterns in `comprehensive_data_sanitizer.py`

### **Permission Errors**
```
❌ Access denied to backup directory
```  
**Solution**: Run as Administrator

### **Missing Dependencies**
```
❌ Could not import required modules
```
**Solution**: `pip install pandas psutil requests`

## 🎯 **Integration with SCRPA Workflow**

### **Pre-Production Checklist**
1. ✅ Run complete security validation suite
2. ✅ Verify 100% compliance score
3. ✅ Confirm CERTIFIED status
4. ✅ Review all generated reports
5. ✅ Address any warnings or recommendations
6. ✅ Save audit reports for compliance records

### **Regular Security Testing** 
- **Weekly**: Quick validation (`test_security_suite.py`)
- **Monthly**: Full security suite (`run_security_tests.py`)
- **After Changes**: Complete validation before deployment
- **Annual**: Comprehensive audit with external review

### **Production Monitoring**
- Monitor network connections during operation
- Review sanitization audit logs regularly  
- Validate no external API configurations added
- Maintain current security reports for compliance

---

**🔒 Security Notice**: This testing suite ensures your SCRPA system meets the highest standards for police data processing security. All testing uses synthetic data and validates localhost-only AI processing with comprehensive PII protection.