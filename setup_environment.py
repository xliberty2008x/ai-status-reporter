#!/usr/bin/env python3
"""
Environment setup helper for the Project Status Log system.
This script helps you configure your Notion API key and test the connection.
"""

import os
import sys
from pathlib import Path
from notion_client import Client
from notion_client.errors import APIResponseError


def test_notion_connection(api_key, database_id):
    """Test the Notion API connection and database access."""
    try:
        client = Client(auth=api_key)
        
        # Try to retrieve the database
        print(f"Testing connection to database: {database_id}")
        response = client.databases.retrieve(database_id=database_id)
        
        print("✅ Connection successful!")
        print(f"Database title: {response.get('title', [{}])[0].get('plain_text', 'N/A')}")
        
        # Check if it's the right database
        properties = response.get('properties', {})
        expected_properties = ['Log Entry', 'Date', 'Project Name', 'Team', 'Platform']
        
        missing = [prop for prop in expected_properties if prop not in properties]
        if missing:
            print(f"⚠️  Warning: Expected properties not found: {missing}")
            print("   Make sure you're using the correct database ID.")
        else:
            print("✅ Database structure verified!")
        
        return True
        
    except APIResponseError as e:
        print(f"❌ API Error: {e}")
        if e.code == 'unauthorized':
            print("   Check that your API key is correct and the integration has access to the database.")
        elif e.code == 'object_not_found':
            print("   The database was not found. Check the database ID.")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def setup_environment():
    """Interactive setup for environment variables."""
    print("="*60)
    print("PROJECT STATUS LOG - ENVIRONMENT SETUP")
    print("="*60)
    
    print("\nThis script will help you set up your Notion API connection.")
    print("\nPrerequisites:")
    print("1. Create a Notion integration at https://www.notion.so/my-integrations")
    print("2. Copy the Internal Integration Token")
    print("3. Share your database with the integration")
    print("   - Open the database in Notion")
    print("   - Click '...' menu → 'Add connections'")
    print("   - Select your integration")
    
    print("\n" + "-"*60)
    
    # Get API key
    current_key = os.getenv("NOTION_API_KEY")
    if current_key:
        print(f"\n✓ Existing API key found (starts with: {current_key[:10]}...)")
        use_existing = input("Use existing key? (yes/no): ")
        if use_existing.lower() in ['yes', 'y']:
            api_key = current_key
        else:
            api_key = input("Enter your Notion API key: ").strip()
    else:
        api_key = input("\nEnter your Notion API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Exiting.")
        return
    
    # Get database ID
    default_db_id = "d94056721a9b4a4fa836743010fafec7"
    current_db = os.getenv("NOTION_DATABASE_ID", default_db_id)
    
    print(f"\n✓ Default database ID: {current_db}")
    use_default = input("Use this database ID? (yes/no): ")
    
    if use_default.lower() in ['yes', 'y']:
        database_id = current_db
    else:
        database_id = input("Enter your database ID: ").strip()
        # Clean up the ID if it's a URL
        if "notion.so" in database_id:
            # Extract ID from URL
            parts = database_id.split("/")
            for part in parts:
                if len(part) == 32 and all(c in "0123456789abcdef" for c in part):
                    database_id = part
                    print(f"Extracted ID: {database_id}")
                    break
    
    # Test connection
    print("\n" + "-"*60)
    print("Testing connection...")
    
    if test_notion_connection(api_key, database_id):
        # Save to .env file
        env_file = Path(".env")
        
        print("\n" + "-"*60)
        save_env = input("\nSave configuration to .env file? (yes/no): ")
        
        if save_env.lower() in ['yes', 'y']:
            env_content = f"""# Notion API Configuration
NOTION_API_KEY={api_key}
NOTION_DATABASE_ID={database_id}

# Slack API Configuration (for future use)
# SLACK_BOT_TOKEN=your_slack_bot_token_here
# SLACK_CHANNEL_ID=C09111P5JN6
"""
            with open(env_file, "w") as f:
                f.write(env_content)
            
            print("✅ Configuration saved to .env file")
            
            # Add .env to .gitignore if not already there
            gitignore = Path(".gitignore")
            if gitignore.exists():
                with open(gitignore, "r") as f:
                    content = f.read()
                if ".env" not in content:
                    with open(gitignore, "a") as f:
                        f.write("\n# Environment variables\n.env\n")
                    print("✅ Added .env to .gitignore")
        
        # Export for current session
        print("\n" + "-"*60)
        print("\nTo use these settings in your current terminal session, run:")
        print(f"  export NOTION_API_KEY='{api_key}'")
        print(f"  export NOTION_DATABASE_ID='{database_id}'")
        
        print("\n✅ Setup complete! You can now run:")
        print("  python src/upload_mockup_to_notion.py")
        
    else:
        print("\n❌ Setup failed. Please check your credentials and try again.")


if __name__ == "__main__":
    try:
        setup_environment()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)

