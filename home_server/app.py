# app.py
import json
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt

from config import MQTT_BROKER,MQTT_PORT,USERNAME,PASSWORD,MQTT_TOPIC_COMMAND,MQTT_TOPIC_STATUS
from config import FLASK_HOST,FLASK_PORT,DEVICES,SECRET_KEY

# Flask应用初始化
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
# socketio = SocketIO(app)
socketio = SocketIO(app,cors_allowed_origins="*")  # 允许所有来源，或指定具体来源,解决跨域问题


device_status = {    
            "living_room_light": {
                "name": "Living Room Light",
                "type": "switch",
                "status": {
                    "is_working":"on",
                    },
                # "function":{
                #     "toggle": "on_or_off"
                # }
            },
            "servo666": {
                "name": "Servo Motor",
                "type": "servo",
                "status": {
                    "is_working": "off",
                    "angle": 0,
                },
                # "function":{
                #     "toggle": "on_or_off",
                #     "set_angle":"angle"
                # },
            },
            "ir_remote666":{
                "name": "IR Remote",
                "type": "ir_remote",
                "status": {
                    "is_working": "off",
                    "cmd_status": {
                        "working_model":"制冷",
                        "temperature":"25",
                        "wind_model":"固定",
                    },
                },
                # "function":{
                #     "toggle": "on_or_off",
                #     "set_cmd_status":{
                #         "working_model":"制冷",
                #         "temperature":"25",
                #         "wind_model":"固定",
                #     }
                # },
            }
        }

# MQTT基础模块
def create_mqtt_client():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "py-mqtt-server")
    client.connect(MQTT_BROKER,MQTT_PORT, 60)
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(USERNAME, PASSWORD)
    # client.reconnect_delay_set(min_delay=1, max_delay=120)  # 设置最小重连间隔为 1 秒，最大重连间隔为 120 秒

    return client

def on_connect(client,userdata,flags,rc,properties):
    """
    连接成功时订阅设备状态主题
    """
    # print(f"MQTT Connected with code: {rc}---{properties}---{flags}")
    if rc == 0:
    # if rc == "Success":
        # print(rc)
        client.subscribe(MQTT_TOPIC_STATUS + "+")
        # client.subscribe(MQTT_TOPIC_COMMAND + "+")
    else:
        print(f"MQTT Connection failed with code: {rc}")

def on_message(client,userdata,msg):
    """
        接收消息时设备状态更新

        接收command 格式：{
            "device_id": {
                "type": "Device Type",
                "command": "cmd",
                "params":["args"]
            }
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
    try:
        device_id = msg.topic.split("/")[2]
        rec_info = json.loads(msg.payload)
        
        # 动态注册新设备
        if device_id not in device_status:
            device_status[device_id] = {
                "name": f"Device {device_id}",
                "type": rec_info.get("type", "unknown"),
                "status": {},
                "funtion":{},
            }
        
        # 深度合并状态
        new_status = rec_info.get("status", {})
        current_status = device_status[device_id]["status"]
        
        # 使用递归合并字典
        def deep_update(target, src):
            for k, v in src.items():
                if isinstance(v, dict):
                    target[k] = deep_update(target.get(k, {}), v)
                else:
                    target[k] = v
            return target
        
        deep_update(current_status, new_status)
        
        # 广播状态更新
        socketio.emit('update_device_status', {
            device_id: {
                "type": device_status[device_id]["type"],
                "status": current_status
            }
        })
        
    except Exception as e:
        print(f"Error processing message: {str(e)} Raw data: \n{msg.payload}")

def publish(client,device_id,payload,qos=1):
    """
    发布消息
    """
    topic = MQTT_TOPIC_COMMAND + device_id
    client.publish(topic, json.dumps(payload),qos=qos)

mqtt_client = create_mqtt_client()
mqtt_client.loop_start()


@app.route('/')
def index():
    return render_template('indexVue.html')
    # return render_template('index.html')

@app.route('/api/control', methods=['POST'])
def control_device():
    data = request.json
    print("POST data: ",data)
    device_id = data.get('device_id')
    device_type = data.get('device_type')
    command = data.get('command')
    params = data.get('params')
    mqtt_msg = {}
    mqtt_msg={"type":device_type,"command":command, "params":params}
    # print("command:", mqtt_msg)
    # 转发命令到MQTT
    mqtt_client.publish(MQTT_TOPIC_COMMAND+device_id, json.dumps(mqtt_msg),qos=1)
    print("topic: " +MQTT_TOPIC_COMMAND+device_id+" command: "+ json.dumps(mqtt_msg))
    
    return jsonify({"message": "Command sent", "device_id": device_id})

# WebSocket事件
@socketio.on('connect')
def handle_connect():
    print("Client connected")
    # 发送完整设备树结构
    init_data = {
        dev_id: {
            "name": dev_info.get("name", f"Device {dev_id}"),
            "type": dev_info["type"],
            "status": dev_info["status"]
        } for dev_id, dev_info in device_status.items()
    }
    socketio.emit('device_init', init_data)

# 双向通讯 定义自定义事件处理函数
# 前->后 后端监听前端事件
# @socketio.on('click_event')
# def handle_my_event(json="invalid"):
#     print('Received json: ' + str(json))
#     # 后->前 向后端发送响应消息
#     socketio.emit('my_response', {'data': 'Server received front message: ', 'json': json})


if __name__ == '__main__':
    # 启动Flask应用
    socketio.run(app, host=FLASK_HOST, port=FLASK_PORT,debug=True)
