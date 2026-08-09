import sqlite3

conn = sqlite3.connect("tracefix.db")
cursor = conn.cursor()
cursor.execute("SELECT stack_trace FROM logentry WHERE id = ?", ("log_e6eaf87d",))
row = cursor.fetchone()

if row:
    print(row[0])
else:
    print("No matching log found")