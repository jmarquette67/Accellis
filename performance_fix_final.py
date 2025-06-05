#!/usr/bin/env python3
"""
Final comprehensive performance fix for navigation delays
"""

import os
import re

def fix_all_routing_issues():
    """Fix all remaining routing and performance issues"""
    
    # 1. Fix manager routes blueprint registration
    manager_routes_fixes = [
        ('manager.score_entry', '/scores/new'),
        ('manager.client_list', '/manager/clients'),
        ('manager.dashboard', '/'),
        ('manager.user_manual', '/manager/user-manual'),
        ('manager.advanced_reports', '/manager/advanced-reports'),
        ('manager.all_scoresheets', '/manager/all-scoresheets'),
        ('manager.client_details', '/manager/client-details'),
        ('manager.client_scoresheet', '/manager/client-scoresheet')
    ]
    
    # 2. Apply fixes to all template files
    templates_dir = "templates"
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(templates_dir, filename)
            
            with open(filepath, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Replace all manager.* url_for references with direct URLs
            for old_route, new_route in manager_routes_fixes:
                # Match various url_for patterns
                patterns = [
                    rf"url_for\(['\"]" + re.escape(old_route) + rf"['\"]([^)]*)\)",
                    rf"\{{\s*url_for\(['\"]" + re.escape(old_route) + rf"['\"]([^)]*)\)\s*\}}"
                ]
                
                for pattern in patterns:
                    content = re.sub(pattern, f'"{new_route}"', content)
            
            if content != original_content:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"Fixed {filename}")
    
    print("All routing fixes applied")

if __name__ == "__main__":
    fix_all_routing_issues()