# Unavailability Constraints Implementation

## Overview

This document explains the implementation of the `add_unavailability_constraints` function, which ensures that physicians cannot be assigned to any roles on their unavailable dates.

## Constraint Logic

### Core Principle
Each physician cannot be assigned to any roles on dates when they are unavailable. This includes vacation days, sick leave, personal days, conferences, and any other unavailable dates.

### Implementation
For each physician and each unavailable date:
1. Check if the unavailable date is in the calendar days
2. If yes, set all role assignment variables for that physician on that date to 0 (false)

## Code Implementation

```python
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
                
                # For each role, set the assignment variable to 0 (false)
                for role in self.input_data.roles:
                    var_name = f"{physician.name}_{day_str}_{role.value}"
                    if var_name in self.variables:
                        # Constraint: Physician cannot be assigned to this role on unavailable date
                        self.model.Add(self.variables[var_name] == 0)
    
    print("Unavailability constraints added successfully.")
```

## Types of Unavailability

The constraint can handle various types of unavailable dates:

- **Vacation**: Planned time off for rest and relaxation
- **Sick Leave**: Unplanned absence due to illness
- **Personal Days**: Personal or family matters
- **Conference**: Professional development and networking
- **Administrative Leave**: Administrative duties or meetings
- **Training**: Professional development and skill building
- **Holidays**: Institutional holidays
- **Other**: Any other unavailable dates

## Constraint Behavior

### What the Constraint Does
- Sets all role assignment variables to 0 for unavailable dates
- Applies to all role types (DP, clinical, administrative, research, time off)
- Only affects dates that are in the calendar
- No exceptions or special handling

### Example
If Dr. Smith is unavailable on 2024-01-15:
- `Dr. Smith_2024-01-15_dp_dermatopathology` = 0
- `Dr. Smith_2024-01-15_osd` = 0
- `Dr. Smith_2024-01-15_admin` = 0
- `Dr. Smith_2024-01-15_vacation` = 0
- All other role variables for Dr. Smith on 2024-01-15 = 0

## Integration with Other Constraints

The unavailability constraint works seamlessly with other constraints:

1. **One Role Per Day**: Unavailable dates have no role assignments, so this constraint is satisfied
2. **Coverage Requirements**: Other available physicians must cover the workload
3. **Annual Targets**: Unavailable days don't count toward annual targets
4. **SDO Constraints**: Unavailable dates are separate from SDO days

## Benefits

1. **Respects Physician Availability**: Ensures physicians are not scheduled when unavailable
2. **Handles Various Absence Types**: Works with any type of unavailable date
3. **Simple and Flexible**: Just add dates to the `unavailable_dates` set
4. **Realistic Scheduling**: Reflects actual physician availability
5. **Prevents Conflicts**: Avoids scheduling conflicts with personal commitments

## Usage

### Setting Unavailable Dates
```python
physician = Physician.create_with_effective_fte_calculation(
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
```

### Applying Constraints
```python
constraint_builder = ConstraintBuilder(model, variables, input_data)
constraint_builder.add_unavailability_constraints()
```

## Testing

The implementation includes comprehensive tests in `test_unavailability_constraints.py` that verify:

- Correct handling of unavailable dates
- Proper constraint creation for all roles
- Integration with calendar days
- Different types of unavailability

## Example Scenarios

### Scenario 1: Vacation Days
- Physician takes vacation on 2024-01-15 and 2024-01-16
- All role assignments for these dates are set to 0
- Other physicians must cover the workload

### Scenario 2: Sick Leave
- Physician is sick on 2024-01-08 and 2024-01-09
- All role assignments for these dates are set to 0
- Coverage requirements must be met by available physicians

### Scenario 3: Conference Attendance
- Physician attends conference on 2024-01-22
- All role assignments for this date are set to 0
- Professional development time is protected

## Next Steps

The unavailability constraint provides a solid foundation for respecting physician availability. The next steps would be to implement:

1. **SDO constraints** - Ensure proper distribution of scheduled days off
2. **Coverage constraints** - Ensure minimum coverage requirements are met
3. **Annual target constraints** - Ensure physicians meet their annual role targets
4. **Workload balancing constraints** - Balance assignments based on FTE 