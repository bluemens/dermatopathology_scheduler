"""
Main entry point for running the physician scheduler as a module.

Usage: python -m src
"""

from .scheduler import create_scheduler
from .utils import export_schedule_to_csv, export_schedule_to_json
from examples.sample_data import create_small_test_input
from datetime import date


def main():
    """Main function to run the scheduler."""
    print("Physician Scheduler - Running as module")
    print("=" * 40)
    
    # Use small test data for quick execution
    input_data = create_small_test_input()
    
    print(f"Scheduling {len(input_data.physicians)} physicians")
    print(f"Calendar period: {input_data.calendar_days[0]} to {input_data.calendar_days[-1]}")
    print(f"Total days to schedule: {len(input_data.calendar_days)}")
    
    # Create and run the scheduler
    try:
        scheduler = create_scheduler(input_data)
        schedule = scheduler.run_scheduler(time_limit=30)
        
        if schedule:
            print("\nScheduling completed successfully!")
            
            # Export schedule
            timestamp = date.today().strftime("%Y%m%d")
            csv_filename = f"schedule_{timestamp}.csv"
            json_filename = f"schedule_{timestamp}.json"
            
            export_schedule_to_csv(schedule, csv_filename)
            export_schedule_to_json(schedule, json_filename)
            
            print(f"Schedule exported to {csv_filename} and {json_filename}")
            
        else:
            print("Scheduling failed - no solution found")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 