#ifndef MQTT_TOOLS_H
#define MQTT_TOOLS_H

#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// WiFi配置
extern const char *ssid;
extern const char *password;

// MQTT配置
extern const char *mqtt_server;
extern const char *mqtt_user;
extern const char *mqtt_pass;
extern const int mqtt_port;
extern const char *topic_cmd;
extern const char *topic_status;

extern void callback(char* topic, byte* payload, unsigned int length);


// MQTT客户端对象
extern WiFiClient wifiClient;
extern PubSubClient mqttClient;

// 函数声明
void setupWiFi();
void setupMQTT();
void reconnect();

#endif