import sqlite3
conn = sqlite3.connect("tracefix.db")
conn.execute("UPDATE project SET github_repo = ? WHERE id = ?", ("tracefix-test-app", "proj_d9df37a5"))
conn.commit()
print(conn.execute("SELECT id, github_owner, github_repo FROM project WHERE id = ?", ("proj_d9df37a5",)).fetchone())