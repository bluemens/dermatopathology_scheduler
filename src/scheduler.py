"""
Main scheduling engine using Google OR-Tools CP-SAT Solver.

This module contains the core scheduling logic that creates and solves
the constraint satisfaction problem for physician scheduling.
"""

import time
from typing import Dict, List, Any, Optional
from ortools.sat.python import cp_model
from ortools.sat import cp_model_pb2

from .data_models import (
    SchedulingInput, Schedule, ScheduleAssignment, Physician, Role
)
from .constraints import create_constraint_builder
from .utils import validate_scheduling_input, print_schedule_summary, calculate_schedule_metrics


class PhysicianScheduler:
    """
    Main scheduler class that orchestrates the entire scheduling process.
    
    This class handles:
    - Input validation
    - Model creation
    - Variable definition
    - Constraint application
    - Problem solving
    - Solution extraction
    """
    
    def __init__(self, input_data: SchedulingInput):
        """
        Initialize the scheduler with input data.
        
        Args:
            input_data: Complete input data for the scheduling problem
        """
        self.input_data = input_data
        self.model = None
        self.variables = {}
        self.solver = None
        self.solution = None
        
        # Validate input data
        validation_errors = validate_scheduling_input(input_data)
        if validation_errors:
            raise ValueError(f"Input validation failed:\n" + "\n".join(validation_errors))
    
    def create_model(self) -> None:
        """
        Create the OR-Tools CP-SAT model and define decision variables.
        
        This method creates Boolean variables for each (physician, day, role) tuple
        that represents whether a physician is assigned to a specific role on a specific day.
        """
        print("Creating OR-Tools model...")
        
        # Create the model
        self.model = cp_model.CpModel()
        
        # Create decision variables
        # variables[physician_name_day_role] = Boolean variable
        self.variables = {}
        
        for physician in self.input_data.physicians:
            for day in self.input_data.calendar_days:
                for role in self.input_data.roles:
                    var_name = f"{physician.name}_{day.strftime('%Y-%m-%d')}_{role.value}"
                    self.variables[var_name] = self.model.NewBoolVar(var_name)
        
        print(f"Created {len(self.variables)} decision variables")
    
    def add_constraints(self) -> None:
        """
        Add all scheduling constraints to the model.
        
        This method uses the ConstraintBuilder to add all types of constraints
        to the OR-Tools model.
        """
        if not self.model:
            raise RuntimeError("Model must be created before adding constraints")
        
        constraint_builder = create_constraint_builder(self.model, self.variables, self.input_data)
        constraint_builder.add_all_constraints()
    
    def define_objective_function(self) -> None:
        """
        Define the objective function for the optimization problem.
        
        TODO: Implement a meaningful objective function
        - Minimize deviation from target workloads
        - Balance total assignments across physicians
        - Minimize consecutive day assignments
        - Consider physician preferences
        """
        if not self.model:
            raise RuntimeError("Model must be created before defining objective")
        
        print("Defining objective function...")
        
        # TODO: Implement meaningful objective function
        # For now, create a simple placeholder objective
        
        # Example: Minimize total assignments (placeholder)
        objective_terms = []
        for var in self.variables.values():
            objective_terms.append(var)
        
        if objective_terms:
            self.model.Minimize(sum(objective_terms))
        
        print("Objective function defined (placeholder)")
    
    def solve(self, time_limit: int = 300) -> bool:
        """
        Solve the scheduling problem.
        
        Args:
            time_limit: Maximum time to spend solving in seconds
        
        Returns:
            True if a solution was found, False otherwise
        """
        if not self.model:
            raise RuntimeError("Model must be created before solving")
        
        print(f"Solving scheduling problem (time limit: {time_limit}s)...")
        
        # Create solver
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = time_limit
        
        # Solve the problem
        start_time = time.time()
        status = self.solver.Solve(self.model)
        solve_time = time.time() - start_time
        
        print(f"Solve time: {solve_time:.2f} seconds")
        
        # Check solution status
        if status == cp_model.OPTIMAL:
            print("Optimal solution found!")
            return True
        elif status == cp_model.FEASIBLE:
            print("Feasible solution found (may not be optimal)")
            return True
        elif status == cp_model.INFEASIBLE:
            print("Problem is infeasible - no solution exists")
            return False
        elif status == cp_model.MODEL_INVALID:
            print("Model is invalid")
            return False
        else:
            print(f"Unknown solver status: {status}")
            return False
    
    def extract_solution(self) -> Optional[Schedule]:
        """
        Extract the solution from the solver and create a Schedule object.
        
        Returns:
            Schedule object if solution exists, None otherwise
        """
        if not self.solver or not self.variables:
            raise RuntimeError("Problem must be solved before extracting solution")
        
        print("Extracting solution...")
        
        # Extract assignments from solution
        assignments = []
        
        for var_name, var in self.variables.items():
            if self.solver.Value(var) == 1:  # Variable is True in solution
                # Parse variable name: "physician_name_date_role"
                parts = var_name.split('_')
                if len(parts) >= 3:
                    # Handle physician names that might contain underscores
                    role_part = parts[-1]
                    date_part = parts[-2]
                    physician_name = '_'.join(parts[:-2])
                    
                    # Find corresponding physician and role
                    physician = next((p for p in self.input_data.physicians if p.name == physician_name), None)
                    role = next((r for r in self.input_data.roles if r.value == role_part), None)
                    
                    if physician and role:
                        try:
                            day = date.fromisoformat(date_part)
                            assignment = ScheduleAssignment(physician=physician, day=day, role=role)
                            assignments.append(assignment)
                        except ValueError:
                            print(f"Warning: Could not parse date from variable name: {var_name}")
        
        if assignments:
            schedule = Schedule(assignments=assignments, input_data=self.input_data)
            print(f"Extracted {len(assignments)} assignments")
            return schedule
        else:
            print("No assignments found in solution")
            return None
    
    def run_scheduler(self, time_limit: int = 300) -> Optional[Schedule]:
        """
        Run the complete scheduling process.
        
        Args:
            time_limit: Maximum time to spend solving in seconds
        
        Returns:
            Schedule object if successful, None otherwise
        """
        try:
            print("="*60)
            print("PHYSICIAN SCHEDULER")
            print("="*60)
            
            # Step 1: Create model and variables
            self.create_model()
            
            # Step 2: Add constraints
            self.add_constraints()
            
            # Step 3: Define objective function
            self.define_objective_function()
            
            # Step 4: Solve the problem
            if not self.solve(time_limit):
                print("Failed to find a solution")
                return None
            
            # Step 5: Extract solution
            schedule = self.extract_solution()
            
            if schedule:
                # Step 6: Print summary and metrics
                print_schedule_summary(schedule)
                
                metrics = calculate_schedule_metrics(schedule)
                print(f"\nSchedule Quality Metrics:")
                print(f"  Workload Balance: {metrics.get('workload_balance', 0):.3f}")
                print(f"  Coverage Consistency: {metrics.get('coverage_consistency', 0):.3f}")
                print(f"  Average Daily Coverage: {metrics.get('avg_daily_coverage', 0):.1f}")
            
            return schedule
            
        except Exception as e:
            print(f"Error during scheduling: {e}")
            return None
    
    def get_solver_statistics(self) -> Dict[str, Any]:
        """
        Get statistics from the solver.
        
        Returns:
            Dictionary containing solver statistics
        """
        if not self.solver:
            return {}
        
        return {
            'solve_time': self.solver.WallTime(),
            'objective_value': self.solver.ObjectiveValue(),
            'num_branches': self.solver.NumBranches(),
            'num_conflicts': self.solver.NumConflicts(),
            'num_booleans': self.solver.NumBooleans(),
            'num_constraints': self.solver.NumConstraints()
        }


def create_scheduler(input_data: SchedulingInput) -> PhysicianScheduler:
    """
    Factory function to create a physician scheduler.
    
    Args:
        input_data: Complete input data for the scheduling problem
    
    Returns:
        PhysicianScheduler instance
    """
    return PhysicianScheduler(input_data) 