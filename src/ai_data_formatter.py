"""
AI Data Formatter module for preparing data for LangChain/AI agent consumption.
This module transforms status log data into formats optimized for AI processing.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from query_status_log import StatusLogQuery
from aggregate_reports import ReportAggregator


class AIDataFormatter:
    """Format data for AI agent consumption."""
    
    def __init__(self):
        """Initialize the formatter with query and aggregation handlers."""
        self.query = StatusLogQuery()
        self.aggregator = ReportAggregator()
    
    def format_for_ai_context(self, 
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              max_records: int = 100) -> Dict[str, Any]:
        """
        Format data for AI agent context window.
        
        Args:
            start_date: Start of period (defaults to 30 days ago)
            end_date: End of period (defaults to now)
            max_records: Maximum number of records to include
            
        Returns:
            AI-optimized data structure
        """
        # Set default date range
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Fetch logs
        logs = self.query.fetch_logs_by_date_range(start_date, end_date)
        parsed_logs = [self.query.parse_log_entry(log) for log in logs[:max_records]]
        
        # Calculate statistics
        stats = self.aggregator.calculate_statistics(parsed_logs)
        
        # Build AI context
        ai_context = {
            "metadata": {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": (end_date - start_date).days
                },
                "record_count": len(parsed_logs),
                "generated_at": datetime.now().isoformat()
            },
            "summary": {
                "total_changes": len(parsed_logs),
                "unique_projects": len(set(log["project_name"] for log in parsed_logs if log["project_name"])),
                "active_teams": len(set(log["team"] for log in parsed_logs if log["team"])),
                "platforms": list(set(log["platform"] for log in parsed_logs if log["platform"])),
                "status_distribution": stats["status_distribution"]
            },
            "key_insights": self._generate_key_insights(parsed_logs, stats),
            "searchable_index": self.create_searchable_index(parsed_logs),
            "natural_language_summary": self.generate_natural_language_summary(parsed_logs, stats),
            "raw_data": parsed_logs
        }
        
        return ai_context
    
    def create_searchable_index(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create searchable index for AI queries.
        
        Args:
            logs: List of parsed log entries
            
        Returns:
            Indexed data structure for efficient searching
        """
        index = {
            "by_project": defaultdict(list),
            "by_team": defaultdict(list),
            "by_platform": defaultdict(list),
            "by_status": defaultdict(list),
            "by_date": defaultdict(list),
            "by_user": defaultdict(list),
            "status_transitions": defaultdict(list),
            "keywords": defaultdict(set)
        }
        
        for log in logs:
            # Index by project
            if log.get("project_name"):
                index["by_project"][log["project_name"]].append(log["id"])
                self._extract_keywords(log["project_name"], index["keywords"])
            
            # Index by team
            if log.get("team"):
                index["by_team"][log["team"]].append(log["id"])
            
            # Index by platform
            if log.get("platform"):
                index["by_platform"][log["platform"]].append(log["id"])
            
            # Index by status
            if log.get("new_status"):
                index["by_status"][log["new_status"]].append(log["id"])
            
            # Index by date (group by day)
            if log.get("date"):
                date_key = log["date"][:10]  # YYYY-MM-DD
                index["by_date"][date_key].append(log["id"])
            
            # Index by user
            if log.get("changed_by") and isinstance(log["changed_by"], list):
                for user in log["changed_by"]:
                    index["by_user"][user].append(log["id"])
            
            # Index status transitions
            if log.get("previous_status") and log.get("new_status"):
                transition = f"{log['previous_status']}→{log['new_status']}"
                index["status_transitions"][transition].append(log["id"])
            
            # Extract keywords from what's new
            if log.get("whats_new"):
                self._extract_keywords(log["whats_new"], index["keywords"])
        
        # Convert defaultdicts to regular dicts
        return {
            "by_project": dict(index["by_project"]),
            "by_team": dict(index["by_team"]),
            "by_platform": dict(index["by_platform"]),
            "by_status": dict(index["by_status"]),
            "by_date": dict(index["by_date"]),
            "by_user": dict(index["by_user"]),
            "status_transitions": dict(index["status_transitions"]),
            "keywords": {k: list(v) for k, v in index["keywords"].items()}
        }
    
    def generate_natural_language_summary(self, 
                                         logs: List[Dict[str, Any]], 
                                         stats: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate human-readable summary of the data.
        
        Args:
            logs: List of parsed log entries
            stats: Pre-calculated statistics (optional)
            
        Returns:
            Natural language summary
        """
        if not logs:
            return "No status changes found in the specified period."
        
        if not stats:
            stats = self.aggregator.calculate_statistics(logs)
        
        # Calculate date range
        dates = [log["date"] for log in logs if log.get("date")]
        if dates:
            earliest = min(dates)
            latest = max(dates)
            date_range = f"from {earliest[:10]} to {latest[:10]}"
        else:
            date_range = "in the specified period"
        
        # Build summary
        summary_parts = []
        
        # Overview
        summary_parts.append(
            f"During the period {date_range}, there were {len(logs)} status changes "
            f"across {stats.get('summary', {}).get('unique_projects', 0)} projects."
        )
        
        # Team activity
        if stats.get("by_team"):
            top_teams = list(stats["by_team"].items())[:3]
            if top_teams:
                team_summary = "The most active teams were: "
                team_parts = [f"{team} ({count} changes)" for team, count in top_teams]
                summary_parts.append(team_summary + ", ".join(team_parts) + ".")
        
        # Platform distribution
        if stats.get("by_platform"):
            platform_parts = []
            for platform, count in stats["by_platform"].items():
                platform_parts.append(f"{count} on {platform}")
            summary_parts.append(f"Changes were distributed across platforms: {', '.join(platform_parts)}.")
        
        # Status distribution
        status_dist = stats.get("status_distribution", {})
        if status_dist:
            summary_parts.append(
                f"Status distribution shows {status_dist.get('to_do', 0)} projects in To-Do, "
                f"{status_dist.get('in_progress', 0)} In Progress, "
                f"and {status_dist.get('complete', 0)} Complete."
            )
        
        # Most common transitions
        if stats.get("by_status_transition"):
            top_transitions = list(stats["by_status_transition"].items())[:3]
            if top_transitions:
                transition_summary = "The most common status transitions were: "
                transition_parts = [f"{trans} ({count} times)" for trans, count in top_transitions]
                summary_parts.append(transition_summary + ", ".join(transition_parts) + ".")
        
        # Most active projects
        if stats.get("most_active_projects"):
            top_projects = list(stats["most_active_projects"].items())[:3]
            if top_projects:
                project_summary = "The most active projects were: "
                project_parts = [f"{proj} ({count} changes)" for proj, count in top_projects]
                summary_parts.append(project_summary + ", ".join(project_parts) + ".")
        
        return " ".join(summary_parts)
    
    def prepare_qa_context(self, question: str, max_context_items: int = 20) -> Dict[str, Any]:
        """
        Prepare context for Q&A interactions based on the question.
        
        Args:
            question: User's question
            max_context_items: Maximum number of context items to include
            
        Returns:
            Context data optimized for answering the question
        """
        # Lowercase question for keyword matching
        question_lower = question.lower()
        
        # Determine relevant filters based on question keywords
        filters = self._extract_filters_from_question(question_lower)
        
        # Fetch relevant logs based on filters
        relevant_logs = self._fetch_filtered_logs(filters, max_context_items)
        parsed_logs = [self.query.parse_log_entry(log) for log in relevant_logs]
        
        # Build context
        context = {
            "question": question,
            "filters_detected": filters,
            "relevant_data": parsed_logs,
            "data_summary": self.generate_natural_language_summary(parsed_logs) if parsed_logs else "No relevant data found.",
            "suggestions": self._generate_answer_suggestions(question_lower, parsed_logs),
            "metadata": {
                "context_items": len(parsed_logs),
                "generated_at": datetime.now().isoformat()
            }
        }
        
        return context
    
    def format_for_langchain(self, data: Dict[str, Any]) -> str:
        """
        Format data specifically for LangChain consumption.
        
        Args:
            data: Data to format
            
        Returns:
            Formatted string for LangChain
        """
        # Create a structured text representation
        formatted = []
        
        # Add metadata
        formatted.append("=== PROJECT STATUS CHANGE LOG DATA ===\n")
        
        if data.get("metadata"):
            formatted.append("METADATA:")
            formatted.append(f"  Period: {data['metadata'].get('period', {}).get('start', 'N/A')} to {data['metadata'].get('period', {}).get('end', 'N/A')}")
            formatted.append(f"  Total Records: {data['metadata'].get('record_count', 0)}\n")
        
        if data.get("summary"):
            formatted.append("SUMMARY:")
            for key, value in data["summary"].items():
                formatted.append(f"  {key}: {value}")
            formatted.append("")
        
        if data.get("natural_language_summary"):
            formatted.append("OVERVIEW:")
            formatted.append(f"  {data['natural_language_summary']}\n")
        
        if data.get("key_insights"):
            formatted.append("KEY INSIGHTS:")
            for insight in data["key_insights"]:
                formatted.append(f"  - {insight}")
            formatted.append("")
        
        # Add structured data for reference
        if data.get("raw_data"):
            formatted.append("RECENT CHANGES (Last 10):")
            for log in data["raw_data"][:10]:
                formatted.append(f"  - {log.get('project_name', 'Unknown')}: "
                               f"{log.get('previous_status', 'Unknown')} → {log.get('new_status', 'Unknown')} "
                               f"({log.get('date', 'Unknown date')[:10]})")
        
        return "\n".join(formatted)
    
    def _generate_key_insights(self, logs: List[Dict[str, Any]], stats: Dict[str, Any]) -> List[str]:
        """Generate key insights from the data."""
        insights = []
        
        # Insight about most active team
        if stats.get("by_team"):
            top_team = list(stats["by_team"].items())[0]
            insights.append(f"{top_team[0]} is the most active team with {top_team[1]} status changes")
        
        # Insight about status distribution
        status_dist = stats.get("status_distribution", {})
        total = sum(status_dist.values())
        if total > 0 and status_dist.get("complete", 0) > 0:
            completion_rate = (status_dist["complete"] / total) * 100
            insights.append(f"{completion_rate:.1f}% of projects have reached completion status")
        
        # Insight about common transitions
        if stats.get("by_status_transition"):
            top_transition = list(stats["by_status_transition"].items())[0]
            insights.append(f"Most common transition: {top_transition[0]} ({top_transition[1]} occurrences)")
        
        # Insight about platform focus
        if stats.get("by_platform"):
            platforms = list(stats["by_platform"].keys())
            if len(platforms) > 1:
                insights.append(f"Development is active across {len(platforms)} platforms: {', '.join(platforms)}")
        
        # Insight about project velocity
        if logs:
            dates = [log["date"] for log in logs if log.get("date")]
            if dates:
                date_objs = []
                for date in dates:
                    dt = datetime.fromisoformat(date)
                    # Remove timezone info if present
                    if dt.tzinfo:
                        dt = dt.replace(tzinfo=None)
                    date_objs.append(dt)
                days_span = (max(date_objs) - min(date_objs)).days + 1
                if days_span > 0:
                    changes_per_day = len(logs) / days_span
                    insights.append(f"Average of {changes_per_day:.1f} status changes per day")
        
        return insights
    
    def _extract_keywords(self, text: str, keyword_dict: Dict[str, set]):
        """Extract keywords from text and add to keyword dictionary."""
        if not text:
            return
        
        # Simple keyword extraction (can be enhanced with NLP)
        words = text.lower().split()
        for word in words:
            # Clean word (remove punctuation)
            cleaned = ''.join(c for c in word if c.isalnum())
            if len(cleaned) > 3:  # Only keep words longer than 3 characters
                keyword_dict[cleaned].add(text)
    
    def _extract_filters_from_question(self, question: str) -> Dict[str, Any]:
        """Extract filters from a natural language question."""
        filters = {}
        
        # Platform detection
        platforms = ["ios", "amz", "amazon", "gp", "google play", "fire tv"]
        for platform in platforms:
            if platform in question:
                if platform == "amazon":
                    filters["platform"] = "AMZ"
                elif platform == "google play":
                    filters["platform"] = "GP"
                else:
                    filters["platform"] = platform.upper()
                break
        
        # Team detection
        teams = ["growth", "production", "integration", "port", "tools"]
        for team in teams:
            if team in question:
                filters["team_keyword"] = team
                break
        
        # Time period detection
        if "today" in question:
            filters["date_range"] = "today"
        elif "yesterday" in question:
            filters["date_range"] = "yesterday"
        elif "week" in question:
            filters["date_range"] = "week"
        elif "month" in question:
            filters["date_range"] = "month"
        
        # Status detection
        statuses = ["backlog", "development", "qa", "live", "blocked", "paused"]
        for status in statuses:
            if status in question:
                filters["status"] = status.upper()
                break
        
        return filters
    
    def _fetch_filtered_logs(self, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Fetch logs based on extracted filters."""
        logs = []
        
        # Apply date range filter
        if filters.get("date_range"):
            if filters["date_range"] == "today":
                start_date = datetime.now().replace(hour=0, minute=0, second=0)
            elif filters["date_range"] == "yesterday":
                start_date = datetime.now() - timedelta(days=1)
            elif filters["date_range"] == "week":
                start_date = datetime.now() - timedelta(weeks=1)
            elif filters["date_range"] == "month":
                start_date = datetime.now() - timedelta(days=30)
            else:
                start_date = datetime.now() - timedelta(days=30)
            
            logs = self.query.fetch_logs_by_date_range(start_date)
        
        # Apply platform filter
        elif filters.get("platform"):
            logs = self.query.fetch_logs_by_platform(filters["platform"])
        
        # Apply team filter
        elif filters.get("team_keyword"):
            # This would need to be enhanced to match team names containing the keyword
            logs = self.query.fetch_recent_changes(30)
        
        # Default to recent changes
        else:
            logs = self.query.fetch_recent_changes(30)
        
        return logs[:limit]
    
    def _generate_answer_suggestions(self, question: str, logs: List[Dict[str, Any]]) -> List[str]:
        """Generate suggestions for answering the question."""
        suggestions = []
        
        if "how many" in question or "count" in question:
            suggestions.append(f"Total count: {len(logs)} changes found")
        
        if "which project" in question or "what project" in question:
            projects = list(set(log["project_name"] for log in logs if log.get("project_name")))[:5]
            if projects:
                suggestions.append(f"Projects involved: {', '.join(projects)}")
        
        if "who" in question:
            users = []
            for log in logs:
                if log.get("changed_by") and isinstance(log["changed_by"], list):
                    users.extend(log["changed_by"])
            unique_users = list(set(users))[:5]
            if unique_users:
                suggestions.append(f"People involved: {', '.join(unique_users)}")
        
        if "when" in question:
            dates = [log["date"][:10] for log in logs if log.get("date")]
            if dates:
                suggestions.append(f"Date range: {min(dates)} to {max(dates)}")
        
        return suggestions


# Test function
def test_ai_formatter():
    """Test the AI data formatter module."""
    formatter = AIDataFormatter()
    
    print("Testing AIDataFormatter module...")
    print("-" * 50)
    
    # Test formatting for AI context
    print("\n1. Formatting data for AI context:")
    ai_context = formatter.format_for_ai_context(max_records=50)
    print(f"   Metadata: {ai_context['metadata']}")
    print(f"   Summary: {ai_context['summary']}")
    print(f"   Key insights: {len(ai_context.get('key_insights', []))} insights generated")
    
    # Test searchable index creation
    print("\n2. Creating searchable index:")
    if ai_context.get("raw_data"):
        index = formatter.create_searchable_index(ai_context["raw_data"])
        print(f"   Indexed by project: {len(index.get('by_project', {}))} projects")
        print(f"   Indexed by team: {len(index.get('by_team', {}))} teams")
        print(f"   Indexed by platform: {len(index.get('by_platform', {}))} platforms")
    
    # Test natural language summary
    print("\n3. Natural language summary:")
    if ai_context.get("natural_language_summary"):
        print(f"   {ai_context['natural_language_summary'][:200]}...")
    
    # Test Q&A context preparation
    print("\n4. Testing Q&A context preparation:")
    test_questions = [
        "What projects changed status this week?",
        "Show me all iOS projects",
        "How many changes were made by the Growth team?"
    ]
    
    for question in test_questions:
        qa_context = formatter.prepare_qa_context(question)
        print(f"\n   Question: {question}")
        print(f"   Filters detected: {qa_context['filters_detected']}")
        print(f"   Relevant items: {qa_context['metadata']['context_items']}")
        if qa_context.get("suggestions"):
            print(f"   Suggestions: {qa_context['suggestions'][:2]}")
    
    # Test LangChain formatting
    print("\n5. Testing LangChain formatting:")
    langchain_format = formatter.format_for_langchain(ai_context)
    print(f"   Generated {len(langchain_format)} characters of formatted text")
    print(f"   Preview:\n{langchain_format[:500]}...")
    
    # Save sample output
    print("\n6. Saving sample AI context:")
    with open("sample_ai_context.json", "w") as f:
        # Convert to serializable format
        serializable_context = {
            "metadata": ai_context.get("metadata", {}),
            "summary": ai_context.get("summary", {}),
            "key_insights": ai_context.get("key_insights", []),
            "natural_language_summary": ai_context.get("natural_language_summary", "")
        }
        json.dump(serializable_context, f, indent=2)
        print("   Saved to sample_ai_context.json")
    
    print("\n" + "-" * 50)
    print("AI data formatter module test completed!")


if __name__ == "__main__":
    test_ai_formatter()
