import sqlite3
import os

def init_db(db_path="db/event_history.db"):
    if os.path.exists(db_path):
        print("✅ Database already exists. Skipping setup.")
        return
    

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE events (
            system_id TEXT,
            checkpoint_id TEXT,
            timestamp TEXT,
            status TEXT,
            correlation_id TEXT,
            failure_reason TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print(f"✅ Created SQLite DB at {db_path}")

if __name__ == "__main__":
    init_db()
