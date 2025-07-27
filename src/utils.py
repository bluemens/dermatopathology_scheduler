"""
Utility functions for the physician scheduler.

This module contains helper functions for data validation, schedule export,
and other utility operations.
"""

import csv
import json
from typing import Dict, List, Any
from datetime import date, datetime
from .data_models import Schedule, ScheduleAssignment, Physician, Role, SchedulingInput


def validate_scheduling_input(input_data: SchedulingInput) -> List[str]:
    """
    Validate the scheduling input data and return any validation errors.
    
    Args:
        input_data: The scheduling input data to validate
    
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Validate physicians
    for physician in input_data.physicians:
        if physician.fte_percentage <= 0:
            errors.append(f"Physician {physician.name} has invalid FTE: {physician.fte_percentage}")
        
        # Check for duplicate physician names
        name_count = sum(1 for p in input_data.physicians if p.name == physician.name)
        if name_count > 1:
            errors.append(f"Duplicate physician name: {physician.name}")
        
        # Validate derived values for each physician
        derived_errors = physician.validate_derived_values()
        for error in derived_errors:
            errors.append(f"Physician {physician.name}: {error}")
    
    # Validate calendar days
    if len(input_data.calendar_days) != len(set(input_data.calendar_days)):
        errors.append("Duplicate calendar days found")
    
    # Validate coverage requirements
    for role, requirement in input_data.coverage_requirements.items():
        if requirement.min_physicians < 0:
            errors.append(f"Invalid minimum physicians for {role.value}: {requirement.min_physicians}")
        
        if requirement.max_physicians is not None and requirement.max_physicians < requirement.min_physicians:
            errors.append(f"Maximum physicians cannot be less than minimum for {role.value}")
    
    return errors


def export_schedule_to_csv(schedule: Schedule, filename: str) -> None:
    """
    Export the schedule to a CSV file.
    
    Args:
        schedule: The schedule to export
        filename: Output CSV filename
    """
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Date', 'Physician', 'Role']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for assignment in schedule.assignments:
            writer.writerow({
                'Date': assignment.day.strftime('%Y-%m-%d'),
                'Physician': assignment.physician.name,
                'Role': assignment.role.value
            })


def export_schedule_to_json(schedule: Schedule, filename: str) -> None:
    """
    Export the schedule to a JSON file.
    
    Args:
        schedule: The schedule to export
        filename: Output JSON filename
    """
    schedule_data = {
        'assignments': [
            {
                'physician': assignment.physician.name,
                'day': assignment.day.strftime('%Y-%m-%d'),
                'role': assignment.role.value
            }
            for assignment in schedule.assignments
        ],
        'metadata': {
            'total_assignments': len(schedule.assignments),
            'date_range': {
                'start': min(a.day for a in schedule.assignments).strftime('%Y-%m-%d'),
                'end': max(a.day for a in schedule.assignments).strftime('%Y-%m-%d')
            }
        }
    }
    
    with open(filename, 'w') as jsonfile:
        json.dump(schedule_data, jsonfile, indent=2)


def create_schedule_summary(schedule: Schedule) -> Dict[str, Any]:
    """
    Create a summary of the schedule with key statistics.
    
    Args:
        schedule: The schedule to summarize
    
    Returns:
        Dictionary containing schedule summary statistics
    """
    summary = {
        'total_assignments': len(schedule.assignments),
        'date_range': {
            'start': min(a.day for a in schedule.assignments).strftime('%Y-%m-%d'),
            'end': max(a.day for a in schedule.assignments).strftime('%Y-%m-%d')
        },
        'physician_stats': {},
        'role_stats': {},
        'daily_coverage': {}
    }
    
    # Physician statistics
    for physician in schedule.input_data.physicians:
        assignments = schedule.get_assignments_for_physician(physician)
        summary['physician_stats'][physician.name] = {
            'total_assignments': len(assignments),
            'role_breakdown': {}
        }
        
        for role in schedule.input_data.roles:
            role_assignments = [a for a in assignments if a.role == role]
            summary['physician_stats'][physician.name]['role_breakdown'][role.value] = len(role_assignments)
    
    # Role statistics
    for role in schedule.input_data.roles:
        assignments = schedule.get_assignments_for_role(role)
        summary['role_stats'][role.value] = {
            'total_assignments': len(assignments),
            'physician_breakdown': {}
        }
        
        for physician in schedule.input_data.physicians:
            physician_assignments = [a for a in assignments if a.physician == physician]
            summary['role_stats'][role.value]['physician_breakdown'][physician.name] = len(physician_assignments)
    
    # Daily coverage statistics
    for day in schedule.input_data.calendar_days:
        day_assignments = schedule.get_assignments_for_day(day)
        summary['daily_coverage'][day.strftime('%Y-%m-%d')] = {
            'total_physicians': len(day_assignments),
            'role_breakdown': {}
        }
        
        for role in schedule.input_data.roles:
            role_assignments = [a for a in day_assignments if a.role == role]
            summary['daily_coverage'][day.strftime('%Y-%m-%d')]['role_breakdown'][role.value] = len(role_assignments)
    
    return summary


def print_schedule_summary(schedule: Schedule) -> None:
    """
    Print a formatted summary of the schedule to the console.
    
    Args:
        schedule: The schedule to summarize
    """
    summary = create_schedule_summary(schedule)
    
    print("\n" + "="*60)
    print("SCHEDULE SUMMARY")
    print("="*60)
    
    print(f"Total Assignments: {summary['total_assignments']}")
    print(f"Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")
    
    print("\nPHYSICIAN STATISTICS:")
    print("-" * 30)
    for physician_name, stats in summary['physician_stats'].items():
        print(f"\n{physician_name}:")
        print(f"  Total Assignments: {stats['total_assignments']}")
        for role, count in stats['role_breakdown'].items():
            print(f"  {role}: {count}")
    
    print("\nROLE STATISTICS:")
    print("-" * 20)
    for role_name, stats in summary['role_stats'].items():
        print(f"\n{role_name}: {stats['total_assignments']} total assignments")
        for physician_name, count in stats['physician_breakdown'].items():
            print(f"  {physician_name}: {count}")


def calculate_schedule_metrics(schedule: Schedule) -> Dict[str, float]:
    """
    Calculate various metrics for the schedule quality.
    
    Args:
        schedule: The schedule to analyze
    
    Returns:
        Dictionary containing schedule quality metrics
    """
    metrics = {}
    
    # Calculate workload balance
    physician_assignments = {}
    for physician in schedule.input_data.physicians:
        assignments = schedule.get_assignments_for_physician(physician)
        physician_assignments[physician.name] = len(assignments)
    
    if physician_assignments:
        total_assignments = sum(physician_assignments.values())
        avg_assignments = total_assignments / len(physician_assignments)
        
        # Calculate standard deviation of assignments
        variance = sum((count - avg_assignments) ** 2 for count in physician_assignments.values()) / len(physician_assignments)
        std_dev = variance ** 0.5
        
        metrics['workload_balance'] = 1.0 - (std_dev / avg_assignments) if avg_assignments > 0 else 0.0
        metrics['total_assignments'] = total_assignments
        metrics['avg_assignments_per_physician'] = avg_assignments
        metrics['assignment_std_dev'] = std_dev
    
    # Calculate coverage consistency
    daily_coverage = []
    for day in schedule.input_data.calendar_days:
        day_assignments = schedule.get_assignments_for_day(day)
        daily_coverage.append(len(day_assignments))
    
    if daily_coverage:
        avg_daily_coverage = sum(daily_coverage) / len(daily_coverage)
        coverage_variance = sum((count - avg_daily_coverage) ** 2 for count in daily_coverage) / len(daily_coverage)
        coverage_std_dev = coverage_variance ** 0.5
        
        metrics['coverage_consistency'] = 1.0 - (coverage_std_dev / avg_daily_coverage) if avg_daily_coverage > 0 else 0.0
        metrics['avg_daily_coverage'] = avg_daily_coverage
        metrics['coverage_std_dev'] = coverage_std_dev
    
    return metrics 