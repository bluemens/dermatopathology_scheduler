# Role Categorization and SDO Calculation Summary

## Overview

This document summarizes the updates made to the physician scheduler to properly categorize roles and handle Scheduled Day Off (SDO) calculations based on FTE.

## Role Categories

The roles have been organized into the following categories:

### Pathology Roles
- **IMF** (Immuno dermatology)
- **DP** (Dermatopathology)
- **DPD** (Dermatopathology person of day)
- **DPWG** (Dermpath working group)
- **DPED** (Dermpath education)
- **EDUCATION** (Education)

### Clinical Roles
- **OSD** (Outpatient Service Days / Clinic)
- **NVC** (Non-Visit Care)

### Administrative Roles
- **ADMIN** (Administrative)

### Research Roles
- **RESEARCH** (Research)

### Time Off Roles
- **TRIP** (Trip days)
- **VACATION** (Vacation)
- **SDO** (Scheduled Day Off)

## SDO Calculation

Scheduled Day Off (SDO) days are calculated based on FTE:

- **Full-time physicians (FTE 1.0)**: 0 SDO days
- **Part-time physicians**: SDO = (1 - FTE) × 255 institutional days

### Example SDO Calculations:
- FTE 1.0: 0 SDO days
- FTE 0.9: 25.5 SDO days
- FTE 0.8: 51 SDO days
- FTE 0.7: 76.5 SDO days
- FTE 0.6: 102 SDO days
- FTE 0.5: 127.5 SDO days

## Key Changes Made

### 1. Added RoleCategory Enum
```python
class RoleCategory(Enum):
    PATHOLOGY = "pathology"
    CLINICAL = "clinical"
    ADMINISTRATIVE = "administrative"
    RESEARCH = "research"
    TIME_OFF = "time_off"
```

### 2. Enhanced Role Enum
- Added `category` property to get the category for each role
- Added `get_roles_by_category()` class method to get all roles in a category

### 3. Updated Physician Class
- Added `total_number_of_sdo_days_per_year` field
- Added `calculated_sdo_days` property for SDO calculation
- Updated workday calculation to include SDO days
- Added SDO validation in `validate_derived_values()`
- Updated annual target generation to include SDO
- Added helper methods for role categories

### 4. Updated Constraints
- Added `add_sdo_constraints()` method for SDO-specific constraints
- Added `add_role_category_constraints()` method for category-based constraints
- Updated existing constraint methods to handle role categories

## Usage Examples

### Getting Roles by Category
```python
# Get all pathology roles
pathology_roles = Role.get_roles_by_category(RoleCategory.PATHOLOGY)

# Get all clinical roles
clinical_roles = Role.get_roles_by_category(RoleCategory.CLINICAL)
```

### Creating a Physician with SDO Calculation
```python
physician = Physician.create_with_effective_fte_calculation(
    name="Dr. Example",
    fte_percentage=0.8,  # Part-time
    admin_plus_research_fte_percentage=0.15,
    vacation_category=VacationCategory.CATEGORY_25
)

# SDO days are automatically calculated
print(f"SDO days: {physician.calculated_sdo_days}")
```

### Getting Target Days by Category
```python
# Get total pathology target days
pathology_target = physician.get_target_days_for_category(RoleCategory.PATHOLOGY)

# Get total clinical target days
clinical_target = physician.get_target_days_for_category(RoleCategory.CLINICAL)
```

## Testing

Two test files have been created:

1. **test_role_categories.py**: Comprehensive tests for role categorization and SDO calculation
2. **examples/role_categorization_example.py**: Demonstration examples

## Benefits

1. **Clear Role Organization**: Roles are now properly categorized for constraint building
2. **Automatic SDO Calculation**: SDO days are calculated automatically based on FTE
3. **Flexible Role Management**: Easy to add new roles or modify categories
4. **Constraint Support**: Role categories can be used in constraint building
5. **Validation**: Comprehensive validation ensures data consistency

## Next Steps

The role categorization and SDO calculation are now ready for use in the constraint system. The next steps would be to:

1. Implement the actual constraint logic in the `ConstraintBuilder` class
2. Add role-specific coverage requirements
3. Implement workload balancing based on role categories
4. Add preference handling for different role categories 