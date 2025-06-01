#include <IRremoteESP8266.h>
#include <IRrecv.h>
#include <IRsend.h>
#include "ir_storage.h"

// 定义红外接收和发送的引脚
const uint16_t RECV_PIN = D5;
const uint16_t SEND_PIN = D2;

// 初始化红外接收和发送对象
IRrecv irrecv(RECV_PIN);
IRsend irsend(SEND_PIN);

// 初始化 IRStorage 对象
IRStorage irStorage;

// 红外发送状态机
enum IRState {
    IR_IDLE,
    IR_SENDING,
    IR_SEND_COMPLETE
};

// 全局变量
volatile IRState irState = IR_IDLE;
volatile uint32_t irStartTime = 0;
volatile uint32_t irNextEdge = 0;
volatile uint16_t irDataIndex = 0;
// volatile const IRCommand* currentCmd = nullptr;
IRCommand currentCmd = {1,"null",0xABCD,0x1234,0,{}};


void send_NEC(uint32_t data, uint16_t address);
void send_SONY(uint32_t data, uint16_t address);
void send_RC5(uint32_t data, uint16_t address);


// 初始化红外模块
void ir_init() {
    pinMode(SEND_PIN, OUTPUT);
    digitalWrite(SEND_PIN, LOW);
    pinMode(RECV_PIN, INPUT);
}

// 自定义非阻塞红外发送函数
void ir_send_non_blocking() {
    if (irState != IR_SENDING) return;
    
    uint32_t currentTime = micros();
    
    // 检查是否到达下一个边沿时间
    if (currentTime - irStartTime < irNextEdge) {
        return;
    }
    
    if (currentCmd.dataType == 0) { // RAW 数据
        if (irDataIndex < currentCmd.rawLength) {
            uint16_t duration = currentCmd.rawData[irDataIndex];
            digitalWrite(SEND_PIN, (irDataIndex % 2 == 0) ? HIGH : LOW);
            irNextEdge = duration;
            irDataIndex++;
            return;
        }
    } 
    else if (currentCmd.dataType == 1) { // NEC 协议
        // NEC 协议实现 (38kHz载波)
        send_NEC(currentCmd.dataCode, currentCmd.address);
        // ... [完整实现见下方] ...
    }
    else if (currentCmd.dataType == 2) { // SONY 协议
        // SONY 协议实现 (40kHz载波)
        send_SONY(currentCmd.dataCode, currentCmd.address);
        // ... [完整实现见下方] ...
    }
    else if (currentCmd.dataType == 3) { // RC5 协议
        // RC5 协议实现 (36kHz载波)
        send_RC5(currentCmd.dataCode, currentCmd.address);
        // ... [完整实现见下方] ...
    }
    
    // 发送完成
    digitalWrite(SEND_PIN, LOW);
    irState = IR_SEND_COMPLETE;
}

// 启动红外发送
bool start_ir_send(const char* cmdInfo) {
    if (irState != IR_IDLE) {
        Serial.println("红外发送忙，请稍后");
        return false;
    }

    // IRCommand temp_currentCmd = currentCmd;
    if (!irStorage.getCommand(cmdInfo, &currentCmd)) {
        Serial.printf("错误：找不到命令 '%s'\n", cmdInfo);
        return false;
    }
    
    Serial.printf("开始发送: %s, 类型: %d, 数据0x%08X\n", cmdInfo, currentCmd.dataType,currentCmd.dataCode);
    
    irState = IR_SENDING;
    irStartTime = micros();
    irNextEdge = 0;
    irDataIndex = 0;
    
    return true;
}

// 检查发送状态
bool ir_send_complete() {
    return irState == IR_SEND_COMPLETE;
}

// 主发送函数 (非阻塞)
bool ir_send(const char* cmdInfo) {
    if (start_ir_send(cmdInfo)) {
        pinMode(LED_BUILTIN, OUTPUT);
        while (!ir_send_complete()) {
            digitalWrite(LED_BUILTIN, LOW);
            ir_send_non_blocking();
            ESP.wdtFeed();
            delayMicroseconds(10);
            digitalWrite(LED_BUILTIN, HIGH);
        }
        irState = IR_IDLE;
        digitalWrite(LED_BUILTIN, HIGH);
        return true;
    }
    return false;
}

// NEC协议实现
void send_NEC(uint32_t data, uint16_t address) {
    // 载波频率: 38kHz, 周期: 26.3μs
    const uint32_t carrierPeriod = 26;
    const uint16_t carrierHalf = carrierPeriod / 2;
    
    // NEC协议时序定义
    const uint16_t leaderOn = 9000;
    const uint16_t leaderOff = 4500;
    const uint16_t bitOn = 560;
    const uint16_t zeroOff = 560;
    const uint16_t oneOff = 1690;
    const uint16_t gap = 40000;
    
    // 发送前导码
    for (uint16_t i = 0; i < leaderOn / carrierPeriod; i++) {
        digitalWrite(SEND_PIN, HIGH);
        delayMicroseconds(carrierHalf);
        digitalWrite(SEND_PIN, LOW);
        delayMicroseconds(carrierHalf);
    }
    delayMicroseconds(leaderOff);
    
    // 发送地址 (16位)
    for (int i = 15; i >= 0; i--) {
        bool bitVal = address & (1 << i);
        
        // 发送起始脉冲
        for (uint16_t j = 0; j < bitOn / carrierPeriod; j++) {
            digitalWrite(SEND_PIN, HIGH);
            delayMicroseconds(carrierHalf);
            digitalWrite(SEND_PIN, LOW);
            delayMicroseconds(carrierHalf);
        }
        
        // 发送位值
        delayMicroseconds(bitVal ? oneOff : zeroOff);
    }
    
    // 发送数据 (32位)
    for (int i = 31; i >= 0; i--) {
        bool bitVal = data & (1 << i);
        
        // 发送起始脉冲
        for (uint16_t j = 0; j < bitOn / carrierPeriod; j++) {
            digitalWrite(SEND_PIN, HIGH);
            delayMicroseconds(carrierHalf);
            digitalWrite(SEND_PIN, LOW);
            delayMicroseconds(carrierHalf);
        }
        
        // 发送位值
        delayMicroseconds(bitVal ? oneOff : zeroOff);
    }
    
    // 发送结束脉冲
    for (uint16_t j = 0; j < bitOn / carrierPeriod; j++) {
        digitalWrite(SEND_PIN, HIGH);
        delayMicroseconds(carrierHalf);
        digitalWrite(SEND_PIN, LOW);
        delayMicroseconds(carrierHalf);
    }
    delayMicroseconds(gap);
}

// SONY协议实现
void send_SONY(uint32_t data, uint16_t address) {
    // 载波频率: 40kHz, 周期: 25μs
    const uint32_t carrierPeriod = 25;
    const uint16_t carrierHalf = carrierPeriod / 2;
    
    // SONY协议时序定义
    const uint16_t leaderOn = 2400;
    const uint16_t leaderOff = 600;
    const uint16_t bitOn = 1200;
    const uint16_t bitOff = 600;
    
    // 发送前导码
    for (uint16_t i = 0; i < leaderOn / carrierPeriod; i++) {
        digitalWrite(SEND_PIN, HIGH);
        delayMicroseconds(carrierHalf);
        digitalWrite(SEND_PIN, LOW);
        delayMicroseconds(carrierHalf);
    }
    delayMicroseconds(leaderOff);
    
    // 发送地址 (8位) + 数据 (8位)
    uint32_t fullData = (address << 8) | (data & 0xFF);
    int bits = 12; // 12位SIRC协议
    
    for (int i = bits - 1; i >= 0; i--) {
        bool bitVal = fullData & (1 << i);
        
        // 发送起始脉冲
        for (uint16_t j = 0; j < bitOn / carrierPeriod; j++) {
            digitalWrite(SEND_PIN, HIGH);
            delayMicroseconds(carrierHalf);
            digitalWrite(SEND_PIN, LOW);
            delayMicroseconds(carrierHalf);
        }
        
        // 发送位值
        delayMicroseconds(bitVal ? bitOff * 2 : bitOff);
    }
}

// RC5协议实现
void send_RC5(uint32_t data, uint16_t address) {
    // 载波频率: 36kHz, 周期: 27.8μs
    const uint32_t carrierPeriod = 28;
    const uint16_t carrierHalf = carrierPeriod / 2;
    
    // RC5协议时序定义
    const uint16_t bitDuration = 1778;
    
    // 发送起始位 (2个周期)
    for (int i = 0; i < 2; i++) {
        for (uint16_t j = 0; j < bitDuration / carrierPeriod; j++) {
            digitalWrite(SEND_PIN, HIGH);
            delayMicroseconds(carrierHalf);
            digitalWrite(SEND_PIN, LOW);
            delayMicroseconds(carrierHalf);
        }
    }
    
    // 发送数据 (14位: 2位起始 + 5位地址 + 6位命令)
    uint16_t rc5Data = ((address & 0x1F) << 6) | (data & 0x3F);
    
    for (int i = 13; i >= 0; i--) {
        bool bitVal = rc5Data & (1 << i);
        
        // 曼彻斯特编码
        if (bitVal) {
            // 1: 先高后低
            for (uint16_t j = 0; j < bitDuration / (2 * carrierPeriod); j++) {
                digitalWrite(SEND_PIN, HIGH);
                delayMicroseconds(carrierHalf);
                digitalWrite(SEND_PIN, LOW);
                delayMicroseconds(carrierHalf);
            }
            for (uint16_t j = 0; j < bitDuration / (2 * carrierPeriod); j++) {
                digitalWrite(SEND_PIN, LOW);
                delayMicroseconds(carrierHalf);
                digitalWrite(SEND_PIN, HIGH);
                delayMicroseconds(carrierHalf);
            }
        } else {
            // 0: 先低后高
            for (uint16_t j = 0; j < bitDuration / (2 * carrierPeriod); j++) {
                digitalWrite(SEND_PIN, LOW);
                delayMicroseconds(carrierHalf);
                digitalWrite(SEND_PIN, HIGH);
                delayMicroseconds(carrierHalf);
            }
            for (uint16_t j = 0; j < bitDuration / (2 * carrierPeriod); j++) {
                digitalWrite(SEND_PIN, HIGH);
                delayMicroseconds(carrierHalf);
                digitalWrite(SEND_PIN, LOW);
                delayMicroseconds(carrierHalf);
            }
        }
    }
}



// ir_learn 函数：10s 内接收红外信号，解析打印接收到的红外信号
bool ir_learn(const char* rec_cmdInfo) {
    irrecv.enableIRIn(); // 启用红外接收
    Serial.printf("开始学习红外信号，等待 10 秒... %s",rec_cmdInfo);
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, LOW);

    unsigned long startTime = millis();
    decode_results results;
    bool result = false;

    while (millis() - startTime < 10000) {
        ESP.wdtFeed();
        if (irrecv.decode(&results)) {
            Serial.println("接收到红外信号！");

            IRCommand outCmd;
            strncpy(outCmd.cmdInfo, rec_cmdInfo, sizeof(outCmd.cmdInfo) - 1);
            outCmd.cmdInfo[sizeof(outCmd.cmdInfo) - 1] = '\0'; 

            // 根据接收到的信号类型填充 outCmd
            switch (results.decode_type) {
                case NEC:
                    outCmd.dataType = 1;
                    outCmd.dataCode = results.value;
                    outCmd.address = results.address;
                    outCmd.rawLength = 0;
                    Serial.printf("接收到 NEC 红外信号，编码: 0x%08X，地址: 0x%08X\n", outCmd.dataCode, outCmd.address);
                    break;
                case SONY:
                    outCmd.dataType = 2;
                    outCmd.dataCode = results.value;
                    outCmd.address = results.address;
                    outCmd.rawLength = 0;
                    Serial.printf("接收到 SONY 红外信号，编码: 0x%08X，地址: 0x%08X\n", outCmd.dataCode, outCmd.address);
                    break;
                case RC5:
                    outCmd.dataType = 3;
                    outCmd.dataCode = results.value;
                    outCmd.address = results.address;
                    outCmd.rawLength = 0;
                    Serial.printf("接收到 RC5 红外信号，编码: 0x%08X，地址: 0x%08X\n", outCmd.dataCode, outCmd.address);
                    break;
                case UNKNOWN:
                    outCmd.dataType = 0;
                    outCmd.rawLength = results.rawlen - 1;
                    if (outCmd.rawLength > RAW_DATA_LENGTH) {
                        Serial.println("接收到的 RAW 数据过长，无法保存！");
                        irrecv.resume();
                        return false;
                    }
                    for (uint16_t i = 0; i < outCmd.rawLength; ++i) {
                        outCmd.rawData[i] = results.rawbuf[i + 1];
                    }
                    Serial.printf("接收到 RAW 红外信号，原始数据长度: %d\n", outCmd.rawLength);
                    break;
                default:
                    Serial.println("不支持的红外信号类型！");
                    irrecv.resume();
                    return false;
            }
            
            // === 修改部分开始 ===
            // 检查命令是否已存在
            IRCommand existingCmd;
            if (irStorage.getCommand(rec_cmdInfo, &existingCmd)) {
                // 命令已存在，执行更新操作
                Serial.println("命令已存在，执行更新...");
                if (irStorage.updateCommand(rec_cmdInfo, outCmd)) {
                    Serial.println("更新成功！");
                    result = true;
                } else {
                    Serial.println("更新失败！");
                }
            } else {
                // 命令不存在，执行添加操作
                Serial.println("添加新命令...");
                if (irStorage.addCommand(outCmd)) {
                    Serial.println("添加成功！");
                    result = true;
                } else {
                    Serial.println("添加失败！");
                }
            }
            // === 修改部分结束 ===

            irrecv.resume();
            digitalWrite(LED_BUILTIN, HIGH);
            irStorage.printAllCommands();
            break; // 添加或更新成功后退出循环
        }
    }

    // 添加红外接收禁用
    irrecv.disableIRIn();
    
    if (!result) {
        Serial.println("学习超时，未接收到红外信号！");
        digitalWrite(LED_BUILTIN, HIGH);
    }
    
    return result;
}