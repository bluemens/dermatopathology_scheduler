#!/usr/bin/env python3
"""
Main execution script for the Physician Scheduler.

This script demonstrates how to use the OR-Tools based physician scheduler
to generate daily schedules for a group practice.
"""

import sys
import os
from datetime import date

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.scheduler import create_scheduler
from src.utils import export_schedule_to_csv, export_schedule_to_json
from examples.sample_data import create_sample_scheduling_input, create_small_test_input


def main():
    """Main function to run the physician scheduler."""
    print("Physician Scheduler - OR-Tools Implementation")
    print("=" * 50)
    
    # Choose between full sample data or small test data
    use_small_test = input("Use small test data? (y/n): ").lower().strip() == 'y'
    
    if use_small_test:
        print("Using small test data (2 physicians, 7 days)...")
        input_data = create_small_test_input()
    else:
        print("Using full sample data (4 physicians, 90 days)...")
        input_data = create_sample_scheduling_input()
    
    print(f"\nScheduling {len(input_data.physicians)} physicians")
    print(f"Calendar period: {input_data.calendar_days[0]} to {input_data.calendar_days[-1]}")
    print(f"Total days to schedule: {len(input_data.calendar_days)}")
    print(f"Roles: {[role.value for role in input_data.roles]}")
    
    # Create and run the scheduler
    try:
        scheduler = create_scheduler(input_data)
        
        # Set time limit based on data size
        time_limit = 60 if use_small_test else 300
        
        print(f"\nRunning scheduler with {time_limit}s time limit...")
        schedule = scheduler.run_scheduler(time_limit=time_limit)
        
        if schedule:
            print("\n" + "="*50)
            print("SCHEDULING COMPLETED SUCCESSFULLY!")
            print("="*50)
            
            # Export schedule to files
            timestamp = date.today().strftime("%Y%m%d")
            csv_filename = f"schedule_{timestamp}.csv"
            json_filename = f"schedule_{timestamp}.json"
            
            export_schedule_to_csv(schedule, csv_filename)
            export_schedule_to_json(schedule, json_filename)
            
            print(f"\nSchedule exported to:")
            print(f"  CSV: {csv_filename}")
            print(f"  JSON: {json_filename}")
            
            # Print solver statistics
            stats = scheduler.get_solver_statistics()
            if stats:
                print(f"\nSolver Statistics:")
                print(f"  Solve time: {stats.get('solve_time', 0):.2f} seconds")
                print(f"  Objective value: {stats.get('objective_value', 0)}")
                print(f"  Number of branches: {stats.get('num_branches', 0)}")
                print(f"  Number of conflicts: {stats.get('num_conflicts', 0)}")
            
        else:
            print("\n" + "="*50)
            print("SCHEDULING FAILED!")
            print("="*50)
            print("No valid schedule could be generated.")
            print("This could be due to:")
            print("- Infeasible constraints")
            print("- Insufficient time to find a solution")
            print("- Invalid input data")
            
    except Exception as e:
        print(f"\nError during scheduling: {e}")
        import traceback
        traceback.print_exc()


def run_quick_test():
    """Run a quick test with minimal data."""
    print("Running quick test...")
    
    input_data = create_small_test_input()
    scheduler = create_scheduler(input_data)
    schedule = scheduler.run_scheduler(time_limit=30)
    
    if schedule:
        print("Quick test completed successfully!")
        return True
    else:
        print("Quick test failed!")
        return False


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--quick-test":
        success = run_quick_test()
        sys.exit(0 if success else 1)
    else:
        main() 