"""
SQLite Database - Handles user preferences and watchlists
"""
import sqlite3
import os
from typing import List, Tuple, Dict

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot_data.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            region TEXT DEFAULT 'US',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            movie_id INTEGER,
            movie_title TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, movie_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            movie_id INTEGER,
            movie_title TEXT,
            rating INTEGER,
            rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, movie_id)
        )
    """)

    conn.commit()
    conn.close()


def set_user_region(user_id: int, region: str, username: str = None) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, username, region)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                region=excluded.region,
                username=excluded.username
        """, (user_id, username, region.upper()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error setting region: {e}")
        return False


def get_user_region(user_id: int) -> str:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT region FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else "US"
    except Exception as e:
        print(f"Error getting region: {e}")
        return "US"


def add_to_watchlist(user_id: int, movie_id: int, movie_title: str) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO watchlist (user_id, movie_id, movie_title)
            VALUES (?, ?, ?)
        """, (user_id, movie_id, movie_title))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error adding to watchlist: {e}")
        return False


def get_watchlist(user_id: int) -> List[Tuple]:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT movie_id, movie_title, added_at FROM watchlist WHERE user_id = ? ORDER BY added_at DESC",
            (user_id,)
        )
        items = cursor.fetchall()
        conn.close()
        return items
    except Exception as e:
        print(f"Error getting watchlist: {e}")
        return []


def remove_from_watchlist(user_id: int, movie_id: int) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?",
            (user_id, movie_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error removing from watchlist: {e}")
        return False


def add_rating(user_id: int, movie_id: int, movie_title: str, rating: int) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ratings (user_id, movie_id, movie_title, rating)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, movie_id) DO UPDATE SET
                rating=excluded.rating,
                rated_at=CURRENT_TIMESTAMP
        """, (user_id, movie_id, movie_title, rating))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding rating: {e}")
        return False


def get_user_stats(user_id: int) -> Dict:
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM watchlist WHERE user_id = ?", (user_id,))
        watchlist_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM ratings WHERE user_id = ?", (user_id,))
        ratings_count = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(rating) FROM ratings WHERE user_id = ?", (user_id,))
        avg_rating = cursor.fetchone()[0] or 0

        conn.close()
        return {
            "watchlist_count": watchlist_count,
            "ratings_count": ratings_count,
            "avg_rating": round(avg_rating, 1)
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {"watchlist_count": 0, "ratings_count": 0, "avg_rating": 0}
