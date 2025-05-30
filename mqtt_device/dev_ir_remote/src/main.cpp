#include <Arduino.h>
#include <EEPROM.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "ir_storage.h"
#include "ir_contorl.h"
#include "mqtt_tools.h"

// 设备配置
const char *device_id = "ir_remote666";
const char *command_topic = "devices/command/ir_remote666";
const char *status_topic = "devices/status/ir_remote666";

// 定义状态结构体
struct DeviceStatus {
    bool is_working;
    uint8_t temperature;
    String working_mode;  // 使用String避免缓冲区溢出
    String wind_mode;
} currentStatus;

// 全局变量
bool learning_mode = false;
unsigned long lastReconnectAttempt = 0;

// 函数声明
void callback(char *topic, byte *payload, unsigned int length);
void publish_status();
void parse_set_cmd_status(JsonObject params);

void callback(char *topic, byte *payload, unsigned int length) {
    // 添加WDT喂狗
    ESP.wdtFeed();
    
    Serial.print("Message arrived [");
    Serial.print(topic);
    Serial.print("] Raw payload: ");
    for(unsigned int i=0; i<length; i++) {
        Serial.print((char)payload[i]);
    }
    Serial.println();

    // 使用动态JSON文档防止内存溢出
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, payload, length);
    
    if(error) {
        Serial.print("JSON parse error: ");
        Serial.println(error.c_str());
        return;
    }

    const char* cmd_type = doc["command"];
    if(!cmd_type) {
        Serial.println("Missing command field");
        return;
    }

    Serial.print("Command received: ");
    Serial.print(cmd_type);
    Serial.print(" : ");
    serializeJson(doc["params"], Serial);
    Serial.println();

    if(strcmp(cmd_type, "ir_learn") == 0) {
        const char* cmd_value = doc["params"][0];
        if(!cmd_value) {
            Serial.println("Missing learn value");
            return;
        }
        
        learning_mode = true;
        publish_status();
        
        if(ir_learn(cmd_value)) {
            Serial.println("Learn successful");
        } else {
            Serial.println("Learn failed");
        }
        
        learning_mode = false;
        publish_status();
    } 
    else if(strcmp(cmd_type, "send") == 0) {
        const char* cmd_value = doc["params"][0];
        if(!cmd_value) {
            Serial.println("Missing send value");
            return;
        }
        
        if(ir_send(cmd_value)) {
            Serial.println("Send successful");
        } else {
            Serial.println("Send failed");
        }
    }
    else if(strcmp(cmd_type, "set_cmd_status") == 0) {
        // 直接处理参数数组 [[key, value], [key, value], ...]
        JsonArray params = doc["params"];
        if(params) {
            // 创建临时对象存储参数
            JsonDocument tempDoc;
            
            for(JsonVariant item : params) {
                if(item.is<JsonArray>() && item.size() == 2) {
                    const char* key = item[0];
                    JsonVariant value = item[1];
                    
                    // 根据键名更新状态
                    if(strcmp(key, "working_model") == 0 && value.is<const char*>()) {
                        currentStatus.working_mode = value.as<const char*>();
                    }
                    else if(strcmp(key, "temperature") == 0 && value.is<int>()) {
                        currentStatus.temperature = value.as<int>();
                    }
                    else if(strcmp(key, "wind_model") == 0 && value.is<const char*>()) {
                        currentStatus.wind_mode = value.as<const char*>();
                    }
                }
            }
            
            Serial.println("Updated status from set_cmd_status:");
            Serial.printf(" - Working mode: %s\n", currentStatus.working_mode.c_str());
            Serial.printf(" - Temperature: %d\n", currentStatus.temperature);
            Serial.printf(" - Wind mode: %s\n", currentStatus.wind_mode.c_str());
        } else {
            Serial.println("Invalid params format for set_cmd_status");
        }
        publish_status();
    }
    else if(strcmp(cmd_type, "toggle") == 0) {
        // 处理开关命令
        const char* state = doc["params"][0];
        if(state) {
            currentStatus.is_working = (strcmp(state, "on") == 0);
            Serial.printf("Toggle command: set is_working to %s\n", currentStatus.is_working ? "on" : "off");
            publish_status();
        }
    }
}

// 发布设备状态（根据您提供的格式优化）
void publish_status() {
    JsonDocument doc;
    
    // 设置基本字段
    doc["type"] = "ir_remote";
    
    // 创建状态对象
    JsonObject status = doc.createNestedObject("status");
    status["is_working"] = currentStatus.is_working ? "on" : "off";
    status["angle"] = nullptr; // 固定为null
    
    // 创建命令状态对象
    JsonObject cmd_status = status.createNestedObject("cmd_status");
    cmd_status["working_model"] = currentStatus.working_mode;
    cmd_status["temperature"] = currentStatus.temperature;
    cmd_status["wind_model"] = currentStatus.wind_mode;
    
    // 序列化并发布
    char buffer[256];
    serializeJson(doc, buffer);
    mqttClient.publish(status_topic, buffer);
    
    Serial.print("Status published: ");
    serializeJson(doc, Serial);
    Serial.println();
}

void setup() {
    Serial.begin(9600);
    Serial.println("\nBooting...");
    
    // 初始化状态
    currentStatus.is_working = false;
    currentStatus.temperature = 25;
    currentStatus.working_mode = "制冷";
    currentStatus.wind_mode = "固定";
    
    // 初始化存储
    irStorage.begin();
    
    // 初始化网络
    setupWiFi();
    setupMQTT();
    
    // 配置看门狗和电源管理
    ESP.wdtEnable(15000); // 15秒看门狗
    WiFi.setSleepMode(WIFI_NONE_SLEEP);
    ESP.wdtFeed();
    
    Serial.println("Setup complete");
    irStorage.printAllCommands();
    publish_status(); // 初始状态发布
}

void loop() {
    ESP.wdtFeed(); // 主循环喂狗
    
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi disconnected, reconnecting...");
        setupWiFi();
        delay(1000);
    }

    if (!mqttClient.connected()) {
        if (millis() - lastReconnectAttempt > 5000) { 
            reconnect();
            if(mqttClient.connected()) {
                lastReconnectAttempt = 0;
                publish_status(); // 重连后发布状态
            } else {
                lastReconnectAttempt = millis();
            }
        }
    } else {
        mqttClient.loop();
    }
    
    delay(10);
}