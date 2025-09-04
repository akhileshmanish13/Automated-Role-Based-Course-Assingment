import logging
import sys
import os

from flask import Flask, jsonify, render_template, request

from training_system import (Employee, EmployeeNotFoundError, SystemError,
                             TrainingAssignmentSystem)

# --- Flask App Initialization ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- System Setup (In-memory "database") ---
# Note: In a real app, you'd use a proper database, not a global variable.

# --- Determine the absolute path to the configuration file ---
# This makes the app runnable from any directory, including from a debugger.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, 'config.json')
DATA_PATH = os.path.join(APP_DIR, 'data.json')

system = TrainingAssignmentSystem(data_path=DATA_PATH)

try:
    system.load_configuration_from_file(CONFIG_PATH)

    # Try to load existing employee data.
    # If it fails or file doesn't exist, onboard some initial employees.
    if not system.load_employees_from_file():
        logging.info("No existing data found. Onboarding initial employees.")
        system.add_employee(Employee("E001", "Alice"))
        system.add_employee(Employee("E002", "Bob"))
        system.save_employees_to_file()
except FileNotFoundError:
    # If the config is missing, the app is useless. Stop it immediately.
    logging.critical(f"FATAL: Configuration file not found at {CONFIG_PATH}. The application cannot start.")
    sys.exit(1) # Exit the program with an error code


# --- API Endpoints ---

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """Returns a list of all employees."""
    all_employees = [emp.to_dict() for emp in system.employees.values()]
    return jsonify(all_employees)

@app.route('/api/employees/<string:employee_id>', methods=['GET'])
def get_employee(employee_id):
    """Returns data for a single employee."""
    try:
        employee = system.get_employee(employee_id)
        return jsonify(employee.to_dict())
    except EmployeeNotFoundError as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/employees', methods=['POST'])
def create_employee():
    """Creates a new employee."""
    data = request.get_json()
    if not data or 'name' not in data or not data['name'].strip():
        return jsonify({"error": "Missing or empty 'name' in request body"}), 400

    employee_name = data['name'].strip()

    try:
        new_employee = system.create_employee(employee_name)
        return jsonify(new_employee.to_dict()), 201  # 201 Created
    except Exception as e:
        logging.error(f"An unexpected error occurred while creating employee: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

@app.route('/api/roles', methods=['GET'])
def get_roles():
    """Returns a list of all available roles."""
    all_roles = [role.__dict__ for role in system.roles.values()]
    return jsonify(all_roles)

@app.route('/api/employees/<string:employee_id>/assign-roles', methods=['PUT'])
def assign_roles(employee_id):
    """Assigns a new set of roles to an employee."""
    data = request.get_json()
    if not data or 'role_ids' not in data or not isinstance(data['role_ids'], list):
        return jsonify({"error": "Request body must contain a 'role_ids' list."}), 400

    new_role_ids = data['role_ids']

    try:
        system.assign_roles_to_employee(employee_id, new_role_ids)
        updated_employee = system.get_employee(employee_id)
        return jsonify(updated_employee.to_dict())
    except EmployeeNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except SystemError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.error(f"An unexpected error occurred while assigning roles: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500


# --- Main Execution ---
if __name__ == "__main__":
    # Setting debug=True allows for auto-reloading when you save the file.
    # Do not use debug=True in a production environment.
    app.run(debug=True, port=5001)