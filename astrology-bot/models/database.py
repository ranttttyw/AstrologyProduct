"""
数据库模块 — SQLite
"""
import sqlite3
import json
import os
from datetime import datetime
from config import DB_PATH


def get_db():
    """获取数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 让查询结果可以用字段名访问
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            openid TEXT PRIMARY KEY,
            nickname TEXT DEFAULT '',
            gender TEXT DEFAULT '',
            occupation TEXT DEFAULT '',
            birth_date TEXT,
            birth_time TEXT,
            birth_city TEXT,
            chart_data TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            last_active TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            openid TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'chat',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (openid) REFERENCES users(openid)
        );

        CREATE INDEX IF NOT EXISTS idx_messages_openid
            ON messages(openid, created_at DESC);

        CREATE TABLE IF NOT EXISTS horoscope_cache (
            date TEXT NOT NULL,
            openid TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            PRIMARY KEY (date, openid)
        );
    """)
    conn.commit()

    # 迁移：给旧表加新字段（如果还没有的话）
    try:
        conn.execute("ALTER TABLE users ADD COLUMN gender TEXT DEFAULT ''")
    except Exception:
        pass  # 字段已存在
    try:
        conn.execute("ALTER TABLE users ADD COLUMN occupation TEXT DEFAULT ''")
    except Exception:
        pass
    conn.commit()

    conn.close()
    print("数据库初始化完成")


# ========== 用户操作 ==========

def get_user(openid: str):
    """获取用户信息"""
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE openid = ?", (openid,)).fetchone()
    conn.close()
    if user:
        return dict(user)
    return None


def create_user(openid: str, nickname: str = ""):
    """创建新用户"""
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO users (openid, nickname) VALUES (?, ?)",
        (openid, nickname)
    )
    conn.commit()
    conn.close()


def update_user_chart(openid: str, birth_date: str, birth_time: str,
                      birth_city: str, chart_data: dict):
    """更新用户星盘信息"""
    conn = get_db()
    conn.execute(
        """UPDATE users
           SET birth_date = ?, birth_time = ?, birth_city = ?,
               chart_data = ?, last_active = datetime('now', 'localtime')
           WHERE openid = ?""",
        (birth_date, birth_time, birth_city, json.dumps(chart_data, ensure_ascii=False), openid)
    )
    conn.commit()
    conn.close()


def update_last_active(openid: str):
    """更新最后活跃时间"""
    conn = get_db()
    conn.execute(
        "UPDATE users SET last_active = datetime('now', 'localtime') WHERE openid = ?",
        (openid,)
    )
    conn.commit()
    conn.close()


def update_nickname(openid: str, nickname: str):
    """更新用户昵称"""
    conn = get_db()
    conn.execute(
        "UPDATE users SET nickname = ? WHERE openid = ?",
        (nickname, openid)
    )
    conn.commit()
    conn.close()


def update_user_info(openid: str, gender: str = None, occupation: str = None):
    """更新用户性别和职业"""
    conn = get_db()
    if gender is not None:
        conn.execute("UPDATE users SET gender = ? WHERE openid = ?", (gender, openid))
    if occupation is not None:
        conn.execute("UPDATE users SET occupation = ? WHERE openid = ?", (occupation, openid))
    conn.commit()
    conn.close()


def clear_horoscope_cache(openid: str):
    """清除用户运势缓存（星盘更新后调用）"""
    conn = get_db()
    conn.execute("DELETE FROM horoscope_cache WHERE openid = ?", (openid,))
    conn.commit()
    conn.close()


# ========== 消息操作 ==========

def save_message(openid: str, role: str, content: str, message_type: str = "chat"):
    """保存聊天消息"""
    conn = get_db()
    conn.execute(
        "INSERT INTO messages (openid, role, content, message_type) VALUES (?, ?, ?, ?)",
        (openid, role, content, message_type)
    )
    conn.commit()
    conn.close()


def get_recent_messages(openid: str, limit: int = 10):
    """获取最近的聊天记录"""
    conn = get_db()
    rows = conn.execute(
        """SELECT role, content FROM messages
           WHERE openid = ?
           ORDER BY created_at DESC LIMIT ?""",
        (openid, limit)
    ).fetchall()
    conn.close()
    # 反转顺序（从旧到新）
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


# ========== 运势缓存 ==========

def get_cached_horoscope(openid: str, date: str):
    """获取缓存的今日运势"""
    conn = get_db()
    row = conn.execute(
        "SELECT content FROM horoscope_cache WHERE openid = ? AND date = ?",
        (openid, date)
    ).fetchone()
    conn.close()
    return row["content"] if row else None


def save_horoscope_cache(openid: str, date: str, content: str):
    """缓存今日运势"""
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO horoscope_cache (date, openid, content) VALUES (?, ?, ?)",
        (date, openid, content)
    )
    conn.commit()
    conn.close()
