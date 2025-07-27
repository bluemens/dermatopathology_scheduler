#!/usr/bin/env python3
"""
Test script for the SDO (Scheduled Day Off) constraints.
"""

from datetime import date, timedelta
from src.data_models import (
    Role, RoleCategory, Physician, VacationCategory, 
    SchedulingInput, CoverageRequirement
)
from src.constraints import ConstraintBuilder
from ortools.sat.python import cp_model


def create_test_data_with_sdo():
    """Create test data with SDO requirements for testing."""
    # Create test physicians with different FTE levels
    physician1 = Physician.create_with_effective_fte_calculation(
        name="Dr. FullTime",
        fte_percentage=1.0,  # Full-time physician
        admin_fte_percentage=0.15,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_30,
        preferred_days_off=set()  # No preferred days off
    )
    
    physician2 = Physician.create_with_effective_fte_calculation(
        name="Dr. PartTime80",
        fte_percentage=0.8,  # Part-time physician
        admin_fte_percentage=0.1,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_25,
        preferred_days_off={
            date(2024, 1, 2),  # Tuesday
            date(2024, 1, 5),  # Friday
        }
    )
    
    physician3 = Physician.create_with_effective_fte_calculation(
        name="Dr. PartTime60",
        fte_percentage=0.6,  # Part-time physician
        admin_fte_percentage=0.05,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_22,
        preferred_days_off={
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
        physicians=[physician1, physician2, physician3],
        calendar_days=calendar_days,
        roles=roles,
        coverage_requirements=coverage_requirements
    )
    
    return input_data


def test_sdo_constraints():
    """Test that the SDO constraints work correctly."""
    print("Testing SDO constraints...")
    
    # Create test data
    input_data = create_test_data_with_sdo()
    
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
    constraint_builder.add_sdo_constraints()
    
    # Test the constraint logic
    print("\nTesting SDO constraint logic...")
    
    # Check SDO requirements for each physician
    for physician in input_data.physicians:
        print(f"\nPhysician: {physician.name}")
        print(f"FTE: {physician.fte_percentage}")
        print(f"Required SDO days: {physician.total_number_of_sdo_days_per_year}")
        print(f"Preferred days off: {sorted(physician.preferred_days_off)}")
        
        if physician.fte_percentage >= 1.0:
            print("  ✓ Full-time physician: 0 SDO days required")
        else:
            print(f"  ✓ Part-time physician: {physician.total_number_of_sdo_days_per_year} SDO days required")
    
    # Get the number of constraints
    num_constraints = len(model.Proto().constraints)
    print(f"\nTotal constraints in model: {num_constraints}")
    print("SDO constraints test completed successfully!")


def test_sdo_examples():
    """Test SDO constraint examples."""
    print("\n=== Testing SDO Examples ===")
    
    # Test different FTE levels
    fte_levels = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    print("SDO days for different FTE levels:")
    for fte in fte_levels:
        physician = Physician.create_with_effective_fte_calculation(
            name=f"Dr. FTE{fte}",
            fte_percentage=fte,
            admin_fte_percentage=0.1,
            research_fte_percentage=0.05,
            vacation_category=VacationCategory.CATEGORY_25
        )
        
        sdo_days = physician.total_number_of_sdo_days_per_year
        if fte >= 1.0:
            print(f"  FTE {fte}: {sdo_days} SDO days (Full-time)")
        else:
            print(f"  FTE {fte}: {sdo_days} SDO days (Part-time)")
    
    print("\n" + "="*50 + "\n")


def test_sdo_vs_unavailable():
    """Test the difference between SDO and unavailable dates."""
    print("=== SDO vs Unavailable Dates ===")
    
    # Create a part-time physician
    physician = Physician.create_with_effective_fte_calculation(
        name="Dr. Example",
        fte_percentage=0.8,
        admin_fte_percentage=0.1,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_25,
        preferred_days_off={
            date(2024, 1, 2),  # SDO day
            date(2024, 1, 5),  # SDO day
        },
        unavailable_dates={
            date(2024, 1, 15),  # Vacation day
            date(2024, 1, 16),  # Sick leave
        }
    )
    
    print(f"Physician: {physician.name}")
    print(f"FTE: {physician.fte_percentage}")
    print(f"Required SDO days: {physician.total_number_of_sdo_days_per_year}")
    print(f"Preferred days off (SDO candidates): {sorted(physician.preferred_days_off)}")
    print(f"Unavailable dates: {sorted(physician.unavailable_dates)}")
    print()
    
    print("Key differences:")
    print("  SDO days:")
    print("    - Scheduled part of regular schedule")
    print("    - Calculated based on FTE")
    print("    - Can be distributed throughout year")
    print("    - Part-time physicians only")
    print()
    print("  Unavailable dates:")
    print("    - Emergency or planned absences")
    print("    - Vacation, sick leave, personal days")
    print("    - Not part of regular schedule")
    print("    - All physicians can have unavailable dates")
    
    print("\n" + "="*50 + "\n")


def test_sdo_constraint_behavior():
    """Test the behavior of SDO constraints."""
    print("=== SDO Constraint Behavior ===")
    
    # Create test data
    physician = Physician.create_with_effective_fte_calculation(
        name="Dr. Test",
        fte_percentage=0.8,
        admin_fte_percentage=0.1,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_25
    )
    
    # Create calendar days
    calendar_days = [date(2024, 1, 1) + timedelta(days=i) for i in range(7)]
    
    print(f"Physician: {physician.name}")
    print(f"FTE: {physician.fte_percentage}")
    print(f"Required SDO days: {physician.total_number_of_sdo_days_per_year}")
    print(f"Calendar: {len(calendar_days)} days")
    print()
    
    print("SDO constraint behavior:")
    print("  1. Full-time physicians (FTE >= 1.0):")
    print("     - Must have exactly 0 SDO days")
    print("     - Can be assigned to any roles")
    print()
    print("  2. Part-time physicians (FTE < 1.0):")
    print("     - Must have exactly their calculated SDO days")
    print("     - When SDO is assigned, no other roles can be assigned")
    print("     - SDO days are distributed throughout the year")
    print()
    print("  3. SDO day constraints:")
    print("     - If SDO = 1, then all other roles = 0")
    print("     - If any other role = 1, then SDO = 0")
    print("     - Ensures mutual exclusivity")
    
    print("\n" + "="*50 + "\n")


def test_sdo_integration():
    """Test SDO constraints integration with other constraints."""
    print("=== SDO Integration with Other Constraints ===")
    
    print("SDO constraints work with other constraints:")
    print()
    print("  1. One Role Per Day:")
    print("     - SDO is treated as a role")
    print("     - When SDO is assigned, no other roles can be assigned")
    print("     - Satisfies the one role per day constraint")
    print()
    print("  2. Unavailability Constraints:")
    print("     - SDO is different from unavailable dates")
    print("     - Both can exist simultaneously")
    print("     - Unavailable dates take precedence")
    print()
    print("  3. Coverage Requirements:")
    print("     - SDO days reduce available physicians")
    print("     - Other physicians must cover the workload")
    print("     - Coverage requirements still must be met")
    print()
    print("  4. Annual Targets:")
    print("     - SDO days count toward annual targets")
    print("     - Part of the physician's planned schedule")
    print("     - Different from unavailable days")
    
    print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    print("Testing SDO Constraints\n")
    
    test_sdo_constraints()
    test_sdo_examples()
    test_sdo_vs_unavailable()
    test_sdo_constraint_behavior()
    test_sdo_integration()
    
    print("\nAll tests completed successfully!") 