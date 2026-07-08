import sqlite3

DB_NAME = "db.sqlite3"

# Tables you want to delete
tables_to_delete = [
    "live_tracking_trackingsession",
    "live_tracking_livelocation",
    "live_tracking_smslog",
    "live_tracking_trackingsms",
]

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = OFF;")

for table in tables_to_delete:
    try:
        cursor.execute(f'DROP TABLE IF EXISTS "{table}";')
        print(f"✅ Dropped: {table}")
    except Exception as e:
        print(f"❌ Error dropping {table}: {e}")

cursor.execute("PRAGMA foreign_keys = ON;")
conn.commit()
conn.close()

print("Done.")