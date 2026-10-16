import sqlite3

def init_db():
    conn = sqlite3.connect('bot_database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # ইউজার টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0.0,
            pending_withdraw REAL DEFAULT 0.0,
            pending_work REAL DEFAULT 0.0,
            total_income REAL DEFAULT 0.0,
            completed_tasks INTEGER DEFAULT 0,
            review_tasks INTEGER DEFAULT 0
        )
    ''')
    
    # সাবমিশন টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            category TEXT,
            total_ids INTEGER,
            status TEXT DEFAULT 'Pending',
            date TEXT
        )
    ''')
    
    # উইথড্র টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdraws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            method TEXT,
            account_info TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
