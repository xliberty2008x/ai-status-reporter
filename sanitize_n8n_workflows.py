#!/usr/bin/env python3
"""
Sanitize n8n workflow files by replacing sensitive information with placeholders.
Creates sanitized versions with .sanitized.json extension.
"""

import json
import re
from pathlib import Path
import shutil


def sanitize_value(value):
    """Replace sensitive values with placeholders."""
    if isinstance(value, str):
        # Replace Notion database IDs (32 character hex strings)
        value = re.sub(r'[a-f0-9]{32}', 'YOUR_DATABASE_ID_HERE', value)
        
        # Replace Notion URLs
        value = re.sub(
            r'https://www\.notion\.so/[^/]+/[a-f0-9]{32}[^"]*',
            'https://www.notion.so/YOUR_WORKSPACE/YOUR_DATABASE_ID_HERE',
            value
        )
        
        # Replace Slack webhook URLs
        value = re.sub(
            r'https://hooks\.slack\.com/services/[A-Z0-9/]+',
            'https://hooks.slack.com/services/YOUR_WEBHOOK_URL_HERE',
            value
        )
        
        # Replace Slack tokens
        value = re.sub(r'xoxb-[0-9A-Za-z-]+', 'xoxb-YOUR_SLACK_TOKEN_HERE', value)
        
        # Replace API keys
        value = re.sub(r'sk-[0-9A-Za-z]+', 'sk-YOUR_API_KEY_HERE', value)
        value = re.sub(r'Bearer [0-9A-Za-z-]+', 'Bearer YOUR_TOKEN_HERE', value)
        
        # Replace instance IDs
        value = re.sub(
            r'"instanceId":\s*"[a-f0-9]{48}"',
            '"instanceId": "YOUR_INSTANCE_ID_HERE"',
            value
        )
        
        # Replace workspace names in URLs
        value = re.sub(r'notion\.so/viragames/', 'notion.so/YOUR_WORKSPACE/', value)
        
    return value


def sanitize_dict(obj):
    """Recursively sanitize all values in a dictionary."""
    if isinstance(obj, dict):
        return {k: sanitize_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_dict(item) for item in obj]
    elif isinstance(obj, str):
        return sanitize_value(obj)
    else:
        return obj


def process_workflow_file(file_path):
    """Process a single workflow file and create sanitized version."""
    print(f"Processing: {file_path.name}")
    
    try:
        # Read the original file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse JSON
        workflow_data = json.loads(content)
        
        # Sanitize the data
        sanitized_data = sanitize_dict(workflow_data)
        
        # Create sanitized filename
        sanitized_path = file_path.parent / f"{file_path.stem}.sanitized.json"
        
        # Write sanitized version
        with open(sanitized_path, 'w', encoding='utf-8') as f:
            json.dump(sanitized_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ Created sanitized version: {sanitized_path.name}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"  ❌ Error parsing JSON: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error processing file: {e}")
        return False


def main():
    """Main function to sanitize all n8n workflow files."""
    print("🔒 Sanitizing n8n workflow files...")
    print("-" * 50)
    
    # Define the workflows directory
    workflows_dir = Path(__file__).parent / "src" / "n8n_workflows"
    
    if not workflows_dir.exists():
        print(f"❌ Workflows directory not found: {workflows_dir}")
        return
    
    # Find all JSON files (excluding already sanitized ones)
    workflow_files = [
        f for f in workflows_dir.glob("*.json") 
        if not f.name.endswith('.sanitized.json')
    ]
    
    if not workflow_files:
        print("❌ No workflow files found to sanitize")
        return
    
    print(f"Found {len(workflow_files)} workflow files to sanitize\n")
    
    # Process each file
    success_count = 0
    for file_path in workflow_files:
        if process_workflow_file(file_path):
            success_count += 1
    
    print("\n" + "-" * 50)
    print(f"✅ Successfully sanitized {success_count}/{len(workflow_files)} files")
    
    # Update .gitignore recommendations
    print("\n📝 Recommended .gitignore entries:")
    print("# Original n8n workflows with sensitive data")
    print("src/n8n_workflows/*.json")
    print("!src/n8n_workflows/*.sanitized.json")
    
    print("\n💡 Next steps:")
    print("1. Review the sanitized files to ensure no sensitive data remains")
    print("2. Update .gitignore to exclude original workflow files")
    print("3. Commit only the .sanitized.json files to the repository")
    print("4. Users should copy .sanitized.json files and replace placeholders with their own values")


if __name__ == "__main__":
    main()
