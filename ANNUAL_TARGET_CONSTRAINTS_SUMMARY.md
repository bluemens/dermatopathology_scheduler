# Annual Target Constraints Summary

## Overview

The `add_annual_target_constraints` function ensures that each physician meets their exact annual role targets while following role-to-metric mappings and special rules for trip and vacation days.

## Core Metrics (Exact Requirements)

Each physician must hit **exactly** on the following core metrics:

1. **`total_number_of_days_per_year`** - Sum of all work-related roles (excluding vacation, trip, SDO)
2. **`total_number_of_pathology_days_per_year`** - Sum of all PATHOLOGY roles
3. **`total_number_of_clinical_days_per_year`** - Sum of all CLINICAL roles
4. **`total_number_of_osd_days_per_year`** - Sum of OSD role assignments
5. **`total_number_of_nvc_days_per_year`** - Sum of NVC role assignments
6. **`total_number_of_admin_days_per_year`** - Sum of ADMIN role assignments
7. **`total_number_of_sdo_days_per_year`** - Sum of SDO role assignments

## Role-to-Metric Mappings

### Pathology Roles
- **Roles**: IMF, DP, DPD, DPWG, DPED, EDUCATION
- **Metric**: `total_number_of_pathology_days_per_year`
- **Calculation**: `sum(all PATHOLOGY roles)`

### Clinical Roles
- **Roles**: OSD, NVC
- **Metric**: `total_number_of_clinical_days_per_year`
- **Calculation**: `sum(all CLINICAL roles)`

### Administrative Roles
- **Roles**: ADMIN
- **Metric**: `total_number_of_admin_days_per_year`
- **Calculation**: `sum(all ADMIN roles)`

### Research Roles
- **Roles**: RESEARCH
- **Metric**: `total_number_of_research_days_per_year`
- **Calculation**: `sum(all RESEARCH roles)`

### Individual Role Metrics
- **OSD Role**: `total_number_of_osd_days_per_year`
- **NVC Role**: `total_number_of_nvc_days_per_year`

## Special Rules

### Trip Days
- **Rule**: Not required to use all 18 trip days
- **Unused Days**: Become available for any assignment
- **Constraint**: `sum(trip_vars) <= 18`
- **Example**: If only 15 trip days used, 3 days become work days

### Vacation Days
- **Rule**: Can use up to allocated vacation days
- **Banking**: Can bank up to 10 unused vacation days for next year
- **Constraint**: `sum(vacation_vars) <= allocated_vacation_days`
- **Example**: If allocated 25 days but use 20, can bank 5

## Half-Day Structure

All calculations use the half-day structure with morning and afternoon periods:

```python
# Convert to integer units for OR-Tools compatibility
target_days = int(physician.target_days * 2)  # half-days * 2 = integer units
self.model.Add(sum(role_vars) == target_days)
```

**Example**: 2.5 days = 5 integer units

## Implementation Details

### Core Logic

```python
def add_annual_target_constraints(self) -> None:
    for physician in self.input_data.physicians:
        # 1. Total work days constraint
        work_roles = [role for role in self.input_data.roles 
                     if role not in [Role.VACATION, Role.TRIP, Role.SDO]]
        # ... create variables and add constraint
        
        # 2. Pathology days constraint
        pathology_roles = Role.get_roles_by_category(RoleCategory.PATHOLOGY)
        # ... create variables and add constraint
        
        # 3. Clinical days constraint
        clinical_roles = Role.get_roles_by_category(RoleCategory.CLINICAL)
        # ... create variables and add constraint
        
        # 4-7. Individual role constraints (OSD, NVC, Admin, SDO)
        # ... create variables and add constraints
        
        # 8. Trip days constraint (special rule)
        # ... create variables and add constraint (<= 18)
        
        # 9. Vacation days constraint (special rule)
        # ... create variables and add constraint (<= allocated)
```

### Variable Naming Convention

Variables follow the pattern: `{physician.name}_{day_str}_{period.value}_{role.value}`

**Example**: `Dr. Smith_2024-01-01_morning_imuno dermatology`

### Constraint Types

1. **Exact Constraints** (Core Metrics):
   ```python
   self.model.Add(sum(role_vars) == target_days)
   ```

2. **Upper Bound Constraints** (Special Rules):
   ```python
   self.model.Add(sum(trip_vars) <= max_trip_days)
   self.model.Add(sum(vacation_vars) <= max_vacation_days)
   ```

## Integration with Other Constraints

### One Role Per Half Day
- Annual targets must be met within role limits
- DP roles can be assigned together
- Other roles are limited to one per half day

### Coverage Constraints
- Coverage requirements must be satisfied
- Annual targets must still be met
- May require redistribution of assignments

### SDO Constraints
- SDO days count toward annual targets
- Part-time physicians get proportional SDO days
- Full-time physicians get 0 SDO days

### Unavailability Constraints
- Unavailable physicians cannot be assigned
- Annual targets must still be met by available days
- May require adjustment of targets

## Benefits

### 1. Ensures Fair Workload Distribution
- Each physician meets their exact targets
- Prevents over/under assignment
- Maintains work-life balance

### 2. Supports FTE-Based Scheduling
- Part-time physicians get proportional targets
- Full-time physicians get full targets
- Reflects actual working capacity

### 3. Handles Special Cases
- Trip days can be flexible (up to 18)
- Vacation days can be banked (up to 10)
- Unused time becomes available for work

### 4. Maintains Quality Standards
- Ensures adequate pathology time
- Maintains clinical responsibilities
- Balances administrative duties

### 5. Provides Flexibility
- Half-day structure allows precise scheduling
- Role-to-metric mappings are clear
- Special rules accommodate real-world needs

## Example Scenarios

### Full-Time Physician (FTE 1.0)
- **Total Work Days**: 207 days
- **Pathology Days**: 186 days
- **Clinical Days**: 21 days
- **SDO Days**: 0 days
- **Trip Days**: Up to 18 days
- **Vacation Days**: Up to 30 days

### Part-Time Physician (FTE 0.8)
- **Total Work Days**: 166 days
- **Pathology Days**: 149 days
- **Clinical Days**: 17 days
- **SDO Days**: 51 days
- **Trip Days**: Up to 18 days
- **Vacation Days**: Up to 25 days

### Part-Time Physician (FTE 0.6)
- **Total Work Days**: 124 days
- **Pathology Days**: 112 days
- **Clinical Days**: 12 days
- **SDO Days**: 102 days
- **Trip Days**: Up to 18 days
- **Vacation Days**: Up to 22 days

## Testing

The implementation includes comprehensive tests in `test_annual_target_constraints.py` that verify:

1. **Role-to-metric mappings** work correctly
2. **Special rules** for trip and vacation days are applied
3. **Half-day structure** with integer conversion
4. **Integration** with other constraints
5. **Benefits** of the constraint system

## Usage

```python
# Create constraint builder
constraint_builder = ConstraintBuilder(model, variables, input_data)

# Add annual target constraints
constraint_builder.add_annual_target_constraints()

# The constraints will ensure each physician meets their exact annual targets
# while following role-to-metric mappings and special rules
```

This constraint system provides a robust foundation for ensuring fair and accurate physician scheduling that respects individual capacity, role requirements, and organizational needs. 