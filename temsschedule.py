import streamlit as st
from collections import defaultdict

st.title("Tulane EMS Scheduler")

# from streamlit_gsheets import GSheetsConnection
#
# # Create a connection object.
# sheet = st.connection("gsheets", type=GSheetsConnection)
# df = sheet.read()
#
# # Print results.
# def fetch_employees_from_sheet():
#     employees = []
#     rows = sheet.get_all_records()  # Get all rows from the sheet
#     for row in rows:
#         name = row["Name"]
#         rank = row["Rank"]
#         marker = row["Marker"]
#         donotschedule = row["DoNotSchedule"].split(",") if row["DoNotSchedule"] else []
#         employees.append(Employee(name, rank, donotschedule_list=donotschedule, marker=marker))
#     return employees

# Define Employee class
class Employee:
    def __init__(self, name, rank, available_shifts=None, donotschedule_list=None, marker=False):
        self.name = name
        self.rank = rank
        self.marker = marker  # New marker attribute
        self.available_shifts = available_shifts if available_shifts else []
        self.donotschedule_list = donotschedule_list if donotschedule_list else []
        self.scheduled_shifts = []

    def is_available(self, shift):
        return shift in self.available_shifts

    def can_work_with(self, other_employee):
        return other_employee.name not in self.donotschedule_list


alert_placeholder = st.empty()


# Define ShiftScheduler class
class ShiftScheduler:
    def __init__(self, shifts, employees, past_schedules):
        self.shifts = shifts
        self.employees = employees
        self.past_schedules = past_schedules  # Store past finalized schedules
        self.schedule = {shift: [] for shift in shifts}

    def assign_shifts(self):
        unscheduled_last_time = self.get_unscheduled_employees()

        for shift in self.shifts:
            available_employees = [e for e in self.employees if e.is_available(shift)]

            # Prioritize: (1) Unscheduled employees from last time, (2) Markers, (3) Rank
            available_employees.sort(key=lambda e: (e not in unscheduled_last_time, e.rank, not e.marker))

            assigned_ranks = set()
            self.schedule[shift] = []
            has_marker = False  # Track if at least one marker is assigned

            for emp in available_employees:
                if emp.rank not in assigned_ranks or emp.marker:
                    self.schedule[shift].append(emp)
                    assigned_ranks.add(emp.rank)
                    has_marker = has_marker or emp.marker
                    emp.scheduled_shifts.append(shift)
                if len(assigned_ranks) == 3:
                    break

            self.check_donotschedule_list_conflicts(shift)

            # Alert if no marked employees in the shift
            # Collect all shifts that do not have a marked employee
            # Check if we already displayed an alert for missing shifts
            # if 'alert_displayed' not in st.session_state:
            #     # Collect all shifts that do not have a marked employee
            #     missing_marked_shifts = []
            #
            #     # Loop through all shifts in the schedule
            #     for shift in self.schedule:
            #         if not any(emp.marker for emp in self.schedule[shift]):
            #             missing_marked_shifts.append(shift)
            #
            #     # If there are any shifts without a marked employee, display only one alert
            #     if missing_marked_shifts:
            #         alert_message = "ALERT: The following shifts have no marked employee assigned:\n"
            #         for shift in missing_marked_shifts:
            #             alert_message += f"- {shift}\n"
            #
            #         # Show the alert only once with the full list of missing shifts
            #         st.warning(alert_message)
            #
            #         # Mark that the alert has been displayed
            #         st.session_state.alert_displayed = True

    def get_unscheduled_employees(self):
        """Find employees who were NOT scheduled last time."""
        if not self.past_schedules:
            return set()  # No history, no prioritization needed

        last_schedule = self.past_schedules[-1]  # Get the most recent finalized schedule
        scheduled_last_time = {emp for shift in last_schedule.values() for emp in shift}
        return {emp for emp in self.employees if emp not in scheduled_last_time}

    def check_donotschedule_list_conflicts(self, shift):
        assigned_employees = self.schedule[shift]
        for i, emp1 in enumerate(assigned_employees):
            for emp2 in assigned_employees[i + 1:]:
                if emp1.name in emp2.donotschedule_list or emp2.name in emp1.donotschedule_list:
                    st.warning(
                        f"ALERT: {emp1.name} cannot work with {emp2.name} on {shift} (Do Not Schedule conflict).")

    def display_schedule(self):
        missing_marked_shifts = [shift for shift, employees in self.schedule.items() if
                                 not any(emp.marker for emp in employees)]

        if missing_marked_shifts:
            alert_message = "ALERT: The following shifts have no marked employee assigned:\n"
            for shift in missing_marked_shifts:
                alert_message += f"- {shift}\n"
            alert_placeholder.warning(alert_message)

        return self.schedule


# Initialize session state for schedule history
if 'past_schedules' not in st.session_state:
    st.session_state['past_schedules'] = []

# Initialize session state for employee availability
if 'employee_availability' not in st.session_state:
    st.session_state['employee_availability'] = {}

# Predefined employee data with markers
predefined_employees = [
Employee("A. Thompson", 3, donotschedule_list=["D. Gee"], marker=True),  # Marked employee
    Employee("B. Martinez", 3, marker = True),
    Employee("C. Peterson", 3, marker=True),  # Marked employee
    Employee("D. Gee", 3, marker=True),
    Employee("E. Smith", 3, marker=True),
    Employee("F. Wilson", 3, marker=True),
    Employee("G. Scott", 3, donotschedule_list=["F. Wilson"]),
    Employee("H. Moore", 3, marker=True),  # Marked employee
    Employee("I. Taylor", 3, marker=True),
    Employee("J. Harris", 3, marker=True),
    Employee("K. Young", 3),
    Employee("L. King", 3),
    Employee("M. Lewis", 3),
    Employee("N. Potts", 3, donotschedule_list=["A. Reed"]),
    Employee("B. Giggs", 3, donotschedule_list=["O. Allen"], marker=True),
    Employee("O. Allen", 2),
    Employee("P. Walker", 2, marker=True),  # Marked employee
    Employee("Q. Adams", 2, marker=True),
    Employee("R. Robinson", 2),
    Employee("S. Carter", 2, marker=True),
    Employee("T. Mitchell", 2),
    Employee("U. Karris", 2, marker=True),
    Employee("V. Hill", 2),
    Employee("W. Jackson", 2, marker=True),
    Employee("X. Bieber", 2),
    Employee("Y. Thomas", 2, marker=True),
    Employee("A. Reed", 2),
    Employee("B. Nelson", 2, marker=True),
    Employee("C. Wright", 2),
    Employee("D. Garcia", 1, marker=True),
    Employee("E. Lopez", 1),
    Employee("F. Collins", 1, marker=True),
    Employee("G. Prince", 1, marker=True),  # Marked employee
    Employee("H. Rivera", 1),
    Employee("I. Brooks", 1, marker=True),
    Employee("J. Murphy", 1, marker=True),
    Employee("K. Sanchez", 1),
    Employee("L. Foster", 1, marker=True),
    Employee("M. Bennett", 1),
    Employee("N. Gray", 1, marker=True),
    Employee("O. Wilde", 1),
    Employee("P. Turner", 1, marker=True),
    Employee("Q. Driver", 1),
]

# Streamlit UI
st.title("Shift Scheduler")
tab1, tab2, tab3, tab4 = st.tabs(["Schedule", "Employee Availability", "Past Finalized Schedules", "Manage Employees"])

# Select employee
st.sidebar.header("Select Employee")
employee_names = [emp.name for emp in predefined_employees]
selected_name = st.sidebar.selectbox("Employee Name", employee_names)
selected_employee = next(emp for emp in predefined_employees if emp.name == selected_name)

# Load existing availability from session state
existing_availability = st.session_state['employee_availability'].get(selected_employee.name, [])

# Input availability
available_shifts = st.sidebar.multiselect("Available Shifts",
                                          ["Monday A", "Monday B", "Tuesday A", "Tuesday B", "Wednesday A",
                                           "Wednesday B",
                                           "Thursday A", "Thursday B", "Friday A", "Friday B", "Saturday A",
                                           "Saturday B", "Sunday A", "Sunday B"],
                                          default=existing_availability)

if st.sidebar.button("Set Availability"):
    st.session_state['employee_availability'][selected_employee.name] = available_shifts
    selected_employee.available_shifts = available_shifts
    st.sidebar.success(f"Updated availability for {selected_employee.name}")

# Apply session state availability to employees
for emp in predefined_employees:
    emp.available_shifts = st.session_state['employee_availability'].get(emp.name, [])

st.session_state.alert_displayed = False
# Initialize scheduler
scheduler = ShiftScheduler(
    ["Monday A", "Monday B", "Tuesday A", "Tuesday B", "Wednesday A", "Wednesday B",
     "Thursday A", "Thursday B", "Friday A", "Friday B", "Saturday A", "Saturday B", "Sunday A", "Sunday B"],
    predefined_employees,
    st.session_state['past_schedules'])
scheduler.assign_shifts()
schedule = scheduler.display_schedule()

# Display schedule
with tab1:
    st.header("Generated Schedule")
    for shift, employees in schedule.items():
        st.subheader(shift)
        for emp in employees:
            marker_symbol = "*" if emp.marker else ""  # Display marker
            st.write(f"- {emp.name} (Rank {emp.rank}) {marker_symbol}")
    # Finalize schedule button
    if st.button("Finalize Schedule"):
        st.session_state['past_schedules'].append(schedule)
        st.success("Schedule finalized and saved!")

with tab2:
    st.header("Employee Availability")
    for emp, shifts in st.session_state['employee_availability'].items():
        st.write(f"**{emp}:** {', '.join(shifts)}")

# # Finalize schedule button
# if st.button("Finalize Schedule"):
#     st.session_state['past_schedules'].append(schedule)
#     st.success("Schedule finalized and saved!")

# Display past schedules
with tab3:
    st.header("Past Finalized Schedules")
    for i, past_schedule in enumerate(st.session_state['past_schedules']):
        st.subheader(f"Finalized Schedule #{i + 1}")
        for shift, employees in past_schedule.items():
            st.write(f"**{shift}**: " + ", ".join(emp.name for emp in employees))
with tab4:
    st.title("Manage Employees")
    # Initialize session state
    if 'employees' not in st.session_state:
        st.session_state['employees'] = []  # Start with no predefined employees
    if 'employee_availability' not in st.session_state:
        st.session_state['employee_availability'] = {}

    # Employee creation form
    with st.expander("Create New Employee"):
        st.subheader("Add New Employee")
        new_employee_name = st.text_input("Name")
        new_employee_rank = st.selectbox("Rank", [1, 2, 3])
        new_employee_marker = st.checkbox("Is Marker?")
        new_employee_donotschedule = st.text_input("Do Not Schedule (comma separated names)")

        if st.button("Create Employee"):
            # Create a new employee and add to session state
            donotschedule_list = [x.strip() for x in new_employee_donotschedule.split(',') if x.strip()]
            new_employee = Employee(new_employee_name, new_employee_rank, donotschedule_list=donotschedule_list,
                                    marker=new_employee_marker)
            st.session_state['employees'].append(new_employee)  # Add employee to session state

            # Reset input fields
            st.success(f"Employee {new_employee_name} created successfully!")

    # Employee dropdown to modify or set availability
    st.sidebar.header("Select Employee")
    employee_names = [emp.name for emp in st.session_state['employees']]
    if employee_names:
        selected_name = st.sidebar.selectbox("Employee Name", employee_names, key="employee_dropdown")

        # Get selected employee object
        selected_employee = next(emp for emp in st.session_state['employees'] if emp.name == selected_name)

        # Set availability for the selected employee
        available_shifts = st.sidebar.multiselect("Available Shifts",
                                                  ["Monday A", "Monday B", "Tuesday A", "Tuesday B", "Wednesday A",
                                                   "Wednesday B",
                                                   "Thursday A", "Thursday B", "Friday A", "Friday B", "Saturday A",
                                                   "Saturday B", "Sunday A", "Sunday B"],
                                                  default=st.session_state['employee_availability'].get(
                                                      selected_employee.name, []))

        if st.sidebar.button("Set Availability"):
            st.session_state['employee_availability'][selected_employee.name] = available_shifts
            selected_employee.available_shifts = available_shifts
            st.sidebar.success(f"Updated availability for {selected_employee.name}")

    # Modify employee details
    with st.expander("Modify Employee"):
        st.subheader("Modify Existing Employee")

        if employee_names:
            modify_employee_name = st.selectbox("Select Employee to Modify", employee_names, key="modify_employee_name")
            modify_employee = next(emp for emp in st.session_state['employees'] if emp.name == modify_employee_name)

            modify_employee_rank = st.selectbox("Rank", [1, 2, 3], index=[1, 2, 3].index(modify_employee.rank),
                                                key="modify_employee_rank")
            modify_employee_marker = st.checkbox("Is Marker?", value=modify_employee.marker,
                                                 key="modify_employee_marker")
            modify_employee_donotschedule = st.text_input("Do Not Schedule (comma separated names)",
                                                          ', '.join(modify_employee.donotschedule_list),
                                                          key="modify_employee_donotschedule")

            if st.button("Update Employee", key="update_employee"):
                modify_employee.rank = modify_employee_rank
                modify_employee.marker = modify_employee_marker
                modify_employee.donotschedule_list = [x.strip() for x in modify_employee_donotschedule.split(',') if
                                                      x.strip()]
                st.success(f"Employee {modify_employee.name} updated successfully!")

    # Delete employee functionality
    with st.expander("Delete Employee"):
        st.subheader("Delete Employee")

        if employee_names:
            delete_employee_name = st.selectbox("Select Employee to Delete", employee_names, key="delete_employee_name")
            delete_employee = next(emp for emp in st.session_state['employees'] if emp.name == delete_employee_name)

            if st.button("Delete Employee", key="delete_employee_button"):
                st.session_state['employees'].remove(delete_employee)  # Remove from employees list
                st.session_state['employee_availability'].pop(delete_employee.name, None)  # Remove availability
                st.success(f"Employee {delete_employee_name} deleted successfully!")

    # Display employee list for confirmation
    st.write("Current Employees:")
    for emp in st.session_state['employees']:
        st.write(
            f"- {emp.name}, Rank {emp.rank}, Marker: {emp.marker}, Do Not Schedule: {', '.join(emp.donotschedule_list)}")

