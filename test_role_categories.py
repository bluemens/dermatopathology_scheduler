#!/usr/bin/env python3
"""
Test script for role categorization and SDO calculation.
"""

from src.data_models import Role, RoleCategory, Physician, VacationCategory


def test_role_categories():
    """Test that roles are properly categorized."""
    print("Testing role categorization...")
    
    # Test pathology roles
    pathology_roles = [Role.IMF, Role.DP, Role.DPD, Role.DPWG, Role.DPED, Role.EDUCATION]
    for role in pathology_roles:
        assert role.category == RoleCategory.PATHOLOGY, f"{role.value} should be PATHOLOGY"
        print(f"✓ {role.value} -> {role.category.value}")
    
    # Test clinical roles
    clinical_roles = [Role.OSD, Role.NVC]
    for role in clinical_roles:
        assert role.category == RoleCategory.CLINICAL, f"{role.value} should be CLINICAL"
        print(f"✓ {role.value} -> {role.category.value}")
    
    # Test administrative roles
    assert Role.ADMIN.category == RoleCategory.ADMINISTRATIVE, "ADMIN should be ADMINISTRATIVE"
    print(f"✓ {Role.ADMIN.value} -> {Role.ADMIN.category.value}")
    
    # Test research roles
    assert Role.RESEARCH.category == RoleCategory.RESEARCH, "RESEARCH should be RESEARCH"
    print(f"✓ {Role.RESEARCH.value} -> {Role.RESEARCH.category.value}")
    
    # Test time off roles
    time_off_roles = [Role.TRIP, Role.VACATION, Role.SDO]
    for role in time_off_roles:
        assert role.category == RoleCategory.TIME_OFF, f"{role.value} should be TIME_OFF"
        print(f"✓ {role.value} -> {role.category.value}")
    
    print("All role categorizations are correct!\n")


def test_sdo_calculation():
    """Test SDO calculation for different FTE levels."""
    print("Testing SDO calculation...")
    
    # Test full-time physician (FTE 1.0)
    full_time_physician = Physician.create_with_effective_fte_calculation(
        name="Dr. Full Time",
        fte_percentage=1.0,
        admin_plus_research_fte_percentage=0.2,
        vacation_category=VacationCategory.CATEGORY_25
    )
    
    assert full_time_physician.calculated_sdo_days == 0.0, "Full-time physician should have 0 SDO days"
    print(f"✓ Full-time physician (FTE 1.0): {full_time_physician.calculated_sdo_days} SDO days")
    
    # Test part-time physician (FTE 0.8)
    part_time_physician = Physician.create_with_effective_fte_calculation(
        name="Dr. Part Time",
        fte_percentage=0.8,
        admin_plus_research_fte_percentage=0.1,
        vacation_category=VacationCategory.CATEGORY_25
    )
    
    expected_sdo = (1.0 - 0.8) * 255  # (1 - FTE) * institutional days
    assert abs(part_time_physician.calculated_sdo_days - expected_sdo) < 1.0, f"Part-time physician should have ~{expected_sdo} SDO days"
    print(f"✓ Part-time physician (FTE 0.8): {part_time_physician.calculated_sdo_days} SDO days (expected ~{expected_sdo})")
    
    # Test very part-time physician (FTE 0.5)
    very_part_time_physician = Physician.create_with_effective_fte_calculation(
        name="Dr. Very Part Time",
        fte_percentage=0.5,
        admin_plus_research_fte_percentage=0.1,
        vacation_category=VacationCategory.CATEGORY_25
    )
    
    expected_sdo = (1.0 - 0.5) * 255  # (1 - FTE) * institutional days
    assert abs(very_part_time_physician.calculated_sdo_days - expected_sdo) < 1.0, f"Very part-time physician should have ~{expected_sdo} SDO days"
    print(f"✓ Very part-time physician (FTE 0.5): {very_part_time_physician.calculated_sdo_days} SDO days (expected ~{expected_sdo})")
    
    print("All SDO calculations are correct!\n")


def test_role_distribution():
    """Test that pathology roles are properly distributed."""
    print("Testing pathology role distribution...")
    
    physician = Physician.create_with_effective_fte_calculation(
        name="Dr. Test",
        fte_percentage=0.8,
        admin_plus_research_fte_percentage=0.1,
        vacation_category=VacationCategory.CATEGORY_25
    )
    
    # Get pathology roles
    pathology_roles = Role.get_roles_by_category(RoleCategory.PATHOLOGY)
    print(f"Pathology roles: {[role.value for role in pathology_roles]}")
    
    # Check that pathology days are distributed among pathology roles
    total_pathology_days = physician.total_number_of_pathology_days_per_year
    print(f"Total pathology days: {total_pathology_days}")
    
    # Check annual targets for pathology roles
    for role in pathology_roles:
        target = physician.annual_targets.get(role)
        if target:
            print(f"✓ {role.value}: {target.target_days} days")
        else:
            print(f"✗ {role.value}: No target found")
    
    print("Pathology role distribution test completed!\n")


def test_role_category_methods():
    """Test the role category helper methods."""
    print("Testing role category helper methods...")
    
    physician = Physician.create_with_effective_fte_calculation(
        name="Dr. Test",
        fte_percentage=0.8,
        admin_plus_research_fte_percentage=0.1,
        vacation_category=VacationCategory.CATEGORY_25
    )
    
    # Test getting roles by category
    pathology_roles = physician.get_roles_by_category(RoleCategory.PATHOLOGY)
    clinical_roles = physician.get_roles_by_category(RoleCategory.CLINICAL)
    administrative_roles = physician.get_roles_by_category(RoleCategory.ADMINISTRATIVE)
    research_roles = physician.get_roles_by_category(RoleCategory.RESEARCH)
    time_off_roles = physician.get_roles_by_category(RoleCategory.TIME_OFF)
    
    print(f"✓ Pathology roles: {[role.value for role in pathology_roles]}")
    print(f"✓ Clinical roles: {[role.value for role in clinical_roles]}")
    print(f"✓ Administrative roles: {[role.value for role in administrative_roles]}")
    print(f"✓ Research roles: {[role.value for role in research_roles]}")
    print(f"✓ Time off roles: {[role.value for role in time_off_roles]}")
    
    # Test getting target days for category
    pathology_target = physician.get_target_days_for_category(RoleCategory.PATHOLOGY)
    clinical_target = physician.get_target_days_for_category(RoleCategory.CLINICAL)
    
    print(f"✓ Pathology target days: {pathology_target}")
    print(f"✓ Clinical target days: {clinical_target}")
    
    print("Role category helper methods test completed!\n")


if __name__ == "__main__":
    print("Running role categorization and SDO calculation tests...\n")
    
    test_role_categories()
    test_sdo_calculation()
    test_role_distribution()
    test_role_category_methods()
    
    print("All tests completed successfully!") 