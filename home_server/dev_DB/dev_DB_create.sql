

-- 设备表 devices  
-- 该表用于存储设备的基本信息，每个设备有唯一的 device_id 
 CREATE TABLE IF NOT EXISTS devices (  
    -- 设备唯一标识符，作为主键  
    device_id TEXT PRIMARY KEY COMMENT '设备唯一标识符',  
    name TEXT COMMENT '设备名称',  
    type TEXT COMMENT '设备类型，如 switch、servo、ir_remote 等',  
    description TEXT COMMENT '设备的详细描述'  );  

-- 设备功能表 device_functions 
-- 该表用于存储每个设备的功能信息，与 devices 表通过 device_id 关联  
CREATE TABLE IF NOT EXISTS device_functions (  
    function_id INTEGER PRIMARY KEY AUTOINCREMENT COMMENT '功能唯一标识符',  
    device_id TEXT COMMENT '关联设备表的 device_id，外键',  
    function_name TEXT COMMENT '功能名称，如 status、toggle 等',  
    parameters JSON COMMENT '功能所需的参数信息，以 JSON 格式存储',  
    return_value JSON COMMENT '功能的返回值信息，以 JSON 格式存储',  
    description TEXT COMMENT '功能的详细描述',  
    FOREIGN KEY (device_id) REFERENCES devices(device_id)  );  

-- 设备状态表 device_status  
-- 该表用于存储设备的状态信息，与 devices 表通过 device_id 关联 
 CREATE TABLE IF NOT EXISTS device_status (  
    status_id INTEGER PRIMARY KEY AUTOINCREMENT COMMENT '状态唯一标识符',  
    device_id TEXT COMMENT '关联设备表的 device_id，外键',  
    status_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '状态更新的时间，默认值为当前时间',  
    status_value JSON COMMENT '设备的当前状态信息，以 JSON 格式存储',  
FOREIGN KEY (device_id) REFERENCES devices(device_id)  );  