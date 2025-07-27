# SDO (Scheduled Day Off) Constraints Implementation

## Overview

This document explains the implementation of the `add_sdo_constraints` function, which handles Scheduled Day Off (SDO) days for part-time physicians. SDO days are different from unavailable dates - they are scheduled days off that are part of the physician's regular schedule, not emergency absences.

## Constraint Logic

### Core Principle
SDO days are calculated based on a physician's FTE (Full-Time Equivalent) percentage:
- **Full-time physicians (FTE ≥ 1.0)**: 0 SDO days
- **Part-time physicians (FTE < 1.0)**: SDO days = (1 - FTE) × 255 institutional days

### Implementation
The constraint ensures:
1. Part-time physicians get their required SDO days
2. SDO days are treated as unavailable for all other roles
3. Full-time physicians get 0 SDO days
4. When SDO is assigned, no other roles can be assigned (mutual exclusivity)

## Code Implementation

```python
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
                var_name = f"{physician.name}_{day_str}_{Role.SDO.value}"
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
                var_name = f"{physician.name}_{day_str}_{Role.SDO.value}"
                if var_name in self.variables:
                    sdo_vars.append(self.variables[var_name])
            
            if sdo_vars:
                # Constraint: Part-time physicians must get their required SDO days
                self.model.Add(sum(sdo_vars) == required_sdo_days)
                print(f"  Part-time physician {physician.name}: {required_sdo_days} SDO days required")
            
            # Additional constraint: When SDO is assigned, no other roles can be assigned
            for day in self.input_data.calendar_days:
                day_str = day.strftime('%Y-%m-%d')
                sdo_var_name = f"{physician.name}_{day_str}_{Role.SDO.value}"
                
                if sdo_var_name in self.variables:
                    sdo_var = self.variables[sdo_var_name]
                    
                    # For all other roles, if SDO is assigned (1), then other roles must be 0
                    for role in self.input_data.roles:
                        if role != Role.SDO:  # Skip SDO role itself
                            other_role_var_name = f"{physician.name}_{day_str}_{role.value}"
                            if other_role_var_name in self.variables:
                                other_role_var = self.variables[other_role_var_name]
                                # Constraint: If SDO is assigned, other roles must be 0
                                self.model.Add(other_role_var <= 1 - sdo_var)
    
    print("SDO constraints added successfully.")
```

## SDO Day Calculation

### Formula
SDO days = (1 - FTE) × 255 institutional days

### Examples
- **FTE 0.5**: (1 - 0.5) × 255 = 127.5 days
- **FTE 0.8**: (1 - 0.8) × 255 = 51 days
- **FTE 1.0**: (1 - 1.0) × 255 = 0 days

## Key Differences: SDO vs Unavailable Dates

### SDO Days
- **Purpose**: Scheduled part of regular schedule
- **Calculation**: Based on FTE percentage
- **Distribution**: Can be distributed throughout year
- **Applicability**: Part-time physicians only
- **Annual Targets**: Count toward annual targets
- **Nature**: Planned and predictable

### Unavailable Dates
- **Purpose**: Emergency or planned absences
- **Calculation**: Not calculated, manually specified
- **Distribution**: Specific dates only
- **Applicability**: All physicians can have unavailable dates
- **Annual Targets**: Do not count toward annual targets
- **Nature**: Unplanned or emergency

## Constraint Behavior

### Full-Time Physicians (FTE ≥ 1.0)
- Must have exactly 0 SDO days
- Can be assigned to any roles
- No SDO constraints apply

### Part-Time Physicians (FTE < 1.0)
- Must have exactly their calculated SDO days
- When SDO is assigned, no other roles can be assigned
- SDO days are distributed throughout the year
- Mutual exclusivity with other roles

### SDO Day Constraints
- If SDO = 1, then all other roles = 0
- If any other role = 1, then SDO = 0
- Ensures mutual exclusivity
- Prevents double assignments

## Integration with Other Constraints

### 1. One Role Per Day
- SDO is treated as a role
- When SDO is assigned, no other roles can be assigned
- Satisfies the one role per day constraint
- Mutual exclusivity is enforced

### 2. Unavailability Constraints
- SDO is different from unavailable dates
- Both can exist simultaneously
- Unavailable dates take precedence
- SDO days are planned, unavailable are unplanned

### 3. Coverage Requirements
- SDO days reduce available physicians
- Other physicians must cover the workload
- Coverage requirements still must be met
- Part-time physicians contribute less to coverage

### 4. Annual Targets
- SDO days count toward annual targets
- Part of the physician's planned schedule
- Different from unavailable days
- Reflects actual working capacity

## Benefits

### 1. Realistic Part-Time Scheduling
- Reflects actual working capacity
- Prevents over-scheduling part-time physicians
- Maintains work-life balance

### 2. Fair Workload Distribution
- Part-time physicians get proportional SDO days
- Full-time physicians work full schedules
- Prevents burnout and ensures sustainability

### 3. Flexible Scheduling
- SDO days can be distributed throughout year
- Can accommodate personal preferences
- Allows for seasonal adjustments

### 4. Clear Distinction from Absences
- SDO days are planned part of schedule
- Different from vacation, sick leave, etc.
- Helps with resource planning

### 5. Compliance with Labor Laws
- Ensures part-time workers get appropriate time off
- Prevents over-scheduling violations
- Maintains legal compliance

## Usage

### Setting Preferred Days Off
```python
physician = Physician.create_with_effective_fte_calculation(
    name="Dr. Smith",
    fte_percentage=0.8,
    admin_fte_percentage=0.1,
    research_fte_percentage=0.05,
    vacation_category=VacationCategory.CATEGORY_25,
    preferred_days_off={
        date(2024, 1, 2),  # Tuesday
        date(2024, 1, 5),  # Friday
    }
)
```

### Applying Constraints
```python
constraint_builder = ConstraintBuilder(model, variables, input_data)
constraint_builder.add_sdo_constraints()
```

## Testing

The implementation includes comprehensive tests in `test_sdo_constraints.py` that verify:

- Correct SDO day calculation for different FTE levels
- Proper constraint creation for full-time and part-time physicians
- Mutual exclusivity between SDO and other roles
- Integration with other constraints
- Difference between SDO and unavailable dates

## Example Scenarios

### Scenario 1: Full-Time Physician
- FTE: 1.0
- Required SDO days: 0
- Can be assigned to any roles
- No SDO constraints apply

### Scenario 2: Part-Time Physician (80% FTE)
- FTE: 0.8
- Required SDO days: 51
- Must get exactly 51 SDO days
- When SDO is assigned, no other roles can be assigned

### Scenario 3: Part-Time Physician (60% FTE)
- FTE: 0.6
- Required SDO days: 102
- Must get exactly 102 SDO days
- Higher SDO requirement due to lower FTE

## Next Steps

The SDO constraint provides a solid foundation for handling part-time physician scheduling. The next steps would be to implement:

1. **Coverage constraints** - Ensure minimum coverage requirements are met
2. **Annual target constraints** - Ensure physicians meet their annual role targets
3. **Workload balancing constraints** - Balance assignments based on FTE
4. **Consecutive day constraints** - Limit consecutive clinical days 