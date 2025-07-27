"""
Unit tests for the physician scheduler.

This module contains basic tests to verify the functionality of the
scheduling system components.
"""

import unittest
from datetime import date, timedelta
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.data_models import (
    Physician, Role, AnnualTarget, CoverageRequirement, 
    SchedulingInput, Schedule, ScheduleAssignment, VacationCategory
)
from src.utils import validate_scheduling_input
from examples.sample_data import create_small_test_input


class TestDataModels(unittest.TestCase):
    """Test cases for data model classes."""
    
    def test_physician_creation(self):
        """Test creating a physician with valid data."""
        physician = Physician(
            name="Dr. Test",
            fte_percentage=0.8,
            admin_plus_research_fte_percentage=0.1,
            vacation_category=VacationCategory.CATEGORY_22,
            total_number_of_days_per_year=156,
            total_number_of_pathology_days_per_year=140,
            total_number_of_vacation_days_per_year=17,
            total_number_of_trip_days_per_year=18,
            total_number_of_clinical_days_per_year=14,
            total_number_of_nvc_days_per_year=2,
            total_number_of_osd_days_per_year=16,
            effective_clinical_fte_percentage=0.7,
            preferred_days_off={date(2024, 1, 1)},
            unavailable_dates={date(2024, 1, 1)},
            annual_targets={}
        )
        
        self.assertEqual(physician.name, "Dr. Test")
        self.assertEqual(physician.fte_percentage, 0.8)
        self.assertEqual(len(physician.unavailable_dates), 1)
        self.assertEqual(physician.effective_clinical_fte_percentage, 0.7)
    
    def test_physician_validation(self):
        """Test physician validation with invalid data."""
        # Test invalid FTE
        with self.assertRaises(ValueError):
            Physician(
                name="Dr. Test",
                fte_percentage=1.5,  # Invalid FTE
                admin_plus_research_fte_percentage=0.1,
                vacation_category=VacationCategory.CATEGORY_22,
                total_number_of_days_per_year=156,
                total_number_of_pathology_days_per_year=140,
                total_number_of_vacation_days_per_year=17,
                total_number_of_trip_days_per_year=18,
                total_number_of_clinical_days_per_year=14,
                total_number_of_nvc_days_per_year=2,
                total_number_of_osd_days_per_year=16,
                effective_clinical_fte_percentage=0.7,
                preferred_days_off=set(),
                unavailable_dates=set(),
                annual_targets={}
            )
        
        # Test empty name
        with self.assertRaises(ValueError):
            Physician(
                name="",  # Empty name
                fte_percentage=0.8,
                admin_plus_research_fte_percentage=0.1,
                vacation_category=VacationCategory.CATEGORY_22,
                total_number_of_days_per_year=156,
                total_number_of_pathology_days_per_year=140,
                total_number_of_vacation_days_per_year=17,
                total_number_of_trip_days_per_year=18,
                total_number_of_clinical_days_per_year=14,
                total_number_of_nvc_days_per_year=2,
                total_number_of_osd_days_per_year=16,
                effective_clinical_fte_percentage=0.7,
                preferred_days_off=set(),
                unavailable_dates=set(),
                annual_targets={}
            )
    
    def test_physician_derived_calculations(self):
        """Test the derived calculation methods."""
        physician = Physician(
            name="Dr. Test",
            fte_percentage=1.0,
            admin_plus_research_fte_percentage=0.1,
            vacation_category=VacationCategory.CATEGORY_25,
            total_number_of_days_per_year=189,
            total_number_of_pathology_days_per_year=170,
            total_number_of_vacation_days_per_year=23,
            total_number_of_trip_days_per_year=18,
            total_number_of_clinical_days_per_year=17,
            total_number_of_nvc_days_per_year=2,
            total_number_of_osd_days_per_year=19,
            effective_clinical_fte_percentage=0.9,
            preferred_days_off=set(),
            unavailable_dates=set(),
            annual_targets={}
        )
        
        # Test derived calculations with half-day rounding
        self.assertEqual(physician.workdays_per_year, 230)  # 255 * 0.9 = 229.5 → 230 (rounded)
        self.assertEqual(physician.calculated_vacation_days, 23)  # 25 * 0.9 = 22.5 → 23 (rounded)
        self.assertEqual(physician.calculated_workdays_after_vacation_trip, 189)  # 230 - 23 - 18
        self.assertEqual(physician.calculated_osd_days, 19)  # 189 * 0.1 = 18.9 → 19 (rounded)
        self.assertEqual(physician.calculated_pathology_days, 170)  # 189 * 0.9 = 170.1 → 170 (rounded)
        self.assertEqual(physician.calculated_nvc_days, 2)  # 19 * 0.1 = 1.9 → 2 (rounded)
        self.assertEqual(physician.calculated_clinic_days, 17)  # 19 - 2
    
    def test_annual_target_remaining_days(self):
        """Test calculation of remaining days for annual targets."""
        target = AnnualTarget(Role.CLINICAL, 100, 30)
        self.assertEqual(target.remaining_days, 70)
        
        target = AnnualTarget(Role.CLINICAL, 100, 100)
        self.assertEqual(target.remaining_days, 0)
        
        target = AnnualTarget(Role.CLINICAL, 100, 120)
        self.assertEqual(target.remaining_days, 0)
    
    def test_scheduling_input_creation(self):
        """Test creating a scheduling input with valid data."""
        physicians = [
            Physician(
                name="Dr. Test1",
                fte_percentage=1.0,
                admin_plus_research_fte_percentage=0.1,
                vacation_category=VacationCategory.CATEGORY_25,
                total_number_of_days_per_year=189,
                total_number_of_pathology_days_per_year=170,
                total_number_of_vacation_days_per_year=23,
                total_number_of_trip_days_per_year=18,
                total_number_of_clinical_days_per_year=17,
                total_number_of_nvc_days_per_year=2,
                total_number_of_osd_days_per_year=19,
                effective_clinical_fte_percentage=0.9,
                preferred_days_off=set(),
                unavailable_dates=set(),
                annual_targets={}
            )
        ]
        
        calendar_days = [date(2024, 1, 1), date(2024, 1, 2)]
        roles = [Role.CLINICAL, Role.ADMIN]
        coverage_requirements = {
            Role.CLINICAL: CoverageRequirement(Role.CLINICAL, 1),
            Role.ADMIN: CoverageRequirement(Role.ADMIN, 1)
        }
        
        input_data = SchedulingInput(
            physicians=physicians,
            calendar_days=calendar_days,
            roles=roles,
            coverage_requirements=coverage_requirements
        )
        
        self.assertEqual(len(input_data.physicians), 1)
        self.assertEqual(len(input_data.calendar_days), 2)
        self.assertEqual(len(input_data.roles), 2)
    
    def test_scheduling_input_validation(self):
        """Test scheduling input validation with invalid data."""
        # Test empty physicians list
        with self.assertRaises(ValueError):
            SchedulingInput(
                physicians=[],
                calendar_days=[date(2024, 1, 1)],
                roles=[Role.CLINICAL],
                coverage_requirements={Role.CLINICAL: CoverageRequirement(Role.CLINICAL, 1)}
            )
        
        # Test missing coverage requirement
        with self.assertRaises(ValueError):
            SchedulingInput(
                physicians=[Physician("Dr. Test", 1.0, set(), {})],
                calendar_days=[date(2024, 1, 1)],
                roles=[Role.CLINICAL],
                coverage_requirements={}  # Missing coverage requirement
            )


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""
    
    def test_validate_scheduling_input(self):
        """Test input validation function."""
        # Test valid input
        input_data = create_small_test_input()
        errors = validate_scheduling_input(input_data)
        self.assertEqual(len(errors), 0)
        
        # Test invalid input (duplicate physician names)
        physicians = [
            Physician(
                name="Dr. Test",
                fte_percentage=1.0,
                admin_plus_research_fte_percentage=0.1,
                vacation_category=VacationCategory.CATEGORY_25,
                total_number_of_days_per_year=189,
                total_number_of_pathology_days_per_year=170,
                total_number_of_vacation_days_per_year=23,
                total_number_of_trip_days_per_year=18,
                total_number_of_clinical_days_per_year=17,
                total_number_of_nvc_days_per_year=2,
                total_number_of_osd_days_per_year=19,
                effective_clinical_fte_percentage=0.9,
                preferred_days_off=set(),
                unavailable_dates=set(),
                annual_targets={}
            ),
            Physician(
                name="Dr. Test",  # Duplicate name
                fte_percentage=0.8,
                admin_plus_research_fte_percentage=0.05,
                vacation_category=VacationCategory.CATEGORY_22,
                total_number_of_days_per_year=156,
                total_number_of_pathology_days_per_year=140,
                total_number_of_vacation_days_per_year=17,
                total_number_of_trip_days_per_year=18,
                total_number_of_clinical_days_per_year=14,
                total_number_of_nvc_days_per_year=2,
                total_number_of_osd_days_per_year=16,
                effective_clinical_fte_percentage=0.75,
                preferred_days_off=set(),
                unavailable_dates=set(),
                annual_targets={}
            )
        ]
        
        calendar_days = [date(2024, 1, 1)]
        roles = [Role.CLINICAL]
        coverage_requirements = {Role.CLINICAL: CoverageRequirement(Role.CLINICAL, 1)}
        
        invalid_input = SchedulingInput(
            physicians=physicians,
            calendar_days=calendar_days,
            roles=roles,
            coverage_requirements=coverage_requirements
        )
        
        errors = validate_scheduling_input(invalid_input)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Duplicate physician name" in error for error in errors))


class TestSchedule(unittest.TestCase):
    """Test cases for Schedule class."""
    
    def test_schedule_creation(self):
        """Test creating a schedule with assignments."""
        physician = Physician(
            name="Dr. Test",
            fte_percentage=1.0,
            admin_plus_research_fte_percentage=0.1,
            vacation_category=VacationCategory.CATEGORY_25,
            total_number_of_days_per_year=189,
            total_number_of_pathology_days_per_year=170,
            total_number_of_vacation_days_per_year=23,
            total_number_of_trip_days_per_year=18,
            total_number_of_clinical_days_per_year=17,
            total_number_of_nvc_days_per_year=2,
            total_number_of_osd_days_per_year=19,
            effective_clinical_fte_percentage=0.9,
            preferred_days_off=set(),
            unavailable_dates=set(),
            annual_targets={}
        )
        assignment = ScheduleAssignment(
            physician=physician,
            day=date(2024, 1, 1),
            role=Role.CLINICAL
        )
        
        input_data = create_small_test_input()
        schedule = Schedule(assignments=[assignment], input_data=input_data)
        
        self.assertEqual(len(schedule.assignments), 1)
        self.assertEqual(schedule.assignments[0].physician.name, "Dr. Test")
    
    def test_schedule_filtering_methods(self):
        """Test schedule filtering methods."""
        physician1 = Physician(
            name="Dr. Test1",
            fte_percentage=1.0,
            admin_plus_research_fte_percentage=0.1,
            vacation_category=VacationCategory.CATEGORY_25,
            total_number_of_days_per_year=189,
            total_number_of_pathology_days_per_year=170,
            total_number_of_vacation_days_per_year=23,
            total_number_of_trip_days_per_year=18,
            total_number_of_clinical_days_per_year=17,
            total_number_of_nvc_days_per_year=2,
            total_number_of_osd_days_per_year=19,
            effective_clinical_fte_percentage=0.9,
            preferred_days_off=set(),
            unavailable_dates=set(),
            annual_targets={}
        )
        physician2 = Physician(
            name="Dr. Test2",
            fte_percentage=0.8,
            admin_plus_research_fte_percentage=0.05,
            vacation_category=VacationCategory.CATEGORY_22,
            total_number_of_days_per_year=156,
            total_number_of_pathology_days_per_year=140,
            total_number_of_vacation_days_per_year=17,
            total_number_of_trip_days_per_year=18,
            total_number_of_clinical_days_per_year=14,
            total_number_of_nvc_days_per_year=2,
            total_number_of_osd_days_per_year=16,
            effective_clinical_fte_percentage=0.75,
            preferred_days_off=set(),
            unavailable_dates=set(),
            annual_targets={}
        )
        
        assignment1 = ScheduleAssignment(physician1, date(2024, 1, 1), Role.CLINICAL)
        assignment2 = ScheduleAssignment(physician2, date(2024, 1, 1), Role.ADMIN)
        assignment3 = ScheduleAssignment(physician1, date(2024, 1, 2), Role.CLINICAL)
        
        input_data = create_small_test_input()
        schedule = Schedule(assignments=[assignment1, assignment2, assignment3], input_data=input_data)
        
        # Test filtering by day
        day_assignments = schedule.get_assignments_for_day(date(2024, 1, 1))
        self.assertEqual(len(day_assignments), 2)
        
        # Test filtering by physician
        physician_assignments = schedule.get_assignments_for_physician(physician1)
        self.assertEqual(len(physician_assignments), 2)
        
        # Test filtering by role
        role_assignments = schedule.get_assignments_for_role(Role.CLINICAL)
        self.assertEqual(len(role_assignments), 2)


if __name__ == '__main__':
    unittest.main() 