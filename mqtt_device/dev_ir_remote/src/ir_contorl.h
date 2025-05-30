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

// ir_send 函数：接收某 char* cmdInfo 发送对应红外信号并打印日志
bool ir_send(const char* cmdInfo) {
    IRCommand cmd;
    if (irStorage.getCommand(cmdInfo, &cmd)) {
        Serial.printf("准备发送红外信号: %s\n", cmdInfo);

        switch (cmd.dataType) {
            case 0: // RAW
                irsend.sendRaw(cmd.rawData, cmd.rawLength, 38);
                ESP.wdtFeed();
                Serial.printf("已发送 RAW 红外信号: %s\n", cmdInfo);
                break;
            case 1: // NEC
                irsend.sendNEC(cmd.dataCode, cmd.address);
                ESP.wdtFeed();
                Serial.printf("已发送 NEC 红外信号: %s\n", cmdInfo);
                break;
            case 2: // SONY
                irsend.sendSony(cmd.dataCode, cmd.address);
                ESP.wdtFeed();
                Serial.printf("已发送 SONY 红外信号: %s\n", cmdInfo);
                break;
            case 3: // RC5
                irsend.sendRC5(cmd.dataCode, cmd.address);
                ESP.wdtFeed();
                Serial.printf("已发送 RC5 红外信号: %s\n", cmdInfo);
                break;
            default:
                Serial.printf("不支持的红外信号类型: %s\n", cmdInfo);
                return false;
        }
        ESP.wdtFeed();
        return true;
    } else {
        Serial.printf("未找到对应的红外信号: %s\n", cmdInfo);
        ESP.wdtFeed();
        return false;
    }
}

// ir_learn 函数：10s 内接收红外信号，解析打印接收到的红外信号
bool ir_learn(const char* rec_cmdInfo) {
    irrecv.enableIRIn(); // 启用红外接收
    Serial.println("开始学习红外信号，等待 10 秒...");
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN,LOW);

    unsigned long startTime = millis();
    decode_results results;

    while (millis() - startTime < 10000) {
        ESP.wdtFeed();
        if (irrecv.decode(&results)) {
            Serial.println("接收到红外信号！");

            IRCommand outCmd;

            strncpy(outCmd.cmdInfo, rec_cmdInfo, sizeof(outCmd.cmdInfo) - 1);
            outCmd.cmdInfo[sizeof(outCmd.cmdInfo) - 1] = '\0'; 

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
            
            Serial.println(irStorage.addCommand(outCmd)?"添加成功！":"添加失败！");

            irrecv.resume(); // 继续接收下一个信号

            digitalWrite(LED_BUILTIN, HIGH);
            irStorage.printAllCommands();
            return true;
        }
    }

    Serial.println("学习超时，未接收到红外信号！");
    digitalWrite(LED_BUILTIN, HIGH);

    return false;
}