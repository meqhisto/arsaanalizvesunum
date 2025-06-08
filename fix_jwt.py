#!/usr/bin/env python3
"""
JWT decorator'larını düzeltmek için script
"""

import os
import re

def fix_jwt_decorators():
    """JWT decorator'larını düzeltir."""
    
    # Düzeltilecek dosyalar
    files_to_fix = [
        'blueprints/api/v1/analysis.py',
        'blueprints/api/v1/crm.py',
        'blueprints/api/v1/media.py',
        'blueprints/api/v1/portfolio.py'
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"Fixing {file_path}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # jwt_required_api import'unu kaldır
            content = re.sub(r'jwt_required_api,?\s*', '', content)
            
            # jwt_required_api() decorator'larını jwt_required() ile değiştir
            content = re.sub(r'@jwt_required_api\(\)', '@jwt_required()', content)
            
            # get_current_user import'unu kaldır
            content = re.sub(r'get_current_user,?\s*', '', content)
            
            # get_current_user() çağrılarını değiştir
            content = re.sub(
                r'current_user = get_current_user\(\)\s*\n\s*if not current_user:\s*\n\s*return not_found_response\("User not found"\)',
                'user_id = get_jwt_identity()\n    current_user = User.query.get(user_id)\n    if not current_user:\n        return not_found_response("User not found")',
                content
            )
            
            # Flask-JWT-Extended import'unu ekle
            if 'from flask_jwt_extended import' not in content:
                # Flask import'undan sonra ekle
                content = re.sub(
                    r'(from flask import [^\n]+\n)',
                    r'\1from flask_jwt_extended import jwt_required, get_jwt_identity\n',
                    content
                )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Fixed {file_path}")
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    fix_jwt_decorators()
    print("JWT decorators fixed!")
