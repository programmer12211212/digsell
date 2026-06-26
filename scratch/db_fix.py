import sqlite3

def run_db_fix():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # 1. Add missing column seller_id to telegram_services_telegramproduct
    try:
        cursor.execute("ALTER TABLE telegram_services_telegramproduct ADD COLUMN seller_id char(32) REFERENCES users_user(id) DEFERRABLE INITIALLY DEFERRED")
        conn.commit()
        print("Successfully added seller_id column.")
    except Exception as e:
        print("Failed or column already exists:", e)
        
    conn.close()

if __name__ == '__main__':
    run_db_fix()
