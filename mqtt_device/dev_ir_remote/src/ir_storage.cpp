// #include <EEPROM.h>

// typedef struct {
//   uint8_t dataType;      // 0:RAW, 1:NEC, 2:SONY, 3:RC5
//   char cmdInfo[16];      // 命令描述（开机/关机等）
//   uint32_t dataCode;     // 数据码
//   uint16_t address;      // 地址码
//   uint16_t rawLength;    // RAW数据长度
//   uint16_t rawData[100]; // RAW数据数组（最大支持100个元素）
//   bool isDeleted;        // 是否已删除（逻辑删除）
// } IRCommand;


// class EEPROMManager {
// private:
//   static constexpr int MAX_ENTRIES = 100;          // 最大存储条目数
//   static constexpr size_t CMD_SIZE = sizeof(IRCommand); // 每个命令占用大小
//   static constexpr int START_ADDR = 0;             // EEPROM 起始地址
//   // 使用static constexpr声明编译期常量

//   IRCommand commands[MAX_ENTRIES];      // 缓存命令数组

//   // 查找命令索引（根据 cmdInfo）
//   int findIndexByCmdInfo(const char *cmdInfo) {
//     for (int i = 0; i < MAX_ENTRIES; ++i) {
//       if (!commands[i].isDeleted && strcmp(commands[i].cmdInfo, cmdInfo) == 0)
//         return i;
//     }
//     return -1; // 未找到
//   }

//   // 查找空闲索引
//   int findFreeIndex() {
//     for (int i = 0; i < MAX_ENTRIES; ++i) {
//       if (commands[i].isDeleted) return i;
//     }
//     return -1; // 无空闲
//   }

// public:
//   // 初始化 EEPROM
//   void begin() {
//     EEPROM.begin(MAX_ENTRIES * CMD_SIZE + 40); // 建议增加40字节余量
//     if(EEPROM.read(0) == 0xFF) { // 首次使用标识
//       formatEEPROM();
//     }
//     readAllFromEEPROM();
//   }

//   // 格式化 EEPROM
//   void formatEEPROM() {
//     for (int i = 0; i < MAX_ENTRIES; ++i) {
//       IRCommand cmd = {0};
//       EEPROM.put(START_ADDR + i * CMD_SIZE, cmd);
//     }
//     EEPROM.commit();
//   }

//   // 从 EEPROM 读取所有命令
//   void readAllFromEEPROM() {
//     for (int i = 0; i < MAX_ENTRIES; ++i) {
//       int offset = START_ADDR + i * CMD_SIZE;
//       EEPROM.get(START_ADDR + i * CMD_SIZE, commands[i]);
//     }
//   }

//   // 提交更改到 EEPROM
//   void commit() {
//     for (int i = 0; i < MAX_ENTRIES; ++i) {
//       int offset = START_ADDR + i * CMD_SIZE;
//       EEPROM.put(START_ADDR + i * CMD_SIZE, commands[i]);
//     }
//     EEPROM.commit();
//   }

//   // 添加新命令
//   bool addCommand(const IRCommand &newCmd) {
//     if (findIndexByCmdInfo(newCmd.cmdInfo) != -1) return false; // 已存在

//     int freeIdx = findFreeIndex();
//     if (freeIdx == -1) return false; // 无空闲

//     commands[freeIdx] = newCmd;
//     commands[freeIdx].isDeleted = false;
//     return true;
//   }

//   // 删除命令
//   bool deleteCommand(const char *cmdInfo) {
//     int idx = findIndexByCmdInfo(cmdInfo);
//     if (idx == -1) return false;

//     commands[idx].isDeleted = true;
//     return true;
//   }

//   // 修改命令
//   bool updateCommand(const char *cmdInfo, const IRCommand &newCmd) {
//     int idx = findIndexByCmdInfo(cmdInfo);
//     if (idx == -1) return false;

//     commands[idx] = newCmd;
//     commands[idx].isDeleted = false;
//     return true;
//   }

//   // 查询命令
//   bool getCommand(const char *cmdInfo, IRCommand *outCmd) {
//     int idx = findIndexByCmdInfo(cmdInfo);
//     if (idx == -1) return false;

//     *outCmd = commands[idx];
//     return true;
//   }

//   // 获取所有有效命令
//   int getAllCommands(IRCommand *outCmds[], int maxOut) {
//     int count = 0;
//     for (int i = 0; i < MAX_ENTRIES && count < maxOut; ++i) {
//       if (!commands[i].isDeleted) {
//         outCmds[count++] = &commands[i];
//       }
//     }
//     return count;
//   }

//   // 释放资源
//   void end() {
//     EEPROM.end();
//   }
// };