# db.py
import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname="hr_agent",
        user="postgres",
        password="hussaindb",   # apna actual password daalna
        host="localhost",
        port="5432"
    )


def employee_login(emp_id, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, department, leave_balance FROM employees WHERE id = %s AND password = %s",
        (emp_id, password)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


# Add new policy
def add_policy(title, content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO company_policies (title, content) VALUES (%s, %s)",
        (title, content)
    )
    conn.commit()
    print("✅ Policy added successfully!")
    cur.close()
    conn.close()

# View all policies
def view_policies():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, content, created_at FROM company_policies;")
    rows = cur.fetchall()
    print("\n--- Company Policies ---")
    for row in rows:
        print(f"ID: {row[0]} | Title: {row[1]}\n{row[2]}\n(Added on: {row[3]})\n")
    cur.close()
    conn.close()

def update_password(emp_id, new_password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE employees SET password = %s WHERE id = %s",
        (new_password, emp_id)
    )
    conn.commit()
    print("✅ Password updated successfully!")
    cur.close()
    conn.close()


def view_data():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, department, leave_balance FROM employees;")
    rows = cur.fetchall()
    print("\n--- Employees Data ---")
    for row in rows:
        print(row)
    cur.close()
    conn.close()

def add_data(name, department, leave_balance):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO employees (name, department, leave_balance) VALUES (%s, %s, %s)",
        (name, department, leave_balance)
    )
    conn.commit()
    print("✅ Employee added successfully!")
    cur.close()
    conn.close()

def update_data(emp_id, leave_balance):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE employees SET leave_balance = %s WHERE id = %s",
        (leave_balance, emp_id)
    )
    conn.commit()
    print("✅ Employee updated successfully!")
    cur.close()
    conn.close()

def delete_data(emp_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM employees WHERE id = %s", (emp_id,))
    conn.commit()
    print("✅ Employee deleted successfully!")
    cur.close()
    conn.close()
