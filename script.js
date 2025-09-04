document.addEventListener('DOMContentLoaded', () => {
    const employeeSelect = document.getElementById('employee-select');
    const roleSelect = document.getElementById('role-select');
    const assignBtn = document.getElementById('assign-role-btn');
    const employeeListDiv = document.getElementById('employee-list');
    const newEmployeeNameInput = document.getElementById('new-employee-name');
    const createEmployeeBtn = document.getElementById('create-employee-btn');
    const messageArea = document.getElementById('message-area');

    // --- Data Fetching and Rendering ---

    async function fetchEmployees() {
        try {
            const response = await fetch('/api/employees');
            const employees = await response.json();
            
            // Populate the dropdown
            employeeSelect.innerHTML = employees.map(emp => `<option value="${emp.employee_id}">${emp.name}</option>`).join('');
            
            // Render the employee list
            renderEmployeeList(employees);
        } catch (error) {
            console.error('Failed to fetch employees:', error);
            employeeListDiv.innerHTML = '<p style="color: red;">Error loading employee data.</p>';
        }
    }

    async function fetchRoles() {
        try {
            const response = await fetch('/api/roles');
            const roles = await response.json();
            roleSelect.innerHTML = roles.map(role => `<option value="${role.role_id}">${role.name}</option>`).join('');
        } catch (error) {
            console.error('Failed to fetch roles:', error);
        }
    }

    function renderEmployeeCard(emp) {
        return `
            <div class="employee-card" id="employee-card-${emp.employee_id}">
                <p><strong>Name:</strong> ${emp.name} (ID: ${emp.employee_id})</p>
                <p><strong>Current Role:</strong> ${emp.current_role ? emp.current_role.name : 'Not Assigned'}</p>
                <p><strong>Assigned Courses:</strong></p>
                <ul>
                    ${emp.assigned_courses.length > 0 ? emp.assigned_courses.map(c => `<li>${c.title}</li>`).join('') : '<li>None</li>'}
                </ul>
            </div>
        `;
    }

    function renderEmployeeList(employees) {
        if (!employees || employees.length === 0) {
            employeeListDiv.innerHTML = '<p>No employees found.</p>';
            return;
        }

        employeeListDiv.innerHTML = employees.map(renderEmployeeCard).join('');
    }

    // --- Event Handling ---

    async function handleCreateEmployee() {
        const name = newEmployeeNameInput.value.trim();
        if (!name) {
            showMessage('Please enter a name for the new employee.', 'red');
            return;
        }

        createEmployeeBtn.disabled = true;
        createEmployeeBtn.textContent = 'Creating...';

        try {
            const response = await fetch('/api/employees', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name })
            });

            const newEmployee = await response.json();

            if (!response.ok) {
                throw new Error(newEmployee.error || 'Failed to create employee.');
            }

            showMessage(`Successfully created employee: ${newEmployee.name}.`, 'green');

            // If the "no employees" message is showing, clear it.
            const noEmployeesP = employeeListDiv.querySelector('p');
            if (noEmployeesP && noEmployeesP.textContent === 'No employees found.') {
                employeeListDiv.innerHTML = '';
            }

            // Dynamically update the UI
            // 1. Add to the employee list
            employeeListDiv.insertAdjacentHTML('beforeend', renderEmployeeCard(newEmployee));

            // 2. Add to the dropdown
            const newOption = document.createElement('option');
            newOption.value = newEmployee.employee_id;
            newOption.textContent = newEmployee.name;
            employeeSelect.appendChild(newOption);

            // 3. Select the new employee in the dropdown for immediate action
            employeeSelect.value = newEmployee.employee_id;

            // 4. Highlight the new card and clear input
            const newCard = document.getElementById(`employee-card-${newEmployee.employee_id}`);
            newCard.classList.add('updated');
            setTimeout(() => newCard.classList.remove('updated'), 2000);
            newEmployeeNameInput.value = '';

        } catch (error) {
            console.error('Creation error:', error);
            showMessage(error.message, 'red');
        } finally {
            createEmployeeBtn.disabled = false;
            createEmployeeBtn.textContent = 'Create Employee';
        }
    }

    async function handleAssignRole() {
        const employeeId = employeeSelect.value;
        const roleId = roleSelect.value;

        if (!employeeId || !roleId) {
            showMessage('Please select both an employee and a role.', 'red');
            return;
        }

        assignBtn.disabled = true;
        assignBtn.textContent = 'Assigning...';

        try {
            const response = await fetch(`/api/employees/${employeeId}/assign-role`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role_id: roleId })
            });

            const updatedEmployee = await response.json();

            if (!response.ok) {
                throw new Error(updatedEmployee.error || 'Failed to assign role.');
            }
            
            showMessage(`Successfully assigned new role to ${updatedEmployee.name}.`, 'green');

            // Instead of re-fetching the whole list, just update the one card
            const cardToUpdate = document.getElementById(`employee-card-${updatedEmployee.employee_id}`);
            if (cardToUpdate) {
                cardToUpdate.outerHTML = renderEmployeeCard(updatedEmployee);
                // Find the newly replaced card and highlight it
                const newCard = document.getElementById(`employee-card-${updatedEmployee.employee_id}`);
                newCard.classList.add('updated');
                setTimeout(() => newCard.classList.remove('updated'), 2000);
            } else {
                // Fallback just in case
                fetchEmployees();
            }

        } catch (error) {
            console.error('Assignment error:', error);
            showMessage(error.message, 'red');
        } finally {
            assignBtn.disabled = false;
            assignBtn.textContent = 'Assign Role';
        }
    }

    function showMessage(text, color) {
        messageArea.textContent = text;
        messageArea.style.color = color;
        setTimeout(() => { messageArea.textContent = ''; }, 5000);
    }

    // --- Initial Load ---

    createEmployeeBtn.addEventListener('click', handleCreateEmployee);
    assignBtn.addEventListener('click', handleAssignRole);
    fetchEmployees();
    fetchRoles();
});