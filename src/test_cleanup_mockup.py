#!/usr/bin/env python3
"""
Test data generator for n8n cleanup workflow testing.
Generates records specifically for testing the monthly cleanup process.
Creates records in previous month, current month, and older months to verify proper filtering.
"""

import os
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# Teams and their sub-teams
TEAMS = {
    "AMZ Growth Team": ["Growth", "Optimization", "Analytics"],
    "iOS Team": ["Core", "Features", "QA"],
    "GP Team": ["Development", "Testing", "Release"],
    "Fire TV Team": ["UI/UX", "Backend", "Integration"]
}

# Platforms
PLATFORMS = ["AMZ", "iOS", "GP", "Fire TV"]

# Status transitions for testing
STATUS_TRANSITIONS = [
    ("BACKLOG", "GD CTR TEST"),
    ("GD CTR TEST", "CTR TEST"),
    ("CTR TEST", "CTR TEST DONE"),
    ("CTR TEST DONE", "DEVELOPMENT"),
    ("DEVELOPMENT", "QA"),
    ("QA", "WAITING RELEASE"),
    ("WAITING RELEASE", "RELEASE POOL"),
    ("RELEASE POOL", "LIVE"),
    ("LIVE", "UA TEST"),
    ("UA TEST", "UA"),
    ("UA", "AUTO UA"),
    ("AUTO UA", "PAUSED")
]

# Release types
RELEASE_TYPES = ["Major Release", "Minor Update", "Hotfix", "A/B Test", "Rollback"]

# Sample project names
PROJECT_NAMES = [
    "sncrchz - Snake Run: Crawl Chase",
    "pzzlqst - Puzzle Quest Adventure",
    "rcrspd - Racer Speed Challenge",
    "bldtwr - Build Tower Master",
    "mrgfrm - Merge Farm Tycoon",
    "wrdgme - Word Game Pro",
    "mtchthre - Match Three Saga",
    "idlempre - Idle Empire Builder",
    "srvvlgme - Survival Game X",
    "cshrn - Cash Run Money Race"
]

# What's new messages
WHATS_NEW_MESSAGES = [
    "Updated SDK to latest version",
    "Fixed critical crash on startup",
    "Improved monetization flow",
    "Added new subscription model",
    "Optimized game performance",
    "Fixed memory leaks",
    "Updated privacy policy compliance",
    "Added seasonal event",
    "Improved user retention features",
    "Fixed IAP validation issues",
    "Enhanced analytics tracking",
    "Updated ad mediation",
    "Fixed localization issues",
    "Improved onboarding flow",
    "Added new game mode"
]


class CleanupTestDataGenerator:
    """Generate test data for cleanup workflow testing."""
    
    def __init__(self):
        """Initialize with Notion client."""
        self.notion = Client(auth=os.getenv("NOTION_API_KEY"))
        self.database_id = os.getenv("STATUS_LOG_DB_ID")
        
        if not self.database_id:
            raise ValueError("STATUS_LOG_DB_ID not found in environment variables")
        
        # Calculate date ranges
        self.today = datetime.now()
        self.current_month_start = datetime(self.today.year, self.today.month, 1)
        
        # Previous month
        if self.today.month == 1:
            self.prev_month_start = datetime(self.today.year - 1, 12, 1)
            self.prev_month_end = datetime(self.today.year - 1, 12, 31)
        else:
            self.prev_month_start = datetime(self.today.year, self.today.month - 1, 1)
            # Last day of previous month
            self.prev_month_end = self.current_month_start - timedelta(days=1)
        
        # Two months ago (should be deleted)
        if self.today.month <= 2:
            month_offset = 12 + self.today.month - 2
            year_offset = self.today.year - 1
        else:
            month_offset = self.today.month - 2
            year_offset = self.today.year
        self.two_months_ago_start = datetime(year_offset, month_offset, 1)
        
        # Three months ago (should be deleted)
        if self.today.month <= 3:
            month_offset = 12 + self.today.month - 3
            year_offset = self.today.year - 1
        else:
            month_offset = self.today.month - 3
            year_offset = self.today.year
        self.three_months_ago_start = datetime(year_offset, month_offset, 1)
    
    def generate_test_records(self) -> List[Dict[str, Any]]:
        """Generate test records across different time periods."""
        records = []
        
        print(f"\n📅 Date Ranges for Testing:")
        print(f"   Current Month: {self.current_month_start.strftime('%B %Y')}")
        print(f"   Previous Month: {self.prev_month_start.strftime('%B %Y')} (KEEP)")
        print(f"   Two Months Ago: {self.two_months_ago_start.strftime('%B %Y')} (DELETE)")
        print(f"   Three Months Ago: {self.three_months_ago_start.strftime('%B %Y')} (DELETE)")
        print()
        
        # 1. Current month records (5-7 records) - SHOULD BE KEPT
        num_current = random.randint(5, 7)
        print(f"Generating {num_current} current month records (KEEP)...")
        for i in range(num_current):
            days_offset = random.randint(0, (self.today - self.current_month_start).days)
            record_date = self.current_month_start + timedelta(days=days_offset)
            records.append(self._create_record(record_date, f"Current-{i+1}"))
        
        # 2. Previous month records (8-10 records) - SHOULD BE KEPT
        num_previous = random.randint(8, 10)
        print(f"Generating {num_previous} previous month records (KEEP)...")
        days_in_prev = (self.prev_month_end - self.prev_month_start).days + 1
        for i in range(num_previous):
            days_offset = random.randint(0, days_in_prev - 1)
            record_date = self.prev_month_start + timedelta(days=days_offset)
            records.append(self._create_record(record_date, f"Previous-{i+1}"))
        
        # 3. Two months ago records (10-12 records) - SHOULD BE DELETED
        num_two_months = random.randint(10, 12)
        print(f"Generating {num_two_months} two-months-ago records (DELETE)...")
        for i in range(num_two_months):
            days_offset = random.randint(0, 27)  # Safe range for any month
            record_date = self.two_months_ago_start + timedelta(days=days_offset)
            records.append(self._create_record(record_date, f"TwoMonths-{i+1}"))
        
        # 4. Three months ago records (8-10 records) - SHOULD BE DELETED
        num_three_months = random.randint(8, 10)
        print(f"Generating {num_three_months} three-months-ago records (DELETE)...")
        for i in range(num_three_months):
            days_offset = random.randint(0, 27)  # Safe range for any month
            record_date = self.three_months_ago_start + timedelta(days=days_offset)
            records.append(self._create_record(record_date, f"ThreeMonths-{i+1}"))
        
        # Sort by date for clarity
        records.sort(key=lambda x: x['date'])
        
        return records
    
    def _create_record(self, date: datetime, tag: str) -> Dict[str, Any]:
        """Create a single test record."""
        team = random.choice(list(TEAMS.keys()))
        sub_team = random.choice(TEAMS[team])
        platform = random.choice(PLATFORMS)
        project_name = random.choice(PROJECT_NAMES)
        transition = random.choice(STATUS_TRANSITIONS)
        release_type = random.choice(RELEASE_TYPES)
        whats_new = random.choice(WHATS_NEW_MESSAGES)
        
        # Generate version
        major = random.randint(1, 3)
        minor = random.randint(0, 9)
        patch = random.randint(0, 20)
        version = f"{major}.{minor}.{patch}"
        
        # Create log entry title
        log_entry = f"{date.strftime('%b %d')} - {tag} - Status changed from {transition[0]} to {transition[1]}"
        
        return {
            "log_entry": log_entry,
            "date": date.isoformat(),
            "project_name": project_name,
            "version": version,
            "platform": platform,
            "release_type": release_type,
            "previous_status": transition[0],
            "new_status": transition[1],
            "team": team,
            "sub_team": sub_team,
            "whats_new": f"[{tag}] {whats_new}",
            "automation_source": True,
            "tag": tag  # For tracking in tests
        }
    
    def upload_to_notion(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload test records to Notion database."""
        results = {
            "total": len(records),
            "successful": 0,
            "failed": 0,
            "by_tag": {},
            "errors": []
        }
        
        print(f"\n📤 Uploading {len(records)} test records to Notion...")
        print("-" * 50)
        
        for i, record in enumerate(records, 1):
            try:
                # Prepare Notion properties
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
                    "Release Type": {
                        "select": {
                            "name": record["release_type"]
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
                        "checkbox": record["automation_source"]
                    }
                }
                
                # Create page in Notion
                response = self.notion.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties
                )
                
                results["successful"] += 1
                
                # Track by tag
                tag = record["tag"]
                if tag not in results["by_tag"]:
                    results["by_tag"][tag] = {"uploaded": 0, "total": 0}
                results["by_tag"][tag]["uploaded"] += 1
                
                # Progress indicator
                if i % 5 == 0:
                    print(f"   Uploaded {i}/{len(records)} records...")
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "record": record["log_entry"],
                    "error": str(e)
                })
                print(f"   ❌ Failed to upload: {record['log_entry']}")
                print(f"      Error: {str(e)}")
        
        # Count totals by tag
        for record in records:
            tag = record["tag"]
            if tag not in results["by_tag"]:
                results["by_tag"][tag] = {"uploaded": 0, "total": 0}
            results["by_tag"][tag]["total"] += 1
        
        return results
    
    def generate_summary_report(self, records: List[Dict[str, Any]], upload_results: Dict[str, Any]):
        """Generate a summary report of the test data."""
        report = {
            "test_execution": datetime.now().isoformat(),
            "date_ranges": {
                "current_month": {
                    "start": self.current_month_start.isoformat(),
                    "end": self.today.isoformat(),
                    "should_keep": True
                },
                "previous_month": {
                    "start": self.prev_month_start.isoformat(),
                    "end": self.prev_month_end.isoformat(),
                    "should_keep": True
                },
                "two_months_ago": {
                    "start": self.two_months_ago_start.isoformat(),
                    "should_delete": True
                },
                "three_months_ago": {
                    "start": self.three_months_ago_start.isoformat(),
                    "should_delete": True
                }
            },
            "records_created": {
                "total": len(records),
                "by_month": {},
                "by_action": {
                    "should_keep": 0,
                    "should_delete": 0
                }
            },
            "upload_results": upload_results,
            "cleanup_expectations": {
                "cutoff_date": self.prev_month_start.isoformat(),
                "records_to_keep": [],
                "records_to_delete": []
            }
        }
        
        # Analyze records
        for record in records:
            record_date = datetime.fromisoformat(record["date"])
            month_key = record_date.strftime("%Y-%m")
            
            if month_key not in report["records_created"]["by_month"]:
                report["records_created"]["by_month"][month_key] = 0
            report["records_created"]["by_month"][month_key] += 1
            
            # Determine if should be kept or deleted
            if record_date >= self.prev_month_start:
                report["records_created"]["by_action"]["should_keep"] += 1
                report["cleanup_expectations"]["records_to_keep"].append({
                    "date": record["date"],
                    "tag": record["tag"],
                    "title": record["log_entry"]
                })
            else:
                report["records_created"]["by_action"]["should_delete"] += 1
                report["cleanup_expectations"]["records_to_delete"].append({
                    "date": record["date"],
                    "tag": record["tag"],
                    "title": record["log_entry"]
                })
        
        return report


def main():
    """Main execution function."""
    print("\n" + "=" * 60)
    print("🧪 N8N CLEANUP WORKFLOW TEST DATA GENERATOR")
    print("=" * 60)
    
    try:
        # Initialize generator
        generator = CleanupTestDataGenerator()
        
        # Generate test records
        print("\n1️⃣ Generating test records...")
        records = generator.generate_test_records()
        
        # Save test data locally
        print(f"\n2️⃣ Saving test data to file...")
        test_data_file = "cleanup_test_data.json"
        with open(test_data_file, "w") as f:
            json.dump(records, f, indent=2)
        print(f"   Saved {len(records)} records to {test_data_file}")
        
        # Upload to Notion
        print("\n3️⃣ Uploading to Notion database...")
        upload_results = generator.upload_to_notion(records)
        
        # Generate summary report
        print("\n4️⃣ Generating summary report...")
        report = generator.generate_summary_report(records, upload_results)
        
        # Save report
        report_file = "cleanup_test_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"   Saved report to {report_file}")
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 TEST DATA UPLOAD SUMMARY")
        print("=" * 60)
        print(f"✅ Successfully uploaded: {upload_results['successful']}/{upload_results['total']}")
        
        if upload_results['failed'] > 0:
            print(f"❌ Failed: {upload_results['failed']}")
        
        print("\n📈 Records by Category:")
        for tag, stats in upload_results['by_tag'].items():
            status = "KEEP" if "Current" in tag or "Previous" in tag else "DELETE"
            print(f"   {tag}: {stats['uploaded']}/{stats['total']} uploaded [{status}]")
        
        print("\n🎯 Cleanup Expectations:")
        print(f"   Records to KEEP: {report['records_created']['by_action']['should_keep']}")
        print(f"   Records to DELETE: {report['records_created']['by_action']['should_delete']}")
        print(f"   Cutoff Date: {generator.prev_month_start.strftime('%B %d, %Y')}")
        
        print("\n✨ Test data generation complete!")
        print("\n📝 Next Steps:")
        print("1. Run the n8n cleanup workflow")
        print("2. It should delete records older than", generator.prev_month_start.strftime('%B %d, %Y'))
        print("3. Verify that:")
        print(f"   - {report['records_created']['by_action']['should_keep']} records are kept")
        print(f"   - {report['records_created']['by_action']['should_delete']} records are deleted")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
