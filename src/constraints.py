"""
Constraint definitions for the physician scheduler.

This module contains placeholder functions for various scheduling constraints
that will be applied to the OR-Tools model.
"""

from typing import Dict, List, Any
from ortools.sat.python import cp_model
from .data_models import (
    Physician, Role, RoleCategory, SchedulingInput, CoverageRequirement, HalfDayPeriod,
    RoleRequirement, RolePreference
)


class ConstraintBuilder:
    """Builder class for adding constraints to the OR-Tools model."""
    
    def __init__(self, model: cp_model.CpModel, variables: Dict[str, Any], 
                 input_data: SchedulingInput):
        """
        Initialize the constraint builder.
        
        Args:
            model: The OR-Tools CP-SAT model
            variables: Dictionary of decision variables
            input_data: Input data for the scheduling problem
        """
        self.model = model
        self.variables = variables
        self.input_data = input_data
    
    def add_one_role_per_day_constraints(self) -> None:
        """
        Add constraints ensuring each physician can only be assigned to one role per half day,
        except for DP roles which can have multiple assignments on the same half day.
        
        Each physician can be assigned one role per half day, except for roles starting with "DP"
        (DP, DPD, DPWG, DPED) which can be assigned together. All other roles are limited to
        one per half day per physician.
        
        For example:
        - A physician could be assigned to both DP and DPD (both start with "DP")
        - A physician could NOT be assigned to both DP and OSD (different categories)
        - A physician could NOT be assigned to both OSD and NVC (both clinical, but not DP roles)
        """
        print("Adding one role per half day constraints (with DP exception)...")
        
        for physician in self.input_data.physicians:
            for day in self.input_data.calendar_days:
                day_str = day.strftime('%Y-%m-%d')
                
                for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                    # Get all roles that start with "DP" (can be assigned together)
                    dp_roles = [role for role in self.input_data.roles if role.value.startswith('dp')]
                    
                    # Get all other roles (limited to one per half day)
                    non_dp_roles = [role for role in self.input_data.roles if not role.value.startswith('dp')]
                    
                    # Create variables for DP roles
                    dp_vars = []
                    for role in dp_roles:
                        var_name = f"{physician.name}_{day_str}_{period.value}_{role.value}"
                        if var_name in self.variables:
                            dp_vars.append(self.variables[var_name])
                    
                    # Create variables for non-DP roles
                    non_dp_vars = []
                    for role in non_dp_roles:
                        var_name = f"{physician.name}_{day_str}_{period.value}_{role.value}"
                        if var_name in self.variables:
                            non_dp_vars.append(self.variables[var_name])
                    
                    # Constraint: At most one non-DP role can be assigned per half day
                    if non_dp_vars:
                        self.model.Add(sum(non_dp_vars) <= 1)
                    
                    # For DP roles, we allow multiple assignments but we need to ensure
                    # they don't conflict with non-DP roles from the same category
                    
                    # Get all categories
                    categories = list(RoleCategory)
                    category_vars = {}
                    
                    for category in categories:
                        # Get all roles in this category
                        roles_in_category = Role.get_roles_by_category(category)
                        
                        # Separate DP and non-DP roles in this category
                        dp_roles_in_category = [role for role in roles_in_category if role.value.startswith('dp')]
                        non_dp_roles_in_category = [role for role in roles_in_category if not role.value.startswith('dp')]
                        
                        # Create variables for roles in this category
                        category_role_vars = []
                        for role in roles_in_category:
                            var_name = f"{physician.name}_{day_str}_{period.value}_{role.value}"
                            if var_name in self.variables:
                                category_role_vars.append(self.variables[var_name])
                        
                        # If there are roles in this category, create constraints
                        if category_role_vars:
                            # Create a binary variable to represent if this category is active
                            category_var_name = f"{physician.name}_{day_str}_{period.value}_{category.value}_active"
                            category_vars[category] = self.model.NewBoolVar(category_var_name)
                            
                            # Constraint: If any role in this category is assigned, the category is active
                            self.model.Add(sum(category_role_vars) <= len(category_role_vars) * category_vars[category])
                            
                            # Constraint: If the category is active, at least one role must be assigned
                            self.model.Add(sum(category_role_vars) >= category_vars[category])
                    
                    # Constraint: At most one category can be active per physician per half day
                    if category_vars:
                        self.model.Add(sum(category_vars.values()) <= 1)
        
        print("One role per half day constraints (with DP exception) added successfully.")
    
    def add_unavailability_constraints(self) -> None:
        """
        Add constraints for physician unavailability dates.
        
        This constraint ensures that physicians cannot be assigned to any roles on their
        unavailable dates. Unavailable dates can include vacation, sick leave, personal
        days, or any other dates when the physician cannot work.
        
        For each physician and each unavailable date, all role assignment variables
        for that physician on that date are set to 0 (false).
        """
        print("Adding unavailability constraints...")
        
        for physician in self.input_data.physicians:
            for unavailable_date in physician.unavailable_dates:
                # Check if the unavailable date is in the calendar days
                if unavailable_date in self.input_data.calendar_days:
                    day_str = unavailable_date.strftime('%Y-%m-%d')
                    
                    # For each role and half-day period, set the assignment variable to 0 (false)
                    for role in self.input_data.roles:
                        for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                            var_name = f"{physician.name}_{day_str}_{period.value}_{role.value}"
                            if var_name in self.variables:
                                # Constraint: Physician cannot be assigned to this role on unavailable date
                                self.model.Add(self.variables[var_name] == False)
        
        print("Unavailability constraints added successfully.")
    
    def add_sdo_constraints(self) -> None:
        """
        Add constraints for Scheduled Day Off (SDO) days.
        
        This constraint handles Scheduled Day Off (SDO) days for part-time physicians.
        SDO days are different from unavailable dates - they are scheduled days off
        that are part of the physician's regular schedule, not emergency absences.
        
        For part-time physicians (FTE < 1.0), SDO days are calculated based on their
        reduced FTE and are distributed throughout the year. Full-time physicians
        (FTE = 1.0) have 0 SDO days.
        
        The constraint ensures that:
        1. Part-time physicians get their required SDO days
        2. SDO days are treated as unavailable for all other roles
        3. Full-time physicians get 0 SDO days
        """
        print("Adding SDO constraints...")
        
        for physician in self.input_data.physicians:
            # Full-time physicians (FTE = 1.0) have 0 SDO days
            if physician.fte_percentage >= 1.0:
                # Ensure full-time physicians get 0 SDO days
                sdo_vars = []
                for day in self.input_data.calendar_days:
                    day_str = day.strftime('%Y-%m-%d')
                    for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                        var_name = f"{physician.name}_{day_str}_{period.value}_{Role.SDO.value}"
                        if var_name in self.variables:
                            sdo_vars.append(self.variables[var_name])
                
                if sdo_vars:
                    # Constraint: Full-time physicians must have 0 SDO days
                    self.model.Add(sum(sdo_vars) == 0)
                    print(f"  Full-time physician {physician.name}: 0 SDO days required")
            
            # Part-time physicians (FTE < 1.0) get SDO days proportional to their reduced FTE
            else:
                # Calculate required SDO days
                required_sdo_days = physician.total_number_of_sdo_days_per_year
                
                # Create variables for SDO assignments
                sdo_vars = []
                for day in self.input_data.calendar_days:
                    day_str = day.strftime('%Y-%m-%d')
                    for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                        var_name = f"{physician.name}_{day_str}_{period.value}_{Role.SDO.value}"
                        if var_name in self.variables:
                            sdo_vars.append(self.variables[var_name])
                
                if sdo_vars:
                    # Constraint: Part-time physicians must get their required SDO days
                    # Convert to integer (multiply by 2 since we're working with half-days)
                    required_sdo_half_days = int(required_sdo_days * 2)
                    self.model.Add(sum(sdo_vars) == required_sdo_half_days)
                    print(f"  Part-time physician {physician.name}: {required_sdo_days} SDO days ({required_sdo_half_days} half-days) required")
                
                # Additional constraint: When SDO is assigned, no other roles can be assigned
                for day in self.input_data.calendar_days:
                    day_str = day.strftime('%Y-%m-%d')
                    for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                        sdo_var_name = f"{physician.name}_{day_str}_{period.value}_{Role.SDO.value}"
                        
                        if sdo_var_name in self.variables:
                            sdo_var = self.variables[sdo_var_name]
                            
                            # For all other roles, if SDO is assigned (1), then other roles must be 0
                            for role in self.input_data.roles:
                                if role != Role.SDO:  # Skip SDO role itself
                                    other_role_var_name = f"{physician.name}_{day_str}_{period.value}_{role.value}"
                                    if other_role_var_name in self.variables:
                                        other_role_var = self.variables[other_role_var_name]
                                        # Constraint: If SDO is assigned, other roles must be 0
                                        self.model.Add(other_role_var <= 1 - sdo_var)
        
        print("SDO constraints added successfully.")
    
    def add_coverage_constraints(self) -> None:
        """
        Add constraints for practice-wide coverage requirements.
        
        Coverage requirements:
        1. At least 1 half-day of IMF per day (any physician)
        2. At least 2.5 half-days of DP per day (any physician)
        3. Daily DPD requirements:
           - Morning: 0.5 half-day of DPD
           - Afternoon: 0.5 half-day of DPD
        4. Tuesday/Thursday: Afternoon DPD must also include DPWG (same physician)
        5. Monday-Friday: Afternoon DPD must also include DPED (same physician)
        6. Tuesday/Thursday: Afternoon DPD + DPWG + DPED must be same physician (triplet)
        """
        print("Adding coverage constraints...")
        
        for day in self.input_data.calendar_days:
            day_str = day.strftime('%Y-%m-%d')
            day_of_week = day.weekday()  # 0=Monday, 1=Tuesday, ..., 4=Friday
            
            # 1. IMF Coverage: At least 1 half-day per day
            imf_vars = []
            for physician in self.input_data.physicians:
                for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                    var_name = f"{physician.name}_{day_str}_{period.value}_{Role.IMF.value}"
                    if var_name in self.variables:
                        imf_vars.append(self.variables[var_name])
            
            if imf_vars:
                # Constraint: At least 1 half-day of IMF per day
                self.model.Add(sum(imf_vars) >= 1)
                print(f"  Day {day_str}: IMF coverage >= 1 half-day")
            
            # 2. DP Coverage: At least 2.5 half-days per day (convert to integer: 2.5 * 2 = 5)
            dp_vars = []
            for physician in self.input_data.physicians:
                for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                    var_name = f"{physician.name}_{day_str}_{period.value}_{Role.DP.value}"
                    if var_name in self.variables:
                        dp_vars.append(self.variables[var_name])
            
            if dp_vars:
                # Constraint: At least 5 half-day units of DP per day (2.5 * 2 = 5)
                self.model.Add(sum(dp_vars) >= 5)
                print(f"  Day {day_str}: DP coverage >= 2.5 half-days (5 units)")
            
            # 3. DPD Coverage: Morning and afternoon requirements
            # Morning DPD
            morning_dpd_vars = []
            for physician in self.input_data.physicians:
                var_name = f"{physician.name}_{day_str}_{HalfDayPeriod.MORNING.value}_{Role.DPD.value}"
                if var_name in self.variables:
                    morning_dpd_vars.append(self.variables[var_name])
            
            if morning_dpd_vars:
                # Constraint: Exactly 1 half-day unit of DPD in morning (0.5 * 2 = 1)
                self.model.Add(sum(morning_dpd_vars) == 1)
                print(f"  Day {day_str}: Morning DPD = 0.5 half-day (1 unit)")
            
            # Afternoon DPD
            afternoon_dpd_vars = []
            for physician in self.input_data.physicians:
                var_name = f"{physician.name}_{day_str}_{HalfDayPeriod.AFTERNOON.value}_{Role.DPD.value}"
                if var_name in self.variables:
                    afternoon_dpd_vars.append(self.variables[var_name])
            
            if afternoon_dpd_vars:
                # Constraint: Exactly 1 half-day unit of DPD in afternoon (0.5 * 2 = 1)
                self.model.Add(sum(afternoon_dpd_vars) == 1)
                print(f"  Day {day_str}: Afternoon DPD = 0.5 half-day (1 unit)")
            
            # 4. Afternoon DPD combined role assignments
            # Monday/Wednesday/Friday: DPD + DPED (same physician)
            # Tuesday/Thursday: DPD + DPED + DPWG (all three to same physician)
            if day_of_week in [0, 1, 2, 3, 4]:  # Monday through Friday
                for physician in self.input_data.physicians:
                    dpd_var_name = f"{physician.name}_{day_str}_{HalfDayPeriod.AFTERNOON.value}_{Role.DPD.value}"
                    dped_var_name = f"{physician.name}_{day_str}_{HalfDayPeriod.AFTERNOON.value}_{Role.DPED.value}"
                    
                    if dpd_var_name in self.variables and dped_var_name in self.variables:
                        dpd_var = self.variables[dpd_var_name]
                        dped_var = self.variables[dped_var_name]
                        
                        # Constraint: DPD and DPED must be assigned to the same physician
                        self.model.Add(dpd_var == dped_var)
                        
                        # For Tuesday/Thursday, also include DPWG in the same physician assignment
                        if day_of_week in [1, 3]:  # Tuesday (1) or Thursday (3)
                            dpwg_var_name = f"{physician.name}_{day_str}_{HalfDayPeriod.AFTERNOON.value}_{Role.DPWG.value}"
                            
                            if dpwg_var_name in self.variables:
                                dpwg_var = self.variables[dpwg_var_name]
                                
                                # Constraint: DPD, DPED, and DPWG must all be assigned to the same physician
                                self.model.Add(dpd_var == dpwg_var)
                                print(f"  Day {day_str}: Afternoon DPD + DPED + DPWG triplet for same physician")
                            else:
                                print(f"  Day {day_str}: Afternoon DPD + DPED pair for same physician")
                        else:
                            print(f"  Day {day_str}: Afternoon DPD + DPED pair for same physician")
        
        print("Coverage constraints added successfully.")
    
    def add_annual_target_constraints(self) -> None:
        """
        Add constraints for annual role targets.
        
        Core metrics (exact requirements):
        1. total_number_of_days_per_year - Sum of all work-related roles
        2. total_number_of_pathology_days_per_year - Sum of all PATHOLOGY roles
        3. total_number_of_clinical_days_per_year - Sum of all CLINICAL roles
        4. total_number_of_osd_days_per_year - Sum of OSD role assignments
        5. total_number_of_nvc_days_per_year - Sum of NVC role assignments
        6. total_number_of_admin_days_per_year - Sum of ADMIN role assignments
        7. total_number_of_sdo_days_per_year - Sum of SDO role assignments
        
        Special rules:
        - Trip days: Not required to use all 18, unused days become available for any assignment
        - Vacation days: Can use up to allocated amount, can bank up to 10 for next year
        """
        print("Adding annual target constraints...")
        
        for physician in self.input_data.physicians:
            print(f"  Physician {physician.name}:")
            
            # Get all work-related roles (excluding vacation, trip, SDO)
            work_roles = [role for role in self.input_data.roles 
                         if role not in [Role.VACATION, Role.TRIP, Role.SDO]]
            
            # 1. Total work days constraint
            total_work_vars = []
            for day in self.input_data.calendar_days:
                day_str = day.strftime('%Y-%m-%d')
                for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                    for role in work_roles:
                        var_name = f"{physician.name}_{day_str}_{period.value}_{role.value}"
                        if var_name in self.variables:
                            total_work_vars.append(self.variables[var_name])
            
            if total_work_vars:
                # Convert to integer units (half-days * 2)
                target_work_days = int(physician.total_number_of_days_per_year * 2)
                self.model.Add(sum(total_work_vars) == target_work_days)
                print(f"    Total work days: {physician.total_number_of_days_per_year} days ({target_work_days} units)")
            
            # 2. Pathology days constraint
            pathology_roles = Role.get_roles_by_category(RoleCategory.PATHOLOGY)
            pathology_vars = []
            for day in self.input_data.calendar_days:
                day_str = day.strftime('%Y-%m-%d')
                for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                    for role in pathology_roles:
                        var_name = f"{physician.name}_{day_str}_{period.value}_{role.value}"
                        if var_name in self.variables:
                            pathology_vars.append(self.variables[var_name])
            
            if pathology_vars:
                # Convert to integer units (half-days * 2)
                target_pathology_days = int(physician.total_number_of_pathology_days_per_year * 2)
                self.model.Add(sum(pathology_vars) == target_pathology_days)
                print(f"    Pathology days: {physician.total_number_of_pathology_days_per_year} days ({target_pathology_days} units)")
            
            # 3. Clinical days constraint
            clinical_roles = Role.get_roles_by_category(RoleCategory.CLINICAL)
            clinical_vars = []
            for day in self.input_data.calendar_days:
                day_str = day.strftime('%Y-%m-%d')
                for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                    for role in clinical_roles:
                        var_name = f"{physician.name}_{day_str}_{period.value}_{role.value}"
                        if var_name in self.variables:
                            clinical_vars.append(self.variables[var_name])
            
            if clinical_vars:
                # Convert to integer units (half-days * 2)
                target_clinical_days = int(physician.total_number_of_clinical_days_per_year * 2)
                self.model.Add(sum(clinical_vars) == target_clinical_days)
                print(f"    Clinical days: {physician.total_number_of_clinical_days_per_year} days ({target_clinical_days} units)")
            
            # 4. OSD days constraint
            osd_vars = []
            for day in self.input_data.calendar_days:
                day_str = day.strftime('%Y-%m-%d')
                for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                    var_name = f"{physician.name}_{day_str}_{period.value}_{Role.OSD.value}"
                    if var_name in self.variables:
                        osd_vars.append(self.variables[var_name])
            
            if osd_vars:
                # Convert to integer units (half-days * 2)
                target_osd_days = int(physician.total_number_of_osd_days_per_year * 2)
                self.model.Add(sum(osd_vars) == target_osd_days)
                print(f"    OSD days: {physician.total_number_of_osd_days_per_year} days ({target_osd_days} units)")
            
            # 5. NVC days constraint
            nvc_vars = []
            for day in self.input_data.calendar_days:
                day_str = day.strftime('%Y-%m-%d')
                for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                    var_name = f"{physician.name}_{day_str}_{period.value}_{Role.NVC.value}"
                    if var_name in self.variables:
                        nvc_vars.append(self.variables[var_name])
            
            if nvc_vars:
                # Convert to integer units (half-days * 2)
                target_nvc_days = int(physician.total_number_of_nvc_days_per_year * 2)
                self.model.Add(sum(nvc_vars) == target_nvc_days)
                print(f"    NVC days: {physician.total_number_of_nvc_days_per_year} days ({target_nvc_days} units)")
            
            # 6. Admin days constraint
            admin_vars = []
            for day in self.input_data.calendar_days:
                day_str = day.strftime('%Y-%m-%d')
                for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                    var_name = f"{physician.name}_{day_str}_{period.value}_{Role.ADMIN.value}"
                    if var_name in self.variables:
                        admin_vars.append(self.variables[var_name])
            
            if admin_vars:
                # Convert to integer units (half-days * 2)
                target_admin_days = int(physician.total_number_of_admin_days_per_year * 2)
                self.model.Add(sum(admin_vars) == target_admin_days)
                print(f"    Admin days: {physician.total_number_of_admin_days_per_year} days ({target_admin_days} units)")
            
            # 7. SDO days constraint
            sdo_vars = []
            for day in self.input_data.calendar_days:
                day_str = day.strftime('%Y-%m-%d')
                for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                    var_name = f"{physician.name}_{day_str}_{period.value}_{Role.SDO.value}"
                    if var_name in self.variables:
                        sdo_vars.append(self.variables[var_name])
            
            if sdo_vars:
                # Convert to integer units (half-days * 2)
                target_sdo_days = int(physician.total_number_of_sdo_days_per_year * 2)
                self.model.Add(sum(sdo_vars) == target_sdo_days)
                print(f"    SDO days: {physician.total_number_of_sdo_days_per_year} days ({target_sdo_days} units)")
            
            # 8. Trip days constraint (special rule: not required to use all 18)
            trip_vars = []
            for day in self.input_data.calendar_days:
                day_str = day.strftime('%Y-%m-%d')
                for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                    var_name = f"{physician.name}_{day_str}_{period.value}_{Role.TRIP.value}"
                    if var_name in self.variables:
                        trip_vars.append(self.variables[var_name])
            
            if trip_vars:
                # Trip days: Can use up to 18, unused days become available for any assignment
                max_trip_days = int(18 * 2)  # 18 days = 36 half-day units
                self.model.Add(sum(trip_vars) <= max_trip_days)
                print(f"    Trip days: Up to 18 days ({max_trip_days} units), unused become work days")
            
            # 9. Vacation days constraint (special rule: can bank up to 10)
            vacation_vars = []
            for day in self.input_data.calendar_days:
                day_str = day.strftime('%Y-%m-%d')
                for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                    var_name = f"{physician.name}_{day_str}_{period.value}_{Role.VACATION.value}"
                    if var_name in self.variables:
                        vacation_vars.append(self.variables[var_name])
            
            if vacation_vars:
                # Vacation days: Can use up to allocated amount, can bank up to 10 for next year
                max_vacation_days = int(physician.total_number_of_vacation_days_per_year * 2)
                self.model.Add(sum(vacation_vars) <= max_vacation_days)
                print(f"    Vacation days: Up to {physician.total_number_of_vacation_days_per_year} days ({max_vacation_days} units), can bank up to 10")
        
        print("Annual target constraints added successfully.")
    
    def add_role_requirement_constraints(self) -> None:
        """
        Add constraints for weekly role requirements.
        
        This constraint ensures that each physician meets their weekly role requirements.
        For example, a physician might need to work at least 2 half-days of IMF per week.
        """
        print("Adding role requirement constraints...")
        
        for physician in self.input_data.physicians:
            if not physician.role_requirements:
                continue
                
            print(f"  Physician {physician.name}:")
            
            for requirement in physician.role_requirements:
                # Create variables for this role across all days and periods
                role_vars = []
                for day in self.input_data.calendar_days:
                    day_str = day.strftime('%Y-%m-%d')
                    for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                        var_name = f"{physician.name}_{day_str}_{period.value}_{requirement.role.value}"
                        if var_name in self.variables:
                            role_vars.append(self.variables[var_name])
                
                if role_vars:
                    # Constraint: At least the required frequency of this role per week
                    # Convert to integer units (half-days * 2)
                    required_frequency = requirement.frequency * 2
                    self.model.Add(sum(role_vars) >= required_frequency)
                    print(f"    {requirement.role.value}: At least {requirement.frequency} half-days per week ({required_frequency} units)")
        
        print("Role requirement constraints added successfully.")
    
    def add_role_preference_constraints(self) -> None:
        """
        Add constraints for weekly role preferences.
        
        This constraint adds soft constraints for physician role preferences.
        These preferences are added to the objective function as penalties
        when not satisfied, rather than as hard constraints.
        """
        print("Adding role preference constraints...")
        
        # Store preference penalties for objective function
        self.preference_penalties = []
        
        for physician in self.input_data.physicians:
            if not physician.role_preferences:
                continue
                
            print(f"  Physician {physician.name}:")
            
            for preference in physician.role_preferences:
                # Create variables for this role across all days and periods
                role_vars = []
                for day in self.input_data.calendar_days:
                    day_str = day.strftime('%Y-%m-%d')
                    for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                        var_name = f"{physician.name}_{day_str}_{period.value}_{preference.role.value}"
                        if var_name in self.variables:
                            role_vars.append(self.variables[var_name])
                
                if role_vars:
                    # Create a penalty variable for this preference
                    penalty_var = self.model.NewIntVar(0, 1000, f"{physician.name}_{preference.role.value}_penalty")
                    
                    # Constraint: Penalty = max(0, required_frequency - actual_frequency)
                    # Convert to integer units (half-days * 2)
                    required_frequency = preference.frequency * 2
                    actual_frequency = sum(role_vars)
                    
                    # If actual_frequency < required_frequency, penalty = required_frequency - actual_frequency
                    # Otherwise, penalty = 0
                    self.model.Add(penalty_var >= required_frequency - actual_frequency)
                    self.model.Add(penalty_var >= 0)
                    
                    # Store penalty with weight for objective function
                    self.preference_penalties.append((penalty_var, preference.weight))
                    
                    print(f"    {preference.role.value}: Prefer at least {preference.frequency} half-days per week (weight: {preference.weight})")
        
        print("Role preference constraints added successfully.")
    
    def create_objective_function(self) -> None:
        """
        Create the objective function that minimizes preference violations and unfairness.
        
        This function creates an objective that minimizes the weighted sum of
        preference penalties and fairness penalties, making the solver prefer solutions
        that satisfy physician preferences while maintaining fair team distribution.
        """
        print("Creating objective function with preference and fairness penalties...")
        
        weighted_penalties = []
        
        # Add preference penalties
        if hasattr(self, 'preference_penalties') and self.preference_penalties:
            for penalty_var, weight in self.preference_penalties:
                # Scale penalty by weight (0.0 to 1.0)
                weighted_penalty = penalty_var * int(weight * 100)  # Convert to integer
                weighted_penalties.append(weighted_penalty)
            print(f"  Added {len(self.preference_penalties)} preference penalties")
        
        # Add fairness penalties
        if hasattr(self, 'fairness_penalties') and self.fairness_penalties:
            for penalty_var, weight in self.fairness_penalties:
                # Scale penalty by weight
                weighted_penalty = penalty_var * weight
                weighted_penalties.append(weighted_penalty)
            print(f"  Added {len(self.fairness_penalties)} fairness penalties")
        
        # Add spacing rewards (negative penalties)
        if hasattr(self, 'spacing_rewards') and self.spacing_rewards:
            for reward_var in self.spacing_rewards:
                # Rewards are subtracted from objective (negative penalties)
                weighted_penalties.append(-reward_var)
            print(f"  Added {len(self.spacing_rewards)} spacing rewards")
        
        if weighted_penalties:
            # Create objective variable
            objective = self.model.NewIntVar(-1000000, 1000000, 'objective')  # Allow negative values for rewards
            self.model.Add(objective == sum(weighted_penalties))
            self.model.Minimize(objective)
            
            print(f"  Created objective function with {len(weighted_penalties)} total terms (penalties and rewards)")
        else:
            print("  No penalties or rewards to minimize")
    
    def add_fairness_constraints(self) -> None:
        """
        Add constraints for fair distribution of work based on FTE.
        
        This constraint ensures that assignments are distributed fairly across
        physicians according to their FTE percentages, similar to how annual
        targets work but with more flexibility for the solver.
        
        The fairness constraint works with soft preferences - it can override
        individual preferences if it creates a more equitable team distribution.
        """
        print("Adding fairness constraints...")
        
        # Store fairness penalties for objective function
        self.fairness_penalties = []
        
        # Calculate total FTE across all physicians
        total_fte = sum(physician.fte_percentage for physician in self.input_data.physicians)
        
        for role in self.input_data.roles:
            # Skip vacation, trip, and SDO roles for fairness (these are handled separately)
            if role in [Role.VACATION, Role.TRIP, Role.SDO]:
                continue
                
            print(f"  Role {role.value}:")
            
            # Calculate FTE-proportional fair shares for this role
            fair_shares = {}
            total_role_target = 0
            
            for physician in self.input_data.physicians:
                # Get annual target for this role
                annual_target = self._get_annual_target_for_role(physician, role)
                total_role_target += annual_target
                
                # Calculate fair share based on FTE
                fair_share = (annual_target * physician.fte_percentage) / total_fte
                fair_shares[physician.name] = fair_share
            
            if total_role_target > 0:
                # Create variables for actual assignments and deviations
                for physician in self.input_data.physicians:
                    # Create variable for actual assignments to this role
                    actual_assignments = []
                    for day in self.input_data.calendar_days:
                        day_str = day.strftime('%Y-%m-%d')
                        for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                            var_name = f"{physician.name}_{day_str}_{period.value}_{role.value}"
                            if var_name in self.variables:
                                actual_assignments.append(self.variables[var_name])
                    
                    if actual_assignments:
                        # Create deviation variable (can be positive or negative)
                        deviation_var_name = f"{physician.name}_{role.value}_fairness_deviation"
                        max_deviation = int(total_role_target * 2)  # Allow for significant deviation
                        deviation_var = self.model.NewIntVar(-max_deviation, max_deviation, deviation_var_name)
                        
                        # Constraint: deviation = actual_assignments - fair_share
                        # Convert fair share to integer (multiply by 2 since we're working with half-days)
                        fair_share_int = int(fair_shares[physician.name] * 2)
                        self.model.Add(deviation_var == sum(actual_assignments) - fair_share_int)
                        
                        # Create absolute deviation penalty (always positive)
                        penalty_var_name = f"{physician.name}_{role.value}_fairness_penalty"
                        penalty_var = self.model.NewIntVar(0, max_deviation, penalty_var_name)
                        
                        # Constraint: penalty = |deviation|
                        self.model.Add(penalty_var >= deviation_var)
                        self.model.Add(penalty_var >= -deviation_var)
                        
                        # Store penalty with weight for objective function
                        fairness_weight = 5  # Adjust this weight relative to preference weights
                        self.fairness_penalties.append((penalty_var, fairness_weight))
                        
                        print(f"    {physician.name} (FTE {physician.fte_percentage}): "
                              f"Fair share {fair_shares[physician.name]:.1f} assignments")
        
        print("Fairness constraints added successfully.")
    
    def add_temporal_spacing_constraints(self) -> None:
        """
        Add constraints for temporal spacing of role assignments.
        
        This constraint maximizes the distance between consecutive assignments
        of the same role for each physician, ensuring variety and avoiding
        repetitive work patterns.
        
        The constraint creates rewards (negative penalties) for spreading out
        assignments over time, encouraging the solver to distribute roles
        evenly across the schedule horizon.
        """
        print("Adding temporal spacing constraints...")
        
        # Store spacing rewards for objective function
        self.spacing_rewards = []
        
        # Configurable weight for spacing importance
        spacing_weight = 5  # Adjust this weight relative to other constraints
        
        for physician in self.input_data.physicians:
            print(f"  Physician {physician.name}:")
            
            for role in self.input_data.roles:
                # Skip vacation, trip, and SDO roles for spacing
                if role in [Role.VACATION, Role.TRIP, Role.SDO]:
                    continue
                
                # Get all assignment variables for this role and physician
                role_assignments = []
                assignment_days = []
                
                for i, day in enumerate(self.input_data.calendar_days):
                    day_str = day.strftime('%Y-%m-%d')
                    for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
                        var_name = f"{physician.name}_{day_str}_{period.value}_{role.value}"
                        if var_name in self.variables:
                            role_assignments.append(self.variables[var_name])
                            assignment_days.append(i)  # Store day index
                
                if len(role_assignments) > 1:
                    # Calculate role weight (1 for single roles, 2+ for combined roles)
                    role_weight = self._get_role_weight(role)
                    
                    # Create variables to track minimum distance between consecutive assignments
                    min_distance_var_name = f"{physician.name}_{role.value}_min_distance"
                    max_possible_distance = len(self.input_data.calendar_days)
                    min_distance_var = self.model.NewIntVar(0, max_possible_distance, min_distance_var_name)
                    
                    # Create constraints to find minimum distance between consecutive assignments
                    consecutive_distances = []
                    
                    for i in range(len(assignment_days) - 1):
                        for j in range(i + 1, len(assignment_days)):
                            distance = assignment_days[j] - assignment_days[i]
                            
                            # Create a binary variable to indicate if both assignments are active
                            both_active_var_name = f"{physician.name}_{role.value}_both_active_{i}_{j}"
                            both_active_var = self.model.NewBoolVar(both_active_var_name)
                            
                            # Constraint: both_active = 1 if both assignments are active
                            self.model.Add(both_active_var <= role_assignments[i])
                            self.model.Add(both_active_var <= role_assignments[j])
                            self.model.Add(both_active_var >= role_assignments[i] + role_assignments[j] - 1)
                            
                            # Create distance variable for this pair
                            distance_var_name = f"{physician.name}_{role.value}_distance_{i}_{j}"
                            distance_var = self.model.NewIntVar(0, max_possible_distance, distance_var_name)
                            
                            # Constraint: distance_var = distance if both active, otherwise max_distance
                            self.model.Add(distance_var >= distance - max_possible_distance * (1 - both_active_var))
                            self.model.Add(distance_var <= distance + max_possible_distance * (1 - both_active_var))
                            self.model.Add(distance_var <= max_possible_distance)
                            
                            consecutive_distances.append(distance_var)
                    
                    if consecutive_distances:
                        # Constraint: min_distance_var <= all consecutive distances
                        for distance_var in consecutive_distances:
                            self.model.Add(min_distance_var <= distance_var)
                        
                        # Create reward based on minimum distance (weighted by role weight)
                        reward_var_name = f"{physician.name}_{role.value}_spacing_reward"
                        max_reward = max_possible_distance * role_weight * spacing_weight
                        reward_var = self.model.NewIntVar(0, max_reward, reward_var_name)
                        
                        # Constraint: reward = min_distance * role_weight * spacing_weight
                        self.model.Add(reward_var == min_distance_var * role_weight * spacing_weight)
                        
                        # Store reward (will be subtracted from objective function)
                        self.spacing_rewards.append(reward_var)
                        
                        print(f"    {role.value} (weight {role_weight}): Maximizing minimum distance between assignments")
        
        print("Temporal spacing constraints added successfully.")
    
    def _get_role_weight(self, role: Role) -> int:
        """
        Get the weight for a specific role based on its importance.
        
        Args:
            role: The role to get the weight for
        
        Returns:
            Role weight (integer)
        """
        # Define role weights based on importance
        # Weight 3: Only for DPD+DPED+DPWG (triplet assignments)
        # Weight 2: Only for DPD+DPED (pair assignments)
        # Weight 1: Everything else
        role_weights = {
            Role.DP: 1,      # Core pathology work
            Role.DPD: 1,     # Person of day (weight handled in coverage constraints)
            Role.IMF: 1,     # Immuno dermatology
            Role.OSD: 1,     # Outpatient service
            Role.ADMIN: 1,   # Administrative
            Role.RESEARCH: 1, # Research
            Role.DPWG: 1,    # Working group (weight handled in coverage constraints)
            Role.DPED: 1,    # Education (weight handled in coverage constraints)
            Role.EDUCATION: 1, # Education
            Role.NVC: 1,     # Non-visit care
        }
        
        return role_weights.get(role, 1)  # Default weight of 1
    
    def _get_annual_target_for_role(self, physician: Physician, role: Role) -> float:
        """
        Get the annual target for a specific role for a physician.
        
        Args:
            physician: The physician
            role: The role to get target for
            
        Returns:
            Annual target in half-day units
        """
        if role == Role.OSD:
            return physician.total_number_of_osd_days_per_year * 2
        elif role == Role.NVC:
            return physician.total_number_of_nvc_days_per_year * 2
        elif role == Role.ADMIN:
            return physician.total_number_of_admin_days_per_year * 2
        elif role == Role.SDO:
            return physician.total_number_of_sdo_days_per_year * 2
        elif role == Role.VACATION:
            return physician.total_number_of_vacation_days_per_year * 2
        elif role == Role.TRIP:
            return 18 * 2  # 18 days maximum
        else:
            # For pathology and clinical roles, calculate based on category targets
            if role in Role.get_roles_by_category(RoleCategory.PATHOLOGY):
                return physician.total_number_of_pathology_days_per_year * 2
            elif role in Role.get_roles_by_category(RoleCategory.CLINICAL):
                return physician.total_number_of_clinical_days_per_year * 2
            else:
                # Default: distribute remaining work days proportionally
                work_roles = [r for r in self.input_data.roles 
                             if r not in [Role.VACATION, Role.TRIP, Role.SDO]]
                total_work_target = physician.total_number_of_days_per_year * 2
                return total_work_target / len(work_roles)
    

    
    def add_role_category_constraints(self) -> None:
        """
        Add constraints for role categories.
        
        TODO: Implement the actual constraint logic
        - Ensure pathology roles are properly distributed
        - Handle clinical vs administrative time allocation
        - Balance research time with other responsibilities
        """
        # TODO: Implement constraint logic
        # Example structure:
        # for physician in self.input_data.physicians:
        #     # Pathology category constraints
        #     pathology_roles = Role.get_roles_by_category(RoleCategory.PATHOLOGY)
        #     pathology_vars = [self.variables[f"{physician.name}_{day}_{role.value}"]
        #                     for day in self.input_data.calendar_days
        #                     for role in pathology_roles]
        #     # Ensure pathology time meets targets
        pass
    
    def add_workload_balancing_constraints(self) -> None:
        """
        Add constraints for workload balancing based on FTE.
        
        TODO: Implement the actual constraint logic
        - Balance total assignments based on FTE percentage
        - Consider fair distribution of workload
        - Handle part-time vs full-time physicians
        - Balance role categories based on FTE
        """
        # TODO: Implement constraint logic
        # Example structure:
        # Calculate expected workload based on FTE
        # Add constraints to balance assignments across physicians
        pass
    
    def add_consecutive_day_constraints(self) -> None:
        """
        Add constraints for consecutive day limits.
        
        TODO: Implement the actual constraint logic
        - Limit consecutive clinical days
        - Ensure adequate rest periods
        - Handle weekend and holiday considerations
        - Consider role-specific consecutive day limits
        """
        # TODO: Implement constraint logic
        # Example structure:
        # for physician in self.input_data.physicians:
        #     for i in range(len(self.input_data.calendar_days) - max_consecutive_days):
        #         consecutive_vars = [self.variables[f"{physician.name}_{day}_{Role.CLINICAL.value}"]
        #                           for day in self.input_data.calendar_days[i:i+max_consecutive_days+1]]
        #         self.model.Add(sum(consecutive_vars) <= max_consecutive_days)
        pass
    
    def add_preference_constraints(self) -> None:
        """
        Add constraints for physician preferences.
        
        TODO: Implement the actual constraint logic
        - Handle preferred days for certain roles
        - Consider seniority and experience levels
        - Balance desirable vs undesirable assignments
        - Handle role category preferences
        """
        # TODO: Implement constraint logic
        # Example structure:
        # Add soft constraints for preferences
        # Use weighted penalties in objective function
        pass
    
    def add_all_constraints(self) -> None:
        """
        Add all constraint types to the model.
        
        This is the main method that orchestrates adding all constraints.
        """
        print("Adding scheduling constraints...")
        
        self.add_one_role_per_day_constraints()
        self.add_unavailability_constraints()
        #self.add_sdo_constraints()
        self.add_coverage_constraints()
        self.add_annual_target_constraints()
        #self.add_role_requirement_constraints()
        #self.add_role_preference_constraints()
        #self.add_fairness_constraints()
        # Temporarily disable temporal spacing to debug the basic_string error
        # self.add_temporal_spacing_constraints()
        
        print("All constraints added successfully.")


def create_constraint_builder(model: cp_model.CpModel, variables: Dict[str, Any], 
                            input_data: SchedulingInput) -> ConstraintBuilder:
    """
    Factory function to create a constraint builder.
    
    Args:
        model: The OR-Tools CP-SAT model
        variables: Dictionary of decision variables
        input_data: Input data for the scheduling problem
    
    Returns:
        ConstraintBuilder instance
    """
    return ConstraintBuilder(model, variables, input_data) 