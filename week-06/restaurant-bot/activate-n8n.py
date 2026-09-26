import sqlite3

db = sqlite3.connect('/home/huzaifa/.local/share/containers/storage/volumes/n8n-restaurant-data/_data/database.sqlite')
cursor = db.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print('All tables:', tables)

wf_tables = [t for t in tables if 'workflow' in t.lower() or 'entity' in t.lower()]
print('Workflow tables:', wf_tables)

for t in wf_tables:
    cursor.execute(f'SELECT id, name, active FROM "{t}" WHERE name LIKE "%SpiceRoute%"')
    rows = cursor.fetchall()
    if rows:
        print(f'Found in {t}: id={rows[0][0]}, name={rows[0][1]}, active={rows[0][2]}')
        cursor.execute(f'UPDATE "{t}" SET active = 1 WHERE name LIKE "%SpiceRoute%"')
        db.commit()
        print('Activated!')
        cursor.execute(f'SELECT id, name, active FROM "{t}" WHERE name LIKE "%SpiceRoute%"')
        print('After:', cursor.fetchall())
        break

db.close()
