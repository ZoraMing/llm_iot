import paho.mqtt.client as mqtt
import json
import datetime
import time

from mijia_contorl import use_device

MQTT_BROKER = "47.237.21.234"
MQTT_PORT = 1884

USERNAME = "testuser1"
PASSWORD = "zora666"

# 主题名称
MQTT_TOPIC_COMMAND = "devices/command/"
MQTT_TOPIC_STATUS = "devices/status/"


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
    }
}

# 实体化设备
living_room_light = use_device()

def init_device(device_id):
    meta = DEVICE_META.get(device_id)
    if not meta:
        return None
    mi_status = list(living_room_light.status().values())[0]
    base_status = {
        "name": meta["name"],
        "type": meta["type"],
        "status": {
            "is_working": mi_status,
        },
        "function": meta["function"]
    }
    return base_status

# 全局设备状态存储
device_status = {dev_id: init_device(dev_id) for dev_id in DEVICE_META}

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("Connected to MQTT Broker Successfully!")
        # 订阅主题
        client.subscribe(TOPIC1 + "living_room_light",qos=1)
        # 连接成功后立即上报状态
        for dev_id in DEVICE_META:
            status = {
                "type": DEVICE_META[dev_id]["type"],
                "status": device_status[dev_id]
            }
            client.publish(MQTT_TOPIC_STATUS + dev_id, json.dumps(status),qos=1)
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

        # 执行命令
        dev_type = device_status[device_id]["type"]
        new_status = device_status[device_id]["status"].copy()

        if command == "toggle":
            mi_status = toggle(device_id, params)
            mi_device_name = list(mi_status.keys())[0]
            mi_device_status = list(mi_status.values())[0]
            new_status["is_working"] = mi_device_status
            print(f"{mi_device_name}: status  changed to: {mi_device_status}")

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
        print(f"Error processing message: {str(e)}")


# 控制设备工作
def toggle(device_id, params):
    global living_room_light
    if device_id == "living_room_light":
        if params[0] == "on":
            living_room_light.open()
            # print(living_room_light.open())
        else:
            living_room_light.close()
            # print(living_room_light.close())
    # 等操作结束再查询设备状态
    time.sleep(1)
    
    device_status = living_room_light.status()
    return device_status


if __name__ == '__main__':
    dev_id = f"mi-plug_switch-{datetime.datetime.now().strftime('%m%d%H%M')}"
    dev_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=dev_id)
    dev_mqtt.username_pw_set(username=USERNAME, password=PASSWORD)
    dev_mqtt.on_connect = on_connect
    dev_mqtt.on_disconnect = on_disconnect
    dev_mqtt.on_message = on_message
    print(f">__ mqtt client: <{dev_id}> Connecting to MQTT broker...")

    try:
        dev_mqtt.connect(host=MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        # 自动处理重连
        dev_mqtt.loop_forever()
    except KeyboardInterrupt:
        print("\nManual interrupt. Disconnecting...")
        dev_mqtt.disconnect()
    except Exception as e:
        print("Critical error:", str(e))
        dev_mqtt.disconnect()