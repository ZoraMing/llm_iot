import json
import os
import sys
from mijiaAPI import mijiaAPI, mijiaLogin
from mi_plug import plug

def create_path():
    """创建JSON存储路径并返回认证和设备文件路径"""
    current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    jsons_dir = os.path.join(current_dir, 'jsons')
    
    if not os.path.exists(jsons_dir):
        os.makedirs(jsons_dir)
        print(f"创建文件夹: {jsons_dir}")

    auth_path = os.path.join(jsons_dir, "auth.json")
    devices_path = os.path.join(jsons_dir, "devices.json")
    return auth_path, devices_path

def mi_login(auth_path, devices_path):
    """处理米家登录和设备获取，支持使用现有认证文件"""
    # 检查认证文件是否存在
    if os.path.exists(auth_path):
        print("使用现有认证文件登录...")
        try:
            with open(auth_path, 'r') as f:
                auth = json.load(f)
        except json.JSONDecodeError:
            print("认证文件损坏，重新登录...")
            auth = None
    else:
        auth = None

    # 需要新登录
    if not auth:
        print("开始新的登录流程...")
        api = mijiaLogin()
        auth = api.QRlogin()
        
        with open(auth_path, 'w') as f:
            json.dump(auth, f, indent=2)
        print(f"认证信息已保存到: {auth_path}")

    # 获取设备列表
    api = mijiaAPI(auth)
    try:
        mi_devices = api.get_devices_list()['list']
    except Exception as e:
        print(f"获取设备列表失败: {e}")
        print("尝试使用现有设备文件...")
        if os.path.exists(devices_path):
            with open(devices_path, 'r', encoding="utf-8") as f:
                mi_devices = json.load(f)
        else:
            raise RuntimeError("无法获取设备列表且没有现有设备文件")

    # 保存设备列表
    with open(devices_path, 'w', encoding="utf-8") as f:
        json.dump(mi_devices, f, indent=2, ensure_ascii=False)
    print(f"设备列表已保存到: {devices_path}")
    
    # 打印设备信息
    print("\n发现以下设备:")
    for d in mi_devices:
        print(f"名称: {d['name']} | 在线: {d['isOnline']} | DID: {d['did']}")
    
    return mi_devices


def use_device():
    auth_path, devices_path = create_path()
    mi_devices = mi_login(auth_path, devices_path)

    if not mi_devices:
        print("没有可用的设备")
        sys.exit(1)

    # 使用第一个设备进行演示
    target_device = mi_devices[0]
    # print(f"\n选择设备: {target_device['name']} (DID: {target_device['did']})")

    d1 = plug(target_device['did'], target_device['name'], auth_path)
    return d1


if __name__ == "__main__":
    d1 = use_device()

    # print("\n当前状态:")
    # print(d1.status())
    
    # print("\n关闭设备:")
    # print(d1.close())
    print("\n打开设备:")
    print(d1.open())
    
    print("\n当前状态:")
    print(d1.status())