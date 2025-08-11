# 📊 Security Report Generator for SCRPA
# Author: Claude Code (Anthropic)  
# Purpose: Generate comprehensive security validation reports with compliance checklists
# Features: Police data compliance, CJIS standards, detailed findings, actionable recommendations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class ComplianceRequirement:
    """Represents a compliance requirement."""
    requirement_id: str
    category: str
    description: str
    status: str  # 'compliant', 'non_compliant', 'partial', 'not_tested'
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_level: str = 'medium'  # 'low', 'medium', 'high', 'critical'

class SecurityReportGenerator:
    """Generate comprehensive security validation reports with compliance checklists."""
    
    def __init__(self):
        """Initialize the security report generator."""
        
        # Define police data compliance requirements based on CJIS standards
        self.compliance_requirements = {
            'data_protection': [
                ComplianceRequirement(
                    'DP-001',
                    'Data Protection',
                    'Personal Identifiable Information (PII) must be sanitized before AI processing',
                    'not_tested',
                    risk_level='critical'
                ),
                ComplianceRequirement(
                    'DP-002', 
                    'Data Protection',
                    'Social Security Numbers must be masked or redacted',
                    'not_tested',
                    risk_level='critical'
                ),
                ComplianceRequirement(
                    'DP-003',
                    'Data Protection',
                    'Phone numbers and email addresses must be protected',
                    'not_tested',
                    risk_level='high'
                ),
                ComplianceRequirement(
                    'DP-004',
                    'Data Protection',
                    'Addresses must be limited to block-level only',
                    'not_tested',
                    risk_level='medium'
                ),
                ComplianceRequirement(
                    'DP-005',
                    'Data Protection',
                    'Names must be consistently masked across all records',
                    'not_tested',
                    risk_level='high'
                )
            ],
            'network_security': [
                ComplianceRequirement(
                    'NS-001',
                    'Network Security',
                    'All AI processing must occur on localhost only',
                    'not_tested',
                    risk_level='critical'
                ),
                ComplianceRequirement(
                    'NS-002',
                    'Network Security',
                    'No external API connections permitted during processing',
                    'not_tested',
                    risk_level='critical'
                ),
                ComplianceRequirement(
                    'NS-003',
                    'Network Security',
                    'Network monitoring must detect any external connections',
                    'not_tested',
                    risk_level='high'
                ),
                ComplianceRequirement(
                    'NS-004',
                    'Network Security',
                    'System must validate localhost-only configuration',
                    'not_tested',
                    risk_level='high'
                )
            ],
            'access_control': [
                ComplianceRequirement(
                    'AC-001',
                    'Access Control',
                    'No API keys or external credentials stored in system',
                    'not_tested',
                    risk_level='critical'
                ),
                ComplianceRequirement(
                    'AC-002',
                    'Access Control',
                    'Log files must not contain sensitive information',
                    'not_tested',
                    risk_level='high'
                ),
                ComplianceRequirement(
                    'AC-003',
                    'Access Control',
                    'Backup files must be properly secured',
                    'not_tested',
                    risk_level='medium'
                )
            ],
            'audit_logging': [
                ComplianceRequirement(
                    'AL-001',
                    'Audit Logging',
                    'All data sanitization operations must be logged',
                    'not_tested',
                    risk_level='high'
                ),
                ComplianceRequirement(
                    'AL-002',
                    'Audit Logging',
                    'System must provide audit trail of all processing',
                    'not_tested',
                    risk_level='medium'
                ),
                ComplianceRequirement(
                    'AL-003',
                    'Audit Logging',
                    'Security violations must be immediately flagged',
                    'not_tested',
                    risk_level='high'
                )
            ],
            'error_handling': [
                ComplianceRequirement(
                    'EH-001',
                    'Error Handling',
                    'System must fail securely when AI service unavailable',
                    'not_tested',
                    risk_level='medium'
                ),
                ComplianceRequirement(
                    'EH-002',
                    'Error Handling',
                    'Invalid data must be handled without exposure',
                    'not_tested',
                    risk_level='medium'
                ),
                ComplianceRequirement(
                    'EH-003',
                    'Error Handling',
                    'Error messages must not reveal sensitive information',
                    'not_tested',
                    risk_level='high'
                )
            ]
        }
        
        logger.info("Security Report Generator initialized with compliance requirements")
    
    def update_compliance_status(self, test_results: List[Any]) -> None:
        """Update compliance status based on test results."""
        
        # Map test results to compliance requirements
        test_mapping = {
            'Data Sanitization Effectiveness': ['DP-001', 'DP-002', 'DP-003', 'DP-005'],
            'Address Block-Level Sanitization': ['DP-004'],
            'Localhost URL Validation': ['NS-001', 'NS-004'],
            'External Network Calls': ['NS-002'],
            'Network Security Tests': ['NS-003'],
            'External API Configuration Check': ['AC-001'],
            'Log File Security Check': ['AC-002'],
            'Backup File Security': ['AC-003'],
            'Sanitization Audit Function': ['AL-001', 'AL-003'],
            'Ollama Offline Error Handling': ['EH-001'],
            'Invalid Data Error Handling': ['EH-002']
        }
        
        # Update requirement statuses based on test results
        for test_result in test_results:
            test_name = test_result.test_name
            test_status = test_result.status
            
            # Find matching requirements
            requirement_ids = []
            for pattern, req_ids in test_mapping.items():
                if pattern in test_name:
                    requirement_ids.extend(req_ids)
            
            # Update each matching requirement
            for req_id in requirement_ids:
                req = self._find_requirement(req_id)
                if req:
                    # Map test status to compliance status
                    if test_status == 'pass':
                        req.status = 'compliant'
                        req.evidence.append(f"Test '{test_name}' passed")
                    elif test_status == 'fail':
                        req.status = 'non_compliant'
                        req.evidence.append(f"Test '{test_name}' failed: {test_result.message}")
                        if test_result.recommendations:
                            req.recommendations.extend(test_result.recommendations)
                    elif test_status == 'warning':
                        req.status = 'partial'
                        req.evidence.append(f"Test '{test_name}' had warnings: {test_result.message}")
                        if test_result.recommendations:
                            req.recommendations.extend(test_result.recommendations)
                    else:  # error
                        req.status = 'not_tested'
                        req.evidence.append(f"Test '{test_name}' could not be completed")
    
    def _find_requirement(self, req_id: str) -> Optional[ComplianceRequirement]:
        """Find a compliance requirement by ID."""
        for category_reqs in self.compliance_requirements.values():
            for req in category_reqs:
                if req.requirement_id == req_id:
                    return req
        return None
    
    def generate_compliance_report(self, test_results: List[Any] = None) -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        
        if test_results:
            self.update_compliance_status(test_results)
        
        # Calculate compliance statistics
        all_requirements = []
        for category_reqs in self.compliance_requirements.values():
            all_requirements.extend(category_reqs)
        
        status_counts = {
            'compliant': len([r for r in all_requirements if r.status == 'compliant']),
            'non_compliant': len([r for r in all_requirements if r.status == 'non_compliant']),
            'partial': len([r for r in all_requirements if r.status == 'partial']),
            'not_tested': len([r for r in all_requirements if r.status == 'not_tested'])
        }
        
        # Calculate risk exposure
        risk_counts = {
            'critical': len([r for r in all_requirements if r.risk_level == 'critical' and r.status != 'compliant']),
            'high': len([r for r in all_requirements if r.risk_level == 'high' and r.status != 'compliant']),
            'medium': len([r for r in all_requirements if r.risk_level == 'medium' and r.status != 'compliant']),
            'low': len([r for r in all_requirements if r.risk_level == 'low' and r.status != 'compliant'])
        }
        
        # Overall compliance score
        compliant_count = status_counts['compliant']
        total_count = len(all_requirements)
        compliance_score = (compliant_count / total_count * 100) if total_count > 0 else 0
        
        # Determine overall status
        if risk_counts['critical'] > 0:
            overall_status = 'CRITICAL_VIOLATIONS'
        elif risk_counts['high'] > 2 or status_counts['non_compliant'] > 5:
            overall_status = 'MAJOR_ISSUES'
        elif risk_counts['high'] > 0 or status_counts['non_compliant'] > 0:
            overall_status = 'MINOR_ISSUES'
        elif status_counts['not_tested'] > 5:
            overall_status = 'INCOMPLETE_TESTING'
        else:
            overall_status = 'COMPLIANT'
        
        # Generate detailed requirements by category
        requirements_by_category = {}
        for category, reqs in self.compliance_requirements.items():
            requirements_by_category[category] = [
                {
                    'id': req.requirement_id,
                    'description': req.description,
                    'status': req.status,
                    'risk_level': req.risk_level,
                    'evidence': req.evidence,
                    'recommendations': list(set(req.recommendations))  # Remove duplicates
                }
                for req in reqs
            ]
        
        # Collect critical findings
        critical_findings = []
        for req in all_requirements:
            if req.risk_level == 'critical' and req.status != 'compliant':
                critical_findings.append({
                    'requirement_id': req.requirement_id,
                    'description': req.description,
                    'status': req.status,
                    'evidence': req.evidence,
                    'recommendations': req.recommendations
                })
        
        # Generate recommendations
        all_recommendations = []
        for req in all_requirements:
            if req.status != 'compliant' and req.recommendations:
                all_recommendations.extend(req.recommendations)
        
        unique_recommendations = list(set(all_recommendations))[:10]  # Top 10 unique recommendations
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'Police Data Security Compliance',
                'standards': ['CJIS', 'SCRPA Security Framework'],
                'total_requirements': total_count
            },
            'executive_summary': {
                'overall_status': overall_status,
                'compliance_score': round(compliance_score, 1),
                'critical_violations': risk_counts['critical'],
                'high_risk_issues': risk_counts['high'],
                'compliant_requirements': status_counts['compliant'],
                'non_compliant_requirements': status_counts['non_compliant']
            },
            'compliance_statistics': {
                'status_breakdown': status_counts,
                'risk_exposure': risk_counts,
                'category_compliance': self._calculate_category_compliance()
            },
            'critical_findings': critical_findings,
            'requirements_by_category': requirements_by_category,
            'recommendations': unique_recommendations,
            'certification_status': self._determine_certification_status(overall_status, risk_counts)
        }
        
        return report
    
    def _calculate_category_compliance(self) -> Dict[str, Dict[str, Any]]:
        """Calculate compliance statistics by category."""
        
        category_stats = {}
        
        for category, reqs in self.compliance_requirements.items():
            compliant = len([r for r in reqs if r.status == 'compliant'])
            total = len(reqs)
            compliance_rate = (compliant / total * 100) if total > 0 else 0
            
            # Critical issues in category
            critical_issues = len([r for r in reqs if r.risk_level == 'critical' and r.status != 'compliant'])
            
            category_stats[category] = {
                'compliant_count': compliant,
                'total_count': total,
                'compliance_rate': round(compliance_rate, 1),
                'critical_issues': critical_issues,
                'status': 'PASS' if compliance_rate >= 80 and critical_issues == 0 else 'FAIL'
            }
        
        return category_stats
    
    def _determine_certification_status(self, overall_status: str, risk_counts: Dict[str, int]) -> Dict[str, Any]:
        """Determine certification status for police data processing."""
        
        if overall_status == 'COMPLIANT':
            status = 'CERTIFIED'
            message = 'System meets all police data security requirements'
            valid_until = (datetime.now().replace(year=datetime.now().year + 1)).isoformat()
        elif overall_status == 'MINOR_ISSUES':
            status = 'PROVISIONAL'
            message = 'System approved with minor issues to be addressed'
            valid_until = (datetime.now().replace(month=datetime.now().month + 3)).isoformat()
        else:
            status = 'NOT_CERTIFIED'
            message = 'System does not meet security requirements for police data'
            valid_until = None
        
        return {
            'status': status,
            'message': message,
            'valid_until': valid_until,
            'conditions': self._get_certification_conditions(risk_counts)
        }
    
    def _get_certification_conditions(self, risk_counts: Dict[str, int]) -> List[str]:
        """Get conditions for certification."""
        
        conditions = []
        
        if risk_counts['critical'] > 0:
            conditions.append(f"Resolve {risk_counts['critical']} critical security violations")
        
        if risk_counts['high'] > 0:
            conditions.append(f"Address {risk_counts['high']} high-risk security issues")
        
        if risk_counts['medium'] > 5:
            conditions.append(f"Fix {risk_counts['medium']} medium-risk issues")
        
        return conditions
    
    def generate_html_report(self, report_data: Dict[str, Any], output_path: str = None) -> str:
        """Generate HTML format security report."""
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"security_compliance_report_{timestamp}.html"
        
        # Get status colors and icons
        def get_status_style(status: str) -> Dict[str, str]:
            styles = {
                'compliant': {'color': '#28a745', 'icon': '✅'},
                'non_compliant': {'color': '#dc3545', 'icon': '❌'},
                'partial': {'color': '#ffc107', 'icon': '⚠️'},
                'not_tested': {'color': '#6c757d', 'icon': '❓'}
            }
            return styles.get(status, {'color': '#6c757d', 'icon': '❓'})
        
        def get_risk_style(risk: str) -> str:
            colors = {
                'critical': '#dc3545',
                'high': '#fd7e14', 
                'medium': '#ffc107',
                'low': '#28a745'
            }
            return colors.get(risk, '#6c757d')
        
        # Build HTML content
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SCRPA Security Compliance Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: #1e3a8a; color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 2.5em; text-align: center; }}
        .header .subtitle {{ text-align: center; margin-top: 10px; opacity: 0.9; }}
        .content {{ padding: 30px; }}
        .executive-summary {{ background: #f8f9fa; border-left: 4px solid #1e3a8a; padding: 20px; margin-bottom: 30px; }}
        .status-badge {{ display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold; color: white; }}
        .status-critical {{ background-color: #dc3545; }}
        .status-warning {{ background-color: #ffc107; color: #000; }}
        .status-success {{ background-color: #28a745; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; text-align: center; }}
        .metric-value {{ font-size: 2.5em; font-weight: bold; color: #1e3a8a; }}
        .metric-label {{ color: #6c757d; margin-top: 5px; }}
        .section {{ margin: 30px 0; }}
        .section h2 {{ color: #1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; }}
        .requirement {{ border: 1px solid #dee2e6; border-radius: 8px; margin: 10px 0; padding: 15px; }}
        .requirement-header {{ display: flex; justify-content: between; align-items: center; margin-bottom: 10px; }}
        .requirement-id {{ font-weight: bold; background: #e9ecef; padding: 3px 8px; border-radius: 4px; }}
        .evidence {{ background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-family: monospace; font-size: 0.9em; }}
        .recommendations {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }}
        .critical-finding {{ background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 10px 0; }}
        .footer {{ background: #e9ecef; padding: 20px; text-align: center; color: #6c757d; border-radius: 0 0 8px 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #dee2e6; padding: 12px; text-align: left; }}
        th {{ background-color: #1e3a8a; color: white; }}
        .progress-bar {{ background: #e9ecef; border-radius: 10px; height: 20px; margin: 5px 0; }}
        .progress-fill {{ height: 100%; border-radius: 10px; transition: width 0.3s ease; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 SCRPA Security Compliance Report</h1>
            <div class="subtitle">Police Data Processing Security Validation</div>
            <div class="subtitle">Generated: {report_data['report_metadata']['generated_at']}</div>
        </div>
        
        <div class="content">
            <div class="executive-summary">
                <h2>Executive Summary</h2>
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        <h3>Overall Status: <span class="status-badge {'status-critical' if report_data['executive_summary']['overall_status'] in ['CRITICAL_VIOLATIONS', 'MAJOR_ISSUES'] else 'status-warning' if 'ISSUES' in report_data['executive_summary']['overall_status'] else 'status-success'}">{report_data['executive_summary']['overall_status']}</span></h3>
                    </div>
                    <div>
                        <div class="metric-value">{report_data['executive_summary']['compliance_score']}%</div>
                        <div class="metric-label">Compliance Score</div>
                    </div>
                </div>
                
                <div class="metrics">
                    <div class="metric-card">
                        <div class="metric-value" style="color: #28a745;">{report_data['executive_summary']['compliant_requirements']}</div>
                        <div class="metric-label">Compliant</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" style="color: #dc3545;">{report_data['executive_summary']['non_compliant_requirements']}</div>
                        <div class="metric-label">Non-Compliant</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" style="color: #dc3545;">{report_data['executive_summary']['critical_violations']}</div>
                        <div class="metric-label">Critical Issues</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" style="color: #fd7e14;">{report_data['executive_summary']['high_risk_issues']}</div>
                        <div class="metric-label">High Risk</div>
                    </div>
                </div>
            </div>
"""
        
        # Critical Findings Section
        if report_data['critical_findings']:
            html_content += """
            <div class="section">
                <h2>🚨 Critical Security Findings</h2>
"""
            for finding in report_data['critical_findings']:
                html_content += f"""
                <div class="critical-finding">
                    <strong>{finding['requirement_id']}: {finding['description']}</strong>
                    <div style="margin-top: 10px;">Status: <strong>{finding['status'].replace('_', ' ').title()}</strong></div>
                    {'<div class="evidence">' + '<br>'.join(finding['evidence']) + '</div>' if finding['evidence'] else ''}
                    {'<div class="recommendations"><strong>Actions Required:</strong><ul>' + ''.join([f'<li>{rec}</li>' for rec in finding['recommendations']]) + '</ul></div>' if finding['recommendations'] else ''}
                </div>
"""
            html_content += "</div>"
        
        # Requirements by Category
        html_content += """
            <div class="section">
                <h2>📋 Compliance Requirements by Category</h2>
"""
        
        for category, requirements in report_data['requirements_by_category'].items():
            category_stats = report_data['compliance_statistics']['category_compliance'][category]
            
            html_content += f"""
                <h3>{category.replace('_', ' ').title()}</h3>
                <div style="margin-bottom: 15px;">
                    <span>Compliance Rate: <strong>{category_stats['compliance_rate']}%</strong></span>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {category_stats['compliance_rate']}%; background-color: {'#28a745' if category_stats['compliance_rate'] >= 80 else '#ffc107' if category_stats['compliance_rate'] >= 60 else '#dc3545'};"></div>
                    </div>
                </div>
"""
            
            for req in requirements:
                status_style = get_status_style(req['status'])
                risk_color = get_risk_style(req['risk_level'])
                
                html_content += f"""
                <div class="requirement">
                    <div class="requirement-header">
                        <span class="requirement-id">{req['id']}</span>
                        <span style="color: {status_style['color']};">{status_style['icon']} {req['status'].replace('_', ' ').title()}</span>
                        <span style="background-color: {risk_color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.8em;">{req['risk_level'].upper()}</span>
                    </div>
                    <div>{req['description']}</div>
                    {'<div class="evidence"><strong>Evidence:</strong><br>' + '<br>'.join(req['evidence']) + '</div>' if req['evidence'] else ''}
                    {'<div class="recommendations"><strong>Recommendations:</strong><ul>' + ''.join([f'<li>{rec}</li>' for rec in req['recommendations']]) + '</ul></div>' if req['recommendations'] else ''}
                </div>
"""
        
        html_content += "</div>"
        
        # Recommendations Section
        if report_data['recommendations']:
            html_content += """
            <div class="section">
                <h2>🔧 Priority Recommendations</h2>
                <ol>
"""
            for rec in report_data['recommendations']:
                html_content += f"<li>{rec}</li>"
            
            html_content += "</ol></div>"
        
        # Certification Status
        cert_status = report_data['certification_status']
        cert_color = '#28a745' if cert_status['status'] == 'CERTIFIED' else '#ffc107' if cert_status['status'] == 'PROVISIONAL' else '#dc3545'
        
        html_content += f"""
            <div class="section">
                <h2>📜 Certification Status</h2>
                <div style="background-color: {cert_color}; color: white; padding: 20px; border-radius: 8px; text-align: center;">
                    <h3>{cert_status['status']}</h3>
                    <p>{cert_status['message']}</p>
                    {'<p><strong>Valid Until:</strong> ' + cert_status['valid_until'] + '</p>' if cert_status['valid_until'] else ''}
                    {'<div><strong>Conditions:</strong><ul>' + ''.join([f'<li>{cond}</li>' for cond in cert_status['conditions']]) + '</ul></div>' if cert_status['conditions'] else ''}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>This report was generated by the SCRPA Security Validation Suite</p>
            <p>Report complies with CJIS Security Policy requirements for police data processing</p>
            <p>For questions or concerns, contact your system administrator</p>
        </div>
    </div>
</body>
</html>
"""
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML security report generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Could not generate HTML report: {e}")
            return ""
    
    def save_json_report(self, report_data: Dict[str, Any], output_path: str = None) -> str:
        """Save report in JSON format."""
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"security_compliance_report_{timestamp}.json"
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
            
            logger.info(f"JSON security report saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Could not save JSON report: {e}")
            return ""

def demo_report_generation():
    """Demonstrate report generation capabilities."""
    
    print("📊 SCRPA Security Report Generator Demo")
    print("=" * 50)
    
    # Create report generator
    generator = SecurityReportGenerator()
    
    # Create mock test results for demonstration
    from security_validation_suite import SecurityTestResult
    
    mock_results = [
        SecurityTestResult("Data Sanitization Effectiveness", "sanitization", "pass", "All sensitive data properly sanitized"),
        SecurityTestResult("Localhost URL Validation", "network", "pass", "Valid localhost URL accepted"),
        SecurityTestResult("External Network Calls", "network", "fail", "External connection detected", recommendations=["Block external access"]),
        SecurityTestResult("Log File Security Check", "filesystem", "pass", "No sensitive data in logs"),
        SecurityTestResult("Ollama Offline Error Handling", "error_handling", "warning", "Fallback mode working but could be improved")
    ]
    
    # Generate compliance report
    print("Generating compliance report...")
    report = generator.generate_compliance_report(mock_results)
    
    print(f"📊 Report Summary:")
    print(f"   Overall Status: {report['executive_summary']['overall_status']}")
    print(f"   Compliance Score: {report['executive_summary']['compliance_score']}%")
    print(f"   Critical Violations: {report['executive_summary']['critical_violations']}")
    print(f"   Compliant Requirements: {report['executive_summary']['compliant_requirements']}")
    
    # Save reports
    json_file = generator.save_json_report(report)
    html_file = generator.generate_html_report(report)
    
    print(f"\n📄 Reports Generated:")
    if json_file:
        print(f"   JSON: {json_file}")
    if html_file:
        print(f"   HTML: {html_file}")
    
    print(f"\n✅ Report generation demo complete!")

if __name__ == "__main__":
    demo_report_generation()