import psycopg2

conn = psycopg2.connect(
    dbname="hr_agent",
    user="postgres",
    password="hussaindb",   # apna actual password daalna
    host="localhost",
    port="5432"
)
cur = conn.cursor()

privacy_policy = """
General Company Policy

Leave Policy

Annual Allocation:

15 Sick Leaves per year

15 Paid Leaves per year

7 Casual Leaves per year

Monthly Restriction:

Maximum 5 leaves are allowed in one month.

Any leave beyond this limit will be considered Unpaid Leave.

Special Rules:

No leaves are allowed during the week of a project deadline.

Leaves in the last 5 days of the month require Manager/HR approval.

The last 7 days of each month are considered Blackout Days. Any leave during this period requires Manager/HR approval.

The last Saturday of each month will be a working day, while all other Saturdays will remain off.

Uninformed Absence:

If an employee takes leave without informing or approval, they must submit a leave application.

Salary deduction will be applied for such days.

Work Commitment

If a client meeting is scheduled at night, attendance is mandatory online.

Employees may be required to work overtime or put in extra effort to meet project deadlines.

Professional Conduct

Employees are expected to maintain punctuality and discipline.

The workplace must remain professional – unnecessary gossip, casual interactions, and disturbances are discouraged.

Free time should be utilized for skill development and research.

Performance & Responsibility

Employees are responsible for completing assigned tasks on time.

Any delay must be communicated to the manager in advance.

Violation of policy may lead to disciplinary action.

Additional Notes

The company reserves the right to update policies at any time based on business needs.

All employees will be notified of policy updates via HR notices or email.
"""

cur.execute("""
    INSERT INTO company_policies (title, content)
    VALUES (%s, %s)
""", ("Privacy Policy", privacy_policy))

conn.commit()
print("✅ Privacy Policy added successfully")

cur.close()
conn.close()
