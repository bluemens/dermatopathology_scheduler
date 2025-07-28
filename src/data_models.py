"""
Data models for the physician scheduler.

This module defines the core data structures used throughout the scheduling system.
"""

from dataclasses import dataclass
from typing import List, Dict, Set, Optional
from datetime import date, datetime
from enum import Enum


class HalfDayPeriod(Enum):
    """Enumeration of half-day periods."""
    MORNING = "morning"
    AFTERNOON = "afternoon"


class RoleCategory(Enum):
    """Categories for grouping roles by type."""
    PATHOLOGY = "pathology"
    CLINICAL = "clinical"
    ADMINISTRATIVE = "administrative"
    RESEARCH = "research"
    TIME_OFF = "time_off"


class Role(Enum):
    """Enumeration of assignable roles for physicians."""
    ADMIN = "admin"
    IMF = "imuno dermatology"
    DP = "dp_dermatopathology"
    DPD = "dpd_dermatopathology_person_of_day"
    DPWG = "dpwg_dermpath_working_group"
    DPED = "dped_dermpath_education"
    RESEARCH = "research"
    EDUCATION = "education"
    OSD = "osd"  # Outpatient Service Days / Clinic
    NVC = "nvc"  # Non-Visit Care
    TRIP = "trip"  # Trip days
    VACATION = "vacation"
    SDO = "scheduled_day_off"
    
    @property
    def category(self) -> RoleCategory:
        """Get the category for this role."""
        role_categories = {
            # Pathology roles
            Role.IMF: RoleCategory.PATHOLOGY,
            Role.DP: RoleCategory.PATHOLOGY,
            Role.DPD: RoleCategory.PATHOLOGY,
            Role.DPWG: RoleCategory.PATHOLOGY,
            Role.DPED: RoleCategory.PATHOLOGY,
            Role.EDUCATION: RoleCategory.PATHOLOGY,
            
            # Clinical roles
            Role.OSD: RoleCategory.CLINICAL,
            Role.NVC: RoleCategory.CLINICAL,
            
            # Administrative roles
            Role.ADMIN: RoleCategory.ADMINISTRATIVE,
            
            # Research roles
            Role.RESEARCH: RoleCategory.RESEARCH,
            
            # Time off roles
            Role.TRIP: RoleCategory.TIME_OFF,
            Role.VACATION: RoleCategory.TIME_OFF,
            Role.SDO: RoleCategory.TIME_OFF,
        }
        return role_categories[self]
    
    @classmethod
    def get_roles_by_category(cls, category: RoleCategory) -> List['Role']:
        """Get all roles in a specific category."""
        return [role for role in cls if role.category == category]


class VacationCategory(Enum):
    """Vacation categories with corresponding vacation days."""
    CATEGORY_22 = 22
    CATEGORY_25 = 25
    CATEGORY_30 = 30
    CATEGORY_35 = 35


@dataclass
class AnnualTarget:
    """Annual role targets for a physician."""
    role: Role
    target_days: float
    current_days: float = 0.0
    
    @property
    def remaining_days(self) -> float:
        """Calculate remaining days needed for this role."""
        return max(0.0, self.target_days - self.current_days)


@dataclass
class Physician:
    """Represents a physician with their scheduling constraints and preferences."""
    name: str
    fte_percentage: float  # Full-time equivalent percentage (0.0 to 1.0)
    admin_fte_percentage: float
    research_fte_percentage: float
    vacation_category: VacationCategory
    total_number_of_days_per_year: float
    total_number_of_pathology_days_per_year: float
    total_number_of_vacation_days_per_year: float
    total_number_of_trip_days_per_year: float
    total_number_of_clinical_days_per_year: float
    total_number_of_nvc_days_per_year: float
    total_number_of_osd_days_per_year: float
    total_number_of_sdo_days_per_year: float  # New field for SDO days
    total_number_of_admin_days_per_year: float
    total_number_of_research_days_per_year: float
    effective_clinical_fte_percentage: float
    preferred_days_off: Set[date]
    unavailable_dates: Set[date]  # Dates when physician cannot work
    annual_targets: Dict[Role, AnnualTarget]  # Annual targets for each role
    
    def __post_init__(self):
        """Validate physician data after initialization."""
        if not 0.0 <= self.fte_percentage <= 1.0:
            raise ValueError(f"FTE percentage must be between 0.0 and 1.0, got {self.fte_percentage}")
        
        if not 0.0 <= self.admin_fte_percentage <= 1.0:
            raise ValueError(f"Admin FTE percentage must be between 0.0 and 1.0, got {self.admin_fte_percentage}")
            
        if not 0.0 <= self.research_fte_percentage <= 1.0:
            raise ValueError(f"Research FTE percentage must be between 0.0 and 1.0, got {self.research_fte_percentage}")
        
        if not 0.0 <= self.effective_clinical_fte_percentage <= 1.0:
            raise ValueError(f"Effective Clinical FTE percentage must be between 0.0 and 1.0, got {self.effective_clinical_fte_percentage}")
        
        if not self.name.strip():
            raise ValueError("Physician name cannot be empty")
        
        # Validate that admin+research FTE doesn't exceed total FTE
        if self.admin_fte_percentage + self.research_fte_percentage > self.fte_percentage:
            raise ValueError(f"Admin+Research FTE ({self.admin_fte_percentage + self.research_fte_percentage}) cannot exceed total FTE ({self.fte_percentage})")
        
        # Validate that effective clinical FTE matches calculation
        expected_effective_clinical = self.calculate_effective_clinical_fte(self.fte_percentage, self.admin_fte_percentage, self.research_fte_percentage)
        if abs(self.effective_clinical_fte_percentage - expected_effective_clinical) > 0.001:
            raise ValueError(f"Effective Clinical FTE ({self.effective_clinical_fte_percentage}) should equal {expected_effective_clinical} (calculated from Total FTE {self.fte_percentage} - AdminFTE {self.admin_fte_percentage} - ResearchFTE {self.research_fte_percentage})")
        
        # Validate trip days is constant 18
        if self.total_number_of_trip_days_per_year != 18:
            raise ValueError(f"Trip days must be 18, got {self.total_number_of_trip_days_per_year}")
    
    @staticmethod
    def calculate_effective_clinical_fte(total_fte: float, admin_fte: float, research_fte: float) -> float:
        """
        Calculate effective clinical FTE from total FTE and admin+research FTE.
        
        Args:
            total_fte: Total FTE percentage (0.0 to 1.0)
            admin_fte: Admin FTE percentage (0.0 to 1.0)
            research_fte: Research FTE percentage (0.0 to 1.0)
        
        Returns:
            Effective clinical FTE percentage
        
        Raises:
            ValueError: If inputs are invalid or admin+research FTE exceeds total FTE
        """
        if not 0.0 <= total_fte <= 1.0:
            raise ValueError(f"Total FTE must be between 0.0 and 1.0, got {total_fte}")
        
        if not 0.0 <= admin_fte <= 1.0:
            raise ValueError(f"Admin FTE must be between 0.0 and 1.0, got {admin_fte}")
        
        if not 0.0 <= research_fte <= 1.0:
            raise ValueError(f"Research FTE must be between 0.0 and 1.0, got {research_fte}")
        
        if admin_fte + research_fte > total_fte:
            raise ValueError(f"Admin+Research FTE ({admin_fte + research_fte}) cannot exceed total FTE ({total_fte})")
        
        return total_fte - admin_fte - research_fte
    
    @classmethod
    def create_with_effective_fte_calculation(cls, name: str, fte_percentage: float, 
                                            admin_fte_percentage: float,
                                            research_fte_percentage: float,
                                            vacation_category: VacationCategory,
                                            preferred_days_off: Set[date] = None,
                                            unavailable_dates: Set[date] = None,
                                            annual_targets: Dict[Role, AnnualTarget] = None) -> 'Physician':
        """
        Create a Physician instance with automatic calculation of all derived values.
        
        This method calculates all derived day values based on:
        - Effective Clinical FTE (calculated from total FTE and admin+research FTE)
        - Vacation category and FTE
        - Half-day rounding for all calculations
        
        Args:
            name: Physician name
            fte_percentage: Total FTE percentage
            admin_plus_research_fte_percentage: Admin+Research FTE percentage
            vacation_category: Vacation category
            preferred_days_off: Set of preferred days off (default: empty set)
            unavailable_dates: Set of unavailable dates (default: empty set)
            annual_targets: Annual targets (will be generated if None)
        
        Returns:
            Physician instance with all derived values calculated automatically
        """
        # Calculate effective clinical FTE
        effective_clinical_fte = cls.calculate_effective_clinical_fte(fte_percentage, admin_fte_percentage, research_fte_percentage)
        
        # Create a temporary physician instance to access the property calculations
        temp_physician = cls(
            name=name,
            fte_percentage=fte_percentage,
            admin_fte_percentage=admin_fte_percentage,
            research_fte_percentage=research_fte_percentage,
            vacation_category=vacation_category,
            total_number_of_days_per_year=0.0,  # Will be calculated
            total_number_of_pathology_days_per_year=0.0,  # Will be calculated
            total_number_of_vacation_days_per_year=0.0,  # Will be calculated
            total_number_of_trip_days_per_year=18.0,  # Constant
            total_number_of_clinical_days_per_year=0.0,  # Will be calculated
            total_number_of_nvc_days_per_year=0.0,  # Will be calculated
            total_number_of_osd_days_per_year=0.0,  # Will be calculated
            total_number_of_sdo_days_per_year=0.0,  # Will be calculated
            total_number_of_admin_days_per_year=0.0,  # Will be calculated
            total_number_of_research_days_per_year=0.0,  # Will be calculated
            effective_clinical_fte_percentage=effective_clinical_fte,
            preferred_days_off=preferred_days_off or set(),
            unavailable_dates=unavailable_dates or set(),
            annual_targets=annual_targets or {}
        )
        
        # Calculate all derived values using the property functions
        calculated_workdays = temp_physician.calculated_workdays_after_vacation_trip
        calculated_vacation_days = temp_physician.calculated_vacation_days
        calculated_osd_days = temp_physician.calculated_osd_days
        calculated_pathology_days = temp_physician.calculated_pathology_days
        calculated_nvc_days = temp_physician.calculated_nvc_days
        calculated_clinic_days = temp_physician.calculated_clinic_days
        calculated_sdo_days = temp_physician.calculated_sdo_days
        calculated_admin_days = temp_physician.calculated_admin_days
        calculated_research_days = temp_physician.calculated_research_days
        
        # Create the final physician instance with calculated values
        physician = cls(
            name=name,
            fte_percentage=fte_percentage,
            admin_fte_percentage=admin_fte_percentage,
            research_fte_percentage=research_fte_percentage,
            vacation_category=vacation_category,
            total_number_of_days_per_year=calculated_workdays,
            total_number_of_pathology_days_per_year=calculated_pathology_days,
            total_number_of_vacation_days_per_year=calculated_vacation_days,
            total_number_of_trip_days_per_year=18.0,  # Constant
            total_number_of_clinical_days_per_year=calculated_clinic_days,
            total_number_of_nvc_days_per_year=calculated_nvc_days,
            total_number_of_osd_days_per_year=calculated_osd_days,
            total_number_of_sdo_days_per_year=calculated_sdo_days,
            total_number_of_admin_days_per_year=calculated_admin_days,
            total_number_of_research_days_per_year=calculated_research_days,  
            effective_clinical_fte_percentage=effective_clinical_fte,
            preferred_days_off=preferred_days_off or set(),
            unavailable_dates=unavailable_dates or set(),
            annual_targets=annual_targets or {}
        )
        
        # Generate annual targets if not provided
        if not annual_targets:
            physician.annual_targets = physician.get_annual_targets_from_derived_values()
        
        return physician
    
    @property
    def workdays_per_year(self) -> float:
        """Calculate total workdays per year based on total FTE."""
        # Assuming 255 working days per year (5 days/week * 52 weeks) - 6 Mayo holidays
        # Convert to half-days, calculate, then round to nearest half-day
        half_days = 255 * 2 * self.fte_percentage
        return round(half_days) / 2
    
    @property
    def calculated_vacation_days(self) -> float:
        """Calculate vacation days based on category and FTE."""
        # Vacation days are based on category, prorated by effective clinical FTE
        # Convert to half-days, calculate, then round to nearest half-day
        base_vacation_days = self.vacation_category.value
        half_days = base_vacation_days * 2 * self.effective_clinical_fte_percentage
        return round(half_days) / 2
    
    @property
    def calculated_sdo_days(self) -> float:
        """
        Calculate Scheduled Day Off (SDO) days based on FTE.
        
        SDO days are for part-time physicians. Full-time physicians (FTE 1.0) have 0 SDO days.
        Part-time physicians get SDO days proportional to their reduced FTE.
        """
        if self.fte_percentage >= 1.0:
            return 0.0
        
        # For part-time physicians, calculate SDO days
        # Assuming 255 institutional days per year
        # SDO = (1 - FTE) * institutional days
        institutional_days = 255
        sdo_days = (1.0 - self.fte_percentage) * institutional_days
        
        # Convert to half-days, then round to nearest half-day
        half_days = sdo_days * 2
        return round(half_days) / 2
    
    @property
    def calculated_workdays_after_vacation_trip(self) -> float:
        """Calculate workdays after subtracting vacation and trip days."""
        # Workdays = Institutional Days - Vacation - Trip
        # All calculations done in half-days for precision
        institutional_half_days = 255 * 2 * self.fte_percentage
        vacation_half_days = self.vacation_category.value * 2 * self.effective_clinical_fte_percentage
        trip_half_days = 18 * 2  # Trip days are constant 18 full days = 36 half-days
        
        total_half_days = institutional_half_days - vacation_half_days - trip_half_days
        return round(total_half_days) / 2
    
    @property
    def calculated_osd_days(self) -> float:
        """Calculate Outpatient Service Days (OSDs) = 10% of Workdays."""
        workdays = self.calculated_workdays_after_vacation_trip
        # Convert to half-days, calculate 10%, then round to nearest half-day
        half_days = workdays * 2 * 0.10
        return round(half_days) / 2
    
    @property
    def calculated_pathology_days(self) -> float:
        """Calculate Pathology days = 90% of Workdays."""
        workdays = self.calculated_workdays_after_vacation_trip
        # Convert to half-days, calculate 90%, then round to nearest half-day
        half_days = workdays * 2 * 0.90
        return round(half_days) / 2
    
    @property
    def calculated_nvc_days(self) -> float:
        """Calculate Non-Visit Care days (NVCs) = 10% of OSDs."""
        osd_days = self.calculated_osd_days
        # Convert to half-days, calculate 10%, then round to nearest half-day
        half_days = osd_days * 2 * 0.10
        return round(half_days) / 2
    
    @property
    def calculated_clinic_days(self) -> float:
        """Calculate Clinic days = OSDs - NVCs."""
        osd_days = self.calculated_osd_days
        nvc_days = self.calculated_nvc_days
        # Convert to half-days, subtract, then round to nearest half-day
        half_days = (osd_days - nvc_days) * 2
        return round(half_days) / 2
    
    @property
    def calculated_admin_days(self) -> float:
        """Calculate Admin days = 255 * 2 * admin_plus_research_fte_percentage."""
        return 255 * 2 * self.admin_fte_percentage
    
    @property 
    def calculated_research_days(self) -> float:
        """Calculate Research days = 255 * 2 * research_fte_percentage."""
        return 255 * 2 * self.research_fte_percentage
    
    def validate_derived_values(self) -> List[str]:
        """
        Validate that the provided derived values match calculated values.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check if provided values match calculated values (with tolerance for half-day rounding)
        tolerance = 0.5  # Allow 0.5 day difference due to half-day rounding
        
        # Validate vacation days
        if abs(self.total_number_of_vacation_days_per_year - self.calculated_vacation_days) > tolerance:
            errors.append(f"Vacation days mismatch: provided {self.total_number_of_vacation_days_per_year}, calculated {self.calculated_vacation_days}")
        
        # Validate OSD days
        if abs(self.total_number_of_osd_days_per_year - self.calculated_osd_days) > tolerance:
            errors.append(f"OSD days mismatch: provided {self.total_number_of_osd_days_per_year}, calculated {self.calculated_osd_days}")
        
        # Validate pathology days
        if abs(self.total_number_of_pathology_days_per_year - self.calculated_pathology_days) > tolerance:
            errors.append(f"Pathology days mismatch: provided {self.total_number_of_pathology_days_per_year}, calculated {self.calculated_pathology_days}")
        
        # Validate NVC days
        if abs(self.total_number_of_nvc_days_per_year - self.calculated_nvc_days) > tolerance:
            errors.append(f"NVC days mismatch: provided {self.total_number_of_nvc_days_per_year}, calculated {self.calculated_nvc_days}")
        
        # Validate SDO days
        if abs(self.total_number_of_sdo_days_per_year - self.calculated_sdo_days) > tolerance:
            errors.append(f"SDO days mismatch: provided {self.total_number_of_sdo_days_per_year}, calculated {self.calculated_sdo_days}")
        
        # Check that clinical days = OSD days - NVC days
        expected_clinical = self.total_number_of_osd_days_per_year - self.total_number_of_nvc_days_per_year
        if abs(self.total_number_of_clinical_days_per_year - expected_clinical) > tolerance:
            errors.append(f"Clinical days mismatch: provided {self.total_number_of_clinical_days_per_year}, should be OSD({self.total_number_of_osd_days_per_year}) - NVC({self.total_number_of_nvc_days_per_year}) = {expected_clinical}")
        
        return errors
    
    def get_annual_targets_from_derived_values(self) -> Dict[Role, AnnualTarget]:
        """
        Generate annual targets based on the derived values.
        
        Returns:
            Dictionary of Role to AnnualTarget mappings
        """
        # Calculate admin days with half-day rounding
        admin_half_days = 255 * 2 * self.admin_fte_percentage
        admin_days = round(admin_half_days) / 2
        
        # Calculate research days (part of admin+research FTE)
        research_half_days = 255 * 2 * self.research_fte_percentage  # Assuming 50% of admin+research is research
        research_days = round(research_half_days) / 2
        
        targets = {
            # Pathology roles
            Role.IMF: AnnualTarget(Role.IMF, 0),  # Will be calculated based on pathology distribution
            Role.DP: AnnualTarget(Role.DP, 0),  # Will be calculated based on pathology distribution
            Role.DPD: AnnualTarget(Role.DPD, 0),  # Will be calculated based on pathology distribution
            Role.DPWG: AnnualTarget(Role.DPWG, 0),  # Will be calculated based on pathology distribution
            Role.DPED: AnnualTarget(Role.DPED, 0),  # Will be calculated based on pathology distribution
            Role.EDUCATION: AnnualTarget(Role.EDUCATION, 0),  # Will be calculated based on pathology distribution
            
            # Clinical roles
            Role.OSD: AnnualTarget(Role.OSD, self.total_number_of_osd_days_per_year),
            Role.NVC: AnnualTarget(Role.NVC, self.total_number_of_nvc_days_per_year),
            
            # Administrative and research roles
            Role.ADMIN: AnnualTarget(Role.ADMIN, admin_days),
            Role.RESEARCH: AnnualTarget(Role.RESEARCH, research_days),
            
            # Time off roles
            Role.VACATION: AnnualTarget(Role.VACATION, self.total_number_of_vacation_days_per_year),
            Role.TRIP: AnnualTarget(Role.TRIP, self.total_number_of_trip_days_per_year),
            Role.SDO: AnnualTarget(Role.SDO, self.total_number_of_sdo_days_per_year),
        }
        
        # Distribute pathology days among pathology roles
        pathology_roles = [Role.IMF, Role.DP, Role.DPD, Role.DPWG, Role.DPED, Role.EDUCATION]
        total_pathology_days = self.total_number_of_pathology_days_per_year
        
        # For now, distribute evenly among pathology roles
        # This could be made configurable in the future
        days_per_pathology_role = total_pathology_days / len(pathology_roles)
        for role in pathology_roles:
            targets[role] = AnnualTarget(role, days_per_pathology_role)
        
        return targets
    
    def get_roles_by_category(self, category: RoleCategory) -> List[Role]:
        """Get all roles that belong to a specific category for this physician."""
        return Role.get_roles_by_category(category)
    
    def get_target_days_for_category(self, category: RoleCategory) -> float:
        """Get total target days for a specific role category."""
        roles = self.get_roles_by_category(category)
        return sum(self.annual_targets.get(role, AnnualTarget(role, 0)).target_days for role in roles)


@dataclass
class CoverageRequirement:
    """Minimum coverage requirements for each role per day."""
    role: Role
    min_physicians: int
    max_physicians: Optional[int] = None  # None means no maximum


@dataclass
class SchedulingInput:
    """Complete input data for the scheduling problem."""
    physicians: List[Physician]
    calendar_days: List[date]
    roles: List[Role]
    coverage_requirements: Dict[Role, CoverageRequirement]
    
    def __post_init__(self):
        """Validate scheduling input data."""
        if not self.physicians:
            raise ValueError("At least one physician must be provided")
        
        if not self.calendar_days:
            raise ValueError("At least one calendar day must be provided")
        
        if not self.roles:
            raise ValueError("At least one role must be provided")
        
        # Validate coverage requirements
        for role in self.roles:
            if role not in self.coverage_requirements:
                raise ValueError(f"Coverage requirement missing for role: {role}")


@dataclass
class ScheduleAssignment:
    """Represents a single assignment of a physician to a role on a specific day and half-day period."""
    physician: Physician
    day: date
    half_day_period: HalfDayPeriod
    role: Role


@dataclass
class Schedule:
    """Complete schedule with all assignments."""
    assignments: List[ScheduleAssignment]
    input_data: SchedulingInput
    
    def get_assignments_for_day(self, day: date) -> List[ScheduleAssignment]:
        """Get all assignments for a specific day."""
        return [a for a in self.assignments if a.day == day]
    
    def get_assignments_for_day_period(self, day: date, period: HalfDayPeriod) -> List[ScheduleAssignment]:
        """Get all assignments for a specific day and half-day period."""
        return [a for a in self.assignments if a.day == day and a.half_day_period == period]
    
    def get_assignments_for_physician(self, physician: Physician) -> List[ScheduleAssignment]:
        """Get all assignments for a specific physician."""
        return [a for a in self.assignments if a.physician == physician]
    
    def get_assignments_for_role(self, role: Role) -> List[ScheduleAssignment]:
        """Get all assignments for a specific role."""
        return [a for a in self.assignments if a.role == role]
    
    def get_coverage_for_day_role(self, day: date, role: Role) -> List[Physician]:
        """Get all physicians assigned to a specific role on a specific day."""
        return [a.physician for a in self.assignments if a.day == day and a.role == role]
    
    def get_coverage_for_day_period_role(self, day: date, period: HalfDayPeriod, role: Role) -> List[Physician]:
        """Get all physicians assigned to a specific role on a specific day and half-day period."""
        return [a.physician for a in self.assignments if a.day == day and a.half_day_period == period and a.role == role] 