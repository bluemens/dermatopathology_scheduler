# Implementation Guide: Completing the Physician Scheduler Scaffold

This guide explains how to implement the actual constraint logic and objective functions in the physician scheduler scaffold.

## Current Status

The scaffold provides a complete structure with:
- ✅ Data models and validation
- ✅ OR-Tools model creation and variable definition
- ✅ Placeholder constraint functions
- ✅ Placeholder objective function
- ✅ Solution extraction and export
- ✅ Sample data and testing framework

## Next Steps: Implementing Real Constraints

### 1. One Role Per Day Constraint

**File:** `src/constraints.py` - `add_one_role_per_day_constraints()`

```python
def add_one_role_per_day_constraints(self) -> None:
    """Ensure each physician can only be assigned to one role per day."""
    for physician in self.input_data.physicians:
        for day in self.input_data.calendar_days:
            # Get all role variables for this physician and day
            role_vars = []
            for role in self.input_data.roles:
                var_name = f"{physician.name}_{day.strftime('%Y-%m-%d')}_{role.value}"
                if var_name in self.variables:
                    role_vars.append(self.variables[var_name])
            
            # Ensure sum of all role assignments <= 1
            if role_vars:
                self.model.Add(sum(role_vars) <= 1)
```

### 2. Unavailability Constraints

**File:** `src/constraints.py` - `add_unavailability_constraints()`

```python
def add_unavailability_constraints(self) -> None:
    """Ensure physicians cannot be assigned on unavailable dates."""
    for physician in self.input_data.physicians:
        for unavailable_date in physician.unavailable_dates:
            if unavailable_date in self.input_data.calendar_days:
                for role in self.input_data.roles:
                    var_name = f"{physician.name}_{unavailable_date.strftime('%Y-%m-%d')}_{role.value}"
                    if var_name in self.variables:
                        # Force variable to 0 (no assignment)
                        self.model.Add(self.variables[var_name] == 0)
```

### 3. Coverage Requirements

**File:** `src/constraints.py` - `add_coverage_constraints()`

```python
def add_coverage_constraints(self) -> None:
    """Ensure minimum coverage requirements are met."""
    for day in self.input_data.calendar_days:
        for role, requirement in self.input_data.coverage_requirements.items():
            # Get all physicians assigned to this role on this day
            role_vars = []
            for physician in self.input_data.physicians:
                var_name = f"{physician.name}_{day.strftime('%Y-%m-%d')}_{role.value}"
                if var_name in self.variables:
                    role_vars.append(self.variables[var_name])
            
            if role_vars:
                # Minimum coverage
                self.model.Add(sum(role_vars) >= requirement.min_physicians)
                
                # Maximum coverage (if specified)
                if requirement.max_physicians:
                    self.model.Add(sum(role_vars) <= requirement.max_physicians)
```

### 4. Annual Target Constraints

**File:** `src/constraints.py` - `add_annual_target_constraints()`

```python
def add_annual_target_constraints(self) -> None:
    """Ensure physicians meet their annual role targets."""
    for physician in self.input_data.physicians:
        for role, target in physician.annual_targets.items():
            # Get all assignments for this physician and role
            role_vars = []
            for day in self.input_data.calendar_days:
                var_name = f"{physician.name}_{day.strftime('%Y-%m-%d')}_{role.value}"
                if var_name in self.variables:
                    role_vars.append(self.variables[var_name])
            
            if role_vars:
                # Ensure minimum target is met
                self.model.Add(sum(role_vars) >= target.target_days)
```

### 5. Workload Balancing

**File:** `src/constraints.py` - `add_workload_balancing_constraints()`

```python
def add_workload_balancing_constraints(self) -> None:
    """Balance workload based on FTE percentages."""
    # Calculate expected workload for each physician
    total_days = len(self.input_data.calendar_days)
    physician_targets = {}
    
    for physician in self.input_data.physicians:
        # Calculate expected working days based on FTE
        expected_working_days = int(total_days * physician.fte_percentage * 0.8)  # 80% of FTE days
        physician_targets[physician.name] = expected_working_days
    
    # Add constraints to balance workload
    for physician in self.input_data.physicians:
        # Get all working role assignments (excluding vacation and off)
        working_vars = []
        for day in self.input_data.calendar_days:
            for role in [Role.CLINICAL, Role.ADMIN, Role.PATHOLOGY]:
                var_name = f"{physician.name}_{day.strftime('%Y-%m-%d')}_{role.value}"
                if var_name in self.variables:
                    working_vars.append(self.variables[var_name])
        
        if working_vars:
            target = physician_targets[physician.name]
            # Allow some flexibility (±10%)
            min_work = int(target * 0.9)
            max_work = int(target * 1.1)
            self.model.Add(sum(working_vars) >= min_work)
            self.model.Add(sum(working_vars) <= max_work)
```

## Implementing the Objective Function

**File:** `src/scheduler.py` - `define_objective_function()`

```python
def define_objective_function(self) -> None:
    """Define a meaningful objective function."""
    objective_terms = []
    
    # 1. Minimize deviation from target workloads
    for physician in self.input_data.physicians:
        for role, target in physician.annual_targets.items():
            role_vars = []
            for day in self.input_data.calendar_days:
                var_name = f"{physician.name}_{day.strftime('%Y-%m-%d')}_{role.value}"
                if var_name in self.variables:
                    role_vars.append(self.variables[var_name])
            
            if role_vars:
                # Penalize deviation from target
                assignment_count = sum(role_vars)
                deviation = abs(assignment_count - target.target_days)
                objective_terms.append(deviation * 10)  # Weight factor
    
    # 2. Minimize consecutive working days
    for physician in self.input_data.physicians:
        for i in range(len(self.input_data.calendar_days) - 6):  # 7-day window
            consecutive_vars = []
            for j in range(7):
                day = self.input_data.calendar_days[i + j]
                for role in [Role.CLINICAL, Role.ADMIN, Role.PATHOLOGY]:
                    var_name = f"{physician.name}_{day.strftime('%Y-%m-%d')}_{role.value}"
                    if var_name in self.variables:
                        consecutive_vars.append(self.variables[var_name])
            
            if consecutive_vars:
                # Penalize 7 consecutive working days
                consecutive_penalty = sum(consecutive_vars) * 5
                objective_terms.append(consecutive_penalty)
    
    # 3. Balance weekend assignments
    weekend_assignments = []
    for physician in self.input_data.physicians:
        for day in self.input_data.calendar_days:
            if day.weekday() >= 5:  # Saturday or Sunday
                for role in [Role.CLINICAL, Role.ADMIN, Role.PATHOLOGY]:
                    var_name = f"{physician.name}_{day.strftime('%Y-%m-%d')}_{role.value}"
                    if var_name in self.variables:
                        weekend_assignments.append(self.variables[var_name])
    
    if weekend_assignments:
        # Minimize total weekend assignments
        objective_terms.append(sum(weekend_assignments) * 3)
    
    # Set the objective
    if objective_terms:
        self.model.Minimize(sum(objective_terms))
```

## Testing Your Implementation

1. **Run the tests:**
   ```bash
   python -m pytest tests/
   ```

2. **Test with small data:**
   ```bash
   python main.py --quick-test
   ```

3. **Run full scheduler:**
   ```bash
   python main.py
   ```

## Performance Optimization Tips

1. **Variable Naming:** Use consistent, efficient variable naming
2. **Constraint Ordering:** Add hard constraints first, then soft constraints
3. **Time Limits:** Set appropriate time limits based on problem size
4. **Symmetry Breaking:** Add constraints to break symmetries in the problem
5. **Incremental Solving:** Start with a subset of constraints and add more gradually

## Common Issues and Solutions

1. **Infeasible Problems:**
   - Check coverage requirements vs available physicians
   - Verify unavailability dates don't conflict with minimum coverage
   - Ensure annual targets are reasonable

2. **Long Solve Times:**
   - Reduce the number of calendar days
   - Simplify constraints
   - Use better variable ordering
   - Add symmetry breaking constraints

3. **Poor Solution Quality:**
   - Adjust objective function weights
   - Add more specific constraints
   - Review annual targets and coverage requirements

## Next Steps

1. Implement the constraint functions above
2. Test with small datasets
3. Gradually add more sophisticated constraints
4. Optimize the objective function
5. Add preference handling
6. Implement schedule visualization
7. Add integration with external data sources