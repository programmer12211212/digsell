import sqlite3, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db = os.path.join(BASE, 'db.sqlite3')
print('DB path:', db)
if not os.path.exists(db):
    print('DB not found')
else:
    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.execute("PRAGMA table_info(users_user);")
    rows = cur.fetchall()
    print('users_user columns:')
    for r in rows:
        print(r)
    con.close()
