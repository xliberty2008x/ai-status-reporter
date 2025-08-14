"""
Query module for fetching and filtering data from Project Status Change Log database.
This module provides functions to retrieve status change logs with various filters.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables from src directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)


class StatusLogQuery:
    """Query handler for Project Status Change Log database."""
    
    def __init__(self):
        """Initialize Notion client and database configuration."""
        self.notion = Client(auth=os.getenv("NOTION_API_KEY"))
        self.database_id = os.getenv("STATUS_LOG_DB_ID")
        
        if not self.database_id:
            raise ValueError("STATUS_LOG_DB_ID not found in environment variables")
    
    def fetch_all_logs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch all records from the database.
        
        Args:
            limit: Maximum number of records to fetch
            
        Returns:
            List of log entries
        """
        try:
            results = []
            has_more = True
            start_cursor = None
            
            while has_more:
                response = self.notion.databases.query(
                    database_id=self.database_id,
                    start_cursor=start_cursor,
                    page_size=100,
                    sorts=[
                        {
                            "property": "Date",
                            "direction": "descending"
                        }
                    ]
                )
                
                results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
                
                if limit and len(results) >= limit:
                    return results[:limit]
            
            return results
            
        except Exception as e:
            print(f"Error fetching all logs: {e}")
            return []
    
    def fetch_logs_by_date_range(
        self, 
        start_date: datetime, 
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch logs within a specific date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range (defaults to now)
            
        Returns:
            List of log entries within date range
        """
        if not end_date:
            end_date = datetime.now()
        
        filter_conditions = {
            "and": [
                {
                    "property": "Date",
                    "date": {
                        "on_or_after": start_date.isoformat()
                    }
                },
                {
                    "property": "Date",
                    "date": {
                        "on_or_before": end_date.isoformat()
                    }
                }
            ]
        }
        
        try:
            results = []
            has_more = True
            start_cursor = None
            
            while has_more:
                response = self.notion.databases.query(
                    database_id=self.database_id,
                    filter=filter_conditions,
                    start_cursor=start_cursor,
                    sorts=[
                        {
                            "property": "Date",
                            "direction": "descending"
                        }
                    ]
                )
                
                results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
            
            return results
            
        except Exception as e:
            print(f"Error fetching logs by date range: {e}")
            return []
    
    def fetch_logs_by_team(self, team: str, sub_team: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch logs filtered by team and optionally sub-team.
        
        Args:
            team: Team name to filter by
            sub_team: Optional sub-team name to filter by
            
        Returns:
            List of log entries for the specified team
        """
        filter_conditions = {
            "property": "Team",
            "select": {
                "equals": team
            }
        }
        
        if sub_team:
            filter_conditions = {
                "and": [
                    filter_conditions,
                    {
                        "property": "Sub-team",
                        "select": {
                            "equals": sub_team
                        }
                    }
                ]
            }
        
        try:
            results = []
            has_more = True
            start_cursor = None
            
            while has_more:
                response = self.notion.databases.query(
                    database_id=self.database_id,
                    filter=filter_conditions,
                    start_cursor=start_cursor,
                    sorts=[
                        {
                            "property": "Date",
                            "direction": "descending"
                        }
                    ]
                )
                
                results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
            
            return results
            
        except Exception as e:
            print(f"Error fetching logs by team: {e}")
            return []
    
    def fetch_logs_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """
        Fetch logs filtered by platform.
        
        Args:
            platform: Platform name (GP, AMZ, iOS, Fire TV)
            
        Returns:
            List of log entries for the specified platform
        """
        filter_conditions = {
            "property": "Platform",
            "select": {
                "equals": platform
            }
        }
        
        try:
            results = []
            has_more = True
            start_cursor = None
            
            while has_more:
                response = self.notion.databases.query(
                    database_id=self.database_id,
                    filter=filter_conditions,
                    start_cursor=start_cursor,
                    sorts=[
                        {
                            "property": "Date",
                            "direction": "descending"
                        }
                    ]
                )
                
                results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
            
            return results
            
        except Exception as e:
            print(f"Error fetching logs by platform: {e}")
            return []
    
    def fetch_logs_by_project(self, project_name: str) -> List[Dict[str, Any]]:
        """
        Fetch logs filtered by project name.
        
        Args:
            project_name: Name of the project
            
        Returns:
            List of log entries for the specified project
        """
        filter_conditions = {
            "property": "Project Name",
            "rich_text": {
                "contains": project_name
            }
        }
        
        try:
            results = []
            has_more = True
            start_cursor = None
            
            while has_more:
                response = self.notion.databases.query(
                    database_id=self.database_id,
                    filter=filter_conditions,
                    start_cursor=start_cursor,
                    sorts=[
                        {
                            "property": "Date",
                            "direction": "descending"
                        }
                    ]
                )
                
                results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
            
            return results
            
        except Exception as e:
            print(f"Error fetching logs by project: {e}")
            return []
    
    def fetch_recent_changes(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch recent changes from the last N days.
        
        Args:
            days: Number of days to look back (default 30)
            
        Returns:
            List of recent log entries
        """
        start_date = datetime.now() - timedelta(days=days)
        return self.fetch_logs_by_date_range(start_date)
    
    def fetch_logs_for_cleanup(self) -> List[Dict[str, Any]]:
        """
        Fetch records older than the previous calendar month for cleanup.
        
        Returns:
            List of log entries that should be deleted
        """
        # Get first day of current month
        today = datetime.now()
        first_day_current_month = datetime(today.year, today.month, 1)
        
        # Get first day of previous month
        if today.month == 1:
            first_day_previous_month = datetime(today.year - 1, 12, 1)
        else:
            first_day_previous_month = datetime(today.year, today.month - 1, 1)
        
        # Fetch all records older than first day of previous month
        filter_conditions = {
            "property": "Date",
            "date": {
                "before": first_day_previous_month.isoformat()
            }
        }
        
        try:
            results = []
            has_more = True
            start_cursor = None
            
            while has_more:
                response = self.notion.databases.query(
                    database_id=self.database_id,
                    filter=filter_conditions,
                    start_cursor=start_cursor
                )
                
                results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
            
            return results
            
        except Exception as e:
            print(f"Error fetching logs for cleanup: {e}")
            return []
    
    def fetch_weekly_logs(self, weeks_back: int = 1) -> List[Dict[str, Any]]:
        """
        Fetch logs for the past week(s).
        
        Args:
            weeks_back: Number of weeks to look back
            
        Returns:
            List of log entries from the specified period
        """
        start_date = datetime.now() - timedelta(weeks=weeks_back)
        return self.fetch_logs_by_date_range(start_date)
    
    def fetch_monthly_logs(self, month: Optional[int] = None, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch logs for a specific month.
        
        Args:
            month: Month number (1-12), defaults to current month
            year: Year, defaults to current year
            
        Returns:
            List of log entries from the specified month
        """
        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year
        
        # First day of the month
        start_date = datetime(year, month, 1)
        
        # Last day of the month
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        return self.fetch_logs_by_date_range(start_date, end_date)
    
    @staticmethod
    def extract_field_value(page: Dict[str, Any], field_name: str) -> Any:
        """
        Extract field value from Notion page properties.
        
        Args:
            page: Notion page object
            field_name: Name of the field to extract
            
        Returns:
            Extracted value or None
        """
        properties = page.get("properties", {})
        
        if field_name not in properties:
            return None
        
        field = properties[field_name]
        field_type = field.get("type")
        
        if field_type == "title":
            title_array = field.get("title", [])
            return title_array[0].get("plain_text", "") if title_array else ""
        
        elif field_type == "rich_text":
            text_array = field.get("rich_text", [])
            return text_array[0].get("plain_text", "") if text_array else ""
        
        elif field_type == "select":
            select = field.get("select")
            return select.get("name", "") if select else ""
        
        elif field_type == "status":
            status = field.get("status")
            return status.get("name", "") if status else ""
        
        elif field_type == "date":
            date = field.get("date")
            return date.get("start", "") if date else ""
        
        elif field_type == "checkbox":
            return field.get("checkbox", False)
        
        elif field_type == "people":
            people = field.get("people", [])
            return [person.get("name", "") for person in people]
        
        elif field_type == "relation":
            relations = field.get("relation", [])
            return [rel.get("id", "") for rel in relations]
        
        else:
            return None
    
    def parse_log_entry(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a Notion page into a structured log entry.
        
        Args:
            page: Raw Notion page object
            
        Returns:
            Parsed log entry dictionary
        """
        return {
            "id": page.get("id"),
            "log_entry": self.extract_field_value(page, "Log Entry"),
            "date": self.extract_field_value(page, "Date"),
            "project_name": self.extract_field_value(page, "Project Name"),
            "version": self.extract_field_value(page, "Version"),
            "platform": self.extract_field_value(page, "Platform"),
            "release_type": self.extract_field_value(page, "Release Type"),
            "previous_status": self.extract_field_value(page, "Previous Status"),
            "new_status": self.extract_field_value(page, "New Status"),
            "team": self.extract_field_value(page, "Team"),
            "sub_team": self.extract_field_value(page, "Sub-team"),
            "changed_by": self.extract_field_value(page, "Changed By"),
            "whats_new": self.extract_field_value(page, "What's New"),
            "automation_source": self.extract_field_value(page, "Automation Source"),
            "project_link": self.extract_field_value(page, "Project Link"),
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time")
        }


# Test function for standalone execution
def test_query():
    """Test the query module with various filters."""
    query = StatusLogQuery()
    
    print("Testing StatusLogQuery module...")
    print("-" * 50)
    
    # Test fetching recent changes
    print("\n1. Fetching recent changes (last 7 days):")
    recent_logs = query.fetch_recent_changes(days=7)
    print(f"   Found {len(recent_logs)} recent entries")
    
    if recent_logs:
        first_entry = query.parse_log_entry(recent_logs[0])
        print(f"   Latest entry: {first_entry['project_name']} - {first_entry['previous_status']} → {first_entry['new_status']}")
    
    # Test fetching by team
    print("\n2. Fetching logs by team (AMZ Growth Team):")
    team_logs = query.fetch_logs_by_team("AMZ Growth Team")
    print(f"   Found {len(team_logs)} entries for AMZ Growth Team")
    
    # Test fetching by platform
    print("\n3. Fetching logs by platform (iOS):")
    platform_logs = query.fetch_logs_by_platform("iOS")
    print(f"   Found {len(platform_logs)} entries for iOS platform")
    
    # Test fetching weekly logs
    print("\n4. Fetching weekly logs:")
    weekly_logs = query.fetch_weekly_logs(weeks_back=1)
    print(f"   Found {len(weekly_logs)} entries in the past week")
    
    # Test fetching cleanup candidates
    print("\n5. Checking for cleanup candidates:")
    cleanup_logs = query.fetch_logs_for_cleanup()
    print(f"   Found {len(cleanup_logs)} entries eligible for cleanup")
    
    print("\n" + "-" * 50)
    print("Query module test completed!")


if __name__ == "__main__":
    test_query()

