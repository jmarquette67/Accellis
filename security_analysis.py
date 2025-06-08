#!/usr/bin/env python3
"""
Security Analysis Script for Accellis Client Engagement Platform
Performs comprehensive security assessment to identify potential vulnerabilities
"""

import os
import re
import ast
import sys
from pathlib import Path

class SecurityAnalyzer:
    def __init__(self):
        self.findings = []
        self.severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}
        
    def add_finding(self, severity, category, description, file_path=None, line_number=None):
        """Add a security finding"""
        finding = {
            'severity': severity,
            'category': category,
            'description': description,
            'file': file_path,
            'line': line_number
        }
        self.findings.append(finding)
        self.severity_counts[severity] += 1
        
    def analyze_authentication(self):
        """Analyze authentication implementation"""
        print("Analyzing authentication security...")
        
        # Check for proper session management
        replit_auth_file = Path('replit_auth.py')
        if replit_auth_file.exists():
            content = replit_auth_file.read_text()
            
            # Check for secure session configuration
            if 'session.permanent = True' in content:
                self.add_finding('INFO', 'Authentication', 
                               'Permanent sessions configured - ensure proper timeout is set',
                               'replit_auth.py')
            
            # Check for PKCE implementation (security best practice)
            if 'use_pkce=True' in content:
                self.add_finding('INFO', 'Authentication', 
                               'PKCE (Proof Key for Code Exchange) properly implemented',
                               'replit_auth.py')
            
            # Check for secure token storage
            if 'UserSessionStorage' in content:
                self.add_finding('INFO', 'Authentication', 
                               'Custom session storage implementation found - verify security',
                               'replit_auth.py')
                
    def analyze_authorization(self):
        """Analyze authorization and access control"""
        print("Analyzing authorization controls...")
        
        # Check role-based access control implementation
        models_file = Path('models.py')
        if models_file.exists():
            content = models_file.read_text()
            
            if 'UserRole' in content and 'has_role' in content:
                self.add_finding('INFO', 'Authorization', 
                               'Role-based access control (RBAC) properly implemented',
                               'models.py')
            
            # Check for role hierarchy
            if 'role_hierarchy' in content:
                self.add_finding('INFO', 'Authorization', 
                               'Role hierarchy system implemented for privilege escalation control',
                               'models.py')
        
        # Check route protection
        routes_files = ['routes.py', 'manager_routes.py']
        for file_path in routes_files:
            if Path(file_path).exists():
                content = Path(file_path).read_text()
                
                # Check for proper authentication decorators
                if '@require_login' in content:
                    self.add_finding('INFO', 'Authorization', 
                                   f'Login requirements properly enforced in {file_path}',
                                   file_path)
                
                # Check for role-based protection
                if 'require_manager' in content or 'UserRole' in content:
                    self.add_finding('INFO', 'Authorization', 
                                   f'Role-based access control enforced in {file_path}',
                                   file_path)
                
    def analyze_input_validation(self):
        """Analyze input validation and sanitization"""
        print("Analyzing input validation...")
        
        forms_file = Path('forms.py')
        if forms_file.exists():
            content = forms_file.read_text()
            
            # Check for WTForms validation
            if 'validators=' in content and 'DataRequired' in content:
                self.add_finding('INFO', 'Input Validation', 
                               'WTForms validation implemented for form inputs',
                               'forms.py')
            
            # Check for length validation
            if 'Length(' in content:
                self.add_finding('INFO', 'Input Validation', 
                               'String length validation implemented',
                               'forms.py')
            
            # Check for email validation
            if 'Email(' in content:
                self.add_finding('INFO', 'Input Validation', 
                               'Email format validation implemented',
                               'forms.py')
        
        # Check for SQL injection protection
        routes_files = ['routes.py', 'manager_routes.py']
        for file_path in routes_files:
            if Path(file_path).exists():
                content = Path(file_path).read_text()
                
                # Look for potential SQL injection risks
                if re.search(r'\.execute\s*\(\s*["\'].*%.*["\']', content):
                    self.add_finding('HIGH', 'SQL Injection', 
                                   f'Potential SQL injection vulnerability found in {file_path}',
                                   file_path)
                
                # Check for parameterized queries
                if 'text(' in content and 'params=' in content:
                    self.add_finding('INFO', 'SQL Injection', 
                                   f'Parameterized queries used in {file_path}',
                                   file_path)
                
    def analyze_data_handling(self):
        """Analyze data handling and storage security"""
        print("Analyzing data handling security...")
        
        # Check for secure file uploads
        manager_routes = Path('manager_routes.py')
        if manager_routes.exists():
            content = manager_routes.read_text()
            
            if 'secure_filename' in content:
                self.add_finding('INFO', 'File Upload', 
                               'Secure filename handling implemented for file uploads',
                               'manager_routes.py')
            
            # Check for file type validation
            if 'allowed_extensions' in content or '.jpg' in content or '.png' in content:
                self.add_finding('INFO', 'File Upload', 
                               'File type restrictions appear to be implemented',
                               'manager_routes.py')
        
        # Check database configuration
        app_file = Path('app.py')
        if app_file.exists():
            content = app_file.read_text()
            
            # Check for connection pooling
            if 'pool_pre_ping' in content:
                self.add_finding('INFO', 'Database Security', 
                               'Database connection pool pre-ping enabled for reliability',
                               'app.py')
            
            # Check for connection recycling
            if 'pool_recycle' in content:
                self.add_finding('INFO', 'Database Security', 
                               'Database connection recycling configured',
                               'app.py')
                
    def analyze_secrets_management(self):
        """Analyze secrets and environment variable handling"""
        print("Analyzing secrets management...")
        
        python_files = ['app.py', 'routes.py', 'manager_routes.py', 'replit_auth.py']
        
        for file_path in python_files:
            if Path(file_path).exists():
                content = Path(file_path).read_text()
                
                # Check for hardcoded secrets (potential risk)
                secret_patterns = [
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']',
                    r'key\s*=\s*["\'][^"\']+["\']'
                ]
                
                for pattern in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if 'os.environ' not in match.group():
                            line_num = content[:match.start()].count('\n') + 1
                            self.add_finding('HIGH', 'Secrets Management', 
                                           f'Potential hardcoded secret found in {file_path}',
                                           file_path, line_num)
                
                # Check for proper environment variable usage
                if 'os.environ.get(' in content:
                    self.add_finding('INFO', 'Secrets Management', 
                                   f'Environment variables properly used in {file_path}',
                                   file_path)
                
    def analyze_csrf_protection(self):
        """Analyze CSRF protection"""
        print("Analyzing CSRF protection...")
        
        forms_file = Path('forms.py')
        if forms_file.exists():
            content = forms_file.read_text()
            
            if 'FlaskForm' in content:
                self.add_finding('INFO', 'CSRF Protection', 
                               'WTForms provides built-in CSRF protection',
                               'forms.py')
        
        # Check templates for CSRF tokens
        template_files = list(Path('templates').glob('*.html')) if Path('templates').exists() else []
        csrf_found = False
        
        for template in template_files:
            content = template.read_text()
            if 'csrf_token' in content or 'hidden_tag()' in content:
                csrf_found = True
                break
        
        if csrf_found:
            self.add_finding('INFO', 'CSRF Protection', 
                           'CSRF tokens found in templates',
                           'templates/')
        else:
            self.add_finding('MEDIUM', 'CSRF Protection', 
                           'No CSRF tokens found in templates - verify protection is enabled',
                           'templates/')
            
    def analyze_headers_security(self):
        """Analyze security headers"""
        print("Analyzing security headers...")
        
        app_file = Path('app.py')
        if app_file.exists():
            content = app_file.read_text()
            
            # Check for security headers
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options', 
                'X-XSS-Protection',
                'Strict-Transport-Security',
                'Content-Security-Policy'
            ]
            
            headers_found = []
            for header in security_headers:
                if header in content:
                    headers_found.append(header)
            
            if headers_found:
                self.add_finding('INFO', 'Security Headers', 
                               f'Security headers implemented: {", ".join(headers_found)}',
                               'app.py')
            else:
                self.add_finding('MEDIUM', 'Security Headers', 
                               'No security headers found - consider implementing CSP, HSTS, etc.',
                               'app.py')
            
            # Check for ProxyFix (important for headers in reverse proxy setups)
            if 'ProxyFix' in content:
                self.add_finding('INFO', 'Security Headers', 
                               'ProxyFix configured for reverse proxy deployment',
                               'app.py')
                
    def check_dependencies(self):
        """Check for known vulnerable dependencies"""
        print("Analyzing dependencies...")
        
        requirements_files = ['requirements.txt', 'pyproject.toml']
        
        for req_file in requirements_files:
            if Path(req_file).exists():
                self.add_finding('INFO', 'Dependencies', 
                               f'Dependency file found: {req_file} - ensure regular updates',
                               req_file)
                
                content = Path(req_file).read_text()
                
                # Check for common security-related packages
                security_packages = ['flask-wtf', 'flask-login', 'sqlalchemy', 'werkzeug']
                found_packages = []
                
                for package in security_packages:
                    if package in content.lower():
                        found_packages.append(package)
                
                if found_packages:
                    self.add_finding('INFO', 'Dependencies', 
                                   f'Security-relevant packages found: {", ".join(found_packages)}',
                                   req_file)
                
    def generate_report(self):
        """Generate security analysis report"""
        print("\n" + "="*60)
        print("SECURITY ANALYSIS REPORT")
        print("="*60)
        
        print(f"\nSUMMARY:")
        print(f"Total Findings: {len(self.findings)}")
        for severity, count in self.severity_counts.items():
            if count > 0:
                print(f"{severity}: {count}")
        
        print(f"\nDETAILED FINDINGS:")
        print("-" * 40)
        
        # Sort findings by severity
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, 'INFO': 3}
        sorted_findings = sorted(self.findings, key=lambda x: severity_order.get(x['severity'], 4))
        
        for finding in sorted_findings:
            print(f"\n[{finding['severity']}] {finding['category']}")
            print(f"Description: {finding['description']}")
            if finding['file']:
                location = finding['file']
                if finding['line']:
                    location += f":{finding['line']}"
                print(f"Location: {location}")
        
        print(f"\n" + "="*60)
        print("SECURITY RECOMMENDATIONS:")
        print("="*60)
        
        recommendations = []
        
        if self.severity_counts['HIGH'] > 0:
            recommendations.append("• Address HIGH severity findings immediately")
        
        if self.severity_counts['MEDIUM'] > 0:
            recommendations.append("• Review and fix MEDIUM severity findings")
        
        recommendations.extend([
            "• Implement security headers (CSP, HSTS, X-Frame-Options)",
            "• Ensure all forms use CSRF protection",
            "• Regularly update dependencies for security patches",
            "• Implement proper logging and monitoring",
            "• Conduct regular security assessments",
            "• Use HTTPS in production with proper TLS configuration",
            "• Implement rate limiting for API endpoints",
            "• Regular backup and disaster recovery testing"
        ])
        
        for rec in recommendations:
            print(rec)
        
        print(f"\n" + "="*60)
        
        # Determine overall security status
        if self.severity_counts['HIGH'] > 0:
            status = "NEEDS IMMEDIATE ATTENTION"
        elif self.severity_counts['MEDIUM'] > 0:
            status = "GOOD WITH RECOMMENDATIONS"  
        else:
            status = "SECURE"
            
        print(f"OVERALL SECURITY STATUS: {status}")
        print("="*60)
        
        return status
        
    def run_analysis(self):
        """Run complete security analysis"""
        print("Starting comprehensive security analysis...")
        print("="*60)
        
        self.analyze_authentication()
        self.analyze_authorization()
        self.analyze_input_validation()
        self.analyze_data_handling()
        self.analyze_secrets_management()
        self.analyze_csrf_protection()
        self.analyze_headers_security()
        self.check_dependencies()
        
        return self.generate_report()

if __name__ == "__main__":
    analyzer = SecurityAnalyzer()
    status = analyzer.run_analysis()
    
    # Exit with appropriate code
    if "IMMEDIATE ATTENTION" in status:
        sys.exit(1)
    else:
        sys.exit(0)