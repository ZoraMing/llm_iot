# IR Remote 设备驱动，python
import paho.mqtt.client as mqtt
import json
import logging
from typing import Dict, Any
from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_COMMAND, MQTT_TOPIC_STATUS, USERNAME, PASSWORD

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("IRRemoteDevice")

class IRRemoteDevice:
    def __init__(self):
        """初始化IR遥控器设备"""
        self.config = {
            "dev_id": "ir_remote666",
            "name": "IR Remote",
            "type": "ir_remote",
            "status": {
                "is_working": "off",
                "cmd_status": {
                    "working_model": "制冷",
                    "temperature": "25",
                    "wind_model": "固定"
                }
            }
        }
        
        # 深拷贝存放当前状态
        self.current_status = json.loads(json.dumps(self.config["status"]))
        self.command_topics = {
            "in": f"{MQTT_TOPIC_COMMAND}{self.config['dev_id']}",
            "out": f"{MQTT_TOPIC_STATUS}{self.config['dev_id']}"
        }
        
        # 初始化MQTT客户端
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"ir_remote_{self.config['dev_id']}"
        )
        self._setup_mqtt()

    def _setup_mqtt(self) -> None:
        """配置MQTT连接参数和回调"""
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc, properties) -> None:
        """MQTT连接回调"""
        if rc == 0:
            logger.info(f"Connected to MQTT Broker. Subscribing to {self.command_topics['in']}")
            client.subscribe(self.command_topics['in'], qos=1)
        else:
            logger.error(f"Connection failed with code: {rc}")

    def _on_disconnect(self, client, userdata, rc, properties) -> None:
        """MQTT断开连接回调"""
        logger.warning(f"Disconnected with code: {rc}")
        if rc != 0:
            logger.info("Attempting reconnect...")
            client.reconnect()

    def _on_message(self, client, userdata, msg) -> None:
        """MQTT消息处理回调"""
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received {msg.topic}: {payload}")
            
            # 验证消息格式
            if not all(key in payload for key in ["command", "params"]):
                raise ValueError("Invalid command format")
                
            handler = self._get_command_handler(payload["command"])
            if handler:
                handler(payload["params"])
                self._publish_status()
                logger.info(f"Current status: {self.current_status}")
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

    def _get_command_handler(self, command: str):
        """获取命令处理方法"""
        return {
            "toggle": self._handle_toggle,
            "set_cmd_status": self._handle_set_cmd
        }.get(command)

    def _handle_toggle(self, params: list) -> None:
        """处理开关命令（增加类型兼容）"""
        # 自动转换字符串参数为列表
        if isinstance(params, str):
            params = [params]
        
        # 参数验证（保持原有逻辑）
        if len(params) != 1 or params[0] not in ["on", "off"]:
            raise ValueError("Invalid toggle parameters")
            
        self.current_status["is_working"] = params[0]
        logger.info(f"Toggle status changed to: {params[0]}")

    def _handle_set_cmd(self, params: list) -> None:
        """处理设置命令"""
        if len(params) != 2:
            raise ValueError("Invalid command parameters")
            
        cmd_type, cmd_value = params
        valid_commands = {
            "working_model": ["制冷", "制热", "除湿"],
            "temperature": lambda x: 16 <= int(x) <= 30,
            "wind_model": ["自动", "固定", "摇头"]
        }
        
        # 参数验证
        if cmd_type not in valid_commands:
            raise ValueError(f"Invalid command type: {cmd_type}")
            
        if isinstance(valid_commands[cmd_type], list):
            if cmd_value not in valid_commands[cmd_type]:
                raise ValueError(f"Invalid value for {cmd_type}")
        else:
            if not valid_commands[cmd_type](cmd_value):
                raise ValueError(f"Invalid value for {cmd_type}")
        
        # 更新状态
        self.current_status["cmd_status"][cmd_type] = cmd_value
        self.current_status["is_working"] = "on"
        logger.info(f"Updated {cmd_type} to {cmd_value}")

    def _publish_status(self) -> None:
        """发布当前状态"""
        status_payload = {
            "type": self.config["type"],
            "status": self.current_status.copy()
        }
        self.client.publish(
            self.command_topics["out"],
            payload=json.dumps(status_payload),
            qos=1
        )
        logger.debug("Published status update")

    def run(self) -> None:
        """启动设备连接"""
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            logger.info(f"Starting MQTT loop for {self.config['dev_id']}")
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("Graceful shutdown requested")
            self.client.disconnect()
        except Exception as e:
            logger.critical(f"Fatal error: {str(e)}")
            self.client.disconnect()

if __name__ == '__main__':
    device = IRRemoteDevice()
    device.run()