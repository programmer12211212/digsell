import sqlite3

def inspect_tables():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    tables = [
        'telegram_services_telegramproduct',
        'telegram_services_telegramorder',
        'telegram_services_telegramnotification',
        'telegram_services_telegrampayment',
        'telegram_services_telegramorderlog',
        'telegram_services_telegramrewardclaim',
        'telegram_services_telegramrewardstage'
    ]
    
    for t in tables:
        try:
            cursor.execute(f"SELECT * FROM {t} LIMIT 1")
            col_names = [description[0] for description in cursor.description]
            print(f"Table: {t}\nColumns: {col_names}\n")
        except Exception as e:
            print(f"Table: {t} failed: {e}\n")

if __name__ == '__main__':
    inspect_tables()
