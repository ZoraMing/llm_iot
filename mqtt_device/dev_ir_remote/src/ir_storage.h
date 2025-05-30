#ifndef IR_STORAGE_H
#define IR_STORAGE_H

#include <EEPROM.h>
#include <Arduino.h>

// const int led_pin = D2;
// const int recv_pin = D5;
// {'device_id': 'ir_remote666', 'device_type': 'ir_remote', 'command': 'set_cmd_status', 'params': [['working_model', '制冷'], ['temperature', 18], ['wind_model', '上下']]}
// {'device_id': 'ir_remote666', 'device_type': 'ir_remote', 'command': 'toggle', 'params': ['off']}

#define RAW_DATA_LENGTH 100

typedef struct {
  uint8_t dataType;      // 0:RAW, 1:NEC, 2:SONY, 3:RC5
  char cmdInfo[32];      // 命令描述（开机/关机等）
  uint32_t dataCode;     // 数据码
  uint16_t address;      // 地址码
  uint16_t rawLength;    // RAW数据长度
  uint16_t rawData[RAW_DATA_LENGTH]; // RAW数据数组（最大支持100个元素）
  // bool isDeleted;        // 是否已删除（逻辑删除）
} IRCommand;

class IRStorage {
private:  
  static constexpr int MAX_ENTRIES = 16;          // 最大存储条目数（4096 / 225 ≈ 18）
  static constexpr size_t CMD_SIZE = sizeof(IRCommand); // 每个命令占用大小
  // static constexpr int START_ADDR = 0;             // EEPROM 起始地址
  // static constexpr int INIT_FLAG_ADDR = 4096 - sizeof(uint32_t);  // 初始化标志位地址,将标志位移到存储区外

  static constexpr int INIT_FLAG_ADDR = 0; // 使用EEPROM起始地址
  static constexpr int START_ADDR = sizeof(uint32_t); // EEPROM 起始地址,数据区后移


  IRCommand commands[MAX_ENTRIES];                 // 缓存命令数组

  // 查找命令索引（根据 cmdInfo）
  int findIndexByCmdInfo(const char *cmdInfo) {
    for (int i = 0; i < MAX_ENTRIES; ++i) {
      if (strcmp(commands[i].cmdInfo, cmdInfo) == 0) {
        return i; // 检查 cmdInfo 是否重复
      }
    }
    return -1; // 未找到
  }

  // 判断条目是否为空位
  bool isEmptyEntry(const IRCommand& entry) {
    return entry.cmdInfo[0] == '\0' || entry.address == 0;
  }

  // 设置条目为空位
  void markAsEmpty(IRCommand& entry) {
    memset(&entry, 0, sizeof(IRCommand));
    // //  设置cmdInfo 字符串为空
    // entry.cmdInfo[0] = '\0';
    // entry.address = 0;
    // entry.rawLength = 0;
    // entry.dataCode = 0;
  }

  // 查找空闲索引
  int findFreeIndex() {
    // 优先查找已删除条目
    for (int i = 0; i < MAX_ENTRIES; ++i) {
      if (isEmptyEntry(commands[i])) {
        return i;
      }
    }
    // 次优选择：覆盖最旧条目
    static int roundRobin = 0;
    return (roundRobin++) % MAX_ENTRIES;
  }

public:
  // 供外部访问初始化变量
  static constexpr int MAX_ENTRIES_ = MAX_ENTRIES;
  static constexpr int INIT_FLAG_ADDR_ = INIT_FLAG_ADDR;

  // 初始化 EEPROM
  void begin() {
    EEPROM.begin(4096);

    // 判断是否首次使用,
    if (EEPROM.read(INIT_FLAG_ADDR) != 0x01) {
      formatEEPROM();
      EEPROM.write(INIT_FLAG_ADDR, 0x01);
      EEPROM.commit();
    }

    readAllFromEEPROM();
  }

  // 格式化 EEPROM
  void formatEEPROM() {
    for (int i = 0; i < MAX_ENTRIES; ++i) {
      IRCommand emptyCmd;
      markAsEmpty(emptyCmd); // 显式初始化为空位
      EEPROM.put(START_ADDR + i * CMD_SIZE, emptyCmd);
      ESP.wdtFeed();
    }
    EEPROM.write(INIT_FLAG_ADDR_, 0x00);
    EEPROM.commit();
  }
  
  // 存储状态 不是0x01 则表示新格式化,反之已初始化持久化数据
  bool isFreshFormat() {
      return EEPROM.read(INIT_FLAG_ADDR) != 0x01;
  }

  // 从 EEPROM 读取所有命令
  void readAllFromEEPROM() {
    for (int i = 0; i < MAX_ENTRIES; ++i) {
      int offset = START_ADDR + i * CMD_SIZE;
      EEPROM.get(offset, commands[i]);
      ESP.wdtFeed();
    }
  }

  // 提交更改到 EEPROM
  void commit() {
    for (int i = 0; i < MAX_ENTRIES; ++i) {
      int offset = START_ADDR + i * CMD_SIZE;
      EEPROM.put(offset, commands[i]);
      ESP.wdtFeed();
      delay(20);
    }
    EEPROM.commit();
    ESP.wdtFeed();
    delay(50);
  }

  // 添加新命令
  bool addCommand(const IRCommand &newCmd) {
    // 参数校验
    if (newCmd.dataType == 0 && newCmd.rawLength > RAW_DATA_LENGTH) {
        return false;
    }

    // 检查是否存在同名有效条目
    int existingIdx = findIndexByCmdInfo(newCmd.cmdInfo);
    if (existingIdx != -1 && !isEmptyEntry(commands[existingIdx])) {
        return false; 
    }

    // 查找空闲索引
    int freeIdx = findFreeIndex();
    if (freeIdx == -1) {
        return false;
    }

    // 初始化 RAW 数据（仅当为 RAW 类型时）
    if (newCmd.dataType == 0 && newCmd.rawLength > 0) {
        memcpy(commands[freeIdx].rawData, newCmd.rawData, newCmd.rawLength * sizeof(uint16_t));
    }

    // 赋值结构体
    commands[freeIdx] = newCmd;

    // 设置默认地址（如未指定）
    if (commands[freeIdx].address == 0) {
        commands[freeIdx].address = 0xFFFF;
    }

    commit();
    return true;
}

  // 删除命令
  bool deleteCommand(const char *cmdInfo) {
    int idx = findIndexByCmdInfo(cmdInfo);
    if (idx == -1) return false;

    markAsEmpty(commands[idx]); // 标记为空位
    // EEPROM.put(START_ADDR + idx * CMD_SIZE, commands[idx]);

    commit();
    return true;
  }

  // 修改命令
  bool updateCommand(const char *cmdInfo, const IRCommand &newCmd) {
    int idx = findIndexByCmdInfo(cmdInfo);
    if (idx == -1) return false;

    if (newCmd.dataType == 0 && newCmd.rawLength > RAW_DATA_LENGTH) return false;
    markAsEmpty(commands[idx]);

    commands[idx] = newCmd;
    // EEPROM.put(START_ADDR + idx * CMD_SIZE, commands[idx]);
    commit();
    return true;
  }

  // 查询命令
  bool getCommand(const char *cmdInfo, IRCommand *outCmd) {
    ESP.wdtFeed();
    int idx = findIndexByCmdInfo(cmdInfo);
    if (idx == -1) return false;

    *outCmd = commands[idx];
    return true;
  }

  // 获取所有有效命令
  int getAllCommands(IRCommand** outCmds, int maxOut) {
    int count = 0;
    for (int i = 0; i < MAX_ENTRIES && count < maxOut; ++i) {
        if (!isEmptyEntry(commands[i])) {
          // 增加空指针校验
            if(outCmds != nullptr) {
                outCmds[count] = &commands[i];
            }
            count++; 
        }
        ESP.wdtFeed();
    }
    return count;
  }


  void printAllCommands(){
      IRCommand* cmdList[MAX_ENTRIES_];
      int count = getAllCommands(cmdList, MAX_ENTRIES_);

      Serial.printf("\n=== 有效指令列表（共%d条） ===\n", count);
      
      for(int i = 0; i < count; ++i) {
          const IRCommand* cmd = cmdList[i];
          
          // 打印命令头信息
          Serial.printf("指令[%d]: %s | 类型=%d |编码=0x%08X | 地址=0x%08X | 原始数据长度=%d | 原始数据: [",
                        i,
                        cmd->cmdInfo,
                        cmd->dataType,
                        cmd->dataCode,
                        cmd->address,
                        cmd->rawLength);

          // 打印RAW数据
          for(uint16_t j = 0; j < cmd->rawLength; ++j) {
              if(j > 0) Serial.print(", ");
              Serial.print(cmd->rawData[j]);  // 使用print自动适配类型
          }

          Serial.println("]");
          ESP.wdtFeed();
      }
  }

  // 判断存储是否已满
  bool isStorageFull() {
    return findFreeIndex() == -1; // 无空位即为满
  }

  // 释放资源
  void end() {
    EEPROM.end();
  }
};

#endif