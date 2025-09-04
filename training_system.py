# /usr/local/bin/training_system.py
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# --- Data Models ---

@dataclass
class Course:
    """Represents a single training course."""
    course_id: str
    title: str

@dataclass
class Role:
    """Represents a job role within the organization."""
    role_id: str
    name: str

@dataclass
class Employee:
    """Represents an employee, their role, and their assigned courses."""
    employee_id: str
    name: str
    current_roles: List[Role] = field(default_factory=list)
    assigned_courses: List[Course] = field(default_factory=list)

    def to_dict(self):
        """Serializes the object to a dictionary for JSON responses."""
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "current_roles": [r.__dict__ for r in self.current_roles],
            "assigned_courses": [c.__dict__ for c in self.assigned_courses]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Employee":
        """Creates an Employee instance from a dictionary."""
        # The roles and courses in the dictionary are already dicts, so we can unpack them
        roles = [Role(**r) for r in data.get("current_roles", [])]
        courses = [Course(**c) for c in data.get("assigned_courses", [])]
        return cls(
            employee_id=data["employee_id"],
            name=data["name"],
            current_roles=roles,
            assigned_courses=courses,
        )

# --- Custom Exceptions ---

class SystemError(Exception):
    """Base exception for this system."""
    pass

class EmployeeNotFoundError(SystemError):
    """Raised when an employee ID is not found."""
    pass

# --- Core System ---

class TrainingAssignmentSystem:
    """Manages employees, roles, and automatic training assignments."""

    def __init__(self, data_path: Optional[str] = None):
        self.employees: Dict[str, Employee] = {}
        self.roles: Dict[str, Role] = {}
        self.courses: Dict[str, Course] = {}
        self.role_to_courses_mapping: Dict[str, List[str]] = {}
        self.data_path = data_path

    def load_configuration_from_file(self, config_path: str):
        """Loads roles, courses, and mappings from a JSON file."""
        logging.info(f"Loading configuration from {config_path}...")
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.roles = {r['role_id']: Role(**r) for r in config['roles']}
        self.courses = {c['course_id']: Course(**c) for c in config['courses']}
        self.role_to_courses_mapping = config['role_mappings']
        logging.info(f"Loaded {len(self.roles)} roles, {len(self.courses)} courses, and {len(self.role_to_courses_mapping)} role mappings.")

    def load_employees_from_file(self) -> bool:
        """
        Loads employee data from the data file.
        Returns True if loaded successfully, False otherwise.
        """
        if not self.data_path or not os.path.exists(self.data_path):
            logging.info("Data file not found. Starting with a fresh state.")
            return False

        try:
            with open(self.data_path, 'r') as f:
                employees_data = json.load(f)

            self.employees = {
                emp_data['employee_id']: Employee.from_dict(emp_data)
                for emp_data in employees_data
            }
            logging.info(f"Successfully loaded {len(self.employees)} employee(s) from {self.data_path}")
            return True
        except (json.JSONDecodeError, IOError, KeyError) as e:
            logging.error(f"Failed to load or parse data file {self.data_path}: {e}. Starting fresh.")
            self.employees = {}  # Reset on failure
            return False

    def save_employees_to_file(self):
        """Saves the current state of employees to the data file."""
        if not self.data_path:
            logging.warning("No data_path configured. State will not be saved.")
            return

        employees_data = [emp.to_dict() for emp in self.employees.values()]
        with open(self.data_path, 'w') as f:
            json.dump(employees_data, f, indent=2)

    def add_employee(self, employee: Employee):
        """Adds a new employee to the system."""
        self.employees[employee.employee_id] = employee
        logging.info(f"Onboarded new employee: {employee.name}")

    def get_employee(self, employee_id: str) -> Employee:
        """Retrieves an employee or raises an error if not found."""
        if employee_id not in self.employees:
            raise EmployeeNotFoundError(f"Employee with ID {employee_id} not found.")
        return self.employees[employee_id]

    def create_employee(self, name: str) -> Employee:
        """Creates a new employee with a unique ID and adds them to the system."""
        if not name:
            raise ValueError("Employee name cannot be empty.")

        # Find the highest existing employee ID number to generate a new one
        max_id = 0
        for emp_id in self.employees:
            if emp_id.startswith('E') and emp_id[1:].isdigit():
                try:
                    max_id = max(max_id, int(emp_id[1:]))
                except (ValueError, TypeError):
                    # Ignore IDs that don't fit the pattern
                    continue

        new_id_num = max_id + 1
        new_id = f"E{new_id_num:03d}"

        new_employee = Employee(employee_id=new_id, name=name)
        self.add_employee(new_employee)
        self.save_employees_to_file()
        return new_employee

    def assign_roles_to_employee(self, employee_id: str, new_role_ids: List[str]):
        """
        Assigns a new set of roles to an employee and automatically assigns
        the required training courses. The employee's course list is
        reset to match the new roles' requirements.
        """
        employee = self.get_employee(employee_id)

        new_roles = []
        for role_id in new_role_ids:
            role = self.roles.get(role_id)
            if not role:
                raise SystemError(f"Role with ID {role_id} not found.")
            new_roles.append(role)

        # Sort roles by name for consistent display
        new_roles.sort(key=lambda r: r.name)
        employee.current_roles = new_roles
        logging.info(f"---> Assigning roles {[r.name for r in new_roles]} to {employee.name}...")

        # The employee's training list is now a direct reflection of their new role.
        # Use a set to automatically handle duplicate courses from different roles.
        required_course_ids = set()
        for role_id in new_role_ids:
            required_course_ids.update(self.role_to_courses_mapping.get(role_id, []))

        new_courses = []
        for course_id in sorted(list(required_course_ids)): # sort for consistency
            course = self.courses.get(course_id)
            if course:
                new_courses.append(course)
            else:
                logging.warning(f"Course ID '{course_id}' required by one of the assigned roles was not found.")
        employee.assigned_courses = new_courses
        logging.info(f"Assigned {len(employee.assigned_courses)} unique course(s) to {employee.name} for the new roles.")
        self.save_employees_to_file()