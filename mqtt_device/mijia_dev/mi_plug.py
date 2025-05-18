from mijiaAPI import mijiaAPI
import json 


class plug:
    """
    米家智能插座3,文档地址:
    https://home.miot-spec.com/spec/cuco.plug.v3
    功能:
    open
    close
    status
    """
    def __init__(self,did,name,auth_path):

        # with open('jsons/devices.json', "r",encoding="utf-8") as f: # 读取设备列表
        #     devices = json.load(f)
        # self.did = devices[0]['did'] # 将设备did赋值给变量
        # self.name = devices[0]['name']  # 将设备name赋值给变量
        # with open('jsons/auth.json') as f:
        #     auth = json.load(f)
        # self.api = mijiaAPI(auth) # 登录小米账号

        self.did = did
        self.name = name
        with open(auth_path) as f:
            auth = json.load(f)
        self.api = mijiaAPI(auth)

    def open(self): 
        """打开插座"""
        try:
            ret = self.api.set_devices_prop([
                {"did": self.did, "siid": 2, "piid": 1, "value": True},
            ])
            return {self.name:"on"}

        except: 
            return {self.name: "on ERROR"}
    def close(self):
        """关闭插座"""
        try:
            ret = self.api.set_devices_prop([
                {"did": self.did, "siid": 2, "piid": 1, "value": False},
            ])
            return {self.name: "off"}
        except: 
            return {self.name: "off ERROR"}

    def status(self):
        """获取插座当前通电状态"""
        try:
            # 调用米家API获取设备属性（siid=2, piid=1）
            ret = self.api.get_devices_prop([
                {"did": self.did, "siid": 2, "piid": 1}
            ])
            # 解析返回结果（示例：ret = [{"did": "...", "siid": 2, "piid": 1, "value": True}]）
            if ret and "value" in ret[0]:
                status = "on" if ret[0]["value"] else "off"
                return {self.name: status}
            else:
                return {self.name: "status ERROR: 无返回值"}
        except Exception as e:
            return {self.name: f"status ERROR: {str(e)}"}
