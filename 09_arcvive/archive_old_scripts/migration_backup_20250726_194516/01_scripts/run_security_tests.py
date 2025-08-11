# 🚀 SCRPA Security Test Runner
# Author: Claude Code (Anthropic)
# Purpose: Main entry point for running comprehensive security validation
# Features: Full test suite execution, report generation, user-friendly interface

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main test runner function."""
    
    print("=" * 70)
    print("🔒 SCRPA COMPREHENSIVE SECURITY VALIDATION SUITE")
    print("=" * 70)
    print()
    print("This comprehensive security test will validate:")
    print("  ✓ Network connectivity (localhost-only enforcement)")
    print("  ✓ Data sanitization (PII masking effectiveness)")
    print("  ✓ LLM processing (local Ollama operation)")
    print("  ✓ Configuration audit (no external API configs)")
    print("  ✓ File system security (log and backup protection)")
    print("  ✓ Error handling (graceful failure scenarios)")
    print()
    print("⏱️  Estimated time: 5-10 minutes")
    print("📊 Reports: JSON + HTML formats with compliance checklist")
    print("🔍 Network monitoring: Real-time external connection detection")
    print()
    
    # Confirm execution
    while True:
        response = input("🤔 Start comprehensive security validation? (y/n): ").lower().strip()
        if response == 'y':
            break
        elif response == 'n':
            print("Security validation cancelled.")
            return 0
        else:
            print("Please enter 'y' for yes or 'n' for no.")
    
    print("\n🚀 Starting security validation...")
    start_time = time.time()
    
    try:
        # Import and run security validation
        from security_validation_suite import SCRPASecurityValidator
        from security_report_generator import SecurityReportGenerator
        
        # Initialize validator
        validator = SCRPASecurityValidator()
        
        # Run comprehensive validation
        validation_report = validator.run_comprehensive_validation()
        
        # Generate compliance reports
        print("\n📊 Generating compliance reports...")
        report_generator = SecurityReportGenerator()
        
        compliance_report = report_generator.generate_compliance_report(validation_report.test_results)
        
        # Save reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        json_report = report_generator.save_json_report(
            compliance_report, 
            f"scrpa_security_report_{timestamp}.json"
        )
        
        html_report = report_generator.generate_html_report(
            compliance_report,
            f"scrpa_security_report_{timestamp}.html"
        )
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Final summary
        print("\n" + "=" * 70)
        print("🎉 SECURITY VALIDATION COMPLETE!")
        print("=" * 70)
        
        print(f"⏱️  Execution Time: {execution_time:.1f} seconds")
        print(f"📊 Tests Executed: {validation_report.total_tests}")
        print(f"✅ Passed: {validation_report.passed_tests}")
        print(f"❌ Failed: {validation_report.failed_tests}")
        print(f"⚠️  Warnings: {validation_report.warning_tests}")
        print(f"🚨 Errors: {validation_report.error_tests}")
        
        # Compliance summary
        overall_status = compliance_report['executive_summary']['overall_status']
        compliance_score = compliance_report['executive_summary']['compliance_score']
        critical_violations = compliance_report['executive_summary']['critical_violations']
        
        print(f"\n🔒 COMPLIANCE SUMMARY:")
        print(f"   Status: {overall_status}")
        print(f"   Score: {compliance_score}%")
        print(f"   Critical Issues: {critical_violations}")
        
        # Certification status
        cert_status = compliance_report['certification_status']['status']
        cert_message = compliance_report['certification_status']['message']
        
        print(f"\n📜 CERTIFICATION: {cert_status}")
        print(f"   {cert_message}")
        
        # Reports generated
        print(f"\n📄 REPORTS GENERATED:")
        if json_report:
            print(f"   📋 JSON Report: {json_report}")
        if html_report:
            print(f"   🌐 HTML Report: {html_report}")
        
        # Recommendations
        if compliance_report['recommendations']:
            print(f"\n🔧 TOP RECOMMENDATIONS:")
            for i, rec in enumerate(compliance_report['recommendations'][:3], 1):
                print(f"   {i}. {rec}")
        
        # Return appropriate exit code
        if critical_violations > 0 or validation_report.failed_tests > 5:
            print(f"\n⚠️  CRITICAL ISSUES FOUND - Address before production use!")
            return 2  # Critical issues
        elif validation_report.failed_tests > 0:
            print(f"\n⚠️  Some issues found - Review recommendations")
            return 1  # Minor issues
        else:
            print(f"\n🎯 ALL TESTS PASSED - System is secure!")
            return 0  # Success
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Security validation cancelled by user.")
        return 130
        
    except ImportError as e:
        print(f"\n❌ Could not import required modules: {e}")
        print("Ensure all security validation files are present:")
        print("  - security_validation_suite.py")
        print("  - test_data_generator.py")
        print("  - network_monitor.py")
        print("  - security_report_generator.py")
        print("  - comprehensive_data_sanitizer.py")
        print("  - secure_scrpa_generator.py")
        return 1
        
    except Exception as e:
        print(f"\n❌ Security validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())