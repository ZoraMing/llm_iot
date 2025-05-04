devices_info = """
{
    "living_room_light": {
        "name": "客厅的灯",
        "type": "switch",
        "description": "位于客厅的灯的开关，有开或关两种状态，toggle传参on开灯可以让整个屋子更加明亮舒适，传off则关灯",
        "function": {
            "status": {
                "parameters": {},
                "return": {
                    "is_working": {
                        "type": "string",
                        "enum": ["on", "off"],
                        "description": "设备工作状态"
                    }
                },
                "description": "获取设备工作状态及当前角度"
            },
            "toggle": {
                "parameters": {
                    "status": {
                        "type": "string",
                        "enum": ["on", "off"],
                        "description": "目标开关状态"
                    }
                },
                "description": "切换设备的开关状态，传参on为开，off为关"
            }
        }
    },
    "servo666": {
        "name": "热水器旋钮",
        "type": "servo",
        "description": "通过舵机控制热水器机械旋钮的设备。角度0-180度线性对应热水流量，180度可持续供应80分钟热水，推荐120度满足40分钟常规使用。",
        "functions": {
            "status": {
                "parameters": {},
                "return": {
                    "is_working": {
                        "type": "string",
                        "enum": ["on", "off"],
                        "description": "设备工作状态"
                    },
                    "angle": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 180,
                        "description": "当前旋钮角度值"
                    }
                },
                "description": "获取设备工作状态及当前角度"
            },
            "set_angle": {
                "parameters": {
                    "angle": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 180,
                        "description": "目标角度值（0-180）"
                    }
                },
                "description": "设置热水器旋钮角度"
            }
        }
    },
    "ir_remote666": {
        "name": "空调遥控器",
        "type": "ir_remote",
        "description": "通过红外模拟实现空调控制的虚拟设备。支持模式切换、温度调节及风量控制，两次发送相同风向指令可复位状态。",
        "functions": {
            "status": {
                "parameters": {},
                "return": {
                    "is_working": {
                        "type": "string",
                        "enum": ["on", "off"],
                        "description": "空调电源状态"
                    },
                    "cmd_status": {
                        "type": "object",
                        "properties": {
                            "working_model": {
                                "type": "string",
                                "enum": ["制冷", "制热", "除湿"],
                                "description": "当前运行模式"
                            },
                            "temperature": {
                                "type": "integer",
                                "minimum": 16,
                                "maximum": 30,
                                "description": "设定温度值"
                            },
                            "wind_model": {
                                "type": "string",
                                "enum": ["上下", "摇头", "固定"],
                                "description": "风向模式状态"
                            }
                        }
                    }
                },
                "description": "获取空调完整状态信息"
            },
            "toggle": {
                "parameters": {
                    "status": {
                        "type": "string",
                        "enum": ["on", "off"],
                        "description": "目标电源状态"
                    }
                },
                "description": "切换空调电源开关"
            },
            "set_cmd_status": {
                "parameters": {
                    "working_model": {
                        "type": "string",
                        "enum": ["制冷", "制热", "除湿"],
                        "description": "目标运行模式（可选）"
                    },
                    "temperature": {
                        "type": "integer",
                        "minimum": 16,
                        "maximum": 30,
                        "description": "目标温度值（可选）"
                    },
                    "wind_model": {
                        "type": "string",
                        "enum": ["上下", "摇头", "固定"],
                        "description": "目标风向模式（可选）"
                    }
                },
                "description": "设置空调运行参数（支持部分参数更新）"
            }
        }
    }
}

"""