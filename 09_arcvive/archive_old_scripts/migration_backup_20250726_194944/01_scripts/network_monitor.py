# 🌐 Network Security Monitor for SCRPA
# Author: Claude Code (Anthropic)
# Purpose: Monitor and detect any external network connections during SCRPA processing
# Features: Real-time monitoring, connection logging, security alerts

import socket
import subprocess
import threading
import time
import json
import re
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
import logging
import psutil
import urllib.parse

logger = logging.getLogger(__name__)

@dataclass
class NetworkConnection:
    """Represents a detected network connection."""
    timestamp: str
    local_address: str
    remote_address: str
    remote_host: str
    remote_port: int
    protocol: str
    process_name: str
    process_id: int
    connection_type: str  # 'ESTABLISHED', 'SYN_SENT', 'LISTEN', etc.
    security_risk: str   # 'safe', 'suspicious', 'dangerous'
    description: str

@dataclass
class NetworkAlert:
    """Security alert for suspicious network activity."""
    timestamp: str
    alert_type: str     # 'external_connection', 'suspicious_host', 'blocked_attempt'
    severity: str       # 'low', 'medium', 'high', 'critical'
    connection: NetworkConnection
    message: str
    recommendations: List[str] = field(default_factory=list)

class NetworkSecurityMonitor:
    """Advanced network security monitor for SCRPA system."""
    
    def __init__(self, monitoring_duration: int = 300):
        """
        Initialize network monitor.
        
        Args:
            monitoring_duration: How long to monitor in seconds (default 5 minutes)
        """
        self.monitoring_duration = monitoring_duration
        self.monitoring = False
        self.connections: List[NetworkConnection] = []
        self.alerts: List[NetworkAlert] = []
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Define safe/allowed hosts and patterns
        self.safe_hosts = {
            'localhost', '127.0.0.1', '::1', '0.0.0.0',
            # Local network ranges
            '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16',
            # Link-local
            '169.254.0.0/16', 'fe80::/10'
        }
        
        # Suspicious hosts (AI/ML services)
        self.suspicious_hosts = {
            'api.openai.com', 'api.anthropic.com', 'api-inference.huggingface.co',
            'together.xyz', 'replicate.com', 'cohere.ai', 'ai.meta.com',
            'openai.com', 'anthropic.com', 'huggingface.co'
        }
        
        # Processes to monitor (Python, AI tools, etc.)
        self.monitored_processes = {
            'python.exe', 'python3.exe', 'ollama.exe', 'node.exe',
            'curl.exe', 'wget.exe', 'powershell.exe'
        }
        
        logger.info(f"Network Security Monitor initialized (duration: {monitoring_duration}s)")
    
    def start_monitoring(self) -> None:
        """Start network monitoring in background thread."""
        if self.monitoring:
            logger.warning("Network monitoring already active")
            return
        
        self.monitoring = True
        self.connections.clear()
        self.alerts.clear()
        
        self.monitor_thread = threading.Thread(target=self._monitor_connections, daemon=True)
        self.monitor_thread.start()
        
        logger.info("🔍 Network security monitoring started")
        print("🔍 Network monitoring active - watching for external connections...")
    
    def stop_monitoring(self) -> Tuple[List[NetworkConnection], List[NetworkAlert]]:
        """
        Stop network monitoring and return results.
        
        Returns:
            Tuple of (connections, alerts)
        """
        if not self.monitoring:
            return self.connections, self.alerts
        
        self.monitoring = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        logger.info(f"🔍 Network monitoring stopped: {len(self.connections)} connections, {len(self.alerts)} alerts")
        
        return self.connections, self.alerts
    
    def _monitor_connections(self) -> None:
        """Main monitoring loop."""
        start_time = time.time()
        last_scan = 0
        
        while self.monitoring and (time.time() - start_time) < self.monitoring_duration:
            try:
                current_time = time.time()
                
                # Scan every 2 seconds
                if current_time - last_scan >= 2:
                    self._scan_active_connections()
                    last_scan = current_time
                
                time.sleep(0.5)  # Small sleep to prevent excessive CPU usage
                
            except Exception as e:
                logger.error(f"Error in network monitoring: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _scan_active_connections(self) -> None:
        """Scan for active network connections."""
        try:
            # Get network connections using psutil for better cross-platform support
            connections = psutil.net_connections(kind='inet')
            
            for conn in connections:
                if conn.status == psutil.CONN_ESTABLISHED or conn.status == psutil.CONN_SYN_SENT:
                    self._process_connection(conn)
                    
        except Exception as e:
            logger.debug(f"Error scanning connections with psutil: {e}")
            # Fallback to netstat
            self._scan_with_netstat()
    
    def _scan_with_netstat(self) -> None:
        """Fallback method using netstat command."""
        try:
            # Windows netstat command
            result = subprocess.run(
                ['netstat', '-ano'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                self._parse_netstat_output(result.stdout)
                
        except Exception as e:
            logger.debug(f"Netstat scan failed: {e}")
    
    def _parse_netstat_output(self, output: str) -> None:
        """Parse netstat output to extract connections."""
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if 'ESTABLISHED' in line or 'SYN_SENT' in line:
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        protocol = parts[0]
                        local_addr = parts[1]
                        remote_addr = parts[2]
                        status = parts[3]
                        pid = int(parts[4]) if len(parts) > 4 else 0
                        
                        # Create mock connection object for processing
                        mock_conn = type('MockConn', (), {
                            'laddr': self._parse_address(local_addr),
                            'raddr': self._parse_address(remote_addr),
                            'status': status,
                            'pid': pid
                        })()
                        
                        self._process_connection(mock_conn, protocol=protocol)
                        
                    except Exception as e:
                        logger.debug(f"Error parsing netstat line '{line}': {e}")
    
    def _parse_address(self, addr_str: str) -> Optional[object]:
        """Parse address string into address object."""
        try:
            if ':' in addr_str:
                host, port = addr_str.rsplit(':', 1)
                return type('Addr', (), {'ip': host, 'port': int(port)})()
        except:
            pass
        return None
    
    def _process_connection(self, conn, protocol: str = 'TCP') -> None:
        """Process a detected connection."""
        try:
            if not conn.raddr:
                return  # No remote address
            
            remote_host = conn.raddr.ip
            remote_port = conn.raddr.port
            local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "unknown"
            remote_addr = f"{remote_host}:{remote_port}"
            
            # Skip if we've already logged this connection recently
            recent_connections = [c for c in self.connections[-10:] 
                                if c.remote_address == remote_addr]
            if recent_connections:
                return
            
            # Get process information
            process_name = "unknown"
            process_id = getattr(conn, 'pid', 0)
            
            try:
                if process_id > 0:
                    process = psutil.Process(process_id)
                    process_name = process.name()
            except:
                pass
            
            # Determine security risk
            security_risk = self._assess_security_risk(remote_host, remote_port, process_name)
            
            # Create connection record
            connection = NetworkConnection(
                timestamp=datetime.now().isoformat(),
                local_address=local_addr,
                remote_address=remote_addr,
                remote_host=remote_host,
                remote_port=remote_port,
                protocol=protocol,
                process_name=process_name,
                process_id=process_id,
                connection_type=getattr(conn, 'status', 'ESTABLISHED'),
                security_risk=security_risk,
                description=self._describe_connection(remote_host, remote_port, process_name)
            )
            
            self.connections.append(connection)
            
            # Generate alert if necessary
            if security_risk in ['suspicious', 'dangerous']:
                self._generate_alert(connection)
            
            # Log significant connections
            if security_risk != 'safe':
                logger.warning(f"Network connection: {process_name}({process_id}) -> {remote_addr} [{security_risk}]")
            
        except Exception as e:
            logger.debug(f"Error processing connection: {e}")
    
    def _assess_security_risk(self, host: str, port: int, process: str) -> str:
        """Assess the security risk level of a connection."""
        
        # Check if host is localhost or local network
        if self._is_safe_host(host):
            return 'safe'
        
        # Check against known suspicious hosts
        if self._is_suspicious_host(host):
            return 'dangerous'
        
        # Check for AI/ML service ports
        suspicious_ports = {443, 80, 8080, 8000, 5000, 3000}  # Common API ports
        if port in suspicious_ports and not self._is_safe_host(host):
            return 'suspicious'
        
        # Check process names
        if process.lower() in ['python.exe', 'python3.exe', 'node.exe']:
            return 'suspicious'  # Python/Node making external connections
        
        # Default for external connections
        if not self._is_safe_host(host):
            return 'suspicious'
        
        return 'safe'
    
    def _is_safe_host(self, host: str) -> bool:
        """Check if host is considered safe (localhost/local network)."""
        
        # Direct matches
        if host in self.safe_hosts:
            return True
        
        # Check IP ranges
        try:
            import ipaddress
            ip = ipaddress.ip_address(host)
            
            # Check if it's in private/local ranges
            return (
                ip.is_loopback or 
                ip.is_private or 
                ip.is_link_local or
                ip.is_multicast
            )
        except:
            pass
        
        # Check hostname patterns
        local_patterns = [
            r'^localhost',
            r'^127\.',
            r'^192\.168\.',
            r'^10\.',
            r'^172\.(1[6-9]|2[0-9]|3[0-1])\.'
        ]
        
        for pattern in local_patterns:
            if re.match(pattern, host):
                return True
        
        return False
    
    def _is_suspicious_host(self, host: str) -> bool:
        """Check if host is known to be suspicious (AI services)."""
        
        # Direct hostname matches
        for suspicious in self.suspicious_hosts:
            if suspicious in host.lower():
                return True
        
        # Pattern matching for AI services
        ai_patterns = [
            r'.*openai.*',
            r'.*anthropic.*',
            r'.*huggingface.*',
            r'.*together.*',
            r'.*replicate.*',
            r'.*cohere.*'
        ]
        
        for pattern in ai_patterns:
            if re.match(pattern, host.lower()):
                return True
        
        return False
    
    def _describe_connection(self, host: str, port: int, process: str) -> str:
        """Generate human-readable description of connection."""
        
        if self._is_safe_host(host):
            return f"Local connection to {host}:{port}"
        
        if self._is_suspicious_host(host):
            return f"SUSPICIOUS: Connection to AI service {host}:{port} by {process}"
        
        # Check common ports
        port_descriptions = {
            80: "HTTP web traffic",
            443: "HTTPS secure web traffic", 
            53: "DNS resolution",
            25: "Email (SMTP)",
            110: "Email (POP3)",
            143: "Email (IMAP)",
            993: "Secure Email (IMAPS)",
            995: "Secure Email (POP3S)"
        }
        
        port_desc = port_descriptions.get(port, f"service on port {port}")
        
        if not self._is_safe_host(host):
            return f"External connection to {host} for {port_desc} by {process}"
        
        return f"Connection to {host}:{port} by {process}"
    
    def _generate_alert(self, connection: NetworkConnection) -> None:
        """Generate security alert for suspicious connection."""
        
        if connection.security_risk == 'dangerous':
            severity = 'critical'
            alert_type = 'external_ai_service'
            message = f"CRITICAL: Connection to AI service {connection.remote_host} detected"
            recommendations = [
                "Block external AI service access immediately",
                "Verify SCRPA is using localhost-only processing",
                "Check for misconfigured API endpoints",
                "Review application for external API calls"
            ]
        elif connection.security_risk == 'suspicious':
            severity = 'medium'
            alert_type = 'suspicious_external'
            message = f"Suspicious external connection to {connection.remote_host}:{connection.remote_port}"
            recommendations = [
                "Investigate purpose of external connection",
                "Verify connection is necessary for operation",
                "Consider blocking if not required"
            ]
        else:
            return  # No alert needed
        
        alert = NetworkAlert(
            timestamp=connection.timestamp,
            alert_type=alert_type,
            severity=severity,
            connection=connection,
            message=message,
            recommendations=recommendations
        )
        
        self.alerts.append(alert)
        
        # Immediate console warning for critical alerts
        if severity == 'critical':
            print(f"\n🚨 CRITICAL SECURITY ALERT: {message}")
            print(f"   Process: {connection.process_name} (PID: {connection.process_id})")
            print(f"   Address: {connection.remote_address}")
            print(f"   Time: {connection.timestamp}")
    
    def generate_monitoring_report(self) -> Dict:
        """Generate comprehensive monitoring report."""
        
        # Categorize connections
        safe_connections = [c for c in self.connections if c.security_risk == 'safe']
        suspicious_connections = [c for c in self.connections if c.security_risk == 'suspicious']
        dangerous_connections = [c for c in self.connections if c.security_risk == 'dangerous']
        
        # Process statistics
        process_stats = {}
        for conn in self.connections:
            if conn.process_name not in process_stats:
                process_stats[conn.process_name] = 0
            process_stats[conn.process_name] += 1
        
        # Host statistics
        host_stats = {}
        for conn in self.connections:
            if conn.remote_host not in host_stats:
                host_stats[conn.remote_host] = 0
            host_stats[conn.remote_host] += 1
        
        report = {
            'monitoring_summary': {
                'monitoring_duration': self.monitoring_duration,
                'total_connections': len(self.connections),
                'safe_connections': len(safe_connections),
                'suspicious_connections': len(suspicious_connections),
                'dangerous_connections': len(dangerous_connections),
                'total_alerts': len(self.alerts)
            },
            'security_assessment': {
                'overall_status': self._get_overall_security_status(),
                'critical_alerts': len([a for a in self.alerts if a.severity == 'critical']),
                'external_ai_connections': len(dangerous_connections),
                'localhost_only': len(dangerous_connections) == 0
            },
            'connection_details': [
                {
                    'timestamp': c.timestamp,
                    'remote_host': c.remote_host,
                    'remote_port': c.remote_port,
                    'process': c.process_name,
                    'process_id': c.process_id,
                    'security_risk': c.security_risk,
                    'description': c.description
                }
                for c in self.connections
            ],
            'alerts': [
                {
                    'timestamp': a.timestamp,
                    'type': a.alert_type,
                    'severity': a.severity,
                    'message': a.message,
                    'remote_host': a.connection.remote_host,
                    'process': a.connection.process_name,
                    'recommendations': a.recommendations
                }
                for a in self.alerts
            ],
            'statistics': {
                'connections_by_process': process_stats,
                'connections_by_host': host_stats
            }
        }
        
        return report
    
    def _get_overall_security_status(self) -> str:
        """Determine overall security status."""
        
        critical_alerts = len([a for a in self.alerts if a.severity == 'critical'])
        dangerous_connections = len([c for c in self.connections if c.security_risk == 'dangerous'])
        
        if critical_alerts > 0 or dangerous_connections > 0:
            return 'CRITICAL'
        
        high_alerts = len([a for a in self.alerts if a.severity in ['high', 'medium']])
        if high_alerts > 0:
            return 'WARNING' 
        
        if len(self.connections) == 0:
            return 'NO_CONNECTIONS'
        
        return 'SECURE'
    
    def save_monitoring_report(self, filename: str = None) -> str:
        """Save monitoring report to file."""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"network_monitoring_report_{timestamp}.json"
        
        report = self.generate_monitoring_report()
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Network monitoring report saved: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Could not save monitoring report: {e}")
            return ""

def test_network_monitor():
    """Test the network monitor functionality."""
    
    print("🧪 Testing Network Security Monitor")
    print("=" * 50)
    
    # Create monitor with short duration for testing
    monitor = NetworkSecurityMonitor(monitoring_duration=10)
    
    print("Starting 10-second network monitoring test...")
    monitor.start_monitoring()
    
    # Simulate some network activity
    time.sleep(2)
    
    # Test a localhost connection (should be safe)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('127.0.0.1', 80))  # This will likely fail, but creates activity
        sock.close()
    except:
        pass  # Expected to fail
    
    time.sleep(8)  # Let monitoring complete
    
    connections, alerts = monitor.stop_monitoring()
    
    print(f"\n📊 Monitoring Results:")
    print(f"   Connections detected: {len(connections)}")
    print(f"   Security alerts: {len(alerts)}")
    
    # Show sample connections
    for conn in connections[:3]:
        print(f"   • {conn.process_name} -> {conn.remote_host}:{conn.remote_port} [{conn.security_risk}]")
    
    # Show alerts
    for alert in alerts:
        print(f"   🚨 {alert.severity.upper()}: {alert.message}")
    
    # Generate report
    report_file = monitor.save_monitoring_report()
    if report_file:
        print(f"\n📄 Report saved: {report_file}")
    
    print("\n✅ Network monitor test complete!")

if __name__ == "__main__":
    test_network_monitor()