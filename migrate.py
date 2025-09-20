# migrate.py
import psycopg2

conn = psycopg2.connect(
    dbname="hr_agent",
    user="postgres",
    password="hussaindb",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

cur.execute("ALTER TABLE employees ADD COLUMN password VARCHAR(50);")
conn.commit()

print("✅ Column 'password' added successfully!")

cur.close()
conn.close()
