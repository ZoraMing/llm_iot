#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Servo.h>
#include "mqtt_tools.h"

// 设备配置
const char *device_id = "servo666";
const char *command_topic = "devices/command/servo666";
const char *status_topic = "devices/status/servo666";

// 硬件配置
const int servo_pin = D4;     // GPIO2 (D4)

// 全局变量
int current_angle = 0;
int target_angle = 0;
int init_angle = 0;
bool is_moving = false;

// 舵机对象
Servo servo;


// 函数声明
void handle_movement();
void publish_status();
void callback(char *topic, byte *payload, unsigned int length);


// 转动参数
const int STEP_DELAY = 10;    // 每度转动间隔(ms)
const int MIN_ANGLE = 0;
unsigned long last_step = 0;
const int MAX_ANGLE = 180;

void handle_movement() {
  if (current_angle == target_angle) {
    if (is_moving) {
      is_moving = false;
      publish_status();
    }
    return;
  }

  if (millis() - last_step >= STEP_DELAY) {
    last_step = millis();
    is_moving = true;

    current_angle += (target_angle > current_angle) ? 1 : -1;
    current_angle = constrain(current_angle, MIN_ANGLE, MAX_ANGLE);

    servo.write(current_angle);

    if (current_angle == target_angle) {
       is_moving = false;
      publish_status();
    }
  }
}

// MQTT回调函数（处理接收到的消息）
void callback(char *topic, byte *payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.println("] ");

  JsonDocument doc;
  deserializeJson(doc, payload, length);
  Serial.println("Received JSON: ");
  serializeJson(doc, Serial);
  Serial.println();

  String cmd_type = doc["command"];
  int cmd_value = doc["params"][0].as<int>();

  Serial.println("Command received: " + cmd_type + " : " + String(cmd_value));
  if (cmd_type == "rest") {
    target_angle = init_angle;
    is_moving = false;
    servo.write(target_angle);
    publish_status();
    return;
  }

  if (cmd_type == "set_angle") {
    target_angle = cmd_value;
  }
}

// 发布设备状态到MQTT服务器
void publish_status() {
  JsonDocument doc;
  JsonObject status = doc[device_id].to<JsonObject>();

  status["type"] = "servo";
  JsonObject status_obj = status["status"].to<JsonObject>();
  status_obj["is_working"] = is_moving ? "on" : "off";
  status_obj["angle"] = current_angle;

  char buffer[256];
  serializeJson(doc, buffer);
  mqttClient.publish(status_topic, buffer);
  Serial.println("Status published: " + String(buffer));
}

void setup() {
  Serial.begin(9600);
  servo.attach(servo_pin, 500, 2400); // SG90标准脉冲范围
  servo.write(init_angle);

  setupWiFi();                // 初始化WiFi
  setupMQTT();                // 初始化MQTT
  ESP.wdtEnable(5000);        // 启用看门狗
  WiFi.setSleepMode(WIFI_NONE_SLEEP); // 禁用WiFi睡眠

  Serial.println("setup complete-----");
}
unsigned long lastReconnectAttempt = 0;

void loop() {

  if (WiFi.status() != WL_CONNECTED) {
    Serial.printf("WIFI disconnect,try reconnecting [WiFi] SSID: %s\n", ssid);
    setupWiFi();
  }

  if (!mqttClient.connected()) {
      if (millis() - lastReconnectAttempt > 5000) { 
        reconnect();
        lastReconnectAttempt = millis();
      }
    } else {
      mqttClient.loop(); // 处理MQTT消息
    }

  handle_movement();
  ESP.wdtFeed();
  delay(10);
}