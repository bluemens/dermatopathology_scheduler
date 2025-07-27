#!/usr/bin/env python3
"""
Test script to verify the enhanced Physician data model.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_models import Physician, Role, VacationCategory
from examples.sample_data import create_sample_physicians


def test_effective_fte_calculation():
    """Test the effective FTE calculation function."""
    print("\nTesting Effective FTE Calculation")
    print("=" * 35)
    
    # Test cases
    test_cases = [
        (1.0, 0.1, "Full-time with 10% admin"),
        (0.8, 0.05, "Part-time with 5% admin"),
        (1.0, 0.25, "Full-time with 25% admin"),
        (0.9, 0.05, "90% FTE with 5% admin"),
        (0.75, 0.0, "75% FTE with no admin"),
    ]
    
    for total_fte, admin_fte, description in test_cases:
        effective_fte = Physician.calculate_effective_clinical_fte(total_fte, admin_fte)
        print(f"\n{description}:")
        print(f"  Total FTE: {total_fte}")
        print(f"  Admin+Research FTE: {admin_fte}")
        print(f"  Effective Clinical FTE: {effective_fte} (calculated)")
        print(f"  Verification: {total_fte} - {admin_fte} = {effective_fte}")


def test_physician_creation_with_factory():
    """Test creating physicians using the factory method."""
    print("\nTesting Physician Creation with Factory Method")
    print("=" * 50)
    
    # Test creating a physician with automatic calculation of all derived values
    physician = Physician.create_with_effective_fte_calculation(
        name="Dr. Test Factory",
        fte_percentage=0.85,
        admin_plus_research_fte_percentage=0.15,
        vacation_category=VacationCategory.CATEGORY_25
    )
    
    print(f"Physician: {physician.name}")
    print(f"  Total FTE: {physician.fte_percentage}")
    print(f"  Admin+Research FTE: {physician.admin_plus_research_fte_percentage}")
    print(f"  Effective Clinical FTE: {physician.effective_clinical_fte_percentage} (auto-calculated)")
    print(f"  Vacation Category: {physician.vacation_category.name}")
    print(f"  Annual targets generated: {len(physician.annual_targets)} roles")
    
    print(f"\n  Calculated Values (all auto-generated):")
    print(f"    Workdays per year: {physician.total_number_of_days_per_year}")
    print(f"    Vacation days: {physician.total_number_of_vacation_days_per_year}")
    print(f"    Trip days: {physician.total_number_of_trip_days_per_year} (constant)")
    print(f"    Pathology days: {physician.total_number_of_pathology_days_per_year}")
    print(f"    OSD days: {physician.total_number_of_osd_days_per_year}")
    print(f"    NVC days: {physician.total_number_of_nvc_days_per_year}")
    print(f"    Clinical days: {physician.total_number_of_clinical_days_per_year}")
    
    # Verify that calculated values match property calculations
    print(f"\n  Verification (should match):")
    print(f"    Property workdays: {physician.calculated_workdays_after_vacation_trip}")
    print(f"    Property vacation: {physician.calculated_vacation_days}")
    print(f"    Property pathology: {physician.calculated_pathology_days}")
    print(f"    Property OSD: {physician.calculated_osd_days}")
    print(f"    Property NVC: {physician.calculated_nvc_days}")
    print(f"    Property clinic: {physician.calculated_clinic_days}")


def test_minimal_physician_creation():
    """Test creating physicians with minimal input."""
    print("\nTesting Minimal Physician Creation")
    print("=" * 40)
    
    # Test with just the essential inputs
    test_cases = [
        (1.0, 0.1, VacationCategory.CATEGORY_25, "Full-time with 10% admin"),
        (0.8, 0.05, VacationCategory.CATEGORY_22, "Part-time with 5% admin"),
        (0.75, 0.0, VacationCategory.CATEGORY_30, "75% FTE with no admin"),
    ]
    
    for fte, admin_fte, category, description in test_cases:
        print(f"\n{description}:")
        physician = Physician.create_with_effective_fte_calculation(
            name=f"Dr. {description}",
            fte_percentage=fte,
            admin_plus_research_fte_percentage=admin_fte,
            vacation_category=category
        )
        
        print(f"  Effective Clinical FTE: {physician.effective_clinical_fte_percentage}")
        print(f"  Workdays: {physician.total_number_of_days_per_year}")
        print(f"  Vacation: {physician.total_number_of_vacation_days_per_year}")
        print(f"  Pathology: {physician.total_number_of_pathology_days_per_year}")
        print(f"  OSD: {physician.total_number_of_osd_days_per_year}")
        print(f"  NVC: {physician.total_number_of_nvc_days_per_year}")
        print(f"  Clinic: {physician.total_number_of_clinical_days_per_year}")


def test_physician_calculations():
    """Test the physician calculations and validation."""
    print("Testing Physician Data Model (Half-Day Rounding)")
    print("=" * 50)
    
    # Test with sample physicians
    physicians = create_sample_physicians()
    
    for i, physician in enumerate(physicians, 1):
        print(f"\nPhysician {i}: {physician.name}")
        print(f"  Total FTE: {physician.fte_percentage}")
        print(f"  Admin+Research FTE: {physician.admin_plus_research_fte_percentage}")
        print(f"  Effective Clinical FTE: {physician.effective_clinical_fte_percentage}")
        print(f"  Vacation Category: {physician.vacation_category.name} ({physician.vacation_category.value} days)")
        print(f"  Institutional Days: {physician.workdays_per_year} (rounded to nearest half-day)")
        print(f"  Calculated Vacation Days: {physician.calculated_vacation_days} (rounded to nearest half-day)")
        print(f"  Workdays after Vacation+Trip: {physician.calculated_workdays_after_vacation_trip} (rounded to nearest half-day)")
        print(f"  Calculated OSD days: {physician.calculated_osd_days} (rounded to nearest half-day)")
        print(f"  Calculated Pathology days: {physician.calculated_pathology_days} (rounded to nearest half-day)")
        print(f"  Calculated NVC days: {physician.calculated_nvc_days} (rounded to nearest half-day)")
        print(f"  Calculated Clinic days: {physician.calculated_clinic_days} (rounded to nearest half-day)")
        
        # Validate derived values
        errors = physician.validate_derived_values()
        if errors:
            print(f"  Validation errors:")
            for error in errors:
                print(f"    - {error}")
        else:
            print(f"  ✓ All derived values are valid (within half-day tolerance)")
        
        # Show annual targets
        print(f"  Annual targets:")
        for role, target in physician.annual_targets.items():
            print(f"    {role.value}: {target.target_days} days")


def test_half_day_rounding():
    """Test the half-day rounding calculations."""
    print("\nTesting Half-Day Rounding Examples")
    print("=" * 40)
    
    # Test specific examples
    test_cases = [
        (0.9, VacationCategory.CATEGORY_25, "Dr. Test 90% FTE, Category 25"),
        (0.75, VacationCategory.CATEGORY_22, "Dr. Test 75% FTE, Category 22"),
        (0.85, VacationCategory.CATEGORY_22, "Dr. Test 85% FTE, Category 22"),
    ]
    
    for fte, category, description in test_cases:
        print(f"\n{description}:")
        
        # Calculate institutional days
        institutional_half_days = 255 * 2 * fte
        institutional_days = round(institutional_half_days) / 2
        print(f"  Institutional Days: 255 × {fte} = {255 * fte:.1f} → {institutional_days} (rounded to nearest half-day)")
        
        # Calculate vacation days
        vacation_half_days = category.value * 2 * fte
        vacation_days = round(vacation_half_days) / 2
        print(f"  Vacation Days: {category.value} × {fte} = {category.value * fte:.1f} → {vacation_days} (rounded to nearest half-day)")
        
        # Calculate workdays
        workdays = institutional_days - vacation_days - 18.0  # 18 trip days
        print(f"  Workdays: {institutional_days} - {vacation_days} - 18.0 = {workdays}")
        
        # Calculate OSD and Pathology
        osd_half_days = workdays * 2 * 0.10
        osd_days = round(osd_half_days) / 2
        pathology_half_days = workdays * 2 * 0.90
        pathology_days = round(pathology_half_days) / 2
        print(f"  OSD: {workdays} × 0.1 = {workdays * 0.1:.1f} → {osd_days} (rounded to nearest half-day)")
        print(f"  Pathology: {workdays} × 0.9 = {workdays * 0.9:.1f} → {pathology_days} (rounded to nearest half-day)")
        
        # Calculate NVC
        nvc_half_days = osd_days * 2 * 0.10
        nvc_days = round(nvc_half_days) / 2
        print(f"  NVC: {osd_days} × 0.1 = {osd_days * 0.1:.1f} → {nvc_days} (rounded to nearest half-day)")
        
        # Calculate Clinic
        clinic_days = osd_days - nvc_days
        print(f"  Clinic: {osd_days} - {nvc_days} = {clinic_days}")


def test_half_day_precision_examples():
    """Test specific half-day precision examples."""
    print("\nTesting Half-Day Precision Examples")
    print("=" * 45)
    
    # Test cases that should result in .5 day values
    test_cases = [
        (0.5, VacationCategory.CATEGORY_22, "50% FTE, Category 22"),
        (0.25, VacationCategory.CATEGORY_25, "25% FTE, Category 25"),
        (0.33, VacationCategory.CATEGORY_30, "33% FTE, Category 30"),
    ]
    
    for fte, category, description in test_cases:
        print(f"\n{description}:")
        
        # Create physician and show all calculated values
        physician = Physician.create_with_effective_fte_calculation(
            name=f"Dr. {description}",
            fte_percentage=fte,
            admin_plus_research_fte_percentage=0.0,  # No admin for simplicity
            vacation_category=category
        )
        
        print(f"  Effective Clinical FTE: {physician.effective_clinical_fte_percentage}")
        print(f"  Workdays: {physician.total_number_of_days_per_year}")
        print(f"  Vacation: {physician.total_number_of_vacation_days_per_year}")
        print(f"  Pathology: {physician.total_number_of_pathology_days_per_year}")
        print(f"  OSD: {physician.total_number_of_osd_days_per_year}")
        print(f"  NVC: {physician.total_number_of_nvc_days_per_year}")
        print(f"  Clinic: {physician.total_number_of_clinical_days_per_year}")
        
        # Check if any values have .5 precision
        values = [
            physician.total_number_of_days_per_year,
            physician.total_number_of_vacation_days_per_year,
            physician.total_number_of_pathology_days_per_year,
            physician.total_number_of_osd_days_per_year,
            physician.total_number_of_nvc_days_per_year,
            physician.total_number_of_clinical_days_per_year
        ]
        
        half_day_values = [v for v in values if v % 1 != 0]
        if half_day_values:
            print(f"  ✓ Half-day values found: {half_day_values}")
        else:
            print(f"  All values are whole days")


def test_validation_with_half_days():
    """Test validation with half-day precision."""
    print("\nTesting Validation with Half-Day Precision")
    print("=" * 50)
    
    # Create a physician with automatic calculations
    physician = Physician.create_with_effective_fte_calculation(
        name="Dr. Validation Test",
        fte_percentage=0.75,
        admin_plus_research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_22
    )
    
    print(f"Physician: {physician.name}")
    print(f"  Calculated values (should be valid):")
    print(f"    Workdays: {physician.total_number_of_days_per_year}")
    print(f"    Vacation: {physician.total_number_of_vacation_days_per_year}")
    print(f"    Pathology: {physician.total_number_of_pathology_days_per_year}")
    print(f"    OSD: {physician.total_number_of_osd_days_per_year}")
    print(f"    NVC: {physician.total_number_of_nvc_days_per_year}")
    print(f"    Clinic: {physician.total_number_of_clinical_days_per_year}")
    
    # Validate the derived values
    errors = physician.validate_derived_values()
    if errors:
        print(f"  Validation errors:")
        for error in errors:
            print(f"    - {error}")
    else:
        print(f"  ✓ All derived values are valid (within 0.5 day tolerance)")
    
    # Show property calculations for comparison
    print(f"\n  Property calculations (should match):")
    print(f"    Property workdays: {physician.calculated_workdays_after_vacation_trip}")
    print(f"    Property vacation: {physician.calculated_vacation_days}")
    print(f"    Property pathology: {physician.calculated_pathology_days}")
    print(f"    Property OSD: {physician.calculated_osd_days}")
    print(f"    Property NVC: {physician.calculated_nvc_days}")
    print(f"    Property clinic: {physician.calculated_clinic_days}")


def test_vacation_categories():
    """Test the vacation categories."""
    print("\nTesting Vacation Categories")
    print("=" * 30)
    
    for category in VacationCategory:
        print(f"  {category.name}: {category.value} days")


def test_role_enum():
    """Test the updated Role enum."""
    print("\nTesting Role Enum")
    print("=" * 20)
    
    roles = list(Role)
    for role in roles:
        print(f"  {role.value}")


if __name__ == "__main__":
    test_effective_fte_calculation()
    test_physician_creation_with_factory()
    test_minimal_physician_creation()
    test_physician_calculations()
    test_half_day_rounding()
    test_half_day_precision_examples()
    test_validation_with_half_days()
    test_vacation_categories()
    test_role_enum()
    print("\n✓ All tests completed!") 