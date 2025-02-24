
import paho.mqtt.client as mqtt
import json

from config import MQTT_BROKER,MQTT_PORT,MQTT_TOPIC_COMMAND,MQTT_TOPIC_STATUS,USERNAME,PASSWORD


TOPIC1 = MQTT_TOPIC_COMMAND
# TOPIC2 = MQTT_TOPIC_STATUS

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("Connected to MQTT Broker Successfully!")
        # 订阅主题
        topic1 = TOPIC1 + "+"
        client.subscribe(topic1)
        print("Subscribed to:", topic1)
        # topic2 = TOPIC2 + "+"
        # client.subscribe(topic2)
        # print("Subscribed to:", topic2)
    else:
        print(f"Connection failed with error code: {rc}")


def on_disconnect(client, userdata,flags, rc, properties):
    print(f"Disconnected from MQTT Broker with code: {rc}")
    if rc != 0:
        print("Attempting to reconnect...")

def on_message(client, userdata, msg: mqtt.MQTTMessage):
    """
        接收command 格式：{
            "device_id": {
                    "type": "switch",
                    "command": "toggle",
                    "params": ["on"],
            },
            "device_id": {
                    "type": "ir_remote",
                    "command": "set_cmd_status",
                    "params": [["cmdType1", "cmdStatus1"],
                            ["cmdType2", "cmdStatus2"]],
            },
        }
        返回status格式:{
            "device_id": {
                "type": "Device Type",
                "status": {
                    "status1": "value1",
                    "status2": "value2",
                ...
                }
            }
        }
    """
    # print(msg.topic + " -- " + str(msg.payload))
    try:
        print("Received ",msg.topic," command-------------")
        device_id = msg.topic.split("/")[2]
        rec_info = json.loads(msg.payload)
        print(device_id,rec_info)

        command = rec_info["command"]
        params = rec_info["params"]
        dev_type = rec_info["type"]

        print(command,params,dev_type)
        s_msg = {}
        if command == "toggle":
            # print("Toggle command received")
            rec_status = toggle(device_id,params)
            # print("--func:",cmd," with args: ", str(*args))
            s_msg={"type": "switch", "status": rec_status}
        
        if command == "set_angle":
            # print("Set angle command received")
            rec_status = set_angle(device_id,params)
            # print("--func:",cmd," with args: ", str(*args))
            s_msg={"type": "servo", "status": rec_status}

        if command == "set_cmd_status":
            # print("Set cmd status command received")
            rec_status = set_cmd_status(device_id,params)
            # print("--func:",cmd," with args: ", str(*args))
            s_msg={"type": "ir_remote", "status": rec_status}
        

        client.publish(MQTT_TOPIC_STATUS+device_id, json.dumps(s_msg))
        print("--------------\n",s_msg)

    except Exception as e:
        print("Error processing message:", str(e))

def send_msg(client,topic, msg):
    message = json.dumps(msg)
    client.publish(topic, message)
    print(f"Sent message to {topic}: {message}")


# 模拟设备工作
def toggle(device_id,*args):
    print("Trun ",device_id," statsu = ",args[0])
    return {"is_working":args[0]}

def set_angle(device_id,*args):
    print("Set ",device_id," angle = ",args[0])
    return {"is_working":"on","angle":args[0]}

def set_cmd_status(device_id,fun_list):
    s_msg = {
        "is_working": "on",
        "cmd_status": {

        },
    }
    # for fun in fun_list:
    command = fun_list[0]
    args = fun_list[1:]
    print("\nSet ",device_id," ",command," = ",args[0])
    if command == "working_model":
        s_msg["cmd_status"]["working_model"] = args[0] 
        print("Set ",device_id," working model command ",args[0])
    elif command == "temperature":
        s_msg["cmd_status"]["temperature"] = args[0]
        print("Set ",device_id," temperature command ",args[0])
    elif command == "wind_model":
        s_msg["cmd_status"]["wind_model"] = args[0]
        print("Set ",device_id," wind model command ",args[0])

    return s_msg

if __name__ == '__main__':
    # dev_mqtt = mqtt.Client(client_id="py-mqtt-dev")
    dev_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "py-mqtt-dev")
    # dev_mqtt = mqtt.Client()
    dev_mqtt.username_pw_set(username=USERNAME, password=PASSWORD)
    dev_mqtt.on_connect = on_connect
    dev_mqtt.on_disconnect = on_disconnect
    dev_mqtt.on_message = on_message

    try:
        dev_mqtt.connect(host=MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        dev_mqtt.loop_forever()  # 自动处理重连
    except KeyboardInterrupt:
        print("\nManual interrupt. Disconnecting...")
        dev_mqtt.disconnect()
    except Exception as e:
        print("Critical error:", str(e))
        dev_mqtt.disconnect()