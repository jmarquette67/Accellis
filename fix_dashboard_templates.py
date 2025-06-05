#!/usr/bin/env python3
"""
Fix all template routing errors to resolve authentication login loops
"""

import os
import re

def fix_template_routes():
    """Fix all manager.* routing references in templates"""
    
    template_fixes = {
        "manager.client_list": "/manager/clients",
        "manager.client_table": "/manager/clients", 
        "manager.dashboard": "/manager/dashboard",
        "manager.score_entry": "/manager/score-entry",
        "manager.user_manual": "/manager/user-manual",
        "manager.advanced_reports": "/manager/advanced-reports",
        "manager.client_details": "/manager/client-details",
        "manager.client_scoresheet": "/manager/client-scoresheet",
        "manager.all_scoresheets": "/manager/all-scoresheets"
    }
    
    templates_dir = "templates"
    
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(templates_dir, filename)
            
            with open(filepath, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Fix url_for references
            for old_route, new_route in template_fixes.items():
                # Match url_for('manager.route') patterns
                pattern = r"url_for\(['\"]" + re.escape(old_route) + r"['\"]([^)]*)\)"
                replacement = f'"{new_route}"'
                content = re.sub(pattern, replacement, content)
            
            # Write back if changed
            if content != original_content:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"Fixed routing in {filename}")

if __name__ == "__main__":
    fix_template_routes()
    print("Template routing fixes complete")