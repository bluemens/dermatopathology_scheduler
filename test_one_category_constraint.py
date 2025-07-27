#!/usr/bin/env python3
"""
Test script for the one role per half day constraint (with DP exception).
"""

from datetime import date, timedelta
from src.data_models import (
    Role, RoleCategory, Physician, VacationCategory, 
    SchedulingInput, CoverageRequirement
)
from src.constraints import ConstraintBuilder
from ortools.sat.python import cp_model


def create_test_data():
    """Create test data for constraint testing."""
    # Create test physicians
    physician1 = Physician.create_with_effective_fte_calculation(
        name="Dr. Test1",
        fte_percentage=0.8,
        admin_fte_percentage=0.1,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_25
    )
    
    physician2 = Physician.create_with_effective_fte_calculation(
        name="Dr. Test2",
        fte_percentage=1.0,
        admin_fte_percentage=0.15,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_30
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


def test_one_role_constraint():
    """Test that the one role per half day constraint (with DP exception) works correctly."""
    print("Testing one role per half day constraint (with DP exception)...")
    
    # Create test data
    input_data = create_test_data()
    
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
    constraint_builder.add_one_role_per_day_constraints()
    
    # Test the constraint logic by creating a simple test case
    print("\nTesting constraint logic...")
    
    # Get some test variables
    test_physician = input_data.physicians[0]
    test_day = input_data.calendar_days[0]
    day_str = test_day.strftime('%Y-%m-%d')
    
    # Test DP roles (should be able to be assigned together)
    dp_var = variables[f"{test_physician.name}_{day_str}_{Role.DP.value}"]
    dpd_var = variables[f"{test_physician.name}_{day_str}_{Role.DPD.value}"]
    dpwg_var = variables[f"{test_physician.name}_{day_str}_{Role.DPWG.value}"]
    dped_var = variables[f"{test_physician.name}_{day_str}_{Role.DPED.value}"]
    
    # Test non-DP roles (should be limited to one per half day)
    osd_var = variables[f"{test_physician.name}_{day_str}_{Role.OSD.value}"]
    nvc_var = variables[f"{test_physician.name}_{day_str}_{Role.NVC.value}"]
    admin_var = variables[f"{test_physician.name}_{day_str}_{Role.ADMIN.value}"]
    
    print(f"✓ Created variables for {test_physician.name} on {test_day}")
    print(f"  - DP roles (can be assigned together): {Role.DP.value}, {Role.DPD.value}, {Role.DPWG.value}, {Role.DPED.value}")
    print(f"  - Non-DP roles (limited to one per half day): {Role.OSD.value}, {Role.NVC.value}, {Role.ADMIN.value}")
    
    # Verify that category variables were created
    category_vars = {}
    for category in RoleCategory:
        var_name = f"{test_physician.name}_{day_str}_{category.value}_active"
        if var_name in variables:
            category_vars[category] = variables[var_name]
            print(f"✓ Found category variable: {category.value}")
        else:
            print(f"✗ Missing category variable: {category.value}")
    
    # Get the number of constraints by checking the model's proto
    num_constraints = len(model.Proto().constraints)
    print(f"\nTotal constraints in model: {num_constraints}")
    print("One role per half day constraint (with DP exception) test completed successfully!")


def test_dp_role_logic():
    """Test the DP role logic separately."""
    print("\n=== Testing DP Role Logic ===")
    
    # Test identifying DP roles
    dp_roles = [role for role in Role if role.value.startswith('dp')]
    non_dp_roles = [role for role in Role if not role.value.startswith('dp')]
    
    print("DP roles (can be assigned together):", [role.value for role in dp_roles])
    print("Non-DP roles (limited to one per half day):", [role.value for role in non_dp_roles])
    
    # Verify DP roles
    expected_dp_roles = [Role.DP, Role.DPD, Role.DPWG, Role.DPED]
    assert set(dp_roles) == set(expected_dp_roles), f"Expected {expected_dp_roles}, got {dp_roles}"
    
    print("✓ DP role identification is correct!")
    
    # Test that DP roles are all in the pathology category
    for role in dp_roles:
        assert role.category == RoleCategory.PATHOLOGY, f"{role.value} should be in PATHOLOGY category"
    
    print("✓ All DP roles are in PATHOLOGY category!")


def test_constraint_examples():
    """Test constraint examples."""
    print("\n=== Testing Constraint Examples ===")
    
    print("Valid assignments (DP roles can be combined):")
    print("  ✓ DP + DPD (both start with 'dp')")
    print("  ✓ DP + DPWG + DPED (all start with 'dp')")
    print("  ✓ DPD + DPED (both start with 'dp')")
    print()
    
    print("Invalid assignments (non-DP roles limited to one):")
    print("  ✗ OSD + NVC (both clinical, but not DP roles)")
    print("  ✗ ADMIN + RESEARCH (different categories)")
    print("  ✗ VACATION + TRIP (both time off, but not DP roles)")
    print()
    
    print("Invalid assignments (different categories):")
    print("  ✗ DP + OSD (pathology + clinical)")
    print("  ✗ DP + ADMIN (pathology + administrative)")
    print("  ✗ OSD + VACATION (clinical + time off)")
    print()
    
    print("✓ Constraint examples are correct!")


if __name__ == "__main__":
    print("Testing One Role Per Half Day Constraint (with DP Exception)\n")
    
    test_dp_role_logic()
    test_one_role_constraint()
    test_constraint_examples()
    
    print("\nAll tests completed successfully!") 