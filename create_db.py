import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

# ถ้ามีฐานข้อมูลเดิม ให้ลบทิ้ง (ใช้เฉพาะตอนสร้างใหม่)
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ==========================
# ตารางผู้ใช้
# ==========================
cursor.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

# Admin
cursor.execute("""
INSERT INTO users (username, password, role)
VALUES (?, ?, ?)
""", ("jojo", "2550", "admin"))

# User
cursor.execute("""
INSERT INTO users (username, password, role)
VALUES (?, ?, ?)
""", ("usermax", "1111", "user"))

# ==========================
# ตารางแจ้งซ่อม
# ==========================
cursor.execute("""
CREATE TABLE repairs (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT NOT NULL,
    fullname TEXT NOT NULL,
    department TEXT NOT NULL,

    equipment TEXT NOT NULL,
    problem TEXT NOT NULL,

    video TEXT,

    status TEXT DEFAULT 'รอดำเนินการ',

    parts TEXT,
    parts_price REAL DEFAULT 0,
    labor_price REAL DEFAULT 0,
    discount REAL DEFAULT 0,
    total_price REAL DEFAULT 0,
    note TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ==========================
# ตารางรูปภาพ
# ==========================
cursor.execute("""
CREATE TABLE repair_images (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    repair_id INTEGER NOT NULL,

    filename TEXT NOT NULL,

    FOREIGN KEY(repair_id)
        REFERENCES repairs(id)
        ON DELETE CASCADE
)
""")

conn.commit()
conn.close()

print("สร้างฐานข้อมูลสำเร็จ")