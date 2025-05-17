# MQTT配置
MQTT_BROKER = "your_broker_ip"
MQTT_PORT = 1883
USERNAME = "admin"
PASSWORD = "123456"
MQTT_TOPIC_COMMAND = "devices/command/"
MQTT_TOPIC_STATUS = "devices/status/"

DB_PATH = "dev_DB/app.db"

# Flask配置
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
SECRET_KEY = "MY_SECRET_KEY"
# 设备列表
DEVICES = {
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
        "describe":"洗澡用的热水器，set_angle控制热水器旋钮角度范围为0到180，热水量180够洗80分钟，通常转到120度就可以正常洗40分钟，0度为关闭热水器。",
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
        "describe":"屋子的空调遥控器，功能有打开关闭toggle选择on或off，设置空调状态工具set_cmd_status，有参数working_model设置空调模式，有制冷，制热，除湿模式。参数temperature设置空调温度，范围16到30.参数wind_model设置空调吹风状态，有上下，摇头，固定模式，发送两次上下或摇头取消当前吹风模式，变为固定上下或左右位置，发送固定则直接取消上下和左右摇头，固定当前角度",
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
