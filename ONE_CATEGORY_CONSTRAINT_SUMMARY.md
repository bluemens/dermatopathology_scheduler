# One Role Per Half Day Constraint (with DP Exception) Implementation

## Overview

This document explains the implementation of the `add_one_role_per_day_constraints` function, which ensures that each physician can only be assigned to one role per half day, except for roles starting with "DP" which can be assigned together.

## Constraint Logic

### Core Principle
Each physician can be assigned to **one role per half day**, except for roles starting with "DP" (DP, DPD, DPWG, DPED) which can be assigned together.

### Examples

**Valid Assignments (DP roles can be combined):**
- DP + DPD (both start with "dp")
- DP + DPWG + DPED (all start with "dp")
- DPD + DPED (both start with "dp")

**Invalid Assignments (non-DP roles limited to one):**
- OSD + NVC (both clinical, but not DP roles)
- ADMIN + RESEARCH (different categories)
- VACATION + TRIP (both time off, but not DP roles)

**Invalid Assignments (different categories):**
- DP + OSD (pathology + clinical)
- DP + ADMIN (pathology + administrative)
- OSD + VACATION (clinical + time off)

## Implementation Details

### Variable Structure

The constraint creates two types of variables:

1. **Role Variables**: `{physician.name}_{day}_{role.value}`
   - One Boolean variable per (physician, day, role) combination
   - Represents whether a physician is assigned to a specific role on a specific day

2. **Category Variables**: `{physician.name}_{day}_{category.value}_active`
   - One Boolean variable per (physician, day, category) combination
   - Represents whether a category is active for a physician on a specific day

### Constraint Logic

For each physician and each day:

1. **Non-DP Role Limit**: At most one non-DP role can be assigned per half day
   ```
   sum(non_dp_role_vars) <= 1
   ```

2. **Category Activation**: If any role in a category is assigned, the category is active
   ```
   sum(role_vars_in_category) <= len(role_vars_in_category) * category_active_var
   ```

3. **Category Requirement**: If a category is active, at least one role must be assigned
   ```
   sum(role_vars_in_category) >= category_active_var
   ```

4. **One Category Limit**: At most one category can be active per physician per half day
   ```
   sum(all_category_vars) <= 1
   ```

## Code Implementation

```python
def add_one_role_per_day_constraints(self) -> None:
    """
    Add constraints ensuring each physician can only be assigned to one role per half day,
    except for DP roles which can have multiple assignments on the same half day.
    
    Each physician can be assigned one role per half day, except for roles starting with "DP"
    (DP, DPD, DPWG, DPED) which can be assigned together. All other roles are limited to
    one per half day per physician.
    """
    for physician in self.input_data.physicians:
        for day in self.input_data.calendar_days:
            day_str = day.strftime('%Y-%m-%d')
            
            # Get all roles that start with "DP" (can be assigned together)
            dp_roles = [role for role in self.input_data.roles if role.value.startswith('dp')]
            
            # Get all other roles (limited to one per half day)
            non_dp_roles = [role for role in self.input_data.roles if not role.value.startswith('dp')]
            
            # Create variables for DP roles
            dp_vars = []
            for role in dp_roles:
                var_name = f"{physician.name}_{day_str}_{role.value}"
                if var_name in self.variables:
                    dp_vars.append(self.variables[var_name])
            
            # Create variables for non-DP roles
            non_dp_vars = []
            for role in non_dp_roles:
                var_name = f"{physician.name}_{day_str}_{role.value}"
                if var_name in self.variables:
                    non_dp_vars.append(self.variables[var_name])
            
            # Constraint: At most one non-DP role can be assigned per half day
            if non_dp_vars:
                self.model.Add(sum(non_dp_vars) <= 1)
            
            # Category constraints to ensure proper category separation
            categories = list(RoleCategory)
            category_vars = {}
            
            for category in categories:
                roles_in_category = Role.get_roles_by_category(category)
                category_role_vars = []
                
                for role in roles_in_category:
                    var_name = f"{physician.name}_{day_str}_{role.value}"
                    if var_name in self.variables:
                        category_role_vars.append(self.variables[var_name])
                
                if category_role_vars:
                    category_var_name = f"{physician.name}_{day_str}_{category.value}_active"
                    category_vars[category] = self.model.NewBoolVar(category_var_name)
                    
                    self.model.Add(sum(category_role_vars) <= len(category_role_vars) * category_vars[category])
                    self.model.Add(sum(category_role_vars) >= category_vars[category])
            
            if category_vars:
                self.model.Add(sum(category_vars.values()) <= 1)
```

## DP Roles

The following roles can be assigned together (all start with "dp"):

- **DP** (dermatopathology)
- **DPD** (dermatopathology_person_of_day)
- **DPWG** (dermpath_working_group)
- **DPED** (dermpath_education)

All DP roles are in the PATHOLOGY category.

## Non-DP Roles

All other roles are limited to one per half day per physician:

- **IMF** (immuno dermatology)
- **EDUCATION** (education)
- **OSD** (outpatient service days)
- **NVC** (non-visit care)
- **ADMIN** (administrative)
- **RESEARCH** (research)
- **TRIP** (trip days)
- **VACATION** (vacation)
- **SDO** (scheduled day off)

## Benefits

1. **DP Role Flexibility**: Physicians can be assigned to multiple DP roles simultaneously, allowing for complex pathology workflows and multitasking.

2. **Prevents Conflicting Assignments**: Ensures that physicians cannot be assigned to conflicting work types (e.g., clinical and pathology on the same half day).

3. **Realistic Scheduling**: Reflects actual pathology work patterns where physicians may have multiple responsibilities within the pathology domain.

4. **Optimization Opportunities**: Allows the solver to find optimal DP role combinations while respecting the one-role-per-half-day rule for other roles.

## Testing

The implementation includes comprehensive tests in `test_one_category_constraint.py` that verify:

- Correct DP role identification
- Proper constraint logic for non-DP roles
- Category variable generation
- Constraint count validation

## Usage

The constraint is automatically applied when calling:

```python
constraint_builder = ConstraintBuilder(model, variables, input_data)
constraint_builder.add_one_role_per_day_constraints()
```

## Next Steps

This constraint provides the foundation for the scheduling system. The next steps would be to implement:

1. **Unavailability constraints** - Handle vacation, sick leave, and other unavailable dates
2. **SDO constraints** - Ensure proper distribution of scheduled days off
3. **Coverage constraints** - Ensure minimum coverage requirements are met
4. **Annual target constraints** - Ensure physicians meet their annual role targets
5. **Workload balancing constraints** - Balance assignments based on FTE 