import sqlite3

def fix_missing_columns():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    columns_to_add = [
        ("rarity", "varchar(20) DEFAULT 'common'"),
        ("is_resale", "bool NOT NULL DEFAULT 0"),
        ("price_stars", "integer NULL")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE telegram_services_telegramproduct ADD COLUMN {col_name} {col_type}")
            conn.commit()
            print(f"Successfully added column {col_name}.")
        except Exception as e:
            print(f"Failed to add column {col_name}: {e}")
            
    conn.close()

if __name__ == '__main__':
    fix_missing_columns()
