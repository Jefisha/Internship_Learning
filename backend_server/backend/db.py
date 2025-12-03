import sqlite3, time

con = sqlite3.connect("history.db", check_same_thread=False)
cur = con.cursor()

# Create table
cur.execute("""
CREATE TABLE IF NOT EXISTS history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    answer TEXT,
    timestamp TEXT
)
""")
con.commit()

def save_history(q, a):
    cur.execute("INSERT INTO history (question, answer, timestamp) VALUES (?, ?, ?)",
                (q, a, time.ctime()))
    con.commit()

def get_all_history():
    cur.execute("SELECT * FROM history")
    rows = cur.fetchall()
    return [
        {"id": r[0], "question": r[1], "answer": r[2], "timestamp": r[3]}
        for r in rows
    ]
