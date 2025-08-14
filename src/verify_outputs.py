#!/usr/bin/env python3
"""
Output Verification Tool - Compares Python reference outputs with n8n results
This tool ensures n8n workflows produce EXACTLY the same output as Python scripts
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import difflib


class OutputVerifier:
    """Verifies that n8n outputs match Python reference outputs exactly."""
    
    def __init__(self):
        self.python_dir = Path("test_outputs/python_reference")
        self.n8n_dir = Path("test_outputs/n8n_results")
        self.comparison_dir = Path("test_outputs/comparisons")
        
        # Create directories if they don't exist
        self.python_dir.mkdir(parents=True, exist_ok=True)
        self.n8n_dir.mkdir(parents=True, exist_ok=True)
        self.comparison_dir.mkdir(parents=True, exist_ok=True)
    
    def normalize_data(self, data: Any, ignore_fields: List[str] = None) -> Any:
        """
        Normalize data for comparison, optionally ignoring certain fields.
        
        Args:
            data: Data to normalize
            ignore_fields: List of field names to ignore (e.g., timestamps)
        
        Returns:
            Normalized data
        """
        ignore_fields = ignore_fields or ['executionTime', 'timestamp', 'generated_at']
        
        if isinstance(data, dict):
            return {
                k: self.normalize_data(v, ignore_fields) 
                for k, v in data.items() 
                if k not in ignore_fields
            }
        elif isinstance(data, list):
            return [self.normalize_data(item, ignore_fields) for item in data]
        else:
            return data
    
    def compare_json_files(self, 
                          python_file: str, 
                          n8n_file: str,
                          ignore_fields: List[str] = None) -> Tuple[bool, str]:
        """
        Compare JSON outputs from Python and n8n.
        
        Args:
            python_file: Path to Python reference output
            n8n_file: Path to n8n output
            ignore_fields: Fields to ignore in comparison
        
        Returns:
            Tuple of (match_status, comparison_report)
        """
        try:
            # Load Python reference
            with open(self.python_dir / python_file, 'r') as f:
                python_data = json.load(f)
            
            # Load n8n output
            with open(self.n8n_dir / n8n_file, 'r') as f:
                n8n_data = json.load(f)
            
            # Normalize data
            python_normalized = self.normalize_data(python_data, ignore_fields)
            n8n_normalized = self.normalize_data(n8n_data, ignore_fields)
            
            # Compare
            if python_normalized == n8n_normalized:
                return True, "✅ PERFECT MATCH: Outputs are identical!"
            else:
                # Generate detailed diff
                python_str = json.dumps(python_normalized, indent=2, sort_keys=True)
                n8n_str = json.dumps(n8n_normalized, indent=2, sort_keys=True)
                
                diff = difflib.unified_diff(
                    python_str.splitlines(keepends=True),
                    n8n_str.splitlines(keepends=True),
                    fromfile=f"Python: {python_file}",
                    tofile=f"n8n: {n8n_file}",
                    lineterm=''
                )
                
                diff_text = ''.join(diff)
                return False, f"❌ MISMATCH DETECTED:\n\n{diff_text}"
                
        except FileNotFoundError as e:
            return False, f"❌ FILE NOT FOUND: {e}"
        except json.JSONDecodeError as e:
            return False, f"❌ JSON PARSE ERROR: {e}"
        except Exception as e:
            return False, f"❌ ERROR: {e}"
    
    def compare_text_files(self, 
                          python_file: str, 
                          n8n_file: str) -> Tuple[bool, str]:
        """
        Compare text outputs from Python and n8n.
        
        Args:
            python_file: Path to Python reference output
            n8n_file: Path to n8n output
        
        Returns:
            Tuple of (match_status, comparison_report)
        """
        try:
            # Load files
            with open(self.python_dir / python_file, 'r') as f:
                python_text = f.read()
            
            with open(self.n8n_dir / n8n_file, 'r') as f:
                n8n_text = f.read()
            
            # Compare
            if python_text == n8n_text:
                return True, "✅ PERFECT MATCH: Outputs are identical!"
            else:
                # Generate detailed diff
                diff = difflib.unified_diff(
                    python_text.splitlines(keepends=True),
                    n8n_text.splitlines(keepends=True),
                    fromfile=f"Python: {python_file}",
                    tofile=f"n8n: {n8n_file}",
                    lineterm=''
                )
                
                diff_text = ''.join(diff)
                return False, f"❌ MISMATCH DETECTED:\n\n{diff_text}"
                
        except FileNotFoundError as e:
            return False, f"❌ FILE NOT FOUND: {e}"
        except Exception as e:
            return False, f"❌ ERROR: {e}"
    
    def save_comparison_report(self, 
                               test_name: str,
                               match_status: bool,
                               report: str):
        """
        Save comparison report to file.
        
        Args:
            test_name: Name of the test
            match_status: Whether outputs matched
            report: Detailed comparison report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        status = "PASS" if match_status else "FAIL"
        filename = f"{test_name}_{status}_{timestamp}.txt"
        
        with open(self.comparison_dir / filename, 'w') as f:
            f.write(f"Test: {test_name}\n")
            f.write(f"Status: {status}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write("=" * 60 + "\n\n")
            f.write(report)
        
        print(f"Report saved: {self.comparison_dir / filename}")
    
    def run_verification_suite(self, test_configs: List[Dict[str, Any]]):
        """
        Run a suite of verification tests.
        
        Args:
            test_configs: List of test configurations
        """
        print("\n" + "=" * 60)
        print("RUNNING OUTPUT VERIFICATION SUITE")
        print("=" * 60 + "\n")
        
        results = []
        
        for config in test_configs:
            test_name = config['name']
            python_file = config['python_file']
            n8n_file = config['n8n_file']
            file_type = config.get('type', 'json')
            ignore_fields = config.get('ignore_fields', None)
            
            print(f"Testing: {test_name}")
            print(f"  Python: {python_file}")
            print(f"  n8n:    {n8n_file}")
            
            if file_type == 'json':
                match, report = self.compare_json_files(
                    python_file, n8n_file, ignore_fields
                )
            else:
                match, report = self.compare_text_files(python_file, n8n_file)
            
            results.append({
                'test': test_name,
                'passed': match
            })
            
            print(f"  Result: {report.split('\\n')[0]}\n")
            
            # Save detailed report
            self.save_comparison_report(test_name, match, report)
        
        # Summary
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in results if r['passed'])
        total = len(results)
        
        for result in results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"{status}: {result['test']}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! n8n outputs match Python exactly.")
            print("✅ READY FOR PRODUCTION DEPLOYMENT")
        else:
            print("\n⚠️ SOME TESTS FAILED! n8n outputs do not match Python.")
            print("❌ NOT READY FOR PRODUCTION - Fix discrepancies first")
        
        return passed == total


def main():
    """Main entry point for verification."""
    verifier = OutputVerifier()
    
    # Example test configurations
    test_configs = [
        {
            'name': 'weekly_report',
            'python_file': 'weekly_report.json',
            'n8n_file': 'weekly_report_n8n.json',
            'type': 'json',
            'ignore_fields': ['executionTime', 'timestamp']
        },
        {
            'name': 'monthly_report',
            'python_file': 'monthly_report.json',
            'n8n_file': 'monthly_report_n8n.json',
            'type': 'json',
            'ignore_fields': ['executionTime', 'timestamp']
        },
        # Add more test configurations as needed
    ]
    
    # Check if we have command line arguments for specific tests
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("Usage: python verify_outputs.py [test_name]")
            print("Available tests:")
            for config in test_configs:
                print(f"  - {config['name']}")
            return
        
        # Filter to specific test
        test_name = sys.argv[1]
        test_configs = [c for c in test_configs if c['name'] == test_name]
        
        if not test_configs:
            print(f"Error: Test '{test_name}' not found")
            return
    
    # Run verification
    success = verifier.run_verification_suite(test_configs)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
