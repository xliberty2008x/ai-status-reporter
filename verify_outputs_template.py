#!/usr/bin/env python3
"""
Universal Output Verification Tool for n8n Development
This template can be used in ANY project to verify n8n outputs match Python reference outputs
Copy this to your project and customize the test configurations
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import difflib


class OutputVerifier:
    """Verifies that n8n outputs match Python reference outputs exactly."""
    
    def __init__(self, 
                 python_dir: str = "test_outputs/python_reference",
                 n8n_dir: str = "test_outputs/n8n_results",
                 comparison_dir: str = "test_outputs/comparisons"):
        """
        Initialize verifier with directory paths.
        
        Args:
            python_dir: Directory containing Python reference outputs
            n8n_dir: Directory containing n8n workflow outputs
            comparison_dir: Directory for comparison reports
        """
        self.python_dir = Path(python_dir)
        self.n8n_dir = Path(n8n_dir)
        self.comparison_dir = Path(comparison_dir)
        
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
        # Default fields to ignore - customize per project
        default_ignore = ['executionTime', 'timestamp', 'generated_at', 
                         'createdAt', 'updatedAt', 'id', 'uuid']
        ignore_fields = ignore_fields or default_ignore
        
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
                          ignore_fields: List[str] = None,
                          sort_arrays: bool = False) -> Tuple[bool, str]:
        """
        Compare JSON outputs from Python and n8n.
        
        Args:
            python_file: Path to Python reference output
            n8n_file: Path to n8n output
            ignore_fields: Fields to ignore in comparison
            sort_arrays: Whether to sort arrays before comparison
        
        Returns:
            Tuple of (match_status, comparison_report)
        """
        try:
            # Load Python reference
            with open(self.python_dir / python_file, 'r', encoding='utf-8') as f:
                python_data = json.load(f)
            
            # Load n8n output
            with open(self.n8n_dir / n8n_file, 'r', encoding='utf-8') as f:
                n8n_data = json.load(f)
            
            # Normalize data
            python_normalized = self.normalize_data(python_data, ignore_fields)
            n8n_normalized = self.normalize_data(n8n_data, ignore_fields)
            
            # Sort arrays if requested
            if sort_arrays:
                python_normalized = self._sort_arrays(python_normalized)
                n8n_normalized = self._sort_arrays(n8n_normalized)
            
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
                
                # Also generate statistics
                stats = self._get_diff_statistics(python_normalized, n8n_normalized)
                
                return False, f"❌ MISMATCH DETECTED:\n\n{stats}\n\nDETAILED DIFF:\n{diff_text}"
                
        except FileNotFoundError as e:
            return False, f"❌ FILE NOT FOUND: {e}"
        except json.JSONDecodeError as e:
            return False, f"❌ JSON PARSE ERROR: {e}"
        except Exception as e:
            return False, f"❌ ERROR: {e}"
    
    def compare_text_files(self, 
                          python_file: str, 
                          n8n_file: str,
                          ignore_lines_with: List[str] = None) -> Tuple[bool, str]:
        """
        Compare text outputs from Python and n8n.
        
        Args:
            python_file: Path to Python reference output
            n8n_file: Path to n8n output
            ignore_lines_with: Ignore lines containing these strings
        
        Returns:
            Tuple of (match_status, comparison_report)
        """
        try:
            # Load files
            with open(self.python_dir / python_file, 'r', encoding='utf-8') as f:
                python_text = f.read()
            
            with open(self.n8n_dir / n8n_file, 'r', encoding='utf-8') as f:
                n8n_text = f.read()
            
            # Filter lines if needed
            if ignore_lines_with:
                python_lines = [
                    line for line in python_text.splitlines()
                    if not any(ignore in line for ignore in ignore_lines_with)
                ]
                n8n_lines = [
                    line for line in n8n_text.splitlines()
                    if not any(ignore in line for ignore in ignore_lines_with)
                ]
                python_text = '\n'.join(python_lines)
                n8n_text = '\n'.join(n8n_lines)
            
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
    
    def _sort_arrays(self, data: Any) -> Any:
        """Recursively sort arrays in data structure."""
        if isinstance(data, dict):
            return {k: self._sort_arrays(v) for k, v in data.items()}
        elif isinstance(data, list):
            # Try to sort if items are sortable
            try:
                return sorted([self._sort_arrays(item) for item in data], 
                            key=lambda x: json.dumps(x, sort_keys=True))
            except:
                return [self._sort_arrays(item) for item in data]
        else:
            return data
    
    def _get_diff_statistics(self, python_data: Any, n8n_data: Any) -> str:
        """Generate statistics about differences."""
        stats = []
        
        # Count items
        if isinstance(python_data, dict) and isinstance(n8n_data, dict):
            python_keys = set(python_data.keys())
            n8n_keys = set(n8n_data.keys())
            
            missing_in_n8n = python_keys - n8n_keys
            extra_in_n8n = n8n_keys - python_keys
            
            if missing_in_n8n:
                stats.append(f"Missing in n8n: {missing_in_n8n}")
            if extra_in_n8n:
                stats.append(f"Extra in n8n: {extra_in_n8n}")
            
            stats.append(f"Python keys: {len(python_keys)}, n8n keys: {len(n8n_keys)}")
        
        elif isinstance(python_data, list) and isinstance(n8n_data, list):
            stats.append(f"Python items: {len(python_data)}, n8n items: {len(n8n_data)}")
        
        return "\n".join(stats) if stats else "No structural differences found"
    
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
        
        with open(self.comparison_dir / filename, 'w', encoding='utf-8') as f:
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
        
        Returns:
            Boolean indicating if all tests passed
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
                    python_file, n8n_file, ignore_fields,
                    sort_arrays=config.get('sort_arrays', False)
                )
            else:
                match, report = self.compare_text_files(
                    python_file, n8n_file,
                    ignore_lines_with=config.get('ignore_lines_with', None)
                )
            
            results.append({
                'test': test_name,
                'passed': match
            })
            
            print(f"  Result: {report.split(chr(10))[0]}\n")
            
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
    
    # ============================================================
    # CUSTOMIZE THESE TEST CONFIGURATIONS FOR YOUR PROJECT
    # ============================================================
    test_configs = [
        {
            'name': 'example_test_1',
            'python_file': 'output1.json',      # Your Python output file
            'n8n_file': 'output1_n8n.json',     # Your n8n output file
            'type': 'json',
            'ignore_fields': ['timestamp', 'id'],  # Fields to ignore
            'sort_arrays': False  # Set to True if array order doesn't matter
        },
        {
            'name': 'example_test_2',
            'python_file': 'report.txt',
            'n8n_file': 'report_n8n.txt',
            'type': 'text',
            'ignore_lines_with': ['Generated on:', 'Time:']  # Lines to ignore
        },
        # Add more test configurations as needed
    ]
    
    # Check if we have command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("Usage: python verify_outputs.py [test_name]")
            print("\nAvailable tests:")
            for config in test_configs:
                print(f"  - {config['name']}")
            print("\nOptions:")
            print("  --help    Show this help message")
            print("  --init    Create directory structure")
            return
        
        if sys.argv[1] == '--init':
            print("Creating directory structure...")
            Path("test_outputs/python_reference").mkdir(parents=True, exist_ok=True)
            Path("test_outputs/n8n_results").mkdir(parents=True, exist_ok=True)
            Path("test_outputs/comparisons").mkdir(parents=True, exist_ok=True)
            print("✅ Directory structure created!")
            return
        
        # Filter to specific test
        test_name = sys.argv[1]
        test_configs = [c for c in test_configs if c['name'] == test_name]
        
        if not test_configs:
            print(f"Error: Test '{test_name}' not found")
            print("Run with --help to see available tests")
            return
    
    # Run verification
    success = verifier.run_verification_suite(test_configs)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
