import sqlite3

conn = sqlite3.connect("tracefix.db")
cursor = conn.cursor()
cursor.execute("SELECT id, project_id, stack_trace FROM logentry ORDER BY id DESC LIMIT 5")
rows = cursor.fetchall()

print(f"Found {len(rows)} rows")
for row in rows:
    print(row[0], row[1], row[2][:150])