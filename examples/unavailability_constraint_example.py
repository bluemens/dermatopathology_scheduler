#!/usr/bin/env python3
"""
Example demonstrating the unavailability constraints.
"""

from datetime import date, timedelta
from src.data_models import (
    Role, RoleCategory, Physician, VacationCategory, 
    SchedulingInput, CoverageRequirement
)
from src.constraints import ConstraintBuilder
from ortools.sat.python import cp_model


def demonstrate_unavailability_constraints():
    """Demonstrate how the unavailability constraints work."""
    print("=== Unavailability Constraints Example ===\n")
    
    # Create physicians with different unavailable dates
    physician1 = Physician.create_with_effective_fte_calculation(
        name="Dr. Smith",
        fte_percentage=0.8,
        admin_fte_percentage=0.1,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_25,
        unavailable_dates={
            date(2024, 1, 15),  # Vacation day
            date(2024, 1, 16),  # Vacation day
            date(2024, 1, 22),  # Conference
        }
    )
    
    physician2 = Physician.create_with_effective_fte_calculation(
        name="Dr. Johnson",
        fte_percentage=1.0,
        admin_fte_percentage=0.15,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_30,
        unavailable_dates={
            date(2024, 1, 8),   # Sick leave
            date(2024, 1, 9),   # Sick leave
            date(2024, 1, 29),  # Personal day
        }
    )
    
    # Create calendar days (January 2024)
    start_date = date(2024, 1, 1)
    calendar_days = [start_date + timedelta(days=i) for i in range(31)]
    
    # Create roles
    roles = [Role.DP, Role.OSD, Role.ADMIN, Role.VACATION, Role.RESEARCH]
    
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
    
    # Create model and variables
    model = cp_model.CpModel()
    variables = {}
    
    # Create variables
    for physician in input_data.physicians:
        for day in input_data.calendar_days:
            for role in input_data.roles:
                var_name = f"{physician.name}_{day.strftime('%Y-%m-%d')}_{role.value}"
                variables[var_name] = model.NewBoolVar(var_name)
    
    print(f"Created {len(variables)} variables")
    
    # Add constraints
    constraint_builder = ConstraintBuilder(model, variables, input_data)
    constraint_builder.add_unavailability_constraints()
    
    print(f"Added unavailability constraints")
    
    # Demonstrate the constraint logic
    print("\n=== Constraint Logic ===")
    print("The unavailability constraint ensures that physicians cannot be assigned")
    print("to any roles on their unavailable dates.")
    print()
    
    for physician in input_data.physicians:
        print(f"Physician: {physician.name}")
        print(f"Unavailable dates: {sorted(physician.unavailable_dates)}")
        
        for unavailable_date in physician.unavailable_dates:
            if unavailable_date in calendar_days:
                day_str = unavailable_date.strftime('%Y-%m-%d')
                print(f"  ✓ {unavailable_date} ({unavailable_date.strftime('%A')}): All roles constrained to 0")
                
                # Show which variables are constrained
                for role in roles:
                    var_name = f"{physician.name}_{day_str}_{role.value}"
                    if var_name in variables:
                        print(f"    - {role.value}: {var_name} = 0")
            else:
                print(f"  ✗ {unavailable_date}: Not in calendar (no constraint needed)")
        print()
    
    print("="*50 + "\n")


def demonstrate_unavailability_types():
    """Demonstrate different types of unavailability."""
    print("=== Types of Unavailability ===\n")
    
    print("The unavailability constraint can handle various types of unavailable dates:")
    print()
    
    unavailability_types = {
        "Vacation": "Planned time off for rest and relaxation",
        "Sick Leave": "Unplanned absence due to illness",
        "Personal Days": "Personal or family matters",
        "Conference": "Professional development and networking",
        "Administrative Leave": "Administrative duties or meetings",
        "Training": "Professional development and skill building",
        "Holidays": "Institutional holidays",
        "Other": "Any other unavailable dates"
    }
    
    for unavailability_type, description in unavailability_types.items():
        print(f"  • {unavailability_type}: {description}")
    
    print("\nAll types are handled the same way:")
    print("  - The date is added to the physician's unavailable_dates set")
    print("  - All role assignment variables for that date are set to 0")
    print("  - No exceptions or special handling required")
    
    print("\n" + "="*50 + "\n")


def demonstrate_constraint_impact():
    """Demonstrate the impact of unavailability constraints."""
    print("=== Impact of Unavailability Constraints ===\n")
    
    # Create a simple example
    physician = Physician.create_with_effective_fte_calculation(
        name="Dr. Example",
        fte_percentage=0.8,
        admin_fte_percentage=0.1,
        research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_25,
        unavailable_dates={
            date(2024, 1, 15),  # Monday
            date(2024, 1, 16),  # Tuesday
        }
    )
    
    # Create a week of calendar days
    calendar_days = [date(2024, 1, 15) + timedelta(days=i) for i in range(5)]  # Mon-Fri
    
    print(f"Physician: {physician.name}")
    print(f"Calendar: {calendar_days[0]} to {calendar_days[-1]}")
    print(f"Unavailable: {sorted(physician.unavailable_dates)}")
    print()
    
    print("Impact on scheduling:")
    print("  Monday (2024-01-15): UNAVAILABLE - No roles can be assigned")
    print("  Tuesday (2024-01-16): UNAVAILABLE - No roles can be assigned")
    print("  Wednesday (2024-01-17): Available - Can be assigned to roles")
    print("  Thursday (2024-01-18): Available - Can be assigned to roles")
    print("  Friday (2024-01-19): Available - Can be assigned to roles")
    print()
    
    print("Constraint behavior:")
    print("  - Monday and Tuesday: All role variables = 0")
    print("  - Wednesday through Friday: Role variables can be 0 or 1")
    print("  - Other constraints (one role per day, etc.) still apply")
    print("  - Coverage requirements must be met by other available physicians")
    
    print("\n" + "="*50 + "\n")


def demonstrate_constraint_benefits():
    """Demonstrate the benefits of unavailability constraints."""
    print("=== Benefits of Unavailability Constraints ===\n")
    
    print("1. Respects Physician Availability:")
    print("   - Ensures physicians are not scheduled when unavailable")
    print("   - Prevents scheduling conflicts with personal commitments")
    print("   - Maintains work-life balance")
    print()
    
    print("2. Handles Various Absence Types:")
    print("   - Vacation, sick leave, personal days")
    print("   - Professional development and conferences")
    print("   - Administrative duties and training")
    print("   - Any other unavailable dates")
    print()
    
    print("3. Simple and Flexible:")
    print("   - Just add dates to unavailable_dates set")
    print("   - No complex logic or special handling")
    print("   - Works with all role types")
    print()
    
    print("4. Integrates with Other Constraints:")
    print("   - Works with one role per day constraints")
    print("   - Works with coverage requirements")
    print("   - Works with annual targets")
    print("   - Maintains overall schedule feasibility")
    print()
    
    print("5. Realistic Scheduling:")
    print("   - Reflects actual physician availability")
    print("   - Prevents impossible assignments")
    print("   - Improves schedule quality and acceptance")
    
    print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    print("Unavailability Constraints Examples\n")
    
    demonstrate_unavailability_constraints()
    demonstrate_unavailability_types()
    demonstrate_constraint_impact()
    demonstrate_constraint_benefits()
    
    print("Example completed!") 