
import paho.mqtt.client as mqtt
import json
import datetime

from config import MQTT_BROKER,MQTT_PORT,MQTT_TOPIC_COMMAND,MQTT_TOPIC_STATUS,USERNAME,PASSWORD


TOPIC1 = MQTT_TOPIC_COMMAND



DEVICE_META = {
    "living_room_light": {
        "name": "Living Room Light",
        "type": "switch",
        "function": {
            "toggle": {
                "params": "on/off",
                "description": "开关控制"
            }
        }
    },
    "servo666": {
        "name": "Servo Motor",
        "type": "servo",
        "function": {
            "toggle": {
                "params": ["on/off"],
                "description": "开关控制"
            },
            "set_angle": {
                "params": 0,
                "description": "角度设置"
            }
        }
    },
    "ir_remote666": {
        "name": "IR Remote",
        "type": "ir_remote",
        "function": {
            "toggle": {
                "params": "on/off",
                "description": "开关控制"
            },
            "set_cmd_status": {
                "params": {
                    "working_model": ["制冷", "制热", "除湿"],
                    "temperature": [16, 30],
                    "wind_model": ["自动", "固定", "摇头"]
                },
                "description": "状态设置"
            }
        }
    }
}

def init_device(device_id):
    meta = DEVICE_META.get(device_id)
    if not meta:
        return None
        
    base_status = {
        "name": meta["name"],
        "type": meta["type"],
        "status": {
            "is_working": "off",
            "angle": 90 if meta["type"] == "servo" else None,
            "cmd_status": {
                "working_model": "制冷",
                "temperature": 25,
                "wind_model": "固定"
            } if meta["type"] == "ir_remote" else {}
        },
        "function": meta["function"]
    }
    return base_status

# 全局设备状态存储
device_status = {dev_id: init_device(dev_id) for dev_id in DEVICE_META}
# print(device_status,"\n=====================")


def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("Connected to MQTT Broker Successfully!")
        # 订阅主题
        client.subscribe(TOPIC1 + "+")
        # 连接成功后立即上报状态
        for dev_id in device_status:
            status = {
                "type": device_status[dev_id]["type"],
                "status": device_status[dev_id]
            }
            # client.publish(MQTT_TOPIC_STATUS + dev_id, json.dumps(status))
            # print(status,"\n=====================")
    else:
        print(f"Connection failed with error code: {rc}")

def on_disconnect(client, userdata,flags, rc, properties):
    print(f"Disconnected from MQTT Broker with code: {rc}")
    if rc != 0:
        print("Attempting to reconnect...")

def on_message(client, userdata, msg: mqtt.MQTTMessage):
    """
    接受payload样式
    {'type': 'ir_remote', 'command': 'set_cmd_status', 'params': [['working_model', '除湿'], ['temperature', 27], ['wind_model', '摇头']]}
    """
    try:
        print(f"Received {msg.topic} command ------------")
        device_id = msg.topic.split("/")[-1]
        data = json.loads(msg.payload)
        
        # 验证设备存在性
        if device_id not in device_status:
            print(f"Unknown device: {device_id}")
            return
            
        # 命令有效性检查
        command = data.get("command")
        params = list(data.get("params", []))
        # print(data,'=== data ===')
            
        # 执行命令
        dev_type = device_status[device_id]["type"]
        new_status = device_status[device_id]["status"].copy()
        
        if command == "toggle":
            new_status["is_working"] = params[0]
        elif command == "set_angle":
            new_status.update({
                "is_working": "on",
                "angle": int(params[0])
            })
        elif command == "set_cmd_status":
            for param in params:
                key, value = param[0],param[1]
                if key == "temperature":
                    value = int(value)
                new_status["cmd_status"][key] = value
            new_status['is_working'] = "on"
        
        # 更新并发布状态
        device_status[device_id]["status"] = new_status
        client.publish(
            MQTT_TOPIC_STATUS + device_id,
            json.dumps({
                "type": dev_type,
                "status": new_status,
                "function": device_status[device_id]["function"]
            })
        )
        print(f"Updated status for {device_id}: {new_status}")

    except Exception as e:
        print(f"Error message: {str(e)}")


def send_msg(client,topic, msg):
    message = json.dumps(msg)
    client.publish(topic, message)
    print(f"Sent message to {topic}: {message}")


# 模拟设备工作
def toggle(device_id, params):
    device = device_status.get(device_id)
    if device and "toggle" in device["function"]:
        new_status = device["status"].copy()
        new_status["is_working"] = params[0]
        return new_status
    return None

def set_angle(device_id, params):
    device = device_status.get(device_id)
    if device and "set_angle" in device["function"]:
        new_status = device["status"].copy()
        new_status.update({
            "is_working": "on",
            "angle": int(params[0])
        })
        return new_status
    return None

def set_cmd_status(device_id, params):
    device = device_status.get(device_id)
    if device and "set_cmd_status" in device["function"]:
        new_status = device["status"].copy()
        for param in params:
            key, value = param
            if key == "temperature":
                value = int(value)
            new_status["cmd_status"][key] = value
        return new_status
    return None

if __name__ == '__main__':
    # dev_mqtt = mqtt.Client(client_id="py-mqtt-dev")
    dev_id = f"py-mqtt-{datetime.datetime.now().strftime('%m%d%H%M')}"
    dev_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=dev_id)
    # dev_mqtt = mqtt.Client()
    dev_mqtt.username_pw_set(username=USERNAME, password=PASSWORD)
    dev_mqtt.on_connect = on_connect
    dev_mqtt.on_disconnect = on_disconnect
    dev_mqtt.on_message = on_message
    print(">__ mqtt client: <",dev_id,"> Connecting to MQTT broker...")

    try:
        dev_mqtt.connect(host=MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        dev_mqtt.loop_forever()  # 自动处理重连
    except KeyboardInterrupt:
        print("\nManual interrupt. Disconnecting...")
        dev_mqtt.disconnect()
    except Exception as e:
        print("Critical error:", str(e))
        dev_mqtt.disconnect()