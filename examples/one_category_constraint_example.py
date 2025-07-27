#!/usr/bin/env python3
"""
Example demonstrating the one role per half day constraint (with DP exception).
"""

from datetime import date, timedelta
from src.data_models import (
    Role, RoleCategory, Physician, VacationCategory, 
    SchedulingInput, CoverageRequirement
)
from src.constraints import ConstraintBuilder
from ortools.sat.python import cp_model


def demonstrate_constraint_logic():
    """Demonstrate how the one role per half day constraint (with DP exception) works."""
    print("=== One Role Per Half Day Constraint (with DP Exception) Example ===\n")
    
    # Create a simple test case
    physician = Physician.create_with_effective_fte_calculation(
        name="Dr. Example",
        fte_percentage=0.8,
        admin_fte_percentage=0.1,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_25
    )
    
    # Create a single test day
    test_day = date(2024, 1, 1)
    calendar_days = [test_day]
    
    # Create all roles
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
        physicians=[physician],
        calendar_days=calendar_days,
        roles=roles,
        coverage_requirements=coverage_requirements
    )
    
    # Create model and variables
    model = cp_model.CpModel()
    variables = {}
    
    # Create variables
    for physician in input_data.physicians:
        for day in input_data.calendar_days:
            for role in input_data.roles:
                var_name = f"{physician.name}_{day.strftime('%Y-%m-%d')}_{role.value}"
                variables[var_name] = model.NewBoolVar(var_name)
    
    print(f"Created {len(variables)} variables for {physician.name} on {test_day}")
    
    # Add constraints
    constraint_builder = ConstraintBuilder(model, variables, input_data)
    constraint_builder.add_one_role_per_day_constraints()
    
    print(f"Added {model.NumConstraints()} constraints")
    
    # Demonstrate the constraint logic
    print("\n=== Constraint Logic ===")
    print("The constraint ensures that each physician can only be assigned to ONE role per half day,")
    print("EXCEPT for roles starting with 'DP' which can be assigned together.")
    print()
    
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
    
    # Show the DP roles
    dp_roles = [role for role in Role if role.value.startswith('dp')]
    non_dp_roles = [role for role in Role if not role.value.startswith('dp')]
    
    print("DP Roles (can be assigned together):")
    for role in dp_roles:
        print(f"  - {role.value}")
    
    print("\nNon-DP Roles (limited to one per half day):")
    for role in non_dp_roles:
        print(f"  - {role.value}")
    
    print("\n" + "="*50 + "\n")


def demonstrate_variable_structure():
    """Demonstrate the variable structure created by the constraint."""
    print("=== Variable Structure Example ===\n")
    
    # Create a simple test case
    physician = Physician.create_with_effective_fte_calculation(
        name="Dr. Test",
        fte_percentage=0.8,
        admin_fte_percentage=0.1,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_25
    )
    
    test_day = date(2024, 1, 1)
    day_str = test_day.strftime('%Y-%m-%d')
    
    print(f"Physician: {physician.name}")
    print(f"Day: {test_day}")
    print()
    
    print("Role Variables (one per role):")
    for role in Role:
        var_name = f"{physician.name}_{day_str}_{role.value}"
        print(f"  {var_name}")
    
    print("\nCategory Variables (created by constraint):")
    for category in RoleCategory:
        var_name = f"{physician.name}_{day_str}_{category.value}_active"
        print(f"  {var_name}")
    
    print("\nConstraint Logic:")
    print("1. Non-DP roles: At most one can be assigned per physician per half day")
    print("2. DP roles: Multiple can be assigned together (DP, DPD, DPWG, DPED)")
    print("3. Category constraints: At most one category can be active per half day")
    print("4. DP roles are all in the PATHOLOGY category")
    
    print("\n" + "="*50 + "\n")


def demonstrate_constraint_benefits():
    """Demonstrate the benefits of this constraint approach."""
    print("=== Constraint Benefits ===\n")
    
    print("Benefits of the one role per half day constraint (with DP exception):")
    print()
    
    print("1. DP Role Flexibility:")
    print("   - Physicians can be assigned to multiple DP roles simultaneously")
    print("   - Allows for complex pathology workflows")
    print("   - Supports education and training activities")
    print("   - Enables multitasking within pathology work")
    print()
    
    print("2. Prevents Conflicting Assignments:")
    print("   - Cannot be assigned to both clinical and pathology on same half day")
    print("   - Prevents administrative work during clinical time")
    print("   - Ensures proper time allocation")
    print("   - Maintains work-life balance")
    print()
    
    print("3. Realistic Scheduling:")
    print("   - Reflects actual pathology work patterns")
    print("   - Allows for multitasking within pathology domain")
    print("   - Prevents over-scheduling in other domains")
    print("   - Maintains focus on primary work type")
    print()
    
    print("4. Optimization Opportunities:")
    print("   - Solver can find optimal DP role combinations")
    print("   - Balances workload across different work types")
    print("   - Maximizes efficiency while respecting constraints")
    print("   - Allows for flexible pathology scheduling")
    
    print("\n" + "="*50 + "\n")


def demonstrate_dp_role_combinations():
    """Demonstrate valid DP role combinations."""
    print("=== Valid DP Role Combinations ===\n")
    
    dp_roles = [Role.DP, Role.DPD, Role.DPWG, Role.DPED]
    
    print("DP roles that can be assigned together:")
    for i, role1 in enumerate(dp_roles):
        for role2 in dp_roles[i+1:]:
            print(f"  ✓ {role1.value} + {role2.value}")
    
    print("\nExample combinations:")
    print("  ✓ DP + DPD (dermatopathology + person of day)")
    print("  ✓ DP + DPWG (dermatopathology + working group)")
    print("  ✓ DP + DPED (dermatopathology + education)")
    print("  ✓ DPD + DPWG (person of day + working group)")
    print("  ✓ DPD + DPED (person of day + education)")
    print("  ✓ DPWG + DPED (working group + education)")
    print()
    
    print("All DP roles can be combined in any combination!")
    print("This allows for flexible pathology scheduling.")
    
    print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    print("One Role Per Half Day Constraint (with DP Exception) Examples\n")
    
    demonstrate_constraint_logic()
    demonstrate_variable_structure()
    demonstrate_constraint_benefits()
    demonstrate_dp_role_combinations()
    
    print("Example completed!") 