import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection
c = connection.cursor()
for t in ['users_user', 'users_wallet', 'orders_order', 'orders_orderitem']:
    try:
        c.execute(f'PRAGMA table_info({t})')
        print(t, [x[1] for x in c.fetchall()])
    except Exception as e:
        print(t, 'ERROR', e)
