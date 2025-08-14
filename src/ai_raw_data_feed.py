"""
AI Raw Data Feed module - Provides raw filtered database records for AI analysis.
This module prepares unprocessed data feeds for AI agents to generate their own insights.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from query_status_log import StatusLogQuery


class AIRawDataFeed:
    """Prepare raw data feeds for AI agent analysis."""
    
    def __init__(self):
        """Initialize the feed generator."""
        self.query = StatusLogQuery()
    
    def create_raw_feed(self,
                       filters: Optional[Dict[str, Any]] = None,
                       max_records: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a raw data feed for AI consumption based on filters.
        
        Args:
            filters: Dictionary of filters to apply
            max_records: Maximum number of records to include
            
        Returns:
            Raw data feed structure for AI
        """
        # Parse filters
        filter_config = self._parse_filters(filters or {})
        
        # Fetch data based on filters
        raw_logs = self._fetch_filtered_data(filter_config, max_records)
        
        # Parse logs to clean structure
        parsed_records = [self.query.parse_log_entry(log) for log in raw_logs]
        
        # Create feed structure
        feed = {
            "feed_metadata": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "source": "Project Status Change Log",
                "database_id": "d94056721a9b4a4fa836743010fafec7",
                "record_count": len(parsed_records),
                "filters_applied": filter_config,
                "data_schema": self._get_data_schema()
            },
            "query_context": {
                "purpose": "Provide raw status change data for AI analysis",
                "expected_analysis": [
                    "Identify patterns in status transitions",
                    "Detect bottlenecks in project flow",
                    "Analyze team productivity",
                    "Find anomalies or issues",
                    "Generate insights about project lifecycle"
                ],
                "available_fields": list(self._get_data_schema().keys())
            },
            "data": parsed_records
        }
        
        return feed
    
    def create_filtered_feed(self,
                            date_range: Optional[Dict[str, Any]] = None,
                            teams: Optional[List[str]] = None,
                            platforms: Optional[List[str]] = None,
                            projects: Optional[List[str]] = None,
                            statuses: Optional[List[str]] = None,
                            max_records: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a filtered raw data feed with specific criteria.
        
        Args:
            date_range: Dict with 'start' and 'end' dates
            teams: List of team names to filter
            platforms: List of platforms to filter
            projects: List of project names to filter
            statuses: List of statuses to filter
            max_records: Maximum number of records
            
        Returns:
            Filtered raw data feed
        """
        # Build filters
        filters = {}
        
        if date_range:
            filters['date_range'] = date_range
        if teams:
            filters['teams'] = teams
        if platforms:
            filters['platforms'] = platforms
        if projects:
            filters['projects'] = projects
        if statuses:
            filters['statuses'] = statuses
        
        return self.create_raw_feed(filters, max_records)
    
    def create_question_context_feed(self, question: str, max_records: int = 50) -> Dict[str, Any]:
        """
        Create a raw feed optimized for answering a specific question.
        
        Args:
            question: Natural language question
            max_records: Maximum number of records
            
        Returns:
            Raw feed with question context
        """
        # Extract potential filters from question
        filters = self._extract_filters_from_question(question.lower())
        
        # Fetch relevant data
        feed = self.create_raw_feed(filters, max_records)
        
        # Add question context
        feed["question_context"] = {
            "original_question": question,
            "detected_intent": self._detect_question_intent(question),
            "suggested_analysis_approach": self._suggest_analysis_approach(question),
            "relevant_fields": self._identify_relevant_fields(question)
        }
        
        return feed
    
    def create_time_series_feed(self, 
                               days: int = 30,
                               group_by: str = "day") -> Dict[str, Any]:
        """
        Create a time-series oriented raw feed for trend analysis.
        
        Args:
            days: Number of days to include
            group_by: Grouping period ('day', 'week', 'month')
            
        Returns:
            Time-series oriented raw feed
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # Fetch data
        logs = self.query.fetch_logs_by_date_range(start_date)
        parsed_records = [self.query.parse_log_entry(log) for log in logs]
        
        # Sort by date for time series analysis
        parsed_records.sort(key=lambda x: x.get("date", ""))
        
        feed = {
            "feed_metadata": {
                "version": "1.0",
                "type": "time_series",
                "generated_at": datetime.now().isoformat(),
                "period": {
                    "start": start_date.isoformat(),
                    "end": datetime.now().isoformat(),
                    "days": days,
                    "grouping": group_by
                },
                "record_count": len(parsed_records)
            },
            "time_series_context": {
                "purpose": "Analyze trends and patterns over time",
                "suggested_metrics": [
                    "Daily/weekly status change velocity",
                    "Status transition patterns",
                    "Team activity trends",
                    "Platform distribution over time",
                    "Project lifecycle duration"
                ],
                "chronological_order": True
            },
            "data": parsed_records
        }
        
        return feed
    
    def create_team_analysis_feed(self, team_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a raw feed optimized for team performance analysis.
        
        Args:
            team_name: Specific team to analyze (None for all teams)
            
        Returns:
            Team-focused raw feed
        """
        if team_name:
            logs = self.query.fetch_logs_by_team(team_name)
            analysis_scope = f"Team: {team_name}"
        else:
            logs = self.query.fetch_recent_changes(30)
            analysis_scope = "All Teams"
        
        parsed_records = [self.query.parse_log_entry(log) for log in logs]
        
        # Group by teams for easier analysis
        teams_data = {}
        for record in parsed_records:
            team = record.get("team", "Unknown")
            if team not in teams_data:
                teams_data[team] = []
            teams_data[team].append(record)
        
        feed = {
            "feed_metadata": {
                "version": "1.0",
                "type": "team_analysis",
                "generated_at": datetime.now().isoformat(),
                "analysis_scope": analysis_scope,
                "record_count": len(parsed_records),
                "team_count": len(teams_data)
            },
            "analysis_context": {
                "purpose": "Analyze team performance and productivity",
                "suggested_metrics": [
                    "Status changes per team",
                    "Average time in each status",
                    "Project completion rates",
                    "Cross-team collaboration patterns",
                    "Bottleneck identification"
                ]
            },
            "data_by_team": teams_data,
            "flat_data": parsed_records
        }
        
        return feed
    
    def create_project_lifecycle_feed(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a feed for analyzing project lifecycles.
        
        Args:
            project_name: Specific project to analyze (None for all)
            
        Returns:
            Project lifecycle focused feed
        """
        if project_name:
            logs = self.query.fetch_logs_by_project(project_name)
        else:
            logs = self.query.fetch_recent_changes(60)  # 60 days for lifecycle analysis
        
        parsed_records = [self.query.parse_log_entry(log) for log in logs]
        
        # Group by project for lifecycle analysis
        projects_data = {}
        for record in parsed_records:
            project = record.get("project_name", "Unknown")
            if project not in projects_data:
                projects_data[project] = []
            projects_data[project].append(record)
        
        # Sort each project's records by date
        for project in projects_data:
            projects_data[project].sort(key=lambda x: x.get("date", ""))
        
        feed = {
            "feed_metadata": {
                "version": "1.0",
                "type": "project_lifecycle",
                "generated_at": datetime.now().isoformat(),
                "record_count": len(parsed_records),
                "project_count": len(projects_data)
            },
            "lifecycle_context": {
                "purpose": "Analyze project progression and lifecycle patterns",
                "suggested_analysis": [
                    "Status transition sequences",
                    "Time spent in each phase",
                    "Identify stuck or blocked projects",
                    "Success vs failure patterns",
                    "Version progression analysis"
                ],
                "data_structure": "Chronologically sorted by project"
            },
            "data_by_project": projects_data,
            "all_records": parsed_records
        }
        
        return feed
    
    def _parse_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize filter configuration."""
        parsed = {
            "date_range": None,
            "teams": [],
            "platforms": [],
            "projects": [],
            "statuses": [],
            "sub_teams": []
        }
        
        # Parse date range
        if "date_range" in filters:
            dr = filters["date_range"]
            if isinstance(dr, dict):
                parsed["date_range"] = {
                    "start": dr.get("start"),
                    "end": dr.get("end")
                }
            elif isinstance(dr, str):
                # Handle string date ranges like "last_week", "last_month"
                parsed["date_range"] = self._parse_string_date_range(dr)
        
        # Parse list filters
        for key in ["teams", "platforms", "projects", "statuses", "sub_teams"]:
            if key in filters:
                value = filters[key]
                if isinstance(value, list):
                    parsed[key] = value
                elif isinstance(value, str):
                    parsed[key] = [value]
        
        return parsed
    
    def _fetch_filtered_data(self, 
                            filter_config: Dict[str, Any],
                            max_records: Optional[int]) -> List[Dict[str, Any]]:
        """Fetch data based on filter configuration."""
        logs = []
        
        # Apply date range filter
        if filter_config.get("date_range"):
            dr = filter_config["date_range"]
            start = datetime.fromisoformat(dr["start"]) if dr.get("start") else datetime.now() - timedelta(days=30)
            end = datetime.fromisoformat(dr["end"]) if dr.get("end") else datetime.now()
            logs = self.query.fetch_logs_by_date_range(start, end)
        else:
            # Default to last 30 days
            logs = self.query.fetch_recent_changes(30)
        
        # Parse all logs first
        parsed_logs = [self.query.parse_log_entry(log) for log in logs]
        
        # Apply additional filters
        filtered = parsed_logs
        
        if filter_config.get("teams"):
            filtered = [log for log in filtered if log.get("team") in filter_config["teams"]]
        
        if filter_config.get("platforms"):
            filtered = [log for log in filtered if log.get("platform") in filter_config["platforms"]]
        
        if filter_config.get("projects"):
            filtered = [log for log in filtered if any(
                proj in log.get("project_name", "") for proj in filter_config["projects"]
            )]
        
        if filter_config.get("statuses"):
            filtered = [log for log in filtered if 
                       log.get("new_status") in filter_config["statuses"] or
                       log.get("previous_status") in filter_config["statuses"]]
        
        if filter_config.get("sub_teams"):
            filtered = [log for log in filtered if log.get("sub_team") in filter_config["sub_teams"]]
        
        # Apply max_records limit
        if max_records:
            filtered = filtered[:max_records]
        
        # Return unparsed logs for fresh parsing
        return logs[:len(filtered)]
    
    def _get_data_schema(self) -> Dict[str, str]:
        """Return the schema of data fields."""
        return {
            "id": "Unique record identifier",
            "log_entry": "Description of the change",
            "date": "ISO format datetime of the change",
            "project_name": "Name of the project",
            "version": "Version number",
            "platform": "Target platform (iOS, AMZ, GP, Fire TV)",
            "release_type": "Type of release",
            "previous_status": "Status before the change",
            "new_status": "Status after the change",
            "team": "Team responsible",
            "sub_team": "Sub-team within the organization",
            "changed_by": "Person who made the change",
            "whats_new": "Description of what changed",
            "automation_source": "Whether created by automation",
            "project_link": "Link to project in Notion",
            "created_time": "Record creation time",
            "last_edited_time": "Last modification time"
        }
    
    def _parse_string_date_range(self, date_string: str) -> Dict[str, str]:
        """Parse string date ranges like 'last_week', 'last_month'."""
        now = datetime.now()
        
        if date_string == "today":
            start = now.replace(hour=0, minute=0, second=0)
            end = now
        elif date_string == "yesterday":
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
            end = now.replace(hour=0, minute=0, second=0)
        elif date_string == "last_week" or date_string == "week":
            start = now - timedelta(weeks=1)
            end = now
        elif date_string == "last_month" or date_string == "month":
            start = now - timedelta(days=30)
            end = now
        else:
            # Default to last 30 days
            start = now - timedelta(days=30)
            end = now
        
        return {
            "start": start.isoformat(),
            "end": end.isoformat()
        }
    
    def _extract_filters_from_question(self, question: str) -> Dict[str, Any]:
        """Extract potential filters from a natural language question."""
        filters = {}
        
        # Time-based keywords
        if "today" in question:
            filters["date_range"] = "today"
        elif "yesterday" in question:
            filters["date_range"] = "yesterday"
        elif "this week" in question or "week" in question:
            filters["date_range"] = "week"
        elif "this month" in question or "month" in question:
            filters["date_range"] = "month"
        
        # Platform keywords
        platforms_map = {
            "ios": "iOS",
            "amazon": "AMZ",
            "amz": "AMZ",
            "google play": "GP",
            "gp": "GP",
            "fire tv": "Fire TV"
        }
        for keyword, platform in platforms_map.items():
            if keyword in question:
                filters["platforms"] = [platform]
                break
        
        # Team keywords
        if "growth" in question:
            filters["teams"] = ["AMZ Growth Team"]
        elif "production" in question:
            filters["teams"] = ["AMZ Production Team"]
        elif "tools" in question:
            filters["teams"] = ["Tools Team"]
        
        # Status keywords
        status_keywords = {
            "backlog": ["BACKLOG"],
            "development": ["DEVELOPMENT"],
            "qa": ["QA"],
            "testing": ["QA", "CTR TEST", "GD CTR TEST"],
            "live": ["LIVE"],
            "blocked": ["BLOCKED"],
            "complete": ["Complete", "CREO DONE"]
        }
        for keyword, statuses in status_keywords.items():
            if keyword in question:
                filters["statuses"] = statuses
                break
        
        return filters
    
    def _detect_question_intent(self, question: str) -> str:
        """Detect the intent behind a question."""
        question_lower = question.lower()
        
        if "how many" in question_lower or "count" in question_lower:
            return "counting"
        elif "trend" in question_lower or "over time" in question_lower:
            return "trend_analysis"
        elif "compare" in question_lower:
            return "comparison"
        elif "why" in question_lower:
            return "root_cause_analysis"
        elif "which" in question_lower or "what" in question_lower:
            return "identification"
        elif "when" in question_lower:
            return "temporal_query"
        elif "who" in question_lower:
            return "attribution"
        elif "bottleneck" in question_lower or "slow" in question_lower:
            return "bottleneck_detection"
        elif "pattern" in question_lower:
            return "pattern_recognition"
        else:
            return "general_inquiry"
    
    def _suggest_analysis_approach(self, question: str) -> List[str]:
        """Suggest analysis approaches based on the question."""
        intent = self._detect_question_intent(question)
        
        approaches = {
            "counting": [
                "Count total records matching criteria",
                "Group by relevant dimensions",
                "Calculate percentages and distributions"
            ],
            "trend_analysis": [
                "Sort data chronologically",
                "Calculate moving averages",
                "Identify peaks and valleys",
                "Look for cyclical patterns"
            ],
            "comparison": [
                "Segment data by comparison groups",
                "Calculate metrics for each group",
                "Identify significant differences"
            ],
            "root_cause_analysis": [
                "Trace status transition paths",
                "Identify common patterns before issues",
                "Look for correlations with team/platform/time"
            ],
            "identification": [
                "Filter data by relevant criteria",
                "Sort by relevant metrics",
                "Return top results"
            ],
            "bottleneck_detection": [
                "Calculate time spent in each status",
                "Identify statuses with longest duration",
                "Find projects stuck in specific states"
            ],
            "pattern_recognition": [
                "Group similar transitions",
                "Identify recurring sequences",
                "Find anomalies or outliers"
            ]
        }
        
        return approaches.get(intent, ["Analyze the provided data comprehensively"])
    
    def _identify_relevant_fields(self, question: str) -> List[str]:
        """Identify which fields are most relevant for answering the question."""
        question_lower = question.lower()
        relevant = ["date", "project_name"]  # Always relevant
        
        if "team" in question_lower:
            relevant.extend(["team", "sub_team"])
        
        if "status" in question_lower or "transition" in question_lower:
            relevant.extend(["previous_status", "new_status"])
        
        if "platform" in question_lower:
            relevant.append("platform")
        
        if "version" in question_lower:
            relevant.append("version")
        
        if "who" in question_lower or "person" in question_lower:
            relevant.append("changed_by")
        
        if "what" in question_lower and "new" in question_lower:
            relevant.append("whats_new")
        
        if "release" in question_lower:
            relevant.append("release_type")
        
        return list(set(relevant))  # Remove duplicates


# Test function to demonstrate different feed types
def demonstrate_feeds():
    """Demonstrate various AI feed formats."""
    feed_generator = AIRawDataFeed()
    
    print("=" * 60)
    print("AI RAW DATA FEED DEMONSTRATIONS")
    print("=" * 60)
    
    # 1. Basic raw feed
    print("\n1. BASIC RAW FEED (Last 7 days, max 10 records):")
    print("-" * 40)
    basic_feed = feed_generator.create_raw_feed(
        filters={"date_range": "week"},
        max_records=10
    )
    print(f"Feed Version: {basic_feed['feed_metadata']['version']}")
    print(f"Record Count: {basic_feed['feed_metadata']['record_count']}")
    print(f"Filters Applied: {basic_feed['feed_metadata']['filters_applied']}")
    print(f"First Record Sample: {basic_feed['data'][0] if basic_feed['data'] else 'No data'}")
    
    # 2. Question-based feed
    print("\n2. QUESTION-BASED FEED:")
    print("-" * 40)
    question = "What projects changed status to LIVE this week?"
    question_feed = feed_generator.create_question_context_feed(question, max_records=10)
    print(f"Question: {question}")
    print(f"Detected Intent: {question_feed['question_context']['detected_intent']}")
    print(f"Relevant Fields: {question_feed['question_context']['relevant_fields']}")
    print(f"Analysis Approach: {question_feed['question_context']['suggested_analysis_approach']}")
    print(f"Records Found: {question_feed['feed_metadata']['record_count']}")
    
    # 3. Team analysis feed
    print("\n3. TEAM ANALYSIS FEED:")
    print("-" * 40)
    team_feed = feed_generator.create_team_analysis_feed("AMZ Growth Team")
    print(f"Analysis Scope: {team_feed['feed_metadata']['analysis_scope']}")
    print(f"Total Records: {team_feed['feed_metadata']['record_count']}")
    print(f"Teams Found: {list(team_feed['data_by_team'].keys())}")
    
    # 4. Time series feed
    print("\n4. TIME SERIES FEED:")
    print("-" * 40)
    time_feed = feed_generator.create_time_series_feed(days=14, group_by="day")
    print(f"Period: {time_feed['feed_metadata']['period']['days']} days")
    print(f"Grouping: {time_feed['feed_metadata']['period']['grouping']}")
    print(f"Records: {time_feed['feed_metadata']['record_count']}")
    print(f"Purpose: {time_feed['time_series_context']['purpose']}")
    
    # 5. Project lifecycle feed
    print("\n5. PROJECT LIFECYCLE FEED:")
    print("-" * 40)
    lifecycle_feed = feed_generator.create_project_lifecycle_feed()
    print(f"Projects Analyzed: {lifecycle_feed['feed_metadata']['project_count']}")
    print(f"Total Records: {lifecycle_feed['feed_metadata']['record_count']}")
    if lifecycle_feed['data_by_project']:
        sample_project = list(lifecycle_feed['data_by_project'].keys())[0]
        print(f"Sample Project: {sample_project}")
        print(f"  Status Changes: {len(lifecycle_feed['data_by_project'][sample_project])}")
    
    # Save sample feeds for review
    print("\n" + "=" * 60)
    print("SAVING SAMPLE FEEDS...")
    
    # Save the question-based feed as it's most comprehensive
    with open("sample_ai_raw_feed.json", "w") as f:
        json.dump(question_feed, f, indent=2, default=str)
    print("✓ Saved question-based feed to sample_ai_raw_feed.json")
    
    # Save time series feed
    with open("sample_ai_timeseries_feed.json", "w") as f:
        json.dump(time_feed, f, indent=2, default=str)
    print("✓ Saved time series feed to sample_ai_timeseries_feed.json")
    
    # Save team analysis feed
    with open("sample_ai_team_feed.json", "w") as f:
        json.dump(team_feed, f, indent=2, default=str)
    print("✓ Saved team analysis feed to sample_ai_team_feed.json")
    
    print("\n" + "=" * 60)
    print("Feed demonstration complete!")
    print("Check the JSON files to see full feed structures.")


if __name__ == "__main__":
    demonstrate_feeds()

