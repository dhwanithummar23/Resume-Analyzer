import sqlite3
import hashlib

DB_NAME = "users.db"


def connect_db():
    return sqlite3.connect(DB_NAME)


def create_users_table():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

def create_history_table():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            resume_score INTEGER,
            job_description TEXT,
            analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users(username, password) VALUES(?, ?)",
            (username, hash_password(password))
        )

        conn.commit()
        conn.close()
        return True

    except sqlite3.IntegrityError:
        conn.close()
        return False


def login_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, hash_password(password))
    )

    user = cursor.fetchone()

    conn.close()

    return user

def save_history(username, score, job_description, analysis):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO history
        (username,resume_score,job_description,analysis)
        VALUES(?,?,?,?)
    """, (
        username,
        score,
        job_description,
        analysis
    ))

    conn.commit()
    conn.close()

def get_history(username):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,resume_score,created_at
        FROM history
        WHERE username=?
        ORDER BY created_at DESC
    """, (username,))

    data = cursor.fetchall()

    conn.close()

    return data

def get_single_history(history_id):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM history
        WHERE id=?
    """, (history_id,))

    data = cursor.fetchone()

    conn.close()

    return data

def delete_history(history_id):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM history WHERE id=?",
        (history_id,)
    )

    conn.commit()
    conn.close()