"""
Report generator module for creating formatted Slack messages.
This module converts aggregated data into Slack-compatible formats.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from aggregate_reports import ReportAggregator


class SlackReportGenerator:
    """Generate formatted reports for Slack."""
    
    def __init__(self):
        """Initialize the report generator."""
        self.aggregator = ReportAggregator()
        
        # Emoji mappings for visual enhancement
        self.platform_emojis = {
            "iOS": "📱",
            "AMZ": "📦",
            "GP": "🎮",
            "Fire TV": "📺"
        }
        
        self.status_emojis = {
            "BACKLOG": "📋",
            "DEVELOPMENT": "👨‍💻",
            "QA": "🧪",
            "LIVE": "🚀",
            "BLOCKED": "🚫",
            "PAUSED": "⏸️",
            "ARCHIVE": "📁"
        }
        
        self.team_emojis = {
            "AMZ Growth Team": "📈",
            "AMZ Production Team": "⚙️",
            "AMZ Integration and Port Team": "🔧",
            "Tools Team": "🛠️"
        }
    
    def generate_weekly_digest(self, weeks_back: int = 1) -> Dict[str, Any]:
        """
        Generate weekly digest for Slack.
        
        Args:
            weeks_back: Number of weeks to look back
            
        Returns:
            Formatted Slack message with blocks and text
        """
        # Get aggregated data
        report_data = self.aggregator.aggregate_weekly_report(weeks_back)
        
        # Build Slack blocks
        blocks = []
        
        # Header block
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📊 Weekly Status Report",
                "emoji": True
            }
        })
        
        # Period info
        start_date = datetime.fromisoformat(report_data['period']['start_date']).strftime("%B %d")
        end_date = datetime.fromisoformat(report_data['period']['end_date']).strftime("%B %d, %Y")
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Period:* {start_date} - {end_date}\n"
                       f"*Total Changes:* {report_data['summary']['total_changes']}\n"
                       f"*Active Projects:* {report_data['summary']['unique_projects']}\n"
                       f"*Active Teams:* {report_data['summary']['active_teams']}"
            }
        })
        
        blocks.append({"type": "divider"})
        
        # Group changes by team and project
        grouped_data = self.aggregator.group_by_team_and_project(report_data['detailed_changes'])
        
        # Add team sections
        for team_name, team_data in grouped_data.items():
            team_emoji = self.team_emojis.get(team_name, "👥")
            
            # Team header
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{team_emoji} {team_name}* ({team_data['total_changes']} changes)"
                }
            })
            
            # Project changes
            project_lines = []
            for project_name, project_data in team_data['projects'].items():
                if project_data['changes']:
                    # Build status path for the project
                    status_path = self._build_status_path_string(project_data['changes'])
                    latest_change = project_data['changes'][0]
                    platform_emoji = self.platform_emojis.get(latest_change.get('platform', ''), "")
                    
                    project_line = f"• *{project_name}* {platform_emoji}\n"
                    project_line += f"  {status_path}\n"
                    
                    if latest_change.get('version'):
                        project_line += f"  Version: {latest_change['version']}\n"
                    
                    if latest_change.get('whats_new'):
                        project_line += f"  _\"{latest_change['whats_new']}_\"\n"
                    
                    project_lines.append(project_line)
            
            if project_lines:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(project_lines[:5])  # Limit to 5 projects per team
                    }
                })
        
        blocks.append({"type": "divider"})
        
        # Summary statistics
        if report_data['by_platform']:
            platform_summary = []
            for platform, data in report_data['by_platform'].items():
                emoji = self.platform_emojis.get(platform, "")
                platform_summary.append(f"{emoji} {platform}: {data['count']}")
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Platform Distribution:*\n" + " | ".join(platform_summary)
                }
            })
        
        # Footer
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                           f"Data from Project Status Change Log"
                }
            ]
        })
        
        # Create plain text fallback
        text_fallback = self._create_text_fallback(report_data, "Weekly")
        
        return {
            "blocks": blocks,
            "text": text_fallback,
            "metadata": report_data['summary']
        }
    
    def generate_monthly_digest(self, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate monthly digest for Slack.
        
        Args:
            month: Month number (1-12)
            year: Year
            
        Returns:
            Formatted Slack message with blocks and text
        """
        # Get aggregated data
        report_data = self.aggregator.aggregate_monthly_report(month, year)
        
        # Build Slack blocks
        blocks = []
        
        # Header block
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📈 Monthly Status Report - {report_data['period']['month_name']} {report_data['period']['year']}",
                "emoji": True
            }
        })
        
        # Summary section
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Total Changes:* {report_data['summary']['total_changes']}\n"
                       f"*Active Projects:* {report_data['summary']['unique_projects']}\n"
                       f"*Active Teams:* {report_data['summary']['active_teams']}"
            }
        })
        
        blocks.append({"type": "divider"})
        
        # Calculate statistics
        stats = self.aggregator.calculate_statistics(report_data['detailed_changes'])
        
        # Status distribution chart (text-based)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Status Distribution:*\n"
                       f"📋 To Do: {stats['status_distribution']['to_do']}\n"
                       f"⚙️ In Progress: {stats['status_distribution']['in_progress']}\n"
                       f"✅ Complete: {stats['status_distribution']['complete']}"
            }
        })
        
        # Top status transitions
        if stats['by_status_transition']:
            top_transitions = list(stats['by_status_transition'].items())[:5]
            transition_text = "*Top Status Transitions:*\n"
            for transition, count in top_transitions:
                transition_text += f"• {transition}: {count}\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": transition_text
                }
            })
        
        blocks.append({"type": "divider"})
        
        # Most active projects
        if stats['most_active_projects']:
            active_projects_text = "*Most Active Projects:*\n"
            for project, count in list(stats['most_active_projects'].items())[:5]:
                active_projects_text += f"• {project}: {count} changes\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": active_projects_text
                }
            })
        
        # Weekly breakdown
        if report_data.get('by_week'):
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Weekly Breakdown:*"
                }
            })
            
            for week_start, week_logs in list(report_data['by_week'].items())[:4]:
                week_date = datetime.fromisoformat(week_start).strftime("%b %d")
                blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Week of {week_date}: {len(week_logs)} changes"
                        }
                    ]
                })
        
        # Footer
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                           f"Data from Project Status Change Log"
                }
            ]
        })
        
        # Create plain text fallback
        text_fallback = self._create_text_fallback(report_data, "Monthly")
        
        return {
            "blocks": blocks,
            "text": text_fallback,
            "metadata": report_data['summary']
        }
    
    def format_slack_message(self, content: str, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Format a simple message for Slack.
        
        Args:
            content: Message content
            title: Optional title
            
        Returns:
            Formatted Slack message
        """
        blocks = []
        
        if title:
            blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title,
                    "emoji": True
                }
            })
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": content
            }
        })
        
        return {
            "blocks": blocks,
            "text": content
        }
    
    def create_status_change_blocks(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create Slack blocks for status changes.
        
        Args:
            changes: List of status changes
            
        Returns:
            List of Slack blocks
        """
        blocks = []
        
        for change in changes[:10]:  # Limit to 10 changes
            # Get emoji for platform and status
            platform_emoji = self.platform_emojis.get(change.get('platform', ''), "")
            from_emoji = self.status_emojis.get(change.get('previous_status', ''), "")
            to_emoji = self.status_emojis.get(change.get('new_status', ''), "")
            
            # Format date
            date_str = ""
            if change.get('date'):
                date_obj = datetime.fromisoformat(change['date'])
                # Remove timezone info if present for formatting
                if date_obj.tzinfo:
                    date_obj = date_obj.replace(tzinfo=None)
                date_str = date_obj.strftime("%b %d, %H:%M")
            
            # Build change text
            change_text = f"*{change.get('project_name', 'Unknown Project')}* {platform_emoji}\n"
            change_text += f"{from_emoji} {change.get('previous_status', 'Unknown')} → "
            change_text += f"{to_emoji} {change.get('new_status', 'Unknown')}\n"
            
            if change.get('version'):
                change_text += f"Version: {change['version']} | "
            
            if change.get('team'):
                change_text += f"Team: {change['team']} | "
            
            change_text += f"_{date_str}_"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": change_text
                }
            })
            
            if change.get('whats_new'):
                blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_\"{change['whats_new']}_\""
                        }
                    ]
                })
            
            blocks.append({"type": "divider"})
        
        return blocks
    
    def _build_status_path_string(self, changes: List[Dict[str, Any]]) -> str:
        """Build a string representation of status transitions."""
        if not changes:
            return ""
        
        # Sort by date (oldest first)
        sorted_changes = sorted(changes, key=lambda x: x.get('date', ''))
        
        # Build path
        statuses = []
        for change in sorted_changes:
            if change.get('previous_status') and change['previous_status'] not in statuses:
                statuses.append(change['previous_status'])
            if change.get('new_status'):
                statuses.append(change['new_status'])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_statuses = []
        for status in statuses:
            if status not in seen:
                seen.add(status)
                unique_statuses.append(status)
        
        # Add emojis and create path
        path_parts = []
        for status in unique_statuses:
            emoji = self.status_emojis.get(status, "")
            path_parts.append(f"{emoji}{status}")
        
        return " → ".join(path_parts)
    
    def _create_text_fallback(self, report_data: Dict[str, Any], report_type: str) -> str:
        """Create plain text fallback for accessibility."""
        text = f"{report_type} Status Report\n"
        text += "=" * 50 + "\n\n"
        
        text += f"Total Changes: {report_data['summary']['total_changes']}\n"
        text += f"Active Projects: {report_data['summary']['unique_projects']}\n"
        text += f"Active Teams: {report_data['summary']['active_teams']}\n\n"
        
        if report_data.get('by_team'):
            text += "Changes by Team:\n"
            for team, data in report_data['by_team'].items():
                text += f"  - {team}: {data['count']} changes\n"
        
        return text


# Test function
def test_report_generator():
    """Test the report generator module."""
    generator = SlackReportGenerator()
    
    print("Testing SlackReportGenerator module...")
    print("-" * 50)
    
    # Test weekly digest
    print("\n1. Generating weekly digest:")
    weekly_digest = generator.generate_weekly_digest(weeks_back=1)
    print(f"   Generated {len(weekly_digest['blocks'])} Slack blocks")
    print(f"   Metadata: {weekly_digest['metadata']}")
    
    # Test monthly digest
    print("\n2. Generating monthly digest:")
    monthly_digest = generator.generate_monthly_digest()
    print(f"   Generated {len(monthly_digest['blocks'])} Slack blocks")
    
    # Test simple message formatting
    print("\n3. Testing simple message formatting:")
    simple_msg = generator.format_slack_message(
        "Test message content",
        title="Test Title"
    )
    print(f"   Generated {len(simple_msg['blocks'])} blocks")
    
    # Save sample output for review
    print("\n4. Saving sample outputs:")
    
    with open("sample_weekly_digest.json", "w") as f:
        json.dump(weekly_digest, f, indent=2)
        print("   Saved weekly digest to sample_weekly_digest.json")
    
    with open("sample_monthly_digest.json", "w") as f:
        json.dump(monthly_digest, f, indent=2)
        print("   Saved monthly digest to sample_monthly_digest.json")
    
    print("\n" + "-" * 50)
    print("Report generator module test completed!")
    print("\nNote: Check the generated JSON files to see Slack block structure")


if __name__ == "__main__":
    test_report_generator()
