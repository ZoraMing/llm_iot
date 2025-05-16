#include "mqtt_tools.h"
#include <ArduinoJson.h>

// WiFi配置
// const char *ssid = "103";
// const char *password = "15821570898";

// const char *ssid = "myWifi";
// const char *password = "12345678";

const char *ssid = "CMCC-7vps";
const char *password = "i2pkq9qe";

// MQTT配置
const char *mqtt_server = "47.237.21.234";
const int mqtt_port = 1884;
const char *mqtt_user = "testuser1";
const char *mqtt_pass = "zora666";
const char *topic_cmd = "devices/command/servo666";
const char *topic_status = "devices/status/servo666";


// MQTT客户端对象
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// WiFi连接函数
void setupWiFi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  WiFi.setSleepMode(WIFI_LIGHT_SLEEP);
}


// MQTT连接函数
void setupMQTT() {
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(callback); // 回调函数在主文件中定义
}

// 重新连接MQTT服务器
void reconnect() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (mqttClient.connect("servo666", mqtt_user, mqtt_pass)) {
      Serial.println("connected");
      mqttClient.subscribe(topic_cmd);
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" retrying in 5 seconds");
      delay(5000);
    }
  }
}