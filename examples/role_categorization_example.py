#!/usr/bin/env python3
"""
Example demonstrating role categorization and SDO calculation.
"""

from src.data_models import Role, RoleCategory, Physician, VacationCategory, AnnualTarget


def demonstrate_role_categories():
    """Demonstrate how roles are categorized."""
    print("=== Role Categorization Demo ===\n")
    
    print("Pathology Roles:")
    pathology_roles = Role.get_roles_by_category(RoleCategory.PATHOLOGY)
    for role in pathology_roles:
        print(f"  - {role.value}")
    
    print("\nClinical Roles:")
    clinical_roles = Role.get_roles_by_category(RoleCategory.CLINICAL)
    for role in clinical_roles:
        print(f"  - {role.value}")
    
    print("\nAdministrative Roles:")
    administrative_roles = Role.get_roles_by_category(RoleCategory.ADMINISTRATIVE)
    for role in administrative_roles:
        print(f"  - {role.value}")
    
    print("\nResearch Roles:")
    research_roles = Role.get_roles_by_category(RoleCategory.RESEARCH)
    for role in research_roles:
        print(f"  - {role.value}")
    
    print("\nTime Off Roles:")
    time_off_roles = Role.get_roles_by_category(RoleCategory.TIME_OFF)
    for role in time_off_roles:
        print(f"  - {role.value}")
    
    print("\n" + "="*50 + "\n")


def demonstrate_sdo_calculation():
    """Demonstrate SDO calculation for different FTE levels."""
    print("=== SDO Calculation Demo ===\n")
    
    # Test different FTE levels
    fte_levels = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
    
    for fte in fte_levels:
        physician = Physician.create_with_effective_fte_calculation(
            name=f"Dr. FTE {fte}",
            fte_percentage=fte,
            admin_plus_research_fte_percentage=0.2,
            vacation_category=VacationCategory.CATEGORY_25
        )
        
        sdo_days = physician.calculated_sdo_days
        expected_sdo = (1.0 - fte) * 255 if fte < 1.0 else 0
        
        print(f"FTE {fte}: {sdo_days:.1f} SDO days (expected: {expected_sdo:.1f})")
    
    print("\n" + "="*50 + "\n")


def demonstrate_physician_calculation():
    """Demonstrate complete physician calculation with role categories."""
    print("=== Complete Physician Calculation Demo ===\n")
    
    # Create a part-time physician
    physician = Physician.create_with_effective_fte_calculation(
        name="Dr. Part Time Example",
        fte_percentage=0.8,
        admin_plus_research_fte_percentage=0.15,
        vacation_category=VacationCategory.CATEGORY_25
    )
    
    print(f"Physician: {physician.name}")
    print(f"FTE: {physician.fte_percentage}")
    print(f"Effective Clinical FTE: {physician.effective_clinical_fte_percentage:.3f}")
    print(f"Admin+Research FTE: {physician.admin_plus_research_fte_percentage}")
    print()
    
    print("Annual Day Allocations:")
    print(f"  Total workdays: {physician.total_number_of_days_per_year:.1f}")
    print(f"  Vacation days: {physician.total_number_of_vacation_days_per_year:.1f}")
    print(f"  Trip days: {physician.total_number_of_trip_days_per_year:.1f}")
    print(f"  SDO days: {physician.total_number_of_sdo_days_per_year:.1f}")
    print()
    
    print("Role Category Breakdown:")
    
    # Pathology roles
    pathology_roles = Role.get_roles_by_category(RoleCategory.PATHOLOGY)
    pathology_days = sum(physician.annual_targets.get(role, AnnualTarget(role, 0)).target_days 
                        for role in pathology_roles)
    print(f"  Pathology: {pathology_days:.1f} days")
    for role in pathology_roles:
        target = physician.annual_targets.get(role)
        if target and target.target_days > 0:
            print(f"    - {role.value}: {target.target_days:.1f} days")
    
    # Clinical roles
    clinical_roles = Role.get_roles_by_category(RoleCategory.CLINICAL)
    clinical_days = sum(physician.annual_targets.get(role, AnnualTarget(role, 0)).target_days 
                       for role in clinical_roles)
    print(f"  Clinical: {clinical_days:.1f} days")
    for role in clinical_roles:
        target = physician.annual_targets.get(role)
        if target and target.target_days > 0:
            print(f"    - {role.value}: {target.target_days:.1f} days")
    
    # Administrative roles
    admin_roles = Role.get_roles_by_category(RoleCategory.ADMINISTRATIVE)
    admin_days = sum(physician.annual_targets.get(role, AnnualTarget(role, 0)).target_days 
                    for role in admin_roles)
    print(f"  Administrative: {admin_days:.1f} days")
    for role in admin_roles:
        target = physician.annual_targets.get(role)
        if target and target.target_days > 0:
            print(f"    - {role.value}: {target.target_days:.1f} days")
    
    # Research roles
    research_roles = Role.get_roles_by_category(RoleCategory.RESEARCH)
    research_days = sum(physician.annual_targets.get(role, AnnualTarget(role, 0)).target_days 
                      for role in research_roles)
    print(f"  Research: {research_days:.1f} days")
    for role in research_roles:
        target = physician.annual_targets.get(role)
        if target and target.target_days > 0:
            print(f"    - {role.value}: {target.target_days:.1f} days")
    
    # Time off roles
    time_off_roles = Role.get_roles_by_category(RoleCategory.TIME_OFF)
    time_off_days = sum(physician.annual_targets.get(role, AnnualTarget(role, 0)).target_days 
                     for role in time_off_roles)
    print(f"  Time Off: {time_off_days:.1f} days")
    for role in time_off_roles:
        target = physician.annual_targets.get(role)
        if target and target.target_days > 0:
            print(f"    - {role.value}: {target.target_days:.1f} days")
    
    print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    print("Role Categorization and SDO Calculation Examples\n")
    
    demonstrate_role_categories()
    demonstrate_sdo_calculation()
    demonstrate_physician_calculation()
    
    print("Example completed!") 