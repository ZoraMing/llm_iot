import sqlite3
import json
import os

# 用户提供的初始设备数据
initial_data = {
    "living_room_light": {
        "name": "客厅的灯",
        "type": "switch",
        "describe": "位于客厅的灯的开关，有开或关两种状态，toggle传参on开灯可以让整个屋子更加明亮舒适，传off则关灯",
        "status": {
            "is_working": "on",
        },
        "function": {"toggle": "on"},
    },
    "servo666": {
        "name": "热水器旋钮",
        "describe": "洗澡用的热水器，set_angle控制热水器旋钮角度范围为0到180，热水量180够洗80分钟，通常转到120度就可以正常洗40分钟，0度为关闭热水器。",
        "type": "servo",
        "status": {
            "is_working": "off",
            "angle": 0,
        },
        "function": {"set_angle": "90"},
    },
    "ir_remote666": {
        "name": "空调遥控器",
        "type": "ir_remote",
        "describe": "屋子的空调遥控器，功能有打开关闭toggle选择on或off，设置空调状态工具set_cmd_status，有参数working_model设置空调模式，有制冷，制热，除湿模式。参数temperature设置空调温度，范围16到30.参数wind_model设置空调吹风状态，有上下，摇头，固定模式，发送两次上下或摇头取消当前吹风模式，变为固定上下或左右位置，发送固定则直接取消上下和左右摇头，固定当前角度",
        "status": {
            "is_working": "off",
            "cmd_status": {
                "working_model": "制冷",
                "temperature": "25",
                "wind_model": "固定",
            },
        },
        "function": {
            "toggle": "on_or_off",
            "set_cmd_status": {
                "working_model": "制冷",
                "temperature": "25",
                "wind_model": "固定",
            },
        },
    },
}

def migrate_data(DB_PATH):
    """迁移初始设备数据到 SQLite 数据库"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    
    # # 创建表结构
    # cursor.execute('''
    #     CREATE TABLE IF NOT EXISTS devices (
    #         device_id TEXT PRIMARY KEY,
    #         name TEXT,
    #         type TEXT,
    #         description TEXT
    #     )
    # ''')

    # cursor.execute('''
    #     CREATE TABLE IF NOT EXISTS device_functions (
    #         function_id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         device_id TEXT,
    #         function_name TEXT,
    #         parameters JSON,
    #         return_value JSON,
    #         description TEXT,
    #         FOREIGN KEY (device_id) REFERENCES devices(device_id)
    #     )
    # ''')

    # cursor.execute('''
    #     CREATE TABLE IF NOT EXISTS device_status (
    #         status_id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         device_id TEXT,
    #         status_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #         status_value JSON,
    #         FOREIGN KEY (device_id) REFERENCES devices(device_id)
    #     )
    # ''')

    # 插入设备数据
    for dev_id, dev_info in initial_data.items():
        # 插入 devices 表
        cursor.execute(
            'INSERT OR IGNORE INTO devices (device_id, name, type, description) VALUES (?, ?, ?, ?)',
            (dev_id, dev_info['name'], dev_info['type'], dev_info['describe'])
        )

        # 插入 device_functions 表
        for func_name, func_param in dev_info.get('function', {}).items():
            if isinstance(func_param, str):
                parameters = json.dumps({"example": func_param})
            else:
                parameters = json.dumps(func_param)

            cursor.execute(
                'INSERT INTO device_functions (device_id, function_name, parameters, description) VALUES (?, ?, ?, ?)',
                (dev_id, func_name, parameters, dev_info['describe'])
            )

        # 插入 device_status 表
        status_value = json.dumps(dev_info['status'])
        cursor.execute(
            'INSERT INTO device_status (device_id, status_value) VALUES (?, ?)',
            (dev_id, status_value)
        )

    # 提交事务并关闭连接
    conn.commit()
    conn.close()

if __name__ == '__main__':
    DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

    print(DB_PATH)
    migrate_data(DB_PATH)