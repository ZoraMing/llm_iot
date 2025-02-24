import threading
import time

# 设备类
class Device:
    """
    设备基类
    """
    def __init__(self,device_id):
        """
        device_id: 设备id
        device_type: 设备类型
        cmd_list: 设备命令及参数列表
        status_list: 设备状态列表
        """
        self.device_id = device_id
        self.device_type =type(self).__name__.lower()
        self.cmd_list = {}
        self.status_list = self.get_status()
    
    def __str__(self):
        return self.device_type

    def get_status(self):
        """
        获取设备状态
        """
        return {} 

class Switch(Device):
    """
    开关类
    """
    def __init__(self,device_id):
        super().__init__(device_id)
        self.status = "off"
        self.__lock = threading.Lock()
        self.cmd_list = {"turn_on_off":["on_or_off"]}

    def get_status(self):
        status_list = {"status",self.status}
        return status_list

    def turn_on_off(self,on_or_off):
        with self.__lock:
            try:
                if on_or_off == "on":
                    print(f"Device {self.device_id} is turning on")
                    self.status = "on"
                elif on_or_off == "off":
                    print(f"Device {self.device_id} is turning off")
                    self.status = "off"
                else:
                    return {"error": "args not match"}
            except Exception as e:
                return {"error": "something wrong: "+str(e)}
        return {"status": self.status}
    
class Servo(Device):
    """
    伺服电机类
    """
    def __init__(self,device_id):
        """
        is_working: 伺服电机是否正在工作
        angle: 伺服电机当前角度
        """
        super().__init__(device_id)
        self.is_working = False
        self.angle = 0
        self.cmd_list = {"turn_servo":["angle"]}
        self._lock = threading.Lock()

    def get_status(self):
        status_list = {
            "is_working":self.is_working,
            "angle":self.angle
        }
        return status_list

    def turn_servo(self,angle):
        with self._lock:
            self.is_working = True
            try:
                if self.is_working:
                    time.sleep(angle/90)
                    print("turning servo to angle: " + str(angle))
                    self.angle = angle
            finally:
                self.is_working = False
        return {"is_working": self.is_working, "angle": self.angle}
# 设备管理模块
class DeviceManager:
    _instance = None
    def __new__(cls, mqtt_client, device_list: dict):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls.mqtt_client = mqtt_client
            # cls.device_list = device_list
            cls.device_list = {
            "living_room_light": {

                "device_type":"switch",
                "fun_list":{
                    "turn_on_off":["on_or_off"]
                },
                "status_list":{
                    "status":"off"
                }
            },
            "servo": {
                "device_type":"servo",
                "fun_list":{
                    "turn_servo":["angle"],
                    "stop_servo":["yes_or_no"]
                },
                "status_list":{
                    "is_working":False,
                    "angle":0
                }
            },
        }

    def add_device(self,device_id,device_type,cmd_list:dict,status_list:dict):
        """
        设备添加
        device_id: 设备id
        device_type: 设备类型
        cmd_list: 设备命令及参数列表
        status_list: 设备状态列表
        """
        
        device_type = device_type.lower()
        if device_type == "switch":
            self.device_list[device_id] = Switch(device_id)
        elif device_type == "servo":
            self.device_list[device_id] = Servo(device_id)



        device_args = {
            "type":device_type,
            "cmd_list":cmd_list,
            "status_list":status_list
        }
        self.device_list[device_id] = device_args

    def remove_device(self,device_id):
        """
        设备删除
        device_id: 设备id
        """
        try:
            self.device_list.remove(device_id)
        except Exception as e:
            print("Error: " + str(e))

    def get_device_status(self,device_id=None):
        """
        获取设备状态
        """
        device_status_list = {}
        for device_id,dev_info in self.device_list:
            device_status_list[device_id]=dev_info["status_list"]
        if device_id:
            return self.device_list[device_id]
        return self.device_list

    def add_device(self):
        """
        设备添加
        """
        pass

    def parser_command(self,command_list:dict):
        """
        解析设备命令
        args: 设备命令列表

        command_list = {
        "living_room_light": {
            "type":"Switch",
            "cmd_list":{
            "turn_on_off":{"on_or_off":"on"}
            }
        },
        "servo1": {
            "type":"Servo",
            "cmd_list":{
                "turn_servo":{"angle":"180"},
                "stop_servo":{"yes_or_no":"yes"}
                }
            }   
        }
        """
        
        ret_msg = {}
        for device_id,device_info in command_list.items():
            # 判断设备是否存在
            if device_id not in self.device_list:
                return {"error": "device not found:"+device_id}
            device_type = device_info["type"]
            if device_type not in self.device_list[device_id]["type"]:
                return {"error": "device type not found:" +device_type}
            for cmd,params in device_info["cmd_list"].items():
                # 判断命令是否存在
                if cmd not in self.device_list[device_id]["cmd_list"]:
                    return {"error": "command not found: "+ cmd}
                if len(params)!= len(self.device_list[device_id]["cmd_list"][cmd]):
                    return {"error": "args not match"}

                # 执行命令

        return ret_msg
