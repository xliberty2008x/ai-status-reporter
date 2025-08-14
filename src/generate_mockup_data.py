"""
Generate mockup data for Project Status Change Log database in Notion.
This script creates 100-200 realistic status change records based on the schema.
"""

import random
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from notion_client import Client
from faker import Faker
from dateutil import rrule
import time

# Initialize Faker for generating realistic data
fake = Faker()

# Database Schema Constants
PLATFORMS = ["GP", "AMZ", "iOS", "Fire TV"]
TEAMS = [
    "AMZ Production Team",
    "AMZ Integration and Port Team", 
    "AMZ Growth Team",
    "Tools Team"
]
SUB_TEAMS = [
    "Growth", "KHACHAPURI", "FUJI", "TOKYO", "OSLO", "BERLIN",
    "PARIS", "LONDON", "MIAMI", "VEGAS", "SYDNEY", "MUMBAI",
    "CAIRO", "ATHENS", "ROME", "MADRID", "LISBON", "DUBLIN",
    "STOCKHOLM", "HELSINKI", "WARSAW", "PRAGUE", "VIENNA",
    "BUDAPEST", "AMSTERDAM"
]

RELEASE_TYPES = [
    "CTR Setting Test", "First Release", "Update", "Full Game",
    "A/B Test", "Remote A/B Test", "Remote Update Subscription", "Re-build"
]

# Status progression paths (realistic flows)
STATUS_FLOWS = {
    "to_do": ["BACKLOG"],
    "in_progress": [
        "GD CTR TEST", "CTR TEST", "CTR TEST DONE", "CTR ARCHIVE",
        "WAITING FOR DEV", "DEVELOPMENT", "QA", "WAITING RELEASE", "RELEASE POOL"
    ],
    "complete": [
        "CREO PRODUCTION", "CREO DONE", "UA TOP SPENDERS", "LIVE",
        "UA TEST", "UA BOOST", "UA SETUP", "UA", "AUTO UA", "PAUSED",
        "UA PAUSED", "SHADOW BAN", "BLOCKED", "ARCHIVE", "SUSPENDED",
        "REJECTED", "Complete"
    ]
}

# Common status transitions (realistic paths)
STATUS_TRANSITIONS = [
    ("BACKLOG", "WAITING FOR DEV"),
    ("WAITING FOR DEV", "DEVELOPMENT"),
    ("DEVELOPMENT", "QA"),
    ("QA", "DEVELOPMENT"),  # Bug found, back to dev
    ("QA", "WAITING RELEASE"),
    ("WAITING RELEASE", "RELEASE POOL"),
    ("RELEASE POOL", "LIVE"),
    ("LIVE", "UA TEST"),
    ("UA TEST", "UA SETUP"),
    ("UA SETUP", "UA"),
    ("UA", "UA BOOST"),
    ("UA", "UA PAUSED"),
    ("UA PAUSED", "UA"),
    ("LIVE", "PAUSED"),
    ("PAUSED", "LIVE"),
    ("BACKLOG", "GD CTR TEST"),
    ("GD CTR TEST", "CTR TEST"),
    ("CTR TEST", "CTR TEST DONE"),
    ("CTR TEST DONE", "CTR ARCHIVE"),
    ("CTR ARCHIVE", "DEVELOPMENT"),
    ("LIVE", "BLOCKED"),
    ("LIVE", "SHADOW BAN"),
    ("LIVE", "ARCHIVE"),
]

# Sample project names (game-like)
PROJECT_NAMES = [
    "Snake Run: Crawl Chase",
    "Dragon Quest Arena",
    "Crystal Match 3D",
    "Tower Defense Pro",
    "Racing Fever Ultimate",
    "Puzzle Kingdom Adventure",
    "Battle Royale Warriors",
    "Farm Heroes Saga",
    "Space Shooter Galaxy",
    "Word Master Challenge",
    "Cooking Frenzy Rush",
    "Zombie Survival Craft",
    "Bubble Pop Mania",
    "Chess Master Online",
    "Card Battle Epic",
    "Idle Tycoon Empire",
    "Match & Merge Quest",
    "Solitaire Journey",
    "Block Puzzle Classic",
    "Hidden Object Mystery",
    "Jewel Blast Adventure",
    "Mahjong Deluxe",
    "Pinball Arcade",
    "Pool Master 3D",
    "Slots Fortune Casino"
]

# Sample change descriptions
CHANGE_DESCRIPTIONS = [
    "Rebuild with single subscription",
    "Fixed crash on iOS 17",
    "Added new levels pack",
    "Performance optimization",
    "UI improvements",
    "Bug fixes and stability improvements",
    "Added holiday theme",
    "Monetization adjustments",
    "Tutorial improvements",
    "Localization updates",
    "Ad placement optimization",
    "New game mode added",
    "Balance adjustments",
    "Graphics quality improvements",
    "Sound effects updated",
    "Leaderboard integration",
    "Social features added",
    "IAP prices adjusted",
    "Retention mechanics improved",
    "Loading time optimized"
]


class NotionMockupGenerator:
    def __init__(self, api_key: str, database_id: str):
        """Initialize Notion client and database connection."""
        self.client = Client(auth=api_key)
        self.database_id = database_id
        self.generated_records = []
        
    def generate_version(self) -> str:
        """Generate a realistic version number."""
        major = random.randint(1, 3)
        minor = random.randint(0, 15)
        patch = random.randint(0, 99)
        return f"{major}.{minor}.{patch}"
    
    def generate_date_range(self, num_records: int) -> List[datetime]:
        """Generate dates spanning the last 30 days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Generate evenly distributed dates
        dates = []
        for i in range(num_records):
            # Weight recent dates more heavily
            if random.random() < 0.6:  # 60% in last 7 days
                days_ago = random.randint(0, 7)
            else:  # 40% in the rest of the month
                days_ago = random.randint(8, 30)
            
            date = end_date - timedelta(days=days_ago, 
                                       hours=random.randint(0, 23),
                                       minutes=random.randint(0, 59))
            dates.append(date)
        
        return sorted(dates)
    
    def generate_project_lifecycle(self, project_name: str, team: str, platform: str) -> List[Dict[str, Any]]:
        """Generate a realistic lifecycle of status changes for a project."""
        records = []
        current_status = "BACKLOG"
        version = self.generate_version()
        sub_team = random.choice(SUB_TEAMS)
        
        # Generate 3-8 status changes per project
        num_changes = random.randint(3, 8)
        
        for _ in range(num_changes):
            # Find valid next statuses
            valid_transitions = [t for t in STATUS_TRANSITIONS if t[0] == current_status]
            if not valid_transitions:
                # If no valid transition, pick a random one
                valid_transitions = random.sample(STATUS_TRANSITIONS, 3)
            
            previous_status = current_status
            current_status = random.choice(valid_transitions)[1]
            
            # Sometimes update version on certain status changes
            if current_status in ["QA", "RELEASE POOL", "LIVE"] and random.random() < 0.3:
                version = self.generate_version()
            
            record = {
                "project_name": project_name,
                "team": team,
                "sub_team": sub_team,
                "platform": platform,
                "version": version,
                "previous_status": previous_status,
                "new_status": current_status,
                "release_type": random.choice(RELEASE_TYPES),
                "whats_new": random.choice(CHANGE_DESCRIPTIONS),
                "changed_by": fake.name()
            }
            records.append(record)
            
            # Sometimes project gets stuck at a status
            if random.random() < 0.2:
                break
                
        return records
    
    def generate_mockup_records(self, num_records: int = 150) -> List[Dict[str, Any]]:
        """Generate specified number of mockup records."""
        all_records = []
        
        # Generate projects with their lifecycles
        num_projects = num_records // 5  # Average 5 status changes per project
        
        for _ in range(num_projects):
            project_name = random.choice(PROJECT_NAMES) + f" {fake.word().capitalize()}"
            team = random.choice(TEAMS)
            platform = random.choice(PLATFORMS)
            
            project_records = self.generate_project_lifecycle(project_name, team, platform)
            all_records.extend(project_records)
        
        # Trim to exact number and assign dates
        all_records = all_records[:num_records]
        dates = self.generate_date_range(len(all_records))
        
        for record, date in zip(all_records, dates):
            record["date"] = date.isoformat()
            record["log_entry"] = f"{record['project_name']} - {record['previous_status']} → {record['new_status']}"
        
        return all_records
    
    def create_notion_page(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single page in Notion database."""
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
                            "content": record["whats_new"]
                        }
                    }
                ]
            },
            "Automation Source": {
                "checkbox": True
            }
        }
        
        # Note: Changed By field would need to be a Person type in Notion
        # For mockup, we'll store it in What's New or skip it
        
        return properties
    
    def upload_to_notion(self, records: List[Dict[str, Any]], batch_size: int = 10):
        """Upload records to Notion database in batches."""
        print(f"Starting upload of {len(records)} records to Notion...")
        
        successful = 0
        failed = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1} ({i+1}-{min(i+batch_size, len(records))} of {len(records)})")
            
            for record in batch:
                try:
                    properties = self.create_notion_page(record)
                    self.client.pages.create(
                        parent={"database_id": self.database_id},
                        properties=properties
                    )
                    successful += 1
                    print(f"  ✓ Created: {record['log_entry']}")
                except Exception as e:
                    failed += 1
                    print(f"  ✗ Failed: {record['log_entry']} - Error: {str(e)}")
                
                # Rate limiting - Notion API has limits
                time.sleep(0.3)
            
            print(f"Batch complete. Progress: {successful + failed}/{len(records)}")
            time.sleep(1)  # Pause between batches
        
        print(f"\n{'='*50}")
        print(f"Upload complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total: {len(records)}")
        
        return successful, failed


def main():
    """Main function to generate and upload mockup data."""
    # Get API credentials from environment or use defaults for testing
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID", "d94056721a9b4a4fa836743010fafec7")
    
    if not api_key:
        print("Error: NOTION_API_KEY not found in environment variables")
        print("Please set your Notion API key:")
        print("  export NOTION_API_KEY='your_api_key_here'")
        return
    
    # Initialize generator
    generator = NotionMockupGenerator(api_key, database_id)
    
    # Generate mockup records
    num_records = 150  # Middle ground between 100-200
    print(f"Generating {num_records} mockup records...")
    records = generator.generate_mockup_records(num_records)
    
    # Display sample records
    print(f"\nGenerated {len(records)} records. Sample:")
    for record in records[:3]:
        print(f"  - {record['log_entry']}")
        print(f"    Date: {record['date']}")
        print(f"    Team: {record['team']} / {record['sub_team']}")
        print(f"    Platform: {record['platform']} v{record['version']}")
        print()
    
    # Ask for confirmation before uploading
    response = input("Do you want to upload these records to Notion? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        generator.upload_to_notion(records)
    else:
        print("Upload cancelled. Records were generated but not uploaded.")
        
        # Optionally save to local file for review
        save_local = input("Save records to local JSON file? (yes/no): ")
        if save_local.lower() in ['yes', 'y']:
            import json
            with open("mockup_records.json", "w") as f:
                json.dump(records, f, indent=2)
            print("Records saved to mockup_records.json")


if __name__ == "__main__":
    main()

