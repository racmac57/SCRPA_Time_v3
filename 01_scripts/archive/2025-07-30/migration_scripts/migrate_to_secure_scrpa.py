# 🔄 SCRPA Security Migration Script
# Author: Claude Code (Anthropic)
# Purpose: Safely migrate from current SCRPA to secure version with full backup and rollback
# Features: Complete backup, security audit, safe migration, verification, rollback capability

import os
import sys
import shutil
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
import logging
import hashlib
import ast
import configparser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scrpa_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SecurityFinding:
    """Security audit finding."""
    finding_type: str  # 'api_key', 'external_url', 'dependency', 'config'
    severity: str     # 'high', 'medium', 'low'
    file_path: str
    line_number: int
    content: str
    description: str
    recommendation: str

@dataclass
class BackupManifest:
    """Backup manifest for rollback capability."""
    timestamp: str
    backup_path: str
    original_files: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    checksum_map: Dict[str, str] = field(default_factory=dict)

@dataclass
class MigrationStatus:
    """Track migration step status."""
    step: str
    status: str  # 'pending', 'running', 'success', 'failed', 'skipped'
    message: str
    timestamp: datetime
    details: Optional[Dict] = None

class SCRPASecurityMigrator:
    """Comprehensive SCRPA security migration manager."""
    
    def __init__(self, project_root: str = None):
        """Initialize the migration manager."""
        
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.project_root / f"migration_backup_{self.timestamp}"
        
        # Migration tracking
        self.migration_steps: List[MigrationStatus] = []
        self.security_findings: List[SecurityFinding] = []
        self.backup_manifest: Optional[BackupManifest] = None
        
        # File patterns to analyze
        self.target_files = [
            "llm_report_generator.py",
            "master_scrpa_processor.py", 
            "unified_data_processor.py",
            "python_cadnotes_processor.py",
            "*.py",  # All Python files
            "*.json",  # Config files
            "*.ini",   # Config files
            "*.env*",  # Environment files
        ]
        
        # Security patterns to search for
        self.security_patterns = {
            'openai_api_key': [
                r'openai[._-]?api[._-]?key',
                r'sk-[A-Za-z0-9]{20,}',
                r'OPENAI_API_KEY'
            ],
            'anthropic_api_key': [
                r'anthropic[._-]?api[._-]?key',
                r'ANTHROPIC_API_KEY',
                r'claude[._-]?api[._-]?key'
            ],
            'huggingface_token': [
                r'huggingface[._-]?token',
                r'HF_TOKEN',
                r'hf_[A-Za-z0-9]{20,}'
            ],
            'external_urls': [
                r'https?://(?!localhost|127\.0\.0\.1|::1)[^\s"\']+',
                r'api\.openai\.com',
                r'api\.anthropic\.com',
                r'api-inference\.huggingface\.co',
                r'together\.xyz'
            ],
            'api_endpoints': [
                r'/v1/chat/completions',
                r'/api/generate',
                r'/v1/completions'
            ]
        }
        
        logger.info(f"🔄 SCRPA Security Migrator initialized for {self.project_root}")
    
    def run_complete_migration(self) -> bool:
        """Run the complete migration process."""
        
        print("=" * 70)
        print("🔒 SCRPA SECURITY MIGRATION")
        print("=" * 70)
        print("This script will safely migrate your SCRPA system to the secure version.")
        print("All original files will be backed up with rollback capability.\n")
        
        try:
            # Step 1: Create comprehensive backup
            if not self._create_comprehensive_backup():
                return False
            
            # Step 2: Perform security audit
            if not self._perform_security_audit():
                return False
            
            # Step 3: Review findings with user
            if not self._review_security_findings():
                return False
            
            # Step 4: Execute migration
            if not self._execute_migration():
                return False
            
            # Step 5: Verify migration
            if not self._verify_migration():
                return False
            
            # Step 6: Generate migration report
            self._generate_migration_report()
            
            print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            print(f"📁 Backup location: {self.backup_dir}")
            print("🔄 Rollback available if needed")
            
            return True
            
        except Exception as e:
            self._log_step("Migration", "failed", f"Unexpected error: {str(e)}")
            logger.exception("Migration failed with unexpected error")
            
            print(f"\n❌ MIGRATION FAILED: {str(e)}")
            print("🔄 All original files are safely backed up")
            print("💡 Check migration log for details")
            
            return False
    
    def _log_step(self, step: str, status: str, message: str, details: Optional[Dict] = None):
        """Log a migration step."""
        step_status = MigrationStatus(
            step=step,
            status=status,
            message=message,
            timestamp=datetime.now(),
            details=details
        )
        self.migration_steps.append(step_status)
        
        status_icon = {
            'pending': '[PENDING]',
            'running': '[RUNNING]',
            'success': '[SUCCESS]',
            'failed': '[FAILED]',
            'skipped': '[SKIPPED]'
        }.get(status, '[UNKNOWN]')
        
        print(f"{status_icon} {step}: {message}")
        
        if status == 'failed':
            logger.error(f"FAILED - {step}: {message}")
        else:
            logger.info(f"{status.upper()} - {step}: {message}")
    
    def _create_comprehensive_backup(self) -> bool:
        """Create comprehensive backup of all relevant files."""
        
        self._log_step("Backup Creation", "running", "Creating comprehensive backup...")
        
        try:
            # Create backup directory structure
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize backup manifest
            self.backup_manifest = BackupManifest(
                timestamp=self.timestamp,
                backup_path=str(self.backup_dir)
            )
            
            # Find all relevant files
            files_to_backup = []
            
            for pattern in self.target_files:
                if '*' in pattern:
                    files_to_backup.extend(self.project_root.glob(pattern))
                    files_to_backup.extend(self.project_root.glob(f"**/{pattern}"))
                else:
                    file_path = self.project_root / pattern
                    if file_path.exists():
                        files_to_backup.append(file_path)
            
            # Remove duplicates and ensure we have files
            files_to_backup = list(set(files_to_backup))
            files_to_backup = [f for f in files_to_backup if f.is_file()]
            
            if not files_to_backup:
                self._log_step("Backup Creation", "failed", "No files found to backup")
                return False
            
            self._log_step("Backup Creation", "running", 
                          f"Backing up {len(files_to_backup)} files...")
            
            # Backup each file with directory structure preservation
            for file_path in files_to_backup:
                try:
                    # Calculate relative path to preserve directory structure
                    rel_path = file_path.relative_to(self.project_root)
                    backup_file_path = self.backup_dir / rel_path
                    
                    # Create parent directories
                    backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(file_path, backup_file_path)
                    
                    # Calculate checksum
                    checksum = self._calculate_file_checksum(file_path)
                    
                    # Add to manifest
                    self.backup_manifest.original_files.append(str(rel_path))
                    self.backup_manifest.checksum_map[str(rel_path)] = checksum
                    
                    logger.debug(f"Backed up: {rel_path}")
                    
                except Exception as e:
                    logger.warning(f"Could not backup {file_path}: {e}")
            
            # Save backup manifest
            manifest_path = self.backup_dir / "backup_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump({
                    'timestamp': self.backup_manifest.timestamp,
                    'backup_path': self.backup_manifest.backup_path,
                    'original_files': self.backup_manifest.original_files,
                    'config_files': self.backup_manifest.config_files,
                    'checksum_map': self.backup_manifest.checksum_map
                }, f, indent=2)
            
            self._log_step("Backup Creation", "success", 
                          f"Backup created with {len(self.backup_manifest.original_files)} files")
            
            return True
            
        except Exception as e:
            self._log_step("Backup Creation", "failed", f"Backup failed: {str(e)}")
            return False
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return "error"
    
    def _perform_security_audit(self) -> bool:
        """Perform comprehensive security audit."""
        
        self._log_step("Security Audit", "running", "Scanning for security issues...")
        
        try:
            # Scan all Python files
            python_files = list(self.project_root.glob("**/*.py"))
            
            for file_path in python_files:
                self._scan_file_for_security_issues(file_path)
            
            # Scan configuration files
            config_patterns = ["*.json", "*.ini", "*.env*", "*.cfg"]
            for pattern in config_patterns:
                for file_path in self.project_root.glob(pattern):
                    self._scan_file_for_security_issues(file_path)
                for file_path in self.project_root.glob(f"**/{pattern}"):
                    self._scan_file_for_security_issues(file_path)
            
            # Check environment variables
            self._check_environment_variables()
            
            # Analyze dependencies
            self._analyze_dependencies()
            
            findings_count = len(self.security_findings)
            high_severity = len([f for f in self.security_findings if f.severity == 'high'])
            
            self._log_step("Security Audit", "success", 
                          f"Audit complete: {findings_count} findings ({high_severity} high severity)")
            
            return True
            
        except Exception as e:
            self._log_step("Security Audit", "failed", f"Security audit failed: {str(e)}")
            return False
    
    def _scan_file_for_security_issues(self, file_path: Path):
        """Scan a single file for security issues."""
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Check each line for security patterns
            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()
                
                # Check for API keys
                for key_type, patterns in self.security_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            
                            severity = 'high' if 'api_key' in key_type or 'token' in key_type else 'medium'
                            
                            finding = SecurityFinding(
                                finding_type=key_type,
                                severity=severity,
                                file_path=str(file_path.relative_to(self.project_root)),
                                line_number=line_num,
                                content=line.strip(),
                                description=f"Potential {key_type} found",
                                recommendation=f"Remove {key_type} and use secure local processing"
                            )
                            
                            self.security_findings.append(finding)
                            logger.debug(f"Security finding: {key_type} in {file_path}:{line_num}")
            
            # Additional checks for Python files
            if file_path.suffix == '.py':
                self._scan_python_imports(file_path, content)
                
        except Exception as e:
            logger.warning(f"Could not scan {file_path}: {e}")
    
    def _scan_python_imports(self, file_path: Path, content: str):
        """Scan Python file for external service imports."""
        
        try:
            tree = ast.parse(content)
            
            external_imports = [
                'openai',
                'anthropic',
                'huggingface_hub',
                'transformers',
                'together'
            ]
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in external_imports:
                            finding = SecurityFinding(
                                finding_type='external_dependency',
                                severity='high',
                                file_path=str(file_path.relative_to(self.project_root)),
                                line_number=node.lineno,
                                content=f"import {alias.name}",
                                description=f"External AI service import: {alias.name}",
                                recommendation="Replace with local Ollama processing"
                            )
                            self.security_findings.append(finding)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and any(ext in node.module for ext in external_imports):
                        finding = SecurityFinding(
                            finding_type='external_dependency',
                            severity='high',
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=node.lineno,
                            content=f"from {node.module} import ...",
                            description=f"External AI service import: {node.module}",
                            recommendation="Replace with local Ollama processing"
                        )
                        self.security_findings.append(finding)
                        
        except Exception as e:
            logger.debug(f"Could not parse Python AST for {file_path}: {e}")
    
    def _check_environment_variables(self):
        """Check environment variables for API keys."""
        
        env_patterns = [
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY', 
            'CLAUDE_API_KEY',
            'HF_TOKEN',
            'HUGGINGFACE_TOKEN',
            'TOGETHER_API_KEY'
        ]
        
        for var_name in env_patterns:
            if os.getenv(var_name):
                finding = SecurityFinding(
                    finding_type='environment_variable',
                    severity='high',
                    file_path='environment',
                    line_number=0,
                    content=f"{var_name}=***",
                    description=f"External API key in environment: {var_name}",
                    recommendation=f"Remove {var_name} environment variable"
                )
                self.security_findings.append(finding)
    
    def _analyze_dependencies(self):
        """Analyze project dependencies for external services."""
        
        # Check requirements.txt
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    requirements = f.read()
                
                external_packages = [
                    'openai',
                    'anthropic',
                    'huggingface-hub',
                    'transformers',
                    'together'
                ]
                
                for package in external_packages:
                    if package in requirements.lower():
                        finding = SecurityFinding(
                            finding_type='dependency',
                            severity='medium',
                            file_path='requirements.txt',
                            line_number=0,
                            content=f"Dependency: {package}",
                            description=f"External AI service dependency: {package}",
                            recommendation=f"Remove {package} dependency, use local Ollama"
                        )
                        self.security_findings.append(finding)
                        
            except Exception as e:
                logger.debug(f"Could not analyze requirements.txt: {e}")
    
    def _review_security_findings(self) -> bool:
        """Review security findings with user."""
        
        if not self.security_findings:
            self._log_step("Security Review", "success", "No security issues found")
            return True
        
        print(f"\n🔍 SECURITY AUDIT RESULTS")
        print("=" * 50)
        
        # Group findings by severity
        high_findings = [f for f in self.security_findings if f.severity == 'high']
        medium_findings = [f for f in self.security_findings if f.severity == 'medium']
        low_findings = [f for f in self.security_findings if f.severity == 'low']
        
        if high_findings:
            print(f"\n❌ HIGH SEVERITY ISSUES ({len(high_findings)}):")
            for finding in high_findings[:5]:  # Show first 5
                print(f"   • {finding.description}")
                print(f"     File: {finding.file_path}:{finding.line_number}")
                print(f"     Fix: {finding.recommendation}")
                print()
        
        if medium_findings:
            print(f"\n⚠️ MEDIUM SEVERITY ISSUES ({len(medium_findings)}):")
            for finding in medium_findings[:3]:  # Show first 3
                print(f"   • {finding.description}")
                print(f"     File: {finding.file_path}:{finding.line_number}")
                print()
        
        if len(self.security_findings) > 8:
            print(f"   ... and {len(self.security_findings) - 8} more issues")
        
        print(f"\n📋 MIGRATION PLAN:")
        print("✅ Replace external API calls with local Ollama")
        print("✅ Remove API keys and tokens")
        print("✅ Add data sanitization before AI processing")
        print("✅ Implement localhost-only validation")
        
        while True:
            response = input(f"\n🤔 Continue with migration? (y/n): ").lower().strip()
            if response == 'y':
                self._log_step("Security Review", "success", "User approved migration")
                return True
            elif response == 'n':
                self._log_step("Security Review", "skipped", "User cancelled migration")
                print("Migration cancelled by user.")
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    
    def _execute_migration(self) -> bool:
        """Execute the actual migration steps."""
        
        self._log_step("Migration Execution", "running", "Executing migration steps...")
        
        try:
            # Step 1: Update main LLM generator file
            if not self._migrate_llm_generator():
                return False
            
            # Step 2: Update processor files
            if not self._migrate_processors():
                return False
            
            # Step 3: Create secure configuration
            if not self._create_secure_config():
                return False
            
            # Step 4: Update import statements
            if not self._update_imports():
                return False
            
            self._log_step("Migration Execution", "success", "All migration steps completed")
            return True
            
        except Exception as e:
            self._log_step("Migration Execution", "failed", f"Migration failed: {str(e)}")
            return False
    
    def _migrate_llm_generator(self) -> bool:
        """Migrate the main LLM generator file."""
        
        llm_file = self.project_root / "llm_report_generator.py"
        
        if not llm_file.exists():
            self._log_step("LLM Migration", "skipped", "llm_report_generator.py not found")
            return True
        
        self._log_step("LLM Migration", "running", "Migrating LLM generator...")
        
        try:
            # Read original file
            with open(llm_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace external API configurations
            content = self._replace_external_apis(content)
            
            # Add security imports
            security_imports = '''
# Security imports
from comprehensive_data_sanitizer import ComprehensiveDataSanitizer
from setup_ollama_secure import SecureOllamaClient
'''
            
            # Find import section and add security imports
            import_pattern = r'(import\s+[^\n]+\n|from\s+[^\n]+\n)+'
            match = re.search(import_pattern, content)
            if match:
                content = content[:match.end()] + security_imports + content[match.end():]
            
            # Write updated file
            with open(llm_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._log_step("LLM Migration", "success", "LLM generator migrated to secure version")
            return True
            
        except Exception as e:
            self._log_step("LLM Migration", "failed", f"LLM migration failed: {str(e)}")
            return False
    
    def _replace_external_apis(self, content: str) -> str:
        """Replace external API calls with local Ollama calls."""
        
        # Replace OpenAI calls
        content = re.sub(
            r'openai\.ChatCompletion\.create\([^)]+\)',
            'self.secure_client.generate_text(prompt)',
            content,
            flags=re.MULTILINE | re.DOTALL
        )
        
        # Replace Anthropic calls
        content = re.sub(
            r'anthropic\.completions\.create\([^)]+\)',
            'self.secure_client.generate_text(prompt)',
            content,
            flags=re.MULTILINE | re.DOTALL
        )
        
        # Replace HuggingFace calls
        content = re.sub(
            r'requests\.post\([^)]*huggingface[^)]+\)',
            'self.secure_client.generate_text(prompt)',
            content,
            flags=re.MULTILINE | re.DOTALL
        )
        
        # Remove API key configurations
        content = re.sub(
            r'["\']?(?:openai|anthropic|huggingface)[._-]?api[._-]?key["\']?\s*[:=]\s*[^\n]+',
            '# API key removed for security',
            content,
            flags=re.IGNORECASE
        )
        
        return content
    
    def _migrate_processors(self) -> bool:
        """Migrate processor files."""
        
        processor_files = [
            "master_scrpa_processor.py",
            "unified_data_processor.py", 
            "python_cadnotes_processor.py"
        ]
        
        migrated_count = 0
        
        for filename in processor_files:
            file_path = self.project_root / filename
            
            if not file_path.exists():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Add data sanitization call before any LLM processing
                sanitization_code = '''
    # SECURITY: Sanitize data before AI processing
    sanitizer = ComprehensiveDataSanitizer()
    sanitized_data = sanitizer.sanitize_dataframe(data)
    
    # Audit sanitization
    violations = sanitizer.audit_unsanitized_data(sanitized_data)
    if any(violations.values()):
        logger.warning("Data sanitization violations detected")
'''
                
                # Find function definitions and add sanitization
                content = re.sub(
                    r'(def\s+process_.*?\(.*?\):.*?\n)',
                    r'\1' + sanitization_code,
                    content,
                    flags=re.MULTILINE | re.DOTALL
                )
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                migrated_count += 1
                logger.info(f"Migrated processor: {filename}")
                
            except Exception as e:
                logger.warning(f"Could not migrate {filename}: {e}")
        
        self._log_step("Processor Migration", "success", 
                      f"Migrated {migrated_count} processor files")
        return True
    
    def _create_secure_config(self) -> bool:
        """Create secure configuration file."""
        
        config_path = self.project_root / "secure_scrpa_config.json"
        
        secure_config = {
            "version": "2.0-secure",
            "migration_date": datetime.now().isoformat(),
            "security": {
                "localhost_only": True,
                "data_sanitization": True,
                "audit_logging": True,
                "external_apis_disabled": True
            },
            "ollama": {
                "api_url": "http://localhost:11434",
                "model": "llama2:7b",
                "timeout": 120,
                "max_retries": 3
            },
            "sanitization": {
                "mask_names": True,
                "mask_phones": True,
                "mask_ssns": True,
                "mask_emails": True,
                "block_level_addresses": True
            },
            "backup": {
                "backup_location": str(self.backup_dir),
                "rollback_available": True
            }
        }
        
        try:
            with open(config_path, 'w') as f:
                json.dump(secure_config, f, indent=2)
            
            self._log_step("Config Creation", "success", 
                          f"Secure configuration created: {config_path}")
            return True
            
        except Exception as e:
            self._log_step("Config Creation", "failed", 
                          f"Config creation failed: {str(e)}")
            return False
    
    def _update_imports(self) -> bool:
        """Update import statements in all Python files."""
        
        python_files = list(self.project_root.glob("*.py"))
        updated_count = 0
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove external API imports
                external_imports = [
                    r'import\s+openai.*\n',
                    r'from\s+openai.*\n',
                    r'import\s+anthropic.*\n',
                    r'from\s+anthropic.*\n',
                    r'import\s+huggingface_hub.*\n',
                    r'from\s+huggingface_hub.*\n'
                ]
                
                for pattern in external_imports:
                    content = re.sub(pattern, '# External import removed for security\n', content)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                updated_count += 1
                
            except Exception as e:
                logger.warning(f"Could not update imports in {file_path}: {e}")
        
        self._log_step("Import Updates", "success", 
                      f"Updated imports in {updated_count} files")
        return True
    
    def _verify_migration(self) -> bool:
        """Verify the migration was successful."""
        
        self._log_step("Migration Verification", "running", "Verifying migration...")
        
        try:
            verification_results = {
                'secure_files_present': False,
                'external_apis_removed': False,
                'config_valid': False,
                'sanitization_added': False
            }
            
            # Check if secure files exist
            secure_files = [
                "secure_scrpa_generator.py",
                "comprehensive_data_sanitizer.py",
                "setup_ollama_secure.py"
            ]
            
            verification_results['secure_files_present'] = all(
                (self.project_root / f).exists() for f in secure_files
            )
            
            # Check configuration
            config_path = self.project_root / "secure_scrpa_config.json"
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    verification_results['config_valid'] = config.get('security', {}).get('localhost_only', False)
                except:
                    pass
            
            # Check for remaining external API calls
            python_files = list(self.project_root.glob("*.py"))
            external_api_found = False
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if any(pattern in content.lower() for pattern in ['openai', 'anthropic', 'huggingface']):
                        if 'import' in content or 'from' in content:
                            external_api_found = True
                            break
                except:
                    pass
            
            verification_results['external_apis_removed'] = not external_api_found
            
            # Check for sanitization
            sanitization_found = any(
                'ComprehensiveDataSanitizer' in f.read_text(encoding='utf-8', errors='ignore')
                for f in python_files
                if f.exists()
            )
            verification_results['sanitization_added'] = sanitization_found
            
            # Calculate success rate
            success_count = sum(verification_results.values())
            total_checks = len(verification_results)
            
            if success_count == total_checks:
                self._log_step("Migration Verification", "success", 
                              f"All {total_checks} verification checks passed")
                return True
            else:
                self._log_step("Migration Verification", "failed", 
                              f"Only {success_count}/{total_checks} verification checks passed")
                
                print(f"\n⚠️ VERIFICATION RESULTS:")
                for check, result in verification_results.items():
                    status = "[PASS]" if result else "[FAIL]"
                    print(f"   {status} {check}")
                
                return False
                
        except Exception as e:
            self._log_step("Migration Verification", "failed", 
                          f"Verification error: {str(e)}")
            return False
    
    def _generate_migration_report(self):
        """Generate comprehensive migration report."""
        
        report_path = self.project_root / f"migration_report_{self.timestamp}.json"
        
        report_data = {
            'migration_info': {
                'timestamp': self.timestamp,
                'project_root': str(self.project_root),
                'backup_location': str(self.backup_dir)
            },
            'security_findings': [
                {
                    'type': f.finding_type,
                    'severity': f.severity,
                    'file': f.file_path,
                    'line': f.line_number,
                    'description': f.description,
                    'recommendation': f.recommendation
                }
                for f in self.security_findings
            ],
            'migration_steps': [
                {
                    'step': s.step,
                    'status': s.status,
                    'message': s.message,
                    'timestamp': s.timestamp.isoformat()
                }
                for s in self.migration_steps
            ],
            'rollback_info': {
                'available': True,
                'backup_manifest': str(self.backup_dir / "backup_manifest.json"),
                'instructions': "Run rollback_scrpa_migration.py to restore original files"
            }
        }
        
        try:
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            print(f"\n📄 Migration report saved: {report_path}")
            
        except Exception as e:
            logger.warning(f"Could not save migration report: {e}")
    
    def create_rollback_script(self):
        """Create rollback script for emergency restoration."""
        
        rollback_script = f'''#!/usr/bin/env python3
# SCRPA Migration Rollback Script
# Auto-generated on {datetime.now().isoformat()}

import shutil
import json
from pathlib import Path

def rollback_migration():
    """Rollback SCRPA migration to original state."""
    
    backup_dir = Path("{self.backup_dir}")
    manifest_path = backup_dir / "backup_manifest.json"
    
    if not manifest_path.exists():
        print("❌ Backup manifest not found!")
        return False
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        print("🔄 Rolling back SCRPA migration...")
        
        restored_count = 0
        for rel_path in manifest['original_files']:
            backup_file = backup_dir / rel_path
            original_file = Path("{self.project_root}") / rel_path
            
            if backup_file.exists():
                original_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, original_file)
                restored_count += 1
                print(f"✅ Restored: {{rel_path}}")
        
        print(f"\\n🎉 Rollback complete! Restored {{restored_count}} files.")
        print("🗑️ You may now delete the migration backup directory.")
        
        return True
        
    except Exception as e:
        print(f"❌ Rollback failed: {{e}}")
        return False

if __name__ == "__main__":
    rollback_migration()
'''
        
        rollback_path = self.project_root / "rollback_scrpa_migration.py"
        
        try:
            with open(rollback_path, 'w') as f:
                f.write(rollback_script)
            
            print(f"🔄 Rollback script created: {rollback_path}")
            
        except Exception as e:
            logger.warning(f"Could not create rollback script: {e}")

def main():
    """Main migration function."""
    
    print("🔒 SCRPA Security Migration Tool")
    print("This tool will migrate your SCRPA system to the secure version.")
    print()
    
    # Get project root
    current_dir = Path.cwd()
    project_root = input(f"Project root directory (default: {current_dir}): ").strip()
    
    if not project_root:
        project_root = current_dir
    else:
        project_root = Path(project_root)
    
    if not project_root.exists():
        print(f"❌ Directory not found: {project_root}")
        return 1
    
    try:
        migrator = SCRPASecurityMigrator(str(project_root))
        
        # Create rollback script first
        migrator.create_rollback_script()
        
        # Run migration
        success = migrator.run_complete_migration()
        
        if success:
            print(f"\n🎯 Migration completed successfully!")
            print(f"📁 Backup: {migrator.backup_dir}")
            print(f"🔄 Rollback: rollback_scrpa_migration.py")
            return 0
        else:
            print(f"\n⚠️ Migration completed with issues.")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Migration cancelled by user.")
        return 130
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())