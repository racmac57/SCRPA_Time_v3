# Claude Code Prompts for SCRPA Security Implementation
🕒 2025-07-25-17-41-30
# SCRPA_Time_v2/claude_prompts
# Author: R. A. Carucci  
# Purpose: Step-by-step Claude prompts to secure SCRPA LLM integration

---

## 🚨 **PROMPT 1: IMMEDIATE SECURITY PATCH**

```
Create a secure replacement for my existing SCRPA report generator that:

1. REMOVES all external LLM providers (OpenAI, HuggingFace, Anthropic)
2. ONLY uses local Ollama processing 
3. ADDS mandatory data sanitization before AI processing
4. MASKS sensitive data: names, phones, SSNs, emails, license plates
5. KEEPS addresses at block level only
6. INCLUDES security validation checks

Requirements:
- Must work with existing pandas DataFrame input
- Should log all sanitization actions  
- Must verify localhost-only connections
- Should handle Ollama connection failures gracefully
- Include audit trail for sensitive data handling

File name: secure_scrpa_generator.py
```

---

## 🚨 **PROMPT 2: DATA SANITIZATION CLASS**

```
Create a comprehensive DataSanitizer class for police incident data that:

SANITIZATION RULES:
- Names → "SUBJECT_1", "SUBJECT_2", etc.
- Phone numbers → "XXX-XXX-XXXX" 
- SSNs → "XXX-XX-XXXX"
- Email addresses → "EMAIL_REDACTED"
- License plates → "PLATE_XXX"
- Full addresses → Keep block number + "XX BLOCK [street name]"

FEATURES NEEDED:
- Process entire pandas DataFrames
- Handle multiple text columns simultaneously
- Maintain consistent name replacements across records
- Regex patterns for all sensitive data types
- Audit function to detect unsanitized data
- Logging of all sanitization actions

Include comprehensive regex patterns and test cases.
```

---

## 🚨 **PROMPT 3: OLLAMA SETUP AUTOMATION**

```
Create an automated Ollama setup script for Windows that:

SETUP TASKS:
1. Checks if Ollama is installed
2. Starts Ollama service automatically
3. Downloads and installs Llama2 model
4. Tests connectivity to http://localhost:11434
5. Validates model is working with test prompt
6. Creates service configuration for auto-start

ERROR HANDLING:
- Clear messages if Ollama not installed
- Network connectivity validation
- Model download progress indication  
- Service startup verification
- Connection timeout handling

OUTPUT:
- Step-by-step progress messages
- Success/failure status for each step
- Troubleshooting guidance for failures
- Configuration validation report

File name: setup_ollama_secure.py
```

---

## 🚨 **PROMPT 4: MIGRATION SCRIPT**

```
Create a migration script that safely transitions from the current SCRPA script to secure version:

BACKUP TASKS:
1. Create timestamped backup of existing files
2. Backup current configuration files
3. Export current LLM settings for review
4. Document what external services were being used

SECURITY AUDIT:
1. Scan for hardcoded API keys in source files
2. Check environment variables for external API keys
3. Identify all network connections in current code
4. List all external dependencies

MIGRATION STEPS:
1. Replace existing LLM configuration
2. Update import statements
3. Add security validation calls
4. Update main execution flow
5. Create new secure configuration file

Include rollback capability and verification tests.
```

---

## 🚨 **PROMPT 5: SECURITY VALIDATION SUITE**

```
Create a comprehensive security testing suite for the SCRPA system:

VALIDATION TESTS:
1. Network connectivity - ensure only localhost calls
2. Data sanitization - verify sensitive data is masked
3. LLM processing - confirm local-only operation
4. Configuration audit - check for external API configs
5. File system access - validate secure file handling

TEST SCENARIOS:
- Process sample police data with known sensitive info
- Attempt external network connections (should fail)
- Validate all regex patterns catch sensitive data
- Test error handling when Ollama is offline
- Verify no data leakage in logs or outputs

REPORTING:
- Pass/fail status for each security check
- Detailed findings for any security issues
- Recommendations for fixing identified problems
- Compliance checklist for police data handling

Output clear ✅/❌ status indicators and actionable recommendations.
```

---

## 🚨 **PROMPT 6: POWER BI INTEGRATION FIX**

```
Update my Power BI M Code queries to work with the new secure SCRPA workflow:

CURRENT ISSUES:
- Crime categorization queries are empty
- Reference table lookups not working  
- Need to integrate with secure Python output

REQUIREMENTS:
1. Fix ALL_CRIMES query to include Crime_Category column
2. Use CallTypeUpdatedWithCategories.csv for lookups
3. Enable filtered queries: Motor_Vehicle_Theft, Burglary_Auto, etc.
4. Connect to secure Python-generated CSV output
5. Maintain 7-day cycle calculations

M CODE STRUCTURE:
- Source: 2025_06_24_10_32_17_ALL_RMS.xlsx (Sheet1)
- Reference: CallTypeUpdatedWithCategories.csv
- Columns: Incident_Type_1/2/3 → Crime_Category logic
- Output: Filtered tables for each crime type

Include complete M Code with error handling and performance optimization.
```

---

## 🚨 **PROMPT 7: COMPLETE WORKFLOW SCRIPT**

```
Create a master workflow script that orchestrates the entire secure SCRPA process:

WORKFLOW PHASES:
1. Security validation and system checks
2. Data loading and initial processing  
3. Mandatory sanitization and audit
4. Local AI report generation
5. Chart creation and visualization
6. Power BI data export
7. Final security verification

FEATURES NEEDED:
- Command-line interface with options
- Progress tracking and status updates
- Comprehensive error handling
- Logging of all operations
- Recovery from partial failures
- Integration with existing file structure

EXECUTION OPTIONS:
- --security-check: Validate configuration only
- --test-run: Process sample data  
- --full-process: Complete workflow
- --charts-only: Generate visualizations only
- --export-powerbi: Create Power BI dataset

Include timing estimates and resource usage monitoring.
```

---

## 🚨 **PROMPT 8: CONFIGURATION MANAGEMENT**

```
Create a centralized configuration system for the secure SCRPA workflow:

CONFIGURATION AREAS:
1. File paths and directory structure
2. Secure LLM settings (local only)
3. Data sanitization rules and patterns
4. Power BI integration settings  
5. Logging and audit preferences
6. Security policy enforcement

FILE STRUCTURE:
- config.json: Main configuration file
- security_policy.json: Data handling rules
- sanitization_patterns.json: Regex patterns
- powerbi_settings.json: BI integration config

FEATURES:
- Environment variable overrides
- Configuration validation
- Secure defaults with safety checks
- Easy updates without code changes
- Documentation for each setting
- Import/export for different environments

Include configuration schema validation and user-friendly documentation.
```

---

## 📋 **IMPLEMENTATION CHECKLIST**

Use these prompts in order:

### **IMMEDIATE (Today)**
- [ ] **Prompt 1**: Create secure replacement (2 hours)
- [ ] **Prompt 2**: Build data sanitizer (1 hour)
- [ ] **Prompt 3**: Setup Ollama automation (1 hour)

### **VALIDATION (Tomorrow)**  
- [ ] **Prompt 4**: Create migration script (1.5 hours)
- [ ] **Prompt 5**: Build security test suite (1.5 hours)
- [ ] Test everything with sample data (1 hour)

### **INTEGRATION (Day 3)**
- [ ] **Prompt 6**: Fix Power BI M Code (2 hours)
- [ ] **Prompt 7**: Create master workflow (2 hours)
- [ ] **Prompt 8**: Centralize configuration (1 hour)

### **DEPLOYMENT (Day 4)**
- [ ] Full system testing (2 hours)
- [ ] Documentation and training (1 hour)
- [ ] Production deployment (1 hour)

---

## 🎯 **SUCCESS CRITERIA**

After implementing all prompts, you should have:

✅ **Zero external data transmission**  
✅ **All sensitive data automatically sanitized**  
✅ **Local-only AI processing with Ollama**  
✅ **Working Power BI integration**  
✅ **Comprehensive security validation**  
✅ **Automated workflow with error handling**  
✅ **Complete audit trail for compliance**

---

**🚨 CRITICAL**: Start with Prompts 1-3 immediately to stop any external data transmission!