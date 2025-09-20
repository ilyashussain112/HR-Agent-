# main.py
import data as db

def handle_view():
    db.view_data()

def handle_add():
    name = input("Enter employee name: ")
    department = input("Enter department: ")
    leave_balance = int(input("Enter leave balance: "))
    db.add_data(name, department, leave_balance)

def handle_update():
    emp_id = int(input("Enter employee ID to update: "))
    leave_balance = int(input("Enter new leave balance: "))
    db.update_data(emp_id, leave_balance)

def handle_delete():
    emp_id = int(input("Enter employee ID to delete: "))
    db.delete_data(emp_id)

def handle_employee_portal():
    print("\n--- Employee Portal ---")
    emp_id = int(input("Enter your Employee ID: "))
    password = input("Enter your password: ")

    emp_data = db.employee_login(emp_id, password)

    if emp_data:
        print("\n✅ Login successful! Here is your data:")
        print(f"ID: {emp_data[0]}")
        print(f"Name: {emp_data[1]}")
        print(f"Department: {emp_data[2]}")
        print(f"Leave Balance: {emp_data[3]}")
    else:
        print("❌ Invalid ID or Password. Please try again.")

def handle_password_update():
    emp_id = int(input("Enter Employee ID: "))
    new_password = input("Enter new password: ")
    db.update_password(emp_id, new_password)


def handle_add_policy():
    title = input("Enter policy title: ")
    content = input("Enter policy content: ")
    db.add_policy(title, content)

def handle_view_policies():
    db.view_policies()

def main_menu():
    print("\n--- HR Agent Menu ---")
    print("1. View all employees (Admin)")
    print("2. Add employee (Admin)")
    print("3. Update employee (Admin)")
    print("4. Delete employee (Admin)")
    print("5. Employee Portal (Self Service)")
    print("6. Update employee password (Admin)")
    print("7. Add Company Policy (Admin)")
    print("8. View Company Policies (All)")
    print("9. Exit")
    return input("Enter choice (1-9): ")

def run():
    while True:
        choice = main_menu()
        actions = {
            "1": handle_view,
            "2": handle_add,
            "3": handle_update,
            "4": handle_delete,
            "5": handle_employee_portal,
            "6": handle_password_update,
            "7": handle_add_policy,
            "8": handle_view_policies,
            "9": exit
        }
        action = actions.get(choice)
        if action:
            action()
        else:
            print("❌ Invalid choice, please try again.")
if __name__ == "__main__":
    run()