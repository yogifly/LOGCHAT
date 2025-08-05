# parsers/apache_parser.py
import re
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import unquote
import ipaddress

class ApacheLogParser:
    """Complete Apache/Nginx access log parser"""
    
    def __init__(self):
        self.parsed_data = None
        self.raw_lines = []
        self.errors = []
        self.total_lines = 0
        self.parsed_lines = 0
        
        # Log format patterns
        self.patterns = {
            # Common Log Format: IP - - [timestamp] "request" status size
            'common': r'^(\S+) \S+ \S+ \[([^\]]+)\] "([^"]*)" (\d+) (\S+)',
            
            # Combined Log Format: Common + referer + user-agent
            'combined': r'^(\S+) \S+ \S+ \[([^\]]+)\] "([^"]*)" (\d+) (\S+) "([^"]*)" "([^"]*)"',
            
            # Custom format with response time
            'custom': r'^(\S+) - - \[([^\]]+)\] "([^"]*)" (\d+) (\d+) "([^"]*)" "([^"]*)" (\d+)',
            
            # Nginx default format
            'nginx': r'^(\S+) - \S+ \[([^\]]+)\] "([^"]*)" (\d+) (\d+) "([^"]*)" "([^"]*)"',
            
            # Error log format
            'error': r'^\[([^\]]+)\] \[([^\]]+)\] \[client (\S+)\] (.*)$'
        }
        
        self.timestamp_formats = [
            '%d/%b/%Y:%H:%M:%S %z',
            '%d/%b/%Y:%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y:%H:%M:%S %z'
        ]
    
    def parse_file(self, file_path: str) -> pd.DataFrame:
        """Parse Apache log file and return DataFrame"""
        logs = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    self.total_lines += 1
                    line = line.strip()
                    
                    if not line or line.startswith('#'):  # Skip empty lines and comments
                        continue
                    
                    self.raw_lines.append(line)
                    
                    try:
                        parsed_line = self.parse_line(line)
                        if parsed_line:
                            parsed_line['line_number'] = line_num
                            parsed_line['raw_line'] = line
                            logs.append(parsed_line)
                            self.parsed_lines += 1
                    except Exception as e:
                        self.errors.append({
                            'line_number': line_num,
                            'line': line,
                            'error': str(e)
                        })
            
            self.parsed_data = pd.DataFrame(logs)
            
            # Add computed columns
            if not self.parsed_data.empty:
                self._add_computed_columns()
            
            return self.parsed_data
            
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")
    
    def parse_line(self, line: str) -> Dict[str, Any]:
        """Parse a single Apache log line"""
        
        # Try each pattern
        for pattern_name, pattern in self.patterns.items():
            match = re.match(pattern, line)
            if match:
                return self._parse_match(match, pattern_name, line)
        
        # If no pattern matches, try fallback parsing
        return self._parse_fallback(line)
    
    def _parse_match(self, match, pattern_type: str, original_line: str) -> Dict[str, Any]:
        """Parse matched regex groups based on pattern type"""
        groups = match.groups()
        
        if pattern_type == 'error':
            return self._parse_error_log(groups, original_line)
        
        # Standard access log parsing
        base_data = {
            'ip': groups[0],
            'timestamp_str': groups[1],
            'request': groups[2] if len(groups) > 2 else '',
            'status_code': int(groups[3]) if len(groups) > 3 and groups[3].isdigit() else 0,
            'response_size': self._parse_size(groups[4]) if len(groups) > 4 else 0,
            'referer': '',
            'user_agent': '',
            'response_time': 0
        }
        
        # Add extra fields based on pattern type
        if pattern_type in ['combined', 'nginx'] and len(groups) >= 7:
            base_data['referer'] = self._clean_field(groups[5])
            base_data['user_agent'] = self._clean_field(groups[6])
        
        if pattern_type == 'custom' and len(groups) >= 8:
            base_data['referer'] = self._clean_field(groups[5])
            base_data['user_agent'] = self._clean_field(groups[6])
            base_data['response_time'] = int(groups[7]) if groups[7].isdigit() else 0
        
        # Parse timestamp
        base_data['timestamp'] = self._parse_timestamp(base_data['timestamp_str'])
        
        # Parse request details
        request_details = self._parse_request(base_data['request'])
        base_data.update(request_details)
        
        # Add analysis fields
        base_data.update(self._analyze_request(base_data))
        
        return base_data
    
    def _parse_error_log(self, groups: tuple, original_line: str) -> Dict[str, Any]:
        """Parse Apache error log format"""
        return {
            'timestamp': self._parse_timestamp(groups[0]),
            'timestamp_str': groups[0],
            'log_level': groups[1],
            'ip': groups[2],
            'message': groups[3],
            'request': groups[3],
            'status_code': 500,  # Error logs are typically 5xx
            'response_size': 0,
            'method': 'ERROR',
            'url': '',
            'protocol': '',
            'referer': '',
            'user_agent': '',
            'response_time': 0,
            'threat_level': 'medium',
            'request_type': 'error',
            'is_suspicious': True
        }
    
    def _parse_fallback(self, line: str) -> Dict[str, Any]:
        """Fallback parsing for non-standard formats"""
        # Extract IP address
        ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', line)
        ip = ip_match.group() if ip_match else 'unknown'
        
        # Extract status code
        status_match = re.search(r'" (\d{3}) ', line)
        status_code = int(status_match.group(1)) if status_match else 0
        
        # Extract timestamp
        timestamp_match = re.search(r'\[([^\]]+)\]', line)
        timestamp_str = timestamp_match.group(1) if timestamp_match else ''
        timestamp = self._parse_timestamp(timestamp_str)
        
        # Extract HTTP method and URL
        request_match = re.search(r'"([^"]*)"', line)
        request = request_match.group(1) if request_match else line
        
        base_data = {
            'ip': ip,
            'timestamp': timestamp,
            'timestamp_str': timestamp_str,
            'request': request,
            'status_code': status_code,
            'response_size': 0,
            'referer': '',
            'user_agent': '',
            'response_time': 0
        }
        
        # Parse request details
        request_details = self._parse_request(request)
        base_data.update(request_details)
        
        # Add analysis fields
        base_data.update(self._analyze_request(base_data))
        
        return base_data
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp with multiple format support"""
        if not timestamp_str:
            return datetime.now()
        
        for fmt in self.timestamp_formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # If all formats fail, return current time
        return datetime.now()
    
    def _parse_size(self, size_str: str) -> int:
        """Parse response size, handle '-' for empty"""
        if size_str == '-' or not size_str:
            return 0
        try:
            return int(size_str)
        except ValueError:
            return 0
    
    def _clean_field(self, field: str) -> str:
        """Clean field value, handle '-' for empty"""
        return '' if field == '-' else field
    
    def _parse_request(self, request: str) -> Dict[str, str]:
        """Parse HTTP request line into components"""
        if not request:
            return {'method': '', 'url': '', 'protocol': '', 'query_params': ''}
        
        # URL decode the request
        try:
            request = unquote(request)
        except:
            pass
        
        parts = request.split()
        result = {'method': '', 'url': '', 'protocol': '', 'query_params': ''}
        
        if len(parts) >= 1:
            result['method'] = parts[0].upper()
        if len(parts) >= 2:
            url = parts[1]
            # Split URL and query parameters
            if '?' in url:
                result['url'], result['query_params'] = url.split('?', 1)
            else:
                result['url'] = url
        if len(parts) >= 3:
            result['protocol'] = parts[2]
        
        return result
    
    def _analyze_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze request for threats and categorization"""
        method = data.get('method', '').upper()
        url = data.get('url', '').lower()
        status_code = data.get('status_code', 0)
        user_agent = data.get('user_agent', '').lower()
        
        analysis = {
            'threat_level': 'low',
            'request_type': 'normal',
            'is_suspicious': False,
            'attack_indicators': []
        }
        
        # Check for suspicious patterns
        suspicious_urls = [
            'admin', 'login', 'wp-admin', 'phpmyadmin', 'shell', 'config',
            'backup', 'test', '.env', 'password', 'passwd', 'shadow'
        ]
        
        attack_patterns = {
            'sql_injection': ['union', 'select', 'drop', 'insert', 'update', "'", '"', '--', '/*'],
            'xss': ['<script', 'javascript:', 'onerror', 'onload', 'alert('],
            'path_traversal': ['../', '..\\', '%2e%2e', 'etc/passwd', 'windows/system32'],
            'command_injection': ['cmd.exe', '/bin/bash', 'wget', 'curl', '|', ';', '&'],
            'file_inclusion': ['file:', 'http:', 'ftp:', 'include', 'require']
        }
        
        # Check for suspicious URLs
        if any(pattern in url for pattern in suspicious_urls):
            analysis['is_suspicious'] = True
            analysis['threat_level'] = 'medium'
            analysis['attack_indicators'].append('suspicious_path')
        
        # Check for attack patterns
        full_request = f"{url} {data.get('query_params', '')}"
        for attack_type, patterns in attack_patterns.items():
            if any(pattern in full_request.lower() for pattern in patterns):
                analysis['is_suspicious'] = True
                analysis['threat_level'] = 'high'
                analysis['attack_indicators'].append(attack_type)
        
        # Check status codes
        if status_code == 401:
            analysis['request_type'] = 'auth_failure'
            analysis['is_suspicious'] = True
        elif status_code == 403:
            analysis['request_type'] = 'access_denied'
            analysis['is_suspicious'] = True
        elif status_code == 404:
            analysis['request_type'] = 'not_found'
            if analysis['is_suspicious']:
                analysis['attack_indicators'].append('probing')
        elif status_code >= 500:
            analysis['request_type'] = 'server_error'
        elif method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            analysis['request_type'] = 'data_modification'
        
        # Check for bot/scanner user agents
        bot_indicators = ['bot', 'crawler', 'spider', 'scan', 'nmap', 'sqlmap', 'nikto']
        if any(indicator in user_agent for indicator in bot_indicators):
            analysis['is_suspicious'] = True
            analysis['attack_indicators'].append('automated_tool')
        
        return analysis
    
    def _add_computed_columns(self):
        """Add computed columns to the DataFrame"""
        if self.parsed_data.empty:
            return
        
        df = self.parsed_data
        
        # Add time-based columns
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['date'] = df['timestamp'].dt.date
        
        # Add IP analysis
        df['is_private_ip'] = df['ip'].apply(self._is_private_ip)
        df['ip_class'] = df['ip'].apply(self._get_ip_class)
        
        # Add file extension
        df['file_extension'] = df['url'].apply(self._get_file_extension)
        
        # Add request size categories
        df['size_category'] = pd.cut(df['response_size'], 
                                   bins=[0, 1000, 10000, 100000, float('inf')],
                                   labels=['small', 'medium', 'large', 'very_large'])
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is in private range"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except:
            return False
    
    def _get_ip_class(self, ip: str) -> str:
        """Get IP address class"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                return 'private'
            elif ip_obj.is_loopback:
                return 'loopback'
            elif ip_obj.is_multicast:
                return 'multicast'
            else:
                return 'public'
        except:
            return 'invalid'
    
    def _get_file_extension(self, url: str) -> str:
        """Extract file extension from URL"""
        if not url or url == '/':
            return 'none'
        
        # Remove query parameters
        url = url.split('?')[0]
        
        # Get extension
        if '.' in url:
            ext = url.split('.')[-1].lower()
            return ext if len(ext) <= 5 else 'none'  # Reasonable extension length
        return 'none'
    
    def get_parsing_stats(self) -> Dict[str, Any]:
        """Get parsing statistics"""
        return {
            'total_lines': self.total_lines,
            'parsed_lines': self.parsed_lines,
            'error_lines': len(self.errors),
            'success_rate': round((self.parsed_lines / self.total_lines) * 100, 2) if self.total_lines > 0 else 0,
            'log_type': 'Apache/Nginx Access Log'
        }
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get comprehensive summary statistics"""
        if self.parsed_data is None or self.parsed_data.empty:
            return {'error': 'No data parsed'}
        
        df = self.parsed_data
        
        return {
            'basic_stats': {
                'total_requests': len(df),
                'unique_ips': df['ip'].nunique(),
                'unique_urls': df['url'].nunique(),
                'date_range': {
                    'start': df['timestamp'].min().isoformat(),
                    'end': df['timestamp'].max().isoformat()
                }
            },
            'status_distribution': df['status_code'].value_counts().to_dict(),
            'method_distribution': df['method'].value_counts().to_dict(),
            'top_ips': df['ip'].value_counts().head(10).to_dict(),
            'top_urls': df['url'].value_counts().head(10).to_dict(),
            'top_user_agents': df['user_agent'].value_counts().head(5).to_dict(),
            'error_analysis': {
                'total_errors': len(df[df['status_code'] >= 400]),
                'error_rate': len(df[df['status_code'] >= 400]) / len(df) * 100,
                '4xx_errors': len(df[df['status_code'].between(400, 499)]),
                '5xx_errors': len(df[df['status_code'].between(500, 599)])
            },
            'security_analysis': {
                'suspicious_requests': len(df[df['is_suspicious'] == True]),
                'threat_levels': df['threat_level'].value_counts().to_dict(),
                'attack_types': df[df['is_suspicious'] == True]['attack_indicators'].explode().value_counts().to_dict() if 'attack_indicators' in df.columns else {},
                'suspicious_ips': df[df['is_suspicious'] == True]['ip'].value_counts().head(10).to_dict()
            },
            'traffic_patterns': {
                'hourly_distribution': df.groupby('hour').size().to_dict(),
                'daily_distribution': df.groupby('day_of_week').size().to_dict(),
                'file_types': df['file_extension'].value_counts().head(10).to_dict()
            }
        }
    
    def get_threat_summary(self) -> Dict[str, Any]:
        """Get focused threat analysis"""
        if self.parsed_data is None or self.parsed_data.empty:
            return {'error': 'No data parsed'}
        
        df = self.parsed_data
        suspicious_df = df[df['is_suspicious'] == True]
        
        if suspicious_df.empty:
            return {'message': 'No threats detected'}
        
        return {
            'total_threats': len(suspicious_df),
            'threat_percentage': len(suspicious_df) / len(df) * 100,
            'threat_by_ip': suspicious_df['ip'].value_counts().head(10).to_dict(),
            'threat_by_type': suspicious_df['request_type'].value_counts().to_dict(),
            'high_risk_requests': len(suspicious_df[suspicious_df['threat_level'] == 'high']),
            'recent_threats': suspicious_df.nlargest(10, 'timestamp')[['timestamp', 'ip', 'url', 'threat_level']].to_dict('records'),
            'attack_timeline': suspicious_df.groupby(suspicious_df['timestamp'].dt.hour).size().to_dict()
        }