import sqlite3

def check():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    try:
        rows = cursor.execute("SELECT * FROM orders_order LIMIT 5").fetchall()
        colnames = [d[0] for d in cursor.description]
        print("Columns:", colnames)
        for r in rows:
            print(dict(zip(colnames, r)))
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    check()
