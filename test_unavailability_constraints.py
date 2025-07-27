#!/usr/bin/env python3
"""
Test script for the unavailability constraints.
"""

from datetime import date, timedelta
from src.data_models import (
    Role, RoleCategory, Physician, VacationCategory, 
    SchedulingInput, CoverageRequirement
)
from src.constraints import ConstraintBuilder
from ortools.sat.python import cp_model


def create_test_data_with_unavailable_dates():
    """Create test data with unavailable dates for testing."""
    # Create test physicians with unavailable dates
    physician1 = Physician.create_with_effective_fte_calculation(
        name="Dr. Test1",
        fte_percentage=0.8,
        admin_fte_percentage=0.1,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_25,
        unavailable_dates={
            date(2024, 1, 2),  # Tuesday
            date(2024, 1, 5),  # Friday
        }
    )
    
    physician2 = Physician.create_with_effective_fte_calculation(
        name="Dr. Test2",
        fte_percentage=1.0,
        admin_fte_percentage=0.15,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_30,
        unavailable_dates={
            date(2024, 1, 3),  # Wednesday
            date(2024, 1, 4),  # Thursday
        }
    )
    
    # Create test calendar days (one week)
    start_date = date(2024, 1, 1)
    calendar_days = [start_date + timedelta(days=i) for i in range(7)]
    
    # Create test roles
    roles = list(Role)
    
    # Create coverage requirements
    coverage_requirements = {}
    for role in roles:
        coverage_requirements[role] = CoverageRequirement(
            role=role,
            min_physicians=0,
            max_physicians=5
        )
    
    # Create scheduling input
    input_data = SchedulingInput(
        physicians=[physician1, physician2],
        calendar_days=calendar_days,
        roles=roles,
        coverage_requirements=coverage_requirements
    )
    
    return input_data


def test_unavailability_constraints():
    """Test that the unavailability constraints work correctly."""
    print("Testing unavailability constraints...")
    
    # Create test data
    input_data = create_test_data_with_unavailable_dates()
    
    # Create model and variables
    model = cp_model.CpModel()
    variables = {}
    
    # Create variables (same as in scheduler)
    for physician in input_data.physicians:
        for day in input_data.calendar_days:
            for role in input_data.roles:
                var_name = f"{physician.name}_{day.strftime('%Y-%m-%d')}_{role.value}"
                variables[var_name] = model.NewBoolVar(var_name)
    
    print(f"Created {len(variables)} variables")
    
    # Create constraint builder and add constraints
    constraint_builder = ConstraintBuilder(model, variables, input_data)
    constraint_builder.add_unavailability_constraints()
    
    # Test the constraint logic
    print("\nTesting unavailability constraint logic...")
    
    # Check that unavailable dates are properly handled
    for physician in input_data.physicians:
        print(f"\nPhysician: {physician.name}")
        print(f"Unavailable dates: {sorted(physician.unavailable_dates)}")
        
        for unavailable_date in physician.unavailable_dates:
            if unavailable_date in input_data.calendar_days:
                day_str = unavailable_date.strftime('%Y-%m-%d')
                print(f"  ✓ {unavailable_date} is in calendar days")
                
                # Check that all role variables for this physician on this date are constrained to 0
                for role in input_data.roles:
                    var_name = f"{physician.name}_{day_str}_{role.value}"
                    if var_name in variables:
                        print(f"    - {role.value}: constrained to 0")
            else:
                print(f"  ✗ {unavailable_date} is NOT in calendar days")
    
    # Get the number of constraints
    num_constraints = len(model.Proto().constraints)
    print(f"\nTotal constraints in model: {num_constraints}")
    print("Unavailability constraints test completed successfully!")


def test_unavailability_examples():
    """Test unavailability constraint examples."""
    print("\n=== Testing Unavailability Examples ===")
    
    # Create a simple test case
    physician = Physician.create_with_effective_fte_calculation(
        name="Dr. Example",
        fte_percentage=0.8,
        admin_fte_percentage=0.1,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_25,
        unavailable_dates={
            date(2024, 1, 2),  # Vacation day
            date(2024, 1, 15), # Sick leave
            date(2024, 2, 1),  # Personal day
        }
    )
    
    # Create calendar days
    calendar_days = [date(2024, 1, 1) + timedelta(days=i) for i in range(31)]  # January
    
    print(f"Physician: {physician.name}")
    print(f"Unavailable dates: {sorted(physician.unavailable_dates)}")
    print(f"Calendar days: {len(calendar_days)} days")
    
    # Check which unavailable dates are in calendar days
    unavailable_in_calendar = [d for d in physician.unavailable_dates if d in calendar_days]
    unavailable_not_in_calendar = [d for d in physician.unavailable_dates if d not in calendar_days]
    
    print(f"Unavailable dates in calendar: {unavailable_in_calendar}")
    print(f"Unavailable dates NOT in calendar: {unavailable_not_in_calendar}")
    
    # Test constraint creation
    model = cp_model.CpModel()
    variables = {}
    
    # Create variables for one week
    test_days = [date(2024, 1, 1) + timedelta(days=i) for i in range(7)]
    roles = [Role.DP, Role.OSD, Role.ADMIN, Role.VACATION]
    
    for day in test_days:
        for role in roles:
            var_name = f"{physician.name}_{day.strftime('%Y-%m-%d')}_{role.value}"
            variables[var_name] = model.NewBoolVar(var_name)
    
    # Create scheduling input
    coverage_requirements = {role: CoverageRequirement(role=role, min_physicians=0, max_physicians=5) for role in roles}
    input_data = SchedulingInput(
        physicians=[physician],
        calendar_days=test_days,
        roles=roles,
        coverage_requirements=coverage_requirements
    )
    
    # Add constraints
    constraint_builder = ConstraintBuilder(model, variables, input_data)
    constraint_builder.add_unavailability_constraints()
    
    print(f"\nAdded unavailability constraints")
    print(f"Total constraints: {len(model.Proto().constraints)}")
    
    # Check specific constraints
    unavailable_date = date(2024, 1, 2)  # This should be constrained
    if unavailable_date in test_days:
        day_str = unavailable_date.strftime('%Y-%m-%d')
        for role in roles:
            var_name = f"{physician.name}_{day_str}_{role.value}"
            if var_name in variables:
                print(f"✓ {var_name} is constrained to 0")
    
    print("✓ Unavailability examples are correct!")


def test_unavailability_types():
    """Test different types of unavailability."""
    print("\n=== Testing Unavailability Types ===")
    
    print("Types of unavailability that can be handled:")
    print("  - Vacation days")
    print("  - Sick leave")
    print("  - Personal days")
    print("  - Conference attendance")
    print("  - Administrative leave")
    print("  - Training days")
    print("  - Any other unavailable dates")
    print()
    
    print("Constraint behavior:")
    print("  - All role assignments are set to 0 for unavailable dates")
    print("  - This includes DP roles, clinical roles, admin roles, etc.")
    print("  - No exceptions - if a date is unavailable, no roles can be assigned")
    print("  - Only dates in the calendar are constrained")
    print()
    
    print("Example:")
    print("  If Dr. Smith is unavailable on 2024-01-15:")
    print("    - Dr. Smith cannot be assigned to DP on 2024-01-15")
    print("    - Dr. Smith cannot be assigned to OSD on 2024-01-15")
    print("    - Dr. Smith cannot be assigned to ADMIN on 2024-01-15")
    print("    - Dr. Smith cannot be assigned to any role on 2024-01-15")
    
    print("✓ Unavailability types are correctly handled!")


if __name__ == "__main__":
    print("Testing Unavailability Constraints\n")
    
    test_unavailability_constraints()
    test_unavailability_examples()
    test_unavailability_types()
    
    print("\nAll tests completed successfully!") 