#!/usr/bin/env python3
"""
Main orchestrator for Project Status Log processing system.
This module coordinates all operations: querying, reporting, AI formatting, and retention.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query_status_log import StatusLogQuery
from aggregate_reports import ReportAggregator
from report_generator import SlackReportGenerator
from ai_data_formatter import AIDataFormatter
from retention_manager import RetentionManager


class StatusLogProcessor:
    """Main orchestrator for status log processing."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the processor with all components.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.query = StatusLogQuery()
        self.aggregator = ReportAggregator()
        self.report_generator = SlackReportGenerator()
        self.ai_formatter = AIDataFormatter()
        self.retention_manager = RetentionManager(dry_run=True)  # Safety: dry-run by default
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Create output directory if needed
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_weekly_report(self, weeks_back: int = 1, save_to_file: bool = True) -> Dict[str, Any]:
        """
        Generate weekly report for Slack.
        
        Args:
            weeks_back: Number of weeks to look back
            save_to_file: Whether to save report to file
            
        Returns:
            Weekly report data
        """
        print(f"Generating weekly report for the past {weeks_back} week(s)...")
        
        # Generate report
        report = self.report_generator.generate_weekly_digest(weeks_back)
        
        # Save to file if requested
        if save_to_file:
            filename = f"weekly_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.output_dir / filename
            with open(filepath, "w") as f:
                json.dump(report, f, indent=2)
            print(f"  ✓ Report saved to {filepath}")
        
        # Print summary
        print(f"  ✓ Generated report with {len(report['blocks'])} Slack blocks")
        print(f"  ✓ Summary: {report['metadata']}")
        
        return report
    
    def generate_monthly_report(self, month: Optional[int] = None, year: Optional[int] = None, 
                              save_to_file: bool = True) -> Dict[str, Any]:
        """
        Generate monthly report for Slack.
        
        Args:
            month: Month number (1-12)
            year: Year
            save_to_file: Whether to save report to file
            
        Returns:
            Monthly report data
        """
        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year
        
        print(f"Generating monthly report for {month}/{year}...")
        
        # Generate report
        report = self.report_generator.generate_monthly_digest(month, year)
        
        # Save to file if requested
        if save_to_file:
            filename = f"monthly_report_{year}_{month:02d}.json"
            filepath = self.output_dir / filename
            with open(filepath, "w") as f:
                json.dump(report, f, indent=2)
            print(f"  ✓ Report saved to {filepath}")
        
        # Print summary
        print(f"  ✓ Generated report with {len(report['blocks'])} Slack blocks")
        print(f"  ✓ Summary: {report['metadata']}")
        
        return report
    
    def prepare_ai_context(self, days: int = 30, save_to_file: bool = True) -> Dict[str, Any]:
        """
        Prepare data context for AI agent.
        
        Args:
            days: Number of days to include
            save_to_file: Whether to save context to file
            
        Returns:
            AI context data
        """
        print(f"Preparing AI context for the past {days} days...")
        
        # Generate AI context
        start_date = datetime.now() - timedelta(days=days)
        ai_context = self.ai_formatter.format_for_ai_context(
            start_date=start_date,
            max_records=100
        )
        
        # Save to file if requested
        if save_to_file:
            filename = f"ai_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.output_dir / filename
            
            # Create serializable version
            serializable = {
                "metadata": ai_context["metadata"],
                "summary": ai_context["summary"],
                "key_insights": ai_context["key_insights"],
                "natural_language_summary": ai_context["natural_language_summary"]
            }
            
            with open(filepath, "w") as f:
                json.dump(serializable, f, indent=2)
            print(f"  ✓ AI context saved to {filepath}")
        
        # Print summary
        print(f"  ✓ Processed {ai_context['metadata']['record_count']} records")
        print(f"  ✓ Generated {len(ai_context['key_insights'])} key insights")
        print(f"  ✓ Natural language summary: {ai_context['natural_language_summary'][:100]}...")
        
        return ai_context
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a question using AI context.
        
        Args:
            question: Natural language question
            
        Returns:
            Answer context
        """
        print(f"Processing question: {question}")
        
        # Prepare Q&A context
        qa_context = self.ai_formatter.prepare_qa_context(question)
        
        # Print results
        print(f"  ✓ Filters detected: {qa_context['filters_detected']}")
        print(f"  ✓ Found {qa_context['metadata']['context_items']} relevant items")
        
        if qa_context.get("suggestions"):
            print("  ✓ Suggestions:")
            for suggestion in qa_context["suggestions"]:
                print(f"    - {suggestion}")
        
        print(f"  ✓ Summary: {qa_context['data_summary'][:200]}...")
        
        return qa_context
    
    def run_retention_cleanup(self, dry_run: bool = True, confirm: bool = False) -> Dict[str, Any]:
        """
        Run retention cleanup process.
        
        Args:
            dry_run: If True, only simulate deletion
            confirm: Must be True to actually delete
            
        Returns:
            Cleanup report
        """
        print(f"Running retention cleanup (dry_run={dry_run})...")
        
        # Update retention manager mode
        self.retention_manager.dry_run = dry_run
        
        # Generate report first
        report = self.retention_manager.generate_deletion_report()
        print(f"  ✓ Found {report['statistics']['total_records_to_delete']} records to delete")
        
        if report['date_range']['oldest'] and report['date_range']['newest']:
            print(f"  ✓ Date range: {report['date_range']['oldest'][:10]} to {report['date_range']['newest'][:10]}")
        
        # Show breakdown
        if report['statistics']['by_team']:
            print("  ✓ By team:")
            for team, count in report['statistics']['by_team'].items():
                print(f"    - {team}: {count}")
        
        # Perform cleanup if confirmed
        if confirm or dry_run:
            result = self.retention_manager.delete_expired_records(confirm=confirm)
            print(f"  ✓ Status: {result['status']}")
            
            if result.get('message'):
                print(f"  ✓ Message: {result['message']}")
            
            if result.get('deleted_count'):
                print(f"  ✓ Deleted: {result['deleted_count']} records")
        else:
            print("  ⚠ Cleanup not confirmed. Use --confirm to proceed.")
        
        # Save report
        filename = f"retention_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)
        print(f"  ✓ Report saved to {filepath}")
        
        return report
    
    def check_system_status(self) -> Dict[str, Any]:
        """
        Check overall system status and health.
        
        Returns:
            System status report
        """
        print("Checking system status...")
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "database": {},
            "retention": {},
            "recent_activity": {}
        }
        
        # Check database connection
        try:
            all_logs = self.query.fetch_all_logs(limit=1)
            status["components"]["database"] = "connected"
            status["database"]["accessible"] = True
        except Exception as e:
            status["components"]["database"] = f"error: {str(e)}"
            status["database"]["accessible"] = False
            return status
        
        # Get database statistics
        recent_logs = self.query.fetch_recent_changes(days=7)
        all_logs_count = len(self.query.fetch_all_logs())
        
        status["database"]["total_records"] = all_logs_count
        status["database"]["recent_7_days"] = len(recent_logs)
        
        # Check retention status
        validation = self.retention_manager.validate_retention_policy()
        status["retention"]["compliant"] = validation["results"]["violation_count"] == 0
        status["retention"]["violations"] = validation["results"]["violation_count"]
        status["retention"]["compliance_rate"] = validation["results"]["compliance_rate"]
        
        # Get recent activity summary
        if recent_logs:
            parsed = [self.query.parse_log_entry(log) for log in recent_logs[:10]]
            stats = self.aggregator.calculate_statistics(parsed)
            
            status["recent_activity"]["last_7_days"] = {
                "total_changes": len(recent_logs),
                "active_teams": len(stats["by_team"]),
                "active_platforms": list(stats["by_platform"].keys()),
                "top_projects": list(stats["most_active_projects"].keys())[:3]
            }
        
        # Check component status
        status["components"]["query_module"] = "operational"
        status["components"]["aggregator"] = "operational"
        status["components"]["report_generator"] = "operational"
        status["components"]["ai_formatter"] = "operational"
        status["components"]["retention_manager"] = "operational"
        
        # Next scheduled tasks
        schedule = self.retention_manager.schedule_cleanup()
        status["next_cleanup"] = {
            "date": schedule["next_cleanup_date"][:10],
            "days_until": schedule["days_until_cleanup"]
        }
        
        # Print summary
        print(f"  ✓ Database: {status['database']['total_records']} total records")
        print(f"  ✓ Recent: {status['database']['recent_7_days']} changes in last 7 days")
        print(f"  ✓ Retention: {status['retention']['compliance_rate']:.1f}% compliant")
        print(f"  ✓ Next cleanup: {status['next_cleanup']['date']} ({status['next_cleanup']['days_until']} days)")
        
        return status
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "retention": {
                "dry_run": True,
                "auto_cleanup": False
            },
            "reports": {
                "weekly_day": "monday",
                "monthly_day": 1
            },
            "ai": {
                "max_context_items": 100,
                "default_days": 30
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, "r") as f:
                loaded_config = json.load(f)
                default_config.update(loaded_config)
        
        return default_config


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Project Status Log Processor - Query, Report, and Manage Status Changes"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Weekly report command
    weekly_parser = subparsers.add_parser("weekly", help="Generate weekly report")
    weekly_parser.add_argument("--weeks", type=int, default=1, help="Number of weeks to look back")
    weekly_parser.add_argument("--no-save", action="store_true", help="Don't save to file")
    
    # Monthly report command
    monthly_parser = subparsers.add_parser("monthly", help="Generate monthly report")
    monthly_parser.add_argument("--month", type=int, help="Month number (1-12)")
    monthly_parser.add_argument("--year", type=int, help="Year")
    monthly_parser.add_argument("--no-save", action="store_true", help="Don't save to file")
    
    # AI context command
    ai_parser = subparsers.add_parser("ai-context", help="Prepare AI context")
    ai_parser.add_argument("--days", type=int, default=30, help="Number of days to include")
    ai_parser.add_argument("--no-save", action="store_true", help="Don't save to file")
    
    # Question command
    qa_parser = subparsers.add_parser("question", help="Answer a question")
    qa_parser.add_argument("query", nargs="+", help="Your question")
    
    # Retention cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Run retention cleanup")
    cleanup_parser.add_argument("--execute", action="store_true", help="Actually delete (not dry-run)")
    cleanup_parser.add_argument("--confirm", action="store_true", help="Confirm deletion")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check system status")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize processor
    processor = StatusLogProcessor()
    
    # Execute command
    if args.command == "weekly":
        processor.generate_weekly_report(
            weeks_back=args.weeks,
            save_to_file=not args.no_save
        )
    
    elif args.command == "monthly":
        processor.generate_monthly_report(
            month=args.month,
            year=args.year,
            save_to_file=not args.no_save
        )
    
    elif args.command == "ai-context":
        processor.prepare_ai_context(
            days=args.days,
            save_to_file=not args.no_save
        )
    
    elif args.command == "question":
        question = " ".join(args.query)
        processor.answer_question(question)
    
    elif args.command == "cleanup":
        processor.run_retention_cleanup(
            dry_run=not args.execute,
            confirm=args.confirm
        )
    
    elif args.command == "status":
        status = processor.check_system_status()
        
        # Save status report
        filename = f"system_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = processor.output_dir / filename
        with open(filepath, "w") as f:
            json.dump(status, f, indent=2)
        print(f"\n  ✓ Full status report saved to {filepath}")
    
    else:
        # Show help if no command specified
        parser.print_help()
        print("\nExamples:")
        print("  python status_log_processor.py weekly")
        print("  python status_log_processor.py monthly --month 7 --year 2025")
        print("  python status_log_processor.py ai-context --days 30")
        print("  python status_log_processor.py question What projects changed this week?")
        print("  python status_log_processor.py cleanup --execute --confirm")
        print("  python status_log_processor.py status")


if __name__ == "__main__":
    main()

