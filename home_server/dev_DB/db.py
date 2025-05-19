# db.py
import sqlite3
import json
import os
from config import DB_PATH  


from dev_DB.migrate import migrate_data

def init_db():
    """初始化数据库和表结构"""
    if os.path.exists(DB_PATH):
        print("数据库文件已存在，跳过创建")
        return

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 创建设备表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                name TEXT,
                type TEXT,
                description TEXT
            )
        ''')

        # 创建设备功能表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_functions (
                function_id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                function_name TEXT,
                parameters JSON,
                return_value JSON,
                description TEXT,
                FOREIGN KEY (device_id) REFERENCES devices(device_id)
            )
        ''')

        # 创建设备状态表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_status (
                status_id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                status_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status_value JSON,
                FOREIGN KEY (device_id) REFERENCES devices(device_id)
            )
        ''')
        conn.commit()

def get_db_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)

def insert_device(device_id, name, type, description=""):
    """插入设备基本信息"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO devices (device_id, name, type, description) VALUES (?, ?, ?, ?)',
            (device_id, name, type, description)
        )
        conn.commit()

def update_device_status(device_id, status_value):
    """更新设备状态"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO device_status (device_id, status_value) VALUES (?, ?)',
            (device_id, json.dumps(status_value))
        )
        conn.commit()

def get_all_devices():
    """获取所有设备的基本信息"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT device_id, name, type FROM devices')
        return {row[0]: {"name": row[1], "type": row[2]} for row in cursor.fetchall()}

def get_device_status(device_id):
    """获取设备最新状态"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT status_value FROM device_status WHERE device_id = ? ORDER BY status_time DESC LIMIT 1',
            (device_id,)
        )
        result = cursor.fetchone()
        return json.loads(result[0]) if result else {}