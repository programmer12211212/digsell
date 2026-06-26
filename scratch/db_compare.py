import sqlite3

def compare():
    db1 = 'db.sqlite3'
    db2 = r'c:\Users\acer\Desktop\platforma (2) (2)\platforma (2)\platforma\db.sqlite3'
    
    conn1 = sqlite3.connect(db1)
    conn2 = sqlite3.connect(db2)
    
    cursor1 = conn1.cursor()
    cursor2 = conn2.cursor()
    
    tables1 = [r[0] for r in cursor1.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    tables2 = [r[0] for r in cursor2.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    
    print(f"Active DB tables: {len(tables1)}, Desktop DB tables: {len(tables2)}")
    
    # Check tables with different row counts
    all_tables = set(tables1).union(set(tables2))
    for table in sorted(all_tables):
        if table.startswith('sqlite_') or table.startswith('django_'):
            continue
        try:
            count1 = cursor1.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except Exception:
            count1 = "N/A"
        try:
            count2 = cursor2.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except Exception:
            count2 = "N/A"
            
        if count1 != count2:
            print(f"Table {table}: Active DB = {count1} | Desktop DB = {count2}")

if __name__ == '__main__':
    compare()
