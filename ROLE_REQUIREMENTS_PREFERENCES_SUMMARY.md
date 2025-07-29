# Role Requirements and Preferences Summary

## Overview

The role requirements and preferences system allows each physician to specify their weekly role requirements (hard constraints) and preferences (soft constraints) with a weight-based penalty system.

## Data Structures

### RoleRequirement
```python
@dataclass
class RoleRequirement:
    role: Role
    frequency: int  # Number of half-days per week
    period: str = "week"  # Time period (default: week)
```

### RolePreference
```python
@dataclass
class RolePreference:
    role: Role
    frequency: int  # Number of half-days per week
    weight: float  # Preference weight (0.0 to 1.0)
    period: str = "week"  # Time period (default: week)
```

## Physician Class Extensions

### New Fields
```python
role_requirements: List[RoleRequirement] = None  # Required role assignments per week
role_preferences: List[RolePreference] = None  # Preferred role assignments per week
```

### Helper Methods
- `get_role_requirement(role: Role) -> Optional[RoleRequirement]`
- `get_role_preference(role: Role) -> Optional[RolePreference]`
- `has_role_requirement(role: Role) -> bool`
- `has_role_preference(role: Role) -> bool`
- `get_weekly_requirements() -> Dict[Role, int]`
- `get_weekly_preferences() -> Dict[Role, tuple]`

## Constraint Functions

### add_role_requirement_constraints()
**Purpose**: Ensures each physician meets their weekly role requirements.

**Logic**:
- Iterates through each physician's role requirements
- Creates variables for each role across all days and periods
- Adds hard constraints: `sum(role_vars) >= required_frequency`
- Converts to integer units for OR-Tools compatibility

**Example**:
```python
# Physician must do at least 2 half-days of IMF per week
RoleRequirement(Role.IMF, 2)
# Constraint: sum(imf_vars) >= 4 (2 * 2 = 4 integer units)
```

### add_role_preference_constraints()
**Purpose**: Adds soft constraints for physician role preferences.

**Logic**:
- Iterates through each physician's role preferences
- Creates penalty variables for preference violations
- Adds constraints: `penalty >= required_frequency - actual_frequency`
- Stores weighted penalties for objective function

**Example**:
```python
# Physician prefers 1 half-day of OSD per week (weight 0.8)
RolePreference(Role.OSD, 1, 0.8)
# Penalty: max(0, 2 - actual_frequency) * 0.8
```

### create_objective_function()
**Purpose**: Creates objective function that minimizes preference violations.

**Logic**:
- Combines all preference penalties with their weights
- Creates weighted penalty terms: `penalty_var * weight`
- Minimizes sum of weighted penalties

## Constraint Hierarchy

### Priority System
1. **Hard Constraints** (Must be satisfied):
   - Annual target constraints
   - Role requirement constraints
   - One role per half day constraints
   - Coverage constraints
   - SDO constraints
   - Unavailability constraints

2. **Soft Constraints** (Optimized when possible):
   - Role preference constraints (with weights)

### Weight System (0.0 to 1.0)
- **0.0**: No penalty (preference ignored)
- **0.5**: Medium penalty
- **1.0**: High penalty (strong preference)

## Integration with Other Constraints

### Annual Target Constraints
- Weekly requirements must fit within annual targets
- Example: 2 IMF/week = 104 IMF/year (52 weeks)
- Must not exceed annual pathology target

### One Role Per Half Day
- Requirements and preferences respect role limits
- DP roles can be assigned together
- Other roles are limited to one per half day

### Coverage Constraints
- Coverage requirements must be satisfied
- Individual requirements must work with coverage needs
- May require redistribution of assignments

### SDO Constraints
- SDO days count toward annual targets
- Requirements and preferences must work with SDO days
- Part-time physicians get proportional requirements

### Unavailability Constraints
- Unavailable physicians cannot be assigned
- Requirements must be met on available days
- Preferences are optimized for available time

## Example Usage

### Creating Physicians with Requirements and Preferences
```python
physician = Physician.create_with_effective_fte_calculation(
    name="Dr. Smith",
    fte_percentage=1.0,
    admin_fte_percentage=0.15,
    research_fte_percentage=0.05,
    vacation_category=VacationCategory.CATEGORY_30,
    role_requirements=[
        RoleRequirement(Role.IMF, 2),  # Must do at least 2 half-days of IMF per week
        RoleRequirement(Role.DP, 3),   # Must do at least 3 half-days of DP per week
    ],
    role_preferences=[
        RolePreference(Role.OSD, 1, 0.8),  # Prefer 1 half-day of OSD per week (weight 0.8)
        RolePreference(Role.ADMIN, 1, 0.5), # Prefer 1 half-day of ADMIN per week (weight 0.5)
    ]
)
```

### Adding Constraints to Model
```python
constraint_builder = ConstraintBuilder(model, variables, input_data)
constraint_builder.add_role_requirement_constraints()
constraint_builder.add_role_preference_constraints()
constraint_builder.create_objective_function()
```

## Benefits

### 1. Individual Physician Needs
- Each physician can specify their role requirements
- Supports different skill sets and preferences
- Allows for personalized scheduling

### 2. Flexible Preference System
- Physicians can express preferences without hard requirements
- Weight system allows for priority ranking
- Solver optimizes for satisfaction when possible

### 3. Workload Balance
- Requirements ensure minimum coverage
- Preferences help distribute workload fairly
- Supports both individual and organizational needs

### 4. Scalability
- Easy to add/remove requirements and preferences
- Supports different physician types (full-time, part-time)
- Can be extended for different time periods

### 5. Quality Assurance
- Requirements ensure critical roles are covered
- Preferences improve physician satisfaction
- Balances organizational needs with individual preferences

## Validation

### RoleRequirement Validation
- Frequency must be non-negative
- Period must be 'week' (for now)

### RolePreference Validation
- Frequency must be non-negative
- Weight must be between 0.0 and 1.0
- Period must be 'week' (for now)

## Testing

The implementation includes comprehensive tests in `test_role_requirements_preferences.py` that verify:

1. **Role requirement constraints** work correctly
2. **Role preference constraints** work correctly
3. **Objective function** minimizes preference violations
4. **Integration** with other constraints
5. **Benefits** of the constraint system

## Examples

The implementation includes demonstration examples in `examples/role_requirements_preferences_example.py` that show:

1. **Basic usage** of requirements and preferences
2. **Difference** between requirements and preferences
3. **Weekly frequency** calculations
4. **Integration** with other constraints
5. **Benefits** of the system

## Future Extensions

### Time Periods
- Currently supports only "week" period
- Can be extended to support "month", "year", etc.

### Specific Days
- Currently supports only frequency requirements
- Can be extended to support specific day requirements (e.g., "every Wednesday")

### Advanced Preferences
- Currently supports only "at least X times per week"
- Can be extended to support "exactly X times" or "between X and Y times"

This system provides a robust foundation for individualizing physician scheduling while maintaining organizational requirements and constraints. 