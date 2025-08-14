#!/usr/bin/env python3
"""
Upload mockup data from JSON file to Notion database.
This script reads the test_mockup_data.json file and uploads it to Notion.
"""

import json
import os
import sys
from pathlib import Path
from notion_client import Client
import time
from datetime import datetime
from dotenv import load_dotenv

# Load .env file from src directory if it exists
script_dir = Path(__file__).parent
env_file = script_dir / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"✓ Loaded environment from {env_file}")
else:
    # Try loading from parent directory
    parent_env = script_dir.parent / '.env'
    if parent_env.exists():
        load_dotenv(parent_env)
        print(f"✓ Loaded environment from {parent_env}")


def load_test_data(file_path="test_mockup_data.json"):
    """Load the test data from JSON file."""
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found. Please run test_mockup_generation.py first.")
        return None
    
    with open(file_path, "r") as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} records from {file_path}")
    return data


def create_notion_properties(record):
    """Convert a record to Notion page properties."""
    properties = {
        "Log Entry": {
            "title": [
                {
                    "text": {
                        "content": record["log_entry"]
                    }
                }
            ]
        },
        "Date": {
            "date": {
                "start": record["date"]
            }
        },
        "Project Name": {
            "rich_text": [
                {
                    "text": {
                        "content": record["project_name"]
                    }
                }
            ]
        },
        "Version": {
            "rich_text": [
                {
                    "text": {
                        "content": record["version"]
                    }
                }
            ]
        },
        "Platform": {
            "select": {
                "name": record["platform"]
            }
        },
        "Previous Status": {
            "status": {
                "name": record["previous_status"]
            }
        },
        "New Status": {
            "status": {
                "name": record["new_status"]
            }
        },
        "Team": {
            "select": {
                "name": record["team"]
            }
        },
        "Sub-team": {
            "select": {
                "name": record["sub_team"]
            }
        },
        "Release Type": {
            "select": {
                "name": record["release_type"]
            }
        },
        "What's New": {
            "rich_text": [
                {
                    "text": {
                        "content": f"{record['whats_new']} (Changed by: {record['changed_by']})"
                    }
                }
            ]
        },
        "Automation Source": {
            "checkbox": True
        }
    }
    
    return properties


def upload_to_notion(api_key, database_id, records, batch_size=5):
    """Upload records to Notion database."""
    client = Client(auth=api_key)
    
    print(f"\n{'='*60}")
    print(f"Starting upload to Notion database")
    print(f"Database ID: {database_id}")
    print(f"Total records to upload: {len(records)}")
    print(f"Batch size: {batch_size}")
    print(f"{'='*60}\n")
    
    successful = 0
    failed = 0
    failed_records = []
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(records) + batch_size - 1) // batch_size
        
        print(f"Processing batch {batch_num}/{total_batches} (records {i+1}-{min(i+batch_size, len(records))})")
        
        for record in batch:
            try:
                properties = create_notion_properties(record)
                response = client.pages.create(
                    parent={"database_id": database_id},
                    properties=properties
                )
                successful += 1
                print(f"  ✓ {record['log_entry'][:60]}...")
            except Exception as e:
                failed += 1
                failed_records.append({
                    "record": record,
                    "error": str(e)
                })
                print(f"  ✗ Failed: {record['log_entry'][:40]}... - {str(e)[:50]}")
            
            # Rate limiting - Notion API has limits
            time.sleep(0.3)
        
        # Progress update
        progress = (successful + failed) / len(records) * 100
        print(f"  Progress: {progress:.1f}% ({successful + failed}/{len(records)})\n")
        
        # Pause between batches
        if batch_num < total_batches:
            time.sleep(1)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"Upload Summary")
    print(f"{'='*60}")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"Total: {len(records)}")
    print(f"Success rate: {(successful/len(records)*100):.1f}%")
    
    if failed_records:
        # Save failed records for debugging
        with open("failed_uploads.json", "w") as f:
            json.dump(failed_records, f, indent=2)
        print(f"\nFailed records saved to 'failed_uploads.json' for debugging")
    
    return successful, failed


def main():
    """Main function to upload mockup data to Notion."""
    print("="*60)
    print("NOTION MOCKUP DATA UPLOADER")
    print("="*60)
    
    # Check for API key
    api_key = os.getenv("NOTION_API_KEY")
    if not api_key:
        print("\n❌ Error: NOTION_API_KEY not found in environment variables")
        print("\nTo set your Notion API key, run:")
        print("  export NOTION_API_KEY='your_api_key_here'")
        print("\nTo get a Notion API key:")
        print("  1. Go to https://www.notion.so/my-integrations")
        print("  2. Create a new integration")
        print("  3. Copy the Internal Integration Token")
        print("  4. Share your database with the integration")
        return
    
    # Database ID from the Project Status Change Log
    database_id = os.getenv("NOTION_DATABASE_ID", "d94056721a9b4a4fa836743010fafec7")
    
    print(f"\n✓ API Key found")
    print(f"✓ Database ID: {database_id}")
    
    # Load test data
    records = load_test_data()
    if not records:
        return
    
    # Show sample data
    print(f"\nSample records to upload:")
    for i, record in enumerate(records[:3], 1):
        print(f"\n  {i}. {record['log_entry']}")
        print(f"     Date: {record['date'][:10]}")
        print(f"     Team: {record['team']}")
    
    print(f"\n  ... and {len(records)-3} more records")
    
    # Confirm upload
    print("\n" + "="*60)
    response = input("Do you want to upload these records to Notion? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        print("\nStarting upload...")
        successful, failed = upload_to_notion(api_key, database_id, records)
        
        if successful > 0:
            print(f"\n✅ Successfully uploaded {successful} records to Notion!")
            print(f"You can view them at: https://www.notion.so/{database_id}")
    else:
        print("\n❌ Upload cancelled.")
        print("Records remain in 'test_mockup_data.json' for future upload.")


if __name__ == "__main__":
    main()
