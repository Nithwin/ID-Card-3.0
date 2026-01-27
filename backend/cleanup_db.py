"""
Database cleanup script to remove test/dummy violation data
"""
import sqlite3
import os

db_path = "database.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Delete all violations (fresh start)
    cursor.execute("DELETE FROM violationlog")
    deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"[INFO] Deleted {deleted} violation records from database")
    print("[INFO] Database cleaned successfully")
else:
    print(f"[ERROR] Database file not found: {db_path}")
