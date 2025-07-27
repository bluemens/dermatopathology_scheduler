"""
Sample data for testing the physician scheduler.

This module provides example data structures that can be used to test
the scheduling system with realistic physician and practice data.
"""

from datetime import date, timedelta
from typing import List, Dict, Set

from src.data_models import (
    Physician, Role, AnnualTarget, CoverageRequirement, SchedulingInput, VacationCategory
)


def create_sample_physicians() -> List[Physician]:
    """
    Create a list of sample physicians with realistic data.
    
    Returns:
        List of Physician objects
    """
    physicians = []
    
    # Sample physician 1: Full-time clinical pathologist (Category 25)
    # Total FTE: 1.0, Admin+Research: 0.1, Effective Clinical: 0.9 (calculated)
    # All other values calculated automatically
    dr_smith = Physician.create_with_effective_fte_calculation(
        name="Dr. Smith",
        fte_percentage=1.0,
        admin_plus_research_fte_percentage=0.1,
        vacation_category=VacationCategory.CATEGORY_25,
        preferred_days_off={
            date(2024, 1, 15),  # MLK Day
            date(2024, 2, 19),  # Presidents Day
            date(2024, 3, 29),  # Good Friday
            date(2024, 5, 27),  # Memorial Day
            date(2024, 7, 4),   # Independence Day
        },
        unavailable_dates={
            date(2024, 1, 15),  # MLK Day
            date(2024, 2, 19),  # Presidents Day
            date(2024, 3, 29),  # Good Friday
            date(2024, 5, 27),  # Memorial Day
            date(2024, 7, 4),   # Independence Day
        }
    )
    physicians.append(dr_smith)
    
    # Sample physician 2: Part-time pathologist (Category 22)
    # Total FTE: 0.8, Admin+Research: 0.05, Effective Clinical: 0.75 (calculated)
    # All other values calculated automatically
    dr_johnson = Physician.create_with_effective_fte_calculation(
        name="Dr. Johnson",
        fte_percentage=0.8,
        admin_plus_research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_22,
        preferred_days_off={
            date(2024, 1, 15),  # MLK Day
            date(2024, 2, 19),  # Presidents Day
            date(2024, 3, 29),  # Good Friday
            date(2024, 5, 27),  # Memorial Day
            date(2024, 7, 4),   # Independence Day
        },
        unavailable_dates={
            date(2024, 1, 15),  # MLK Day
            date(2024, 2, 19),  # Presidents Day
            date(2024, 3, 29),  # Good Friday
            date(2024, 5, 27),  # Memorial Day
            date(2024, 7, 4),   # Independence Day
            date(2024, 6, 10),  # Personal day
            date(2024, 6, 11),  # Personal day
        }
    )
    physicians.append(dr_johnson)
    
    # Sample physician 3: Senior pathologist with more admin duties (Category 30)
    # Total FTE: 1.0, Admin+Research: 0.25, Effective Clinical: 0.75 (calculated)
    # All other values calculated automatically
    dr_williams = Physician.create_with_effective_fte_calculation(
        name="Dr. Williams",
        fte_percentage=1.0,
        admin_plus_research_fte_percentage=0.25,
        vacation_category=VacationCategory.CATEGORY_30,
        preferred_days_off={
            date(2024, 1, 15),  # MLK Day
            date(2024, 2, 19),  # Presidents Day
            date(2024, 3, 29),  # Good Friday
            date(2024, 5, 27),  # Memorial Day
            date(2024, 7, 4),   # Independence Day
        },
        unavailable_dates={
            date(2024, 1, 15),  # MLK Day
            date(2024, 2, 19),  # Presidents Day
            date(2024, 3, 29),  # Good Friday
            date(2024, 5, 27),  # Memorial Day
            date(2024, 7, 4),   # Independence Day
            date(2024, 4, 15),  # Conference
            date(2024, 4, 16),  # Conference
            date(2024, 4, 17),  # Conference
        }
    )
    physicians.append(dr_williams)
    
    # Sample physician 4: Junior pathologist (Category 22)
    # Total FTE: 0.9, Admin+Research: 0.05, Effective Clinical: 0.85 (calculated)
    # All other values calculated automatically
    dr_brown = Physician.create_with_effective_fte_calculation(
        name="Dr. Brown",
        fte_percentage=0.9,
        admin_plus_research_fte_percentage=0.05,
        vacation_category=VacationCategory.CATEGORY_22,
        preferred_days_off={
            date(2024, 1, 15),  # MLK Day
            date(2024, 2, 19),  # Presidents Day
            date(2024, 3, 29),  # Good Friday
            date(2024, 5, 27),  # Memorial Day
            date(2024, 7, 4),   # Independence Day
        },
        unavailable_dates={
            date(2024, 1, 15),  # MLK Day
            date(2024, 2, 19),  # Presidents Day
            date(2024, 3, 29),  # Good Friday
            date(2024, 5, 27),  # Memorial Day
            date(2024, 7, 4),   # Independence Day
        }
    )
    physicians.append(dr_brown)
    
    return physicians


def create_sample_calendar_days(start_date: date = date(2024, 1, 1), 
                               num_days: int = 90) -> List[date]:
    """
    Create a list of calendar days for scheduling.
    
    Args:
        start_date: Starting date for the calendar
        num_days: Number of days to include
    
    Returns:
        List of date objects
    """
    calendar_days = []
    current_date = start_date
    
    for _ in range(num_days):
        calendar_days.append(current_date)
        current_date += timedelta(days=1)
    
    return calendar_days


def create_sample_coverage_requirements() -> Dict[Role, CoverageRequirement]:
    """
    Create sample coverage requirements for each role.
    
    Returns:
        Dictionary mapping roles to coverage requirements
    """
    coverage_requirements = {
        Role.CLINICAL: CoverageRequirement(
            role=Role.CLINICAL,
            min_physicians=1,
            max_physicians=3
        ),
        Role.ADMIN: CoverageRequirement(
            role=Role.ADMIN,
            min_physicians=0,
            max_physicians=2
        ),
        Role.PATHOLOGY: CoverageRequirement(
            role=Role.PATHOLOGY,
            min_physicians=2,
            max_physicians=4
        ),
        Role.OSD: CoverageRequirement(
            role=Role.OSD,
            min_physicians=1,
            max_physicians=2
        ),
        Role.NVC: CoverageRequirement(
            role=Role.NVC,
            min_physicians=0,
            max_physicians=1
        ),
        Role.TRIP: CoverageRequirement(
            role=Role.TRIP,
            min_physicians=0,
            max_physicians=None  # No maximum for trip days
        ),
        Role.VACATION: CoverageRequirement(
            role=Role.VACATION,
            min_physicians=0,
            max_physicians=None  # No maximum for vacation
        ),
        Role.OFF: CoverageRequirement(
            role=Role.OFF,
            min_physicians=0,
            max_physicians=None  # No maximum for off days
        )
    }
    
    return coverage_requirements


def create_sample_scheduling_input() -> SchedulingInput:
    """
    Create a complete sample scheduling input for testing.
    
    Returns:
        SchedulingInput object with sample data
    """
    physicians = create_sample_physicians()
    calendar_days = create_sample_calendar_days()
    roles = list(Role)
    coverage_requirements = create_sample_coverage_requirements()
    
    return SchedulingInput(
        physicians=physicians,
        calendar_days=calendar_days,
        roles=roles,
        coverage_requirements=coverage_requirements
    )


def create_small_test_input() -> SchedulingInput:
    """
    Create a smaller test input for quick testing.
    
    Returns:
        SchedulingInput object with minimal data
    """
    # Create just 2 physicians for quick testing
    physicians = [
        Physician.create_with_effective_fte_calculation(
            name="Dr. Test1",
            fte_percentage=1.0,
            admin_plus_research_fte_percentage=0.1,
            vacation_category=VacationCategory.CATEGORY_25,
            preferred_days_off=set(),
            unavailable_dates=set()
        ),
        Physician.create_with_effective_fte_calculation(
            name="Dr. Test2",
            fte_percentage=0.8,
            admin_plus_research_fte_percentage=0.05,
            vacation_category=VacationCategory.CATEGORY_22,
            preferred_days_off=set(),
            unavailable_dates=set()
        )
    ]
    
    # Create just 7 days for quick testing
    calendar_days = create_sample_calendar_days(num_days=7)
    roles = list(Role)
    coverage_requirements = create_sample_coverage_requirements()
    
    return SchedulingInput(
        physicians=physicians,
        calendar_days=calendar_days,
        roles=roles,
        coverage_requirements=coverage_requirements
    ) 