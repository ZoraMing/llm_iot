#ifndef IR_STORAGE_H
#define IR_STORAGE_H

#include <EEPROM.h>

typedef struct {
  uint8_t dataType;      // 0:RAW, 1:NEC, 2:SONY, 3:RC5
  char cmdInfo[8];      // 命令描述（开机/关机等）
  uint32_t dataCode;     // 数据码
  uint16_t address;      // 地址码
  uint16_t rawLength;    // RAW数据长度
  uint16_t rawData[100]; // RAW数据数组（最大支持100个元素）
  bool isDeleted;        // 是否已删除（逻辑删除）
} IRCommand;

class IRStorage {
private:
  static constexpr int MAX_ENTRIES = 18;          // 最大存储条目数（4096 / 225 ≈ 18）
  static constexpr size_t CMD_SIZE = sizeof(IRCommand); // 每个命令占用大小
  static constexpr int START_ADDR = 0;             // EEPROM 起始地址
  static constexpr int INIT_FLAG_ADDR = 4096 - 1;  // 初始化标志位地址（最后一个字节）

  IRCommand commands[MAX_ENTRIES];                 // 缓存命令数组

  // 查找命令索引（根据 cmdInfo）
  int findIndexByCmdInfo(const char *cmdInfo) {
    for (int i = 0; i < MAX_ENTRIES; ++i) {
      if (!commands[i].isDeleted && strcmp(commands[i].cmdInfo, cmdInfo) == 0)
        return i;
    }
    return -1; // 未找到
  }

  // 查找空闲索引
  int findFreeIndex() {
    for (int i = 0; i < MAX_ENTRIES; ++i) {
      if (commands[i].isDeleted) return i;
    }
    return -1; // 无空闲
  }

public:
  // 初始化 EEPROM
  void begin() {
    EEPROM.begin(4096);

    // 判断是否首次使用
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
      IRCommand cmd = {};
      cmd.isDeleted = true;
      EEPROM.put(START_ADDR + i * CMD_SIZE, cmd);
    }
    EEPROM.commit();
  }

  // 从 EEPROM 读取所有命令
  void readAllFromEEPROM() {
    for (int i = 0; i < MAX_ENTRIES; ++i) {
      int offset = START_ADDR + i * CMD_SIZE;
      EEPROM.get(offset, commands[i]);
    }
  }

  // 提交更改到 EEPROM
  void commit() {
    for (int i = 0; i < MAX_ENTRIES; ++i) {
      int offset = START_ADDR + i * CMD_SIZE;
      EEPROM.put(offset, commands[i]);
    }
    EEPROM.commit();
  }

  // 添加新命令
  bool addCommand(const IRCommand &newCmd) {
    if (findIndexByCmdInfo(newCmd.cmdInfo) != -1) return false; // 已存在
    if (isStorageFull()) return false;

    int freeIdx = findFreeIndex();
    if (freeIdx == -1) return false;

    // 检查 RAW 数据长度是否超出限制
    if (newCmd.dataType == 0 && newCmd.rawLength > 100) return false;

    commands[freeIdx] = newCmd;
    commands[freeIdx].isDeleted = false;
    return true;
  }

  // 删除命令
  bool deleteCommand(const char *cmdInfo) {
    int idx = findIndexByCmdInfo(cmdInfo);
    if (idx == -1) return false;

    commands[idx].isDeleted = true;
    return true;
  }

  // 修改命令
  bool updateCommand(const char *cmdInfo, const IRCommand &newCmd) {
    int idx = findIndexByCmdInfo(cmdInfo);
    if (idx == -1) return false;

    if (newCmd.dataType == 0 && newCmd.rawLength > 100) return false;

    commands[idx] = newCmd;
    commands[idx].isDeleted = false;
    return true;
  }

  // 查询命令
  bool getCommand(const char *cmdInfo, IRCommand *outCmd) {
    int idx = findIndexByCmdInfo(cmdInfo);
    if (idx == -1) return false;

    *outCmd = commands[idx];
    return true;
  }

  // 获取所有有效命令
  int getAllCommands(IRCommand *outCmds[], int maxOut) {
    int count = 0;
    for (int i = 0; i < MAX_ENTRIES && count < maxOut; ++i) {
      if (!commands[i].isDeleted) {
        outCmds[count++] = &commands[i];
      }
    }
    return count;
  }

  // 获取当前有效命令数量
  int getCommandCount() {
    int count = 0;
    for (int i = 0; i < MAX_ENTRIES; ++i) {
      if (!commands[i].isDeleted) count++;
    }
    return count;
  }

  // 判断存储是否已满
  bool isStorageFull() {
    return getCommandCount() >= MAX_ENTRIES;
  }

  // 释放资源
  void end() {
    EEPROM.end();
  }
};

#endif