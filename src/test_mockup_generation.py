"""
Test script to verify mockup data generation without Notion API.
This script generates sample data and saves it to a JSON file for review.
"""

import json
from datetime import datetime
from generate_mockup_data import NotionMockupGenerator, PROJECT_NAMES, TEAMS, PLATFORMS
import random


def test_data_generation():
    """Test the mockup data generation without uploading to Notion."""
    
    print("="*60)
    print("MOCKUP DATA GENERATION TEST")
    print("="*60)
    
    # Create generator instance (without API key for testing)
    generator = NotionMockupGenerator(api_key="test_key", database_id="test_db")
    
    # Generate sample records
    num_records = 150
    print(f"\n1. Generating {num_records} mockup records...")
    records = generator.generate_mockup_records(num_records)
    
    print(f"   ✓ Generated {len(records)} records")
    
    # Analyze the generated data
    print("\n2. Data Analysis:")
    
    # Count by team
    team_counts = {}
    for record in records:
        team = record["team"]
        team_counts[team] = team_counts.get(team, 0) + 1
    
    print("\n   Teams distribution:")
    for team, count in team_counts.items():
        print(f"     - {team}: {count} records")
    
    # Count by platform
    platform_counts = {}
    for record in records:
        platform = record["platform"]
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    print("\n   Platform distribution:")
    for platform, count in platform_counts.items():
        print(f"     - {platform}: {count} records")
    
    # Status transitions analysis
    transitions = {}
    for record in records:
        transition = f"{record['previous_status']} → {record['new_status']}"
        transitions[transition] = transitions.get(transition, 0) + 1
    
    print("\n   Top 10 status transitions:")
    sorted_transitions = sorted(transitions.items(), key=lambda x: x[1], reverse=True)[:10]
    for transition, count in sorted_transitions:
        print(f"     - {transition}: {count} times")
    
    # Date range analysis
    dates = [datetime.fromisoformat(record["date"]) for record in records]
    min_date = min(dates)
    max_date = max(dates)
    
    print(f"\n   Date range: {min_date.date()} to {max_date.date()}")
    print(f"   Span: {(max_date - min_date).days} days")
    
    # Sample records display
    print("\n3. Sample Records (first 5):")
    print("-" * 60)
    
    for i, record in enumerate(records[:5], 1):
        print(f"\nRecord {i}:")
        print(f"  Log Entry: {record['log_entry']}")
        print(f"  Date: {record['date']}")
        print(f"  Project: {record['project_name']}")
        print(f"  Version: {record['version']}")
        print(f"  Platform: {record['platform']}")
        print(f"  Team: {record['team']} / {record['sub_team']}")
        print(f"  Status: {record['previous_status']} → {record['new_status']}")
        print(f"  Release Type: {record['release_type']}")
        print(f"  What's New: {record['whats_new']}")
        print(f"  Changed By: {record['changed_by']}")
    
    # Save to file
    output_file = "test_mockup_data.json"
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)
    
    print("\n" + "="*60)
    print(f"✓ Test complete! Data saved to {output_file}")
    print(f"  Total records: {len(records)}")
    print(f"  File size: {len(json.dumps(records))/1024:.1f} KB")
    print("="*60)
    
    return records


def validate_data_structure(records):
    """Validate that all records have required fields."""
    required_fields = [
        "log_entry", "date", "project_name", "version", "platform",
        "previous_status", "new_status", "team", "sub_team", 
        "release_type", "whats_new", "changed_by"
    ]
    
    print("\n4. Data Validation:")
    valid = True
    
    for i, record in enumerate(records):
        missing = [field for field in required_fields if field not in record]
        if missing:
            print(f"   ✗ Record {i} missing fields: {missing}")
            valid = False
    
    if valid:
        print("   ✓ All records have required fields")
    
    # Check for empty values
    empty_count = 0
    for record in records:
        for field, value in record.items():
            if not value:
                empty_count += 1
                
    if empty_count > 0:
        print(f"   ⚠ Found {empty_count} empty values across all records")
    else:
        print("   ✓ No empty values found")
    
    return valid


if __name__ == "__main__":
    # Run the test
    records = test_data_generation()
    
    # Validate structure
    validate_data_structure(records)
    
    print("\nNext steps:")
    print("1. Review the generated data in 'test_mockup_data.json'")
    print("2. Set your NOTION_API_KEY environment variable")
    print("3. Run 'python src/generate_mockup_data.py' to upload to Notion")

