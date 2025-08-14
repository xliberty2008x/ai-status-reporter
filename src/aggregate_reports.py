"""
Aggregation module for processing status change logs into report formats.
This module transforms raw data into structured reports for weekly/monthly digests.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from query_status_log import StatusLogQuery


class ReportAggregator:
    """Aggregate status change logs for reporting."""
    
    def __init__(self):
        """Initialize the aggregator with query handler."""
        self.query = StatusLogQuery()
    
    def aggregate_weekly_report(self, weeks_back: int = 1) -> Dict[str, Any]:
        """
        Aggregate changes for weekly report.
        
        Args:
            weeks_back: Number of weeks to look back
            
        Returns:
            Aggregated weekly report data
        """
        # Fetch logs for the specified period
        logs = self.query.fetch_weekly_logs(weeks_back)
        parsed_logs = [self.query.parse_log_entry(log) for log in logs]
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks_back)
        
        # Aggregate data
        report = {
            "period": {
                "type": "weekly",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "weeks": weeks_back
            },
            "summary": {
                "total_changes": len(parsed_logs),
                "unique_projects": len(set(log["project_name"] for log in parsed_logs if log["project_name"])),
                "active_teams": len(set(log["team"] for log in parsed_logs if log["team"]))
            },
            "by_team": self._group_by_team(parsed_logs),
            "by_platform": self._group_by_platform(parsed_logs),
            "by_status": self._group_by_status_transition(parsed_logs),
            "status_paths": self._build_project_status_paths(parsed_logs),
            "detailed_changes": parsed_logs
        }
        
        return report
    
    def aggregate_monthly_report(self, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Aggregate changes for monthly report.
        
        Args:
            month: Month number (1-12), defaults to current month
            year: Year, defaults to current year
            
        Returns:
            Aggregated monthly report data
        """
        # Default to current month/year if not specified
        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year
        
        # Fetch logs for the month
        logs = self.query.fetch_monthly_logs(month, year)
        parsed_logs = [self.query.parse_log_entry(log) for log in logs]
        
        # Calculate date range
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        # Aggregate data
        report = {
            "period": {
                "type": "monthly",
                "month": month,
                "year": year,
                "month_name": start_date.strftime("%B"),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_changes": len(parsed_logs),
                "unique_projects": len(set(log["project_name"] for log in parsed_logs if log["project_name"])),
                "active_teams": len(set(log["team"] for log in parsed_logs if log["team"]))
            },
            "by_team": self._group_by_team(parsed_logs),
            "by_platform": self._group_by_platform(parsed_logs),
            "by_status": self._group_by_status_transition(parsed_logs),
            "by_week": self._group_by_week(parsed_logs),
            "status_paths": self._build_project_status_paths(parsed_logs),
            "detailed_changes": parsed_logs
        }
        
        return report
    
    def build_status_path(self, project_name: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Build complete status transition path for a project.
        
        Args:
            project_name: Name of the project
            start_date: Start of period
            end_date: End of period
            
        Returns:
            List of status transitions in chronological order
        """
        # Fetch logs for the project within date range
        project_logs = self.query.fetch_logs_by_project(project_name)
        
        # Filter by date range and parse
        filtered_logs = []
        for log in project_logs:
            parsed = self.query.parse_log_entry(log)
            if parsed["date"]:
                log_date = datetime.fromisoformat(parsed["date"])
                # Remove timezone info for comparison
                if log_date.tzinfo:
                    log_date = log_date.replace(tzinfo=None)
                if start_date <= log_date <= end_date:
                    filtered_logs.append(parsed)
        
        # Sort by date (oldest first)
        filtered_logs.sort(key=lambda x: x["date"] if x["date"] else "")
        
        # Build status path
        status_path = []
        for log in filtered_logs:
            status_path.append({
                "date": log["date"],
                "from_status": log["previous_status"],
                "to_status": log["new_status"],
                "version": log["version"],
                "changed_by": log["changed_by"],
                "whats_new": log["whats_new"]
            })
        
        return status_path
    
    def group_by_team_and_project(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Group logs hierarchically by team and then by project.
        
        Args:
            logs: List of parsed log entries
            
        Returns:
            Hierarchically grouped data
        """
        grouped = defaultdict(lambda: defaultdict(list))
        
        for log in logs:
            team = log.get("team", "Unknown Team")
            project = log.get("project_name", "Unknown Project")
            grouped[team][project].append(log)
        
        # Convert to regular dict and add summaries
        result = {}
        for team, projects in grouped.items():
            result[team] = {
                "team_name": team,
                "total_changes": sum(len(changes) for changes in projects.values()),
                "projects": {}
            }
            
            for project, changes in projects.items():
                # Sort changes by date
                changes.sort(key=lambda x: x.get("date", ""), reverse=True)
                
                result[team]["projects"][project] = {
                    "project_name": project,
                    "changes_count": len(changes),
                    "latest_status": changes[0].get("new_status") if changes else None,
                    "changes": changes
                }
        
        return result
    
    def calculate_statistics(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate various statistics from logs.
        
        Args:
            logs: List of parsed log entries
            
        Returns:
            Statistical summary
        """
        stats = {
            "total_changes": len(logs),
            "by_status_transition": defaultdict(int),
            "by_team": defaultdict(int),
            "by_platform": defaultdict(int),
            "by_release_type": defaultdict(int),
            "most_active_projects": defaultdict(int),
            "most_active_users": defaultdict(int),
            "status_distribution": {
                "to_do": 0,
                "in_progress": 0,
                "complete": 0
            }
        }
        
        # Status groups for categorization
        TO_DO_STATUSES = ["BACKLOG"]
        IN_PROGRESS_STATUSES = [
            "GD CTR TEST", "CTR TEST", "CTR TEST DONE", "CTR ARCHIVE",
            "WAITING FOR DEV", "DEVELOPMENT", "QA", "WAITING RELEASE", "RELEASE POOL"
        ]
        COMPLETE_STATUSES = [
            "CREO PRODUCTION", "CREO DONE", "UA TOP SPENDERS", "LIVE",
            "UA TEST", "UA BOOST", "UA SETUP", "UA", "AUTO UA", "PAUSED",
            "UA PAUSED", "SHADOW BAN", "BLOCKED", "ARCHIVE", "SUSPENDED",
            "REJECTED", "Complete"
        ]
        
        for log in logs:
            # Status transitions
            transition = f"{log.get('previous_status', 'Unknown')} → {log.get('new_status', 'Unknown')}"
            stats["by_status_transition"][transition] += 1
            
            # Teams
            team = log.get("team", "Unknown")
            if team:
                stats["by_team"][team] += 1
            
            # Platforms
            platform = log.get("platform", "Unknown")
            if platform:
                stats["by_platform"][platform] += 1
            
            # Release types
            release_type = log.get("release_type", "Unknown")
            if release_type:
                stats["by_release_type"][release_type] += 1
            
            # Most active projects
            project = log.get("project_name", "Unknown")
            if project:
                stats["most_active_projects"][project] += 1
            
            # Most active users
            changed_by = log.get("changed_by", [])
            if changed_by and isinstance(changed_by, list):
                for user in changed_by:
                    stats["most_active_users"][user] += 1
            
            # Status distribution
            new_status = log.get("new_status", "")
            if new_status in TO_DO_STATUSES:
                stats["status_distribution"]["to_do"] += 1
            elif new_status in IN_PROGRESS_STATUSES:
                stats["status_distribution"]["in_progress"] += 1
            elif new_status in COMPLETE_STATUSES:
                stats["status_distribution"]["complete"] += 1
        
        # Convert defaultdicts to regular dicts and sort
        stats["by_status_transition"] = dict(sorted(
            stats["by_status_transition"].items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        stats["by_team"] = dict(sorted(
            stats["by_team"].items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        stats["by_platform"] = dict(sorted(
            stats["by_platform"].items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        stats["by_release_type"] = dict(sorted(
            stats["by_release_type"].items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        # Top 10 most active projects
        stats["most_active_projects"] = dict(sorted(
            stats["most_active_projects"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])
        
        # Top 10 most active users
        stats["most_active_users"] = dict(sorted(
            stats["most_active_users"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])
        
        return stats
    
    def _group_by_team(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Group logs by team."""
        grouped = defaultdict(list)
        for log in logs:
            team = log.get("team", "Unknown Team")
            grouped[team].append(log)
        
        result = {}
        for team, team_logs in grouped.items():
            result[team] = {
                "count": len(team_logs),
                "projects": list(set(log["project_name"] for log in team_logs if log.get("project_name")))
            }
        
        return dict(result)
    
    def _group_by_platform(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Group logs by platform."""
        grouped = defaultdict(list)
        for log in logs:
            platform = log.get("platform", "Unknown Platform")
            grouped[platform].append(log)
        
        result = {}
        for platform, platform_logs in grouped.items():
            result[platform] = {
                "count": len(platform_logs),
                "projects": list(set(log["project_name"] for log in platform_logs if log.get("project_name")))
            }
        
        return dict(result)
    
    def _group_by_status_transition(self, logs: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group logs by status transition."""
        transitions = defaultdict(int)
        for log in logs:
            transition = f"{log.get('previous_status', 'Unknown')} → {log.get('new_status', 'Unknown')}"
            transitions[transition] += 1
        
        return dict(sorted(transitions.items(), key=lambda x: x[1], reverse=True))
    
    def _group_by_week(self, logs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group monthly logs by week."""
        weekly_groups = defaultdict(list)
        
        for log in logs:
            if log.get("date"):
                log_date = datetime.fromisoformat(log["date"])
                # Remove timezone info if present
                if log_date.tzinfo:
                    log_date = log_date.replace(tzinfo=None)
                week_start = log_date - timedelta(days=log_date.weekday())
                week_key = week_start.strftime("%Y-%m-%d")
                weekly_groups[week_key].append(log)
        
        return dict(sorted(weekly_groups.items()))
    
    def _build_project_status_paths(self, logs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Build status paths for all projects in the logs."""
        project_paths = defaultdict(list)
        
        # Group by project
        for log in logs:
            project = log.get("project_name")
            if project:
                project_paths[project].append({
                    "date": log.get("date"),
                    "from": log.get("previous_status"),
                    "to": log.get("new_status"),
                    "version": log.get("version")
                })
        
        # Sort each project's changes by date
        for project in project_paths:
            project_paths[project].sort(key=lambda x: x.get("date", ""))
        
        return dict(project_paths)


# Test function
def test_aggregation():
    """Test the aggregation module."""
    aggregator = ReportAggregator()
    
    print("Testing ReportAggregator module...")
    print("-" * 50)
    
    # Test weekly aggregation
    print("\n1. Generating weekly report:")
    weekly_report = aggregator.aggregate_weekly_report(weeks_back=1)
    print(f"   Period: {weekly_report['period']['start_date'][:10]} to {weekly_report['period']['end_date'][:10]}")
    print(f"   Total changes: {weekly_report['summary']['total_changes']}")
    print(f"   Unique projects: {weekly_report['summary']['unique_projects']}")
    print(f"   Active teams: {weekly_report['summary']['active_teams']}")
    
    # Test monthly aggregation
    print("\n2. Generating monthly report:")
    monthly_report = aggregator.aggregate_monthly_report()
    print(f"   Month: {monthly_report['period']['month_name']} {monthly_report['period']['year']}")
    print(f"   Total changes: {monthly_report['summary']['total_changes']}")
    print(f"   Unique projects: {monthly_report['summary']['unique_projects']}")
    
    # Test statistics calculation
    if weekly_report['detailed_changes']:
        print("\n3. Calculating statistics:")
        stats = aggregator.calculate_statistics(weekly_report['detailed_changes'])
        print(f"   Status distribution:")
        print(f"     - To Do: {stats['status_distribution']['to_do']}")
        print(f"     - In Progress: {stats['status_distribution']['in_progress']}")
        print(f"     - Complete: {stats['status_distribution']['complete']}")
        
        if stats['by_platform']:
            print(f"   Changes by platform:")
            for platform, count in list(stats['by_platform'].items())[:3]:
                print(f"     - {platform}: {count}")
    
    print("\n" + "-" * 50)
    print("Aggregation module test completed!")


if __name__ == "__main__":
    test_aggregation()
