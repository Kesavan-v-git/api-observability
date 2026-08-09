import sqlite3
conn = sqlite3.connect("tracefix.db")
print(conn.execute("SELECT id, github_owner, github_repo FROM project WHERE id = ?", ("proj_d9df37a5",)).fetchone())
