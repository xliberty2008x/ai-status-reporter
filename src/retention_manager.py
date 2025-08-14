"""
Retention Manager module for handling 1-month data retention policy.
This module manages the cleanup of old records according to PRD requirements.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from notion_client import Client
from dotenv import load_dotenv
from query_status_log import StatusLogQuery

# Load environment variables from src directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)


class RetentionManager:
    """Manage data retention and cleanup for status logs."""
    
    def __init__(self, dry_run: bool = True):
        """
        Initialize the retention manager.
        
        Args:
            dry_run: If True, only simulate deletion without actually deleting
        """
        self.notion = Client(auth=os.getenv("NOTION_API_KEY"))
        self.database_id = os.getenv("STATUS_LOG_DB_ID")
        self.query = StatusLogQuery()
        self.dry_run = dry_run
        
        if not self.database_id:
            raise ValueError("STATUS_LOG_DB_ID not found in environment variables")
    
    def identify_expired_records(self) -> List[Dict[str, Any]]:
        """
        Identify records older than the previous calendar month.
        
        According to PRD: "Delete records older than the previous calendar month"
        
        Returns:
            List of records eligible for deletion
        """
        # Get records for cleanup
        expired_logs = self.query.fetch_logs_for_cleanup()
        
        # Parse and enrich with details
        parsed_logs = []
        for log in expired_logs:
            parsed = self.query.parse_log_entry(log)
            parsed_logs.append(parsed)
        
        return parsed_logs
    
    def delete_expired_records(self, confirm: bool = False) -> Dict[str, Any]:
        """
        Delete records older than the previous calendar month.
        
        Args:
            confirm: Must be True to actually delete (safety mechanism)
            
        Returns:
            Report of deletion operation
        """
        # Get expired records
        expired_records = self.identify_expired_records()
        
        if not expired_records:
            return {
                "status": "success",
                "message": "No expired records found",
                "deleted_count": 0,
                "dry_run": self.dry_run
            }
        
        # Prepare deletion report
        deletion_report = {
            "status": "pending",
            "dry_run": self.dry_run,
            "deletion_date": datetime.now().isoformat(),
            "criteria": {
                "description": "Records older than previous calendar month",
                "cutoff_date": self._get_cutoff_date().isoformat()
            },
            "records_to_delete": len(expired_records),
            "deleted_records": [],
            "failed_deletions": [],
            "summary_by_team": {},
            "summary_by_platform": {},
            "oldest_record": None,
            "newest_record": None
        }
        
        # Analyze records to be deleted
        for record in expired_records:
            # Track by team
            team = record.get("team", "Unknown")
            if team not in deletion_report["summary_by_team"]:
                deletion_report["summary_by_team"][team] = 0
            deletion_report["summary_by_team"][team] += 1
            
            # Track by platform
            platform = record.get("platform", "Unknown")
            if platform not in deletion_report["summary_by_platform"]:
                deletion_report["summary_by_platform"][platform] = 0
            deletion_report["summary_by_platform"][platform] += 1
            
            # Track date range
            if record.get("date"):
                if not deletion_report["oldest_record"] or record["date"] < deletion_report["oldest_record"]:
                    deletion_report["oldest_record"] = record["date"]
                if not deletion_report["newest_record"] or record["date"] > deletion_report["newest_record"]:
                    deletion_report["newest_record"] = record["date"]
        
        # Perform deletion if confirmed and not dry run
        if confirm and not self.dry_run:
            for record in expired_records:
                try:
                    # Delete from Notion
                    self._delete_notion_page(record["id"])
                    
                    # Add to deleted records
                    deletion_report["deleted_records"].append({
                        "id": record["id"],
                        "project_name": record.get("project_name"),
                        "date": record.get("date"),
                        "status_change": f"{record.get('previous_status')} → {record.get('new_status')}"
                    })
                    
                except Exception as e:
                    # Track failed deletions
                    deletion_report["failed_deletions"].append({
                        "id": record["id"],
                        "error": str(e),
                        "project_name": record.get("project_name")
                    })
            
            deletion_report["status"] = "completed"
            deletion_report["deleted_count"] = len(deletion_report["deleted_records"])
            deletion_report["failed_count"] = len(deletion_report["failed_deletions"])
        
        elif not confirm:
            deletion_report["status"] = "not_confirmed"
            deletion_report["message"] = "Deletion not confirmed. Set confirm=True to proceed."
        
        else:  # dry_run = True
            deletion_report["status"] = "dry_run"
            deletion_report["message"] = f"DRY RUN: Would delete {len(expired_records)} records"
            deletion_report["deleted_count"] = 0
        
        return deletion_report
    
    def generate_deletion_report(self, include_details: bool = False) -> Dict[str, Any]:
        """
        Generate a detailed report about what would be deleted.
        
        Args:
            include_details: If True, include full record details
            
        Returns:
            Detailed deletion report
        """
        expired_records = self.identify_expired_records()
        
        report = {
            "report_date": datetime.now().isoformat(),
            "retention_policy": {
                "description": "Delete records older than previous calendar month",
                "cutoff_date": self._get_cutoff_date().isoformat()
            },
            "statistics": {
                "total_records_to_delete": len(expired_records),
                "by_month": {},
                "by_team": {},
                "by_platform": {},
                "by_status_transition": {}
            },
            "date_range": {
                "oldest": None,
                "newest": None
            }
        }
        
        # Analyze records
        for record in expired_records:
            # Group by month
            if record.get("date"):
                month_key = record["date"][:7]  # YYYY-MM
                if month_key not in report["statistics"]["by_month"]:
                    report["statistics"]["by_month"][month_key] = 0
                report["statistics"]["by_month"][month_key] += 1
                
                # Update date range
                if not report["date_range"]["oldest"] or record["date"] < report["date_range"]["oldest"]:
                    report["date_range"]["oldest"] = record["date"]
                if not report["date_range"]["newest"] or record["date"] > report["date_range"]["newest"]:
                    report["date_range"]["newest"] = record["date"]
            
            # Group by team
            team = record.get("team", "Unknown")
            if team not in report["statistics"]["by_team"]:
                report["statistics"]["by_team"][team] = 0
            report["statistics"]["by_team"][team] += 1
            
            # Group by platform
            platform = record.get("platform", "Unknown")
            if platform not in report["statistics"]["by_platform"]:
                report["statistics"]["by_platform"][platform] = 0
            report["statistics"]["by_platform"][platform] += 1
            
            # Group by status transition
            transition = f"{record.get('previous_status', 'Unknown')} → {record.get('new_status', 'Unknown')}"
            if transition not in report["statistics"]["by_status_transition"]:
                report["statistics"]["by_status_transition"][transition] = 0
            report["statistics"]["by_status_transition"][transition] += 1
        
        # Add record details if requested
        if include_details:
            report["records"] = []
            for record in expired_records:
                report["records"].append({
                    "id": record["id"],
                    "project_name": record.get("project_name"),
                    "date": record.get("date"),
                    "team": record.get("team"),
                    "platform": record.get("platform"),
                    "status_change": f"{record.get('previous_status')} → {record.get('new_status')}",
                    "version": record.get("version"),
                    "changed_by": record.get("changed_by")
                })
        
        return report
    
    def schedule_cleanup(self) -> Dict[str, Any]:
        """
        Information about when cleanup should be scheduled.
        
        Returns:
            Scheduling recommendations
        """
        now = datetime.now()
        
        # Calculate next cleanup date (first day of next month)
        if now.month == 12:
            next_cleanup = datetime(now.year + 1, 1, 1)
        else:
            next_cleanup = datetime(now.year, now.month + 1, 1)
        
        # Calculate what would be deleted in next cleanup
        cutoff_date = self._get_cutoff_date()
        
        return {
            "current_date": now.isoformat(),
            "next_cleanup_date": next_cleanup.isoformat(),
            "days_until_cleanup": (next_cleanup - now).days,
            "cleanup_schedule": {
                "frequency": "monthly",
                "day_of_month": 1,
                "recommended_time": "02:00 UTC",
                "description": "Run on the first day of each month"
            },
            "current_cutoff_date": cutoff_date.isoformat(),
            "retention_window": {
                "description": "Keep current month + previous month",
                "minimum_days": 30,
                "maximum_days": 62  # Max days in 2 months
            },
            "cron_expression": "0 2 1 * *",  # 2 AM on the 1st of every month
            "n8n_schedule": {
                "trigger": "Schedule",
                "cron": "0 2 1 * *",
                "timezone": "UTC"
            }
        }
    
    def validate_retention_policy(self) -> Dict[str, Any]:
        """
        Validate that retention policy is working correctly.
        
        Returns:
            Validation report
        """
        # Fetch all logs
        all_logs = self.query.fetch_all_logs()
        parsed_logs = [self.query.parse_log_entry(log) for log in all_logs]
        
        # Get cutoff date
        cutoff_date = self._get_cutoff_date()
        
        # Check for violations
        violations = []
        compliant_count = 0
        
        for log in parsed_logs:
            if log.get("date"):
                log_date = datetime.fromisoformat(log["date"])
                # Remove timezone info for comparison (make both naive)
                if log_date.tzinfo:
                    log_date = log_date.replace(tzinfo=None)
                if log_date < cutoff_date:
                    violations.append({
                        "id": log["id"],
                        "project_name": log.get("project_name"),
                        "date": log["date"],
                        "days_over_retention": (cutoff_date - log_date).days
                    })
                else:
                    compliant_count += 1
        
        return {
            "validation_date": datetime.now().isoformat(),
            "policy": {
                "description": "Records should not be older than previous calendar month",
                "cutoff_date": cutoff_date.isoformat()
            },
            "results": {
                "total_records": len(parsed_logs),
                "compliant_records": compliant_count,
                "violation_count": len(violations),
                "compliance_rate": (compliant_count / len(parsed_logs) * 100) if parsed_logs else 100
            },
            "violations": violations[:10],  # Show first 10 violations
            "recommendation": "Run cleanup immediately" if violations else "System is compliant"
        }
    
    def _get_cutoff_date(self) -> datetime:
        """
        Calculate the cutoff date for retention.
        Records older than this date should be deleted.
        
        Returns:
            Cutoff date (first day of previous month)
        """
        today = datetime.now()
        
        # Get first day of previous month
        if today.month == 1:
            cutoff = datetime(today.year - 1, 12, 1)
        else:
            cutoff = datetime(today.year, today.month - 1, 1)
        
        return cutoff
    
    def _delete_notion_page(self, page_id: str):
        """
        Delete a page from Notion (archive it).
        
        Args:
            page_id: ID of the page to delete
        """
        # In Notion API, we archive pages instead of deleting
        self.notion.pages.update(
            page_id=page_id,
            archived=True
        )
    
    def restore_archived_page(self, page_id: str):
        """
        Restore an archived page (undo deletion).
        
        Args:
            page_id: ID of the page to restore
        """
        self.notion.pages.update(
            page_id=page_id,
            archived=False
        )


# Test function
def test_retention_manager():
    """Test the retention manager module."""
    # Initialize in dry-run mode for safety
    manager = RetentionManager(dry_run=True)
    
    print("Testing RetentionManager module...")
    print("-" * 50)
    
    # Test identifying expired records
    print("\n1. Identifying expired records:")
    expired = manager.identify_expired_records()
    print(f"   Found {len(expired)} records eligible for deletion")
    
    if expired:
        print(f"   Date range: {expired[0].get('date', 'N/A')} to {expired[-1].get('date', 'N/A')}")
    
    # Test deletion report generation
    print("\n2. Generating deletion report:")
    report = manager.generate_deletion_report(include_details=False)
    print(f"   Cutoff date: {report['retention_policy']['cutoff_date'][:10]}")
    print(f"   Records to delete: {report['statistics']['total_records_to_delete']}")
    
    if report['statistics']['by_team']:
        print("   By team:")
        for team, count in report['statistics']['by_team'].items():
            print(f"     - {team}: {count}")
    
    # Test scheduling information
    print("\n3. Cleanup scheduling information:")
    schedule = manager.schedule_cleanup()
    print(f"   Next cleanup: {schedule['next_cleanup_date'][:10]}")
    print(f"   Days until cleanup: {schedule['days_until_cleanup']}")
    print(f"   Cron expression: {schedule['cron_expression']}")
    
    # Test validation
    print("\n4. Validating retention policy:")
    validation = manager.validate_retention_policy()
    print(f"   Total records: {validation['results']['total_records']}")
    print(f"   Compliant: {validation['results']['compliant_records']}")
    print(f"   Violations: {validation['results']['violation_count']}")
    print(f"   Compliance rate: {validation['results']['compliance_rate']:.1f}%")
    print(f"   Recommendation: {validation['recommendation']}")
    
    # Test dry-run deletion
    print("\n5. Testing dry-run deletion:")
    deletion_result = manager.delete_expired_records(confirm=True)  # Still dry-run
    print(f"   Status: {deletion_result['status']}")
    print(f"   Message: {deletion_result.get('message', 'N/A')}")
    
    # Save reports
    print("\n6. Saving sample reports:")
    
    with open("retention_report.json", "w") as f:
        json.dump(report, f, indent=2)
        print("   Saved deletion report to retention_report.json")
    
    with open("retention_schedule.json", "w") as f:
        json.dump(schedule, f, indent=2)
        print("   Saved schedule info to retention_schedule.json")
    
    print("\n" + "-" * 50)
    print("Retention manager module test completed!")
    print("\nNOTE: Manager is in DRY-RUN mode. No records were actually deleted.")
    print("To perform actual deletion, initialize with dry_run=False and confirm=True")


if __name__ == "__main__":
    test_retention_manager()
