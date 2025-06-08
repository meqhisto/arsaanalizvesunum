#!/usr/bin/env python3
"""
Script to update all HTML templates to extend base.html and use Tailwind CSS classes
"""

import os
import re
from pathlib import Path

def update_template_file(file_path):
    """Update a single template file to use base.html and Tailwind CSS"""
    
    # Skip files that already extend base.html
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already extends base.html
    if 'extends "base.html"' in content:
        print(f"✅ {file_path} already extends base.html")
        return
    
    # Skip if it's base.html itself
    if file_path.name == 'base.html':
        print(f"⏭️  Skipping {file_path} (base template)")
        return
    
    # Skip non-HTML files
    if not file_path.suffix == '.html':
        print(f"⏭️  Skipping {file_path} (not HTML)")
        return
    
    print(f"🔄 Updating {file_path}...")
    
    # Extract title from existing HTML
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
    title = title_match.group(1) if title_match else "Arsa Analiz Platformu"
    
    # Extract body content (everything between <body> and </body>)
    body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
    if not body_match:
        print(f"❌ Could not find body content in {file_path}")
        return
    
    body_content = body_match.group(1).strip()
    
    # Extract any JavaScript from the original file
    js_matches = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
    js_content = '\n'.join(js_matches) if js_matches else ""
    
    # Clean up body content - remove container divs and update classes
    body_content = update_css_classes(body_content)
    
    # Create new template content
    new_content = f'''{{{% extends "base.html" %}}

{{{% block title %}}}{title}{{{% endblock %}}

{{{% block content %}}
{body_content}
{{{% endblock %}}'''
    
    # Add JavaScript block if there was any
    if js_content.strip():
        new_content += f'''

{{{% block extra_js %}}
<script>
{js_content}
</script>
{{{% endblock %}}'''
    
    # Write the updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Updated {file_path}")

def update_css_classes(content):
    """Update Bootstrap classes to Tailwind CSS classes"""
    
    # Common Bootstrap to Tailwind mappings
    replacements = {
        # Layout
        r'\bcontainer\b': 'max-w-7xl mx-auto px-4',
        r'\bcontainer-fluid\b': 'w-full px-4',
        r'\brow\b': 'grid md:grid-cols-12 gap-4',
        r'\bcol-12\b': 'col-span-12',
        r'\bcol-md-6\b': 'md:col-span-6',
        r'\bcol-md-4\b': 'md:col-span-4',
        r'\bcol-md-3\b': 'md:col-span-3',
        r'\bcol-lg-8\b': 'lg:col-span-8',
        r'\bcol-lg-4\b': 'lg:col-span-4',
        
        # Flexbox
        r'\bd-flex\b': 'flex',
        r'\bjustify-content-center\b': 'justify-center',
        r'\bjustify-content-between\b': 'justify-between',
        r'\balign-items-center\b': 'items-center',
        r'\bflex-column\b': 'flex-col',
        
        # Spacing
        r'\bmb-3\b': 'mb-4',
        r'\bmb-4\b': 'mb-6',
        r'\bmb-5\b': 'mb-8',
        r'\bmt-3\b': 'mt-4',
        r'\bmt-4\b': 'mt-6',
        r'\bmt-5\b': 'mt-8',
        r'\bp-3\b': 'p-4',
        r'\bp-4\b': 'p-6',
        r'\bp-5\b': 'p-8',
        
        # Text
        r'\btext-center\b': 'text-center',
        r'\btext-muted\b': 'text-gray-600',
        r'\bfw-bold\b': 'font-bold',
        r'\bfw-medium\b': 'font-medium',
        r'\bfs-4\b': 'text-xl',
        r'\bfs-5\b': 'text-lg',
        
        # Buttons
        r'\bbtn btn-primary\b': 'btn-primary',
        r'\bbtn btn-secondary\b': 'btn-secondary',
        r'\bbtn btn-success\b': 'bg-success-500 hover:bg-success-600 text-white px-4 py-2 rounded-lg transition-colors',
        r'\bbtn btn-warning\b': 'bg-warning-500 hover:bg-warning-600 text-white px-4 py-2 rounded-lg transition-colors',
        r'\bbtn btn-danger\b': 'bg-error-500 hover:bg-error-600 text-white px-4 py-2 rounded-lg transition-colors',
        r'\bbtn-lg\b': 'px-8 py-3 text-lg',
        r'\bbtn-sm\b': 'px-3 py-1 text-sm',
        
        # Cards
        r'\bcard\b': 'card',
        r'\bcard-header\b': 'card-header',
        r'\bcard-body\b': 'card-body',
        r'\bcard-title\b': 'text-xl font-semibold text-gray-900',
        
        # Forms
        r'\bform-control\b': 'form-control w-full',
        r'\bform-select\b': 'form-select w-full',
        r'\bform-label\b': 'block text-sm font-medium text-gray-700 mb-2',
        
        # Alerts
        r'\balert alert-success\b': 'alert alert-success',
        r'\balert alert-warning\b': 'alert alert-warning',
        r'\balert alert-danger\b': 'alert alert-danger',
        r'\balert alert-info\b': 'alert alert-info',
        
        # Background
        r'\bbg-light\b': 'bg-gray-50',
        r'\bbg-white\b': 'bg-white',
        r'\bbg-primary\b': 'bg-primary-600',
        
        # Icons - Bootstrap Icons to Font Awesome
        r'\bbi bi-([a-zA-Z-]+)\b': r'fas fa-\1',
        r'\bme-2\b': 'mr-2',
        r'\bme-3\b': 'mr-3',
        r'\bms-2\b': 'ml-2',
        r'\bms-3\b': 'ml-3',
    }
    
    # Apply replacements
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)
    
    return content

def main():
    """Main function to update all templates"""
    
    # Get the templates directory
    templates_dir = Path('templates')
    
    if not templates_dir.exists():
        print("❌ Templates directory not found!")
        return
    
    # Find all HTML files
    html_files = list(templates_dir.rglob('*.html'))
    
    print(f"🔍 Found {len(html_files)} HTML files")
    print("=" * 50)
    
    # Update each file
    for html_file in html_files:
        try:
            update_template_file(html_file)
        except Exception as e:
            print(f"❌ Error updating {html_file}: {e}")
    
    print("=" * 50)
    print("✅ Template update process completed!")
    print("\n📝 Next steps:")
    print("1. Run 'npm run build' to rebuild CSS")
    print("2. Test the application")
    print("3. Check for any broken layouts")

if __name__ == "__main__":
    main()
