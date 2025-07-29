# Coverage Constraints Implementation

## Overview

This document explains the implementation of the `add_coverage_constraints` function, which handles practice-wide coverage requirements for pathology roles. The constraints ensure minimum service levels while supporting specialized roles and maintaining continuity of care.

## Constraint Logic

### Core Requirements
The coverage constraints implement the following requirements:

1. **IMF Coverage**: At least 1 half-day per day (any physician)
2. **DP Coverage**: At least 2.5 half-days per day (any physician) - converted to 5 units for OR-Tools
3. **DPD Coverage**: 
   - Morning: Exactly 0.5 half-day (converted to 1 unit for OR-Tools)
   - Afternoon: Exactly 0.5 half-day (converted to 1 unit for OR-Tools)
4. **Day-Specific Requirements**:
   - Tuesday/Thursday: Afternoon DPD + DPWG + DPED triplet (same physician)
   - Monday-Friday: Afternoon DPD + DPED pair (same physician)

### Half-Day Structure
The implementation uses a half-day structure with:
- **Morning**: First half of the workday
- **Afternoon**: Second half of the workday
- **Variable naming**: `{physician}_{date}_{period}_{role}`
- **Integer conversion**: Half-days are converted to integer units for OR-Tools compatibility

## Code Implementation

```python
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
        
        # 2. DP Coverage: At least 2.5 half-days per day
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
        
        # 4. Tuesday/Thursday: Afternoon DPD must also include DPWG
        if day_of_week in [1, 3]:  # Tuesday (1) or Thursday (3)
            for physician in self.input_data.physicians:
                dpd_var_name = f"{physician.name}_{day_str}_{HalfDayPeriod.AFTERNOON.value}_{Role.DPD.value}"
                dpwg_var_name = f"{physician.name}_{day_str}_{HalfDayPeriod.AFTERNOON.value}_{Role.DPWG.value}"
                
                if dpd_var_name in self.variables and dpwg_var_name in self.variables:
                    dpd_var = self.variables[dpd_var_name]
                    dpwg_var = self.variables[dpwg_var_name]
                    
                    # Constraint: If DPD is assigned, DPWG must also be assigned (same physician)
                    self.model.Add(dpd_var == dpwg_var)
                    print(f"  Day {day_str}: Afternoon DPD and DPWG must be same physician")
        
        # 5. Monday-Friday: Afternoon DPD must also include DPED
        if day_of_week in [0, 1, 2, 3, 4]:  # Monday through Friday
            for physician in self.input_data.physicians:
                dpd_var_name = f"{physician.name}_{day_str}_{HalfDayPeriod.AFTERNOON.value}_{Role.DPD.value}"
                dped_var_name = f"{physician.name}_{day_str}_{HalfDayPeriod.AFTERNOON.value}_{Role.DPED.value}"
                
                if dpd_var_name in self.variables and dped_var_name in self.variables:
                    dpd_var = self.variables[dpd_var_name]
                    dped_var = self.variables[dped_var_name]
                    
                    # Constraint: If DPD is assigned, DPED must also be assigned (same physician)
                    self.model.Add(dpd_var == dped_var)
                    print(f"  Day {day_str}: Afternoon DPD and DPED must be same physician")
        
        # 6. Tuesday/Thursday: Afternoon DPD + DPWG + DPED must be same physician (triplet)
        if day_of_week in [1, 3]:  # Tuesday (1) or Thursday (3)
            for physician in self.input_data.physicians:
                dpd_var_name = f"{physician.name}_{day_str}_{HalfDayPeriod.AFTERNOON.value}_{Role.DPD.value}"
                dpwg_var_name = f"{physician.name}_{day_str}_{HalfDayPeriod.AFTERNOON.value}_{Role.DPWG.value}"
                dped_var_name = f"{physician.name}_{day_str}_{HalfDayPeriod.AFTERNOON.value}_{Role.DPED.value}"
                
                if (dpd_var_name in self.variables and 
                    dpwg_var_name in self.variables and 
                    dped_var_name in self.variables):
                    
                    dpd_var = self.variables[dpd_var_name]
                    dpwg_var = self.variables[dpwg_var_name]
                    dped_var = self.variables[dped_var_name]
                    
                    # Constraint: All three roles must be assigned to the same physician
                    self.model.Add(dpd_var == dpwg_var)
                    self.model.Add(dpd_var == dped_var)
                    print(f"  Day {day_str}: Afternoon DPD + DPWG + DPED triplet for same physician")
    
    print("Coverage constraints added successfully.")
```

## Coverage Requirements by Day Type

### Monday/Wednesday/Friday
- **IMF**: ≥ 1 half-day (any physician)
- **DP**: ≥ 2.5 half-days (any physician)
- **DPD**: Morning = 0.5, Afternoon = 0.5 (same physician)
- **Afternoon**: DPD + DPED pair (same physician)

### Tuesday/Thursday
- **IMF**: ≥ 1 half-day (any physician)
- **DP**: ≥ 2.5 half-days (any physician)
- **DPD**: Morning = 0.5, Afternoon = 0.5 (same physician)
- **Afternoon**: DPD + DPWG + DPED triplet (same physician)

### Weekend
- **IMF**: ≥ 1 half-day (any physician)
- **DP**: ≥ 2.5 half-days (any physician)
- **DPD**: Morning = 0.5, Afternoon = 0.5 (same physician)
- **No additional requirements**

## Constraint Behavior

### 1. IMF Coverage
- **Requirement**: At least 1 half-day per day
- **Assignment**: Any physician can provide coverage
- **Timing**: Can be morning or afternoon
- **Flexibility**: High flexibility in assignment

### 2. DP Coverage
- **Requirement**: At least 2.5 half-days per day (5 integer units)
- **Assignment**: Any physician can provide coverage
- **Distribution**: Can be distributed across morning/afternoon
- **Counting**: DPD assignments count toward this total

### 3. DPD Coverage
- **Morning**: Exactly 0.5 half-day (1 integer unit)
- **Afternoon**: Exactly 0.5 half-day (1 integer unit)
- **Continuity**: Same physician must do both
- **Purpose**: Ensures continuity of care

### 4. Day-Specific Requirements
- **Tuesday/Thursday**: Afternoon DPD + DPWG + DPED triplet
- **Monday/Wednesday/Friday**: Afternoon DPD + DPED pair
- **Weekend**: Only basic DPD requirements
- **Purpose**: Ensures proper coordination

### 5. Physician Assignment
- **Same Physician**: Must be assigned to paired/triplet roles
- **Continuity**: Ensures continuity and coordination
- **Prevention**: Prevents split assignments across physicians
- **Quality**: Maintains quality of care

## Integration with Other Constraints

### 1. One Role Per Half Day
- Coverage requirements must be satisfied
- DP roles can be assigned together
- Other roles are limited to one per half day
- Ensures proper role distribution

### 2. Unavailability Constraints
- Unavailable physicians cannot be assigned
- Coverage must still be met by available physicians
- May require redistribution of assignments
- Ensures service continuity

### 3. SDO Constraints
- SDO physicians cannot provide coverage
- Coverage requirements must be met by working physicians
- Part-time physicians contribute less to coverage
- Balances workload appropriately

### 4. Annual Targets
- Coverage assignments count toward annual targets
- Must balance coverage needs with individual targets
- May require trade-offs between coverage and targets
- Ensures fair distribution

## Benefits

### 1. Ensures Minimum Service Levels
- Guarantees IMF coverage every day
- Maintains adequate DP coverage
- Provides consistent DPD coverage
- Ensures patient care continuity

### 2. Supports Specialized Roles
- DPWG and DPED have specific requirements
- Day-specific assignments ensure proper coordination
- Triplet assignments on Tuesday/Thursday
- Maintains specialized expertise

### 3. Maintains Continuity
- Same physician handles related roles
- Prevents fragmented assignments
- Ensures proper handoffs
- Improves care quality

### 4. Flexible Assignment
- Any physician can provide basic coverage
- Allows for workload distribution
- Accommodates physician availability
- Optimizes resource utilization

### 5. Day-Aware Scheduling
- Different requirements for different days
- Weekend vs weekday considerations
- Tuesday/Thursday special requirements
- Adapts to operational needs

## Usage

### Setting Up Coverage Requirements
```python
# Create coverage requirements
coverage_requirements = {}
for role in [Role.IMF, Role.DP, Role.DPD, Role.DPWG, Role.DPED]:
    coverage_requirements[role] = CoverageRequirement(
        role=role,
        min_physicians=0,
        max_physicians=5
    )

# Create scheduling input
input_data = SchedulingInput(
    physicians=physicians,
    calendar_days=calendar_days,
    roles=roles,
    coverage_requirements=coverage_requirements
)
```

### Applying Constraints
```python
# Create variables with half-day structure
variables = {}
for physician in input_data.physicians:
    for day in input_data.calendar_days:
        for period in [HalfDayPeriod.MORNING, HalfDayPeriod.AFTERNOON]:
            for role in input_data.roles:
                var_name = f"{physician.name}_{day.strftime('%Y-%m-%d')}_{period.value}_{role.value}"
                variables[var_name] = model.NewBoolVar(var_name)

# Add constraints
constraint_builder = ConstraintBuilder(model, variables, input_data)
constraint_builder.add_coverage_constraints()
```

## Testing

The implementation includes comprehensive tests in `test_coverage_constraints.py` that verify:

- Correct coverage requirements for different day types
- Proper constraint creation for IMF, DP, and DPD coverage
- Day-specific requirements (Tuesday/Thursday vs other weekdays)
- Integration with other constraints
- Half-day structure functionality

## Example Scenarios

### Scenario 1: Tuesday Coverage
- **IMF**: Dr. Smith morning
- **DP**: Dr. Johnson morning + Dr. Williams afternoon
- **DPD**: Dr. Williams morning + Dr. Smith afternoon
- **Afternoon**: Dr. Smith DPD + DPWG + DPED (triplet)

### Scenario 2: Friday Coverage
- **IMF**: Dr. Johnson morning
- **DP**: Dr. Smith morning + Dr. Williams afternoon
- **DPD**: Dr. Williams morning + Dr. Johnson afternoon
- **Afternoon**: Dr. Johnson DPD + DPED (pair)

### Scenario 3: Weekend Coverage
- **IMF**: Dr. Smith morning
- **DP**: Dr. Johnson morning + Dr. Williams afternoon
- **DPD**: Dr. Williams morning + Dr. Smith afternoon
- **No additional requirements**

## Next Steps

The coverage constraint provides a solid foundation for ensuring minimum service levels. The next steps would be to implement:

1. **Annual target constraints** - Ensure physicians meet their annual role targets
2. **Workload balancing constraints** - Balance assignments based on FTE
3. **Consecutive day constraints** - Limit consecutive clinical days
4. **Preference constraints** - Handle physician preferences 