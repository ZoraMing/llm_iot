# MQTT配置
MQTT_BROKER = "your_broker_ip"
MQTT_PORT = 1883
USERNAME = "admin"
PASSWORD = "123456"
MQTT_TOPIC_COMMAND = "devices/command/"
MQTT_TOPIC_STATUS = "devices/status/"

# Flask配置
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
SECRET_KEY = "MY_SECRET_KEY"
# 设备列表
DEVICES = {
    "living_room_light": {
        "name": "Living Room Light",
        "type": "switch",
        "status": {
            "is_working": "on",
        },
        "function": {"toggle": "on_or_off"},
    },
    "servo666": {
        "name": "Servo Motor",
        "type": "servo",
        "status": {
            "is_working": "off",
            "angle": 0,
        },
        "function": {"toggle": "on_or_off", "set_angle": "angle"},
    },
    "ir_remote666": {
        "name": "IR Remote",
        "type": "ir_remote",
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
