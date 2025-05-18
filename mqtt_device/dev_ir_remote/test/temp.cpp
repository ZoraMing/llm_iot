// #include <ESP8266WiFi.h>
// #include <PubSubClient.h>
// #include <ArduinoJson.h>

// #include <IRremoteESP8266.h>
// #include <IRsend.h>
// #include <ir_Samsung.h>


// // 配置区
// const char* ssid = "your_SSID";
// const char* password = "your_PASSWORD";
// const char* mqtt_server = "your.broker.com";
// const int mqtt_port = 1883;
// const char* mqtt_user = "username";
// const char* mqtt_pass = "password";

// // 设备配置
// const char* device_id = "ir_remote666";
// const char* command_topic = "devices/command/ir_remote666";
// const char* status_topic = "devices/status/ir_remote666";

// // 状态结构体
// struct DeviceStatus {
//   bool is_working = false;
//   char work_mode[10] = "制冷";
//   int temperature = 25;
//   char wind_mode[10] = "固定";
// };

// // 全局对象
// WiFiClient espClient;
// PubSubClient client(espClient);
// DeviceStatus current_status;

// // 初始化函数
// void setup_wifi();
// void reconnect();
// void mqtt_callback(char* topic, byte* payload, unsigned int length);
// void handle_toggle(JsonArray params);
// void handle_set_cmd(JsonArray params);
// void publish_status();




// // WiFi连接
// void setup_wifi() {
//   delay(10);
//   Serial.println("\nConnecting to ");
//   Serial.println(ssid);

//   WiFi.begin(ssid, password);

//   while (WiFi.status() != WL_CONNECTED) {
//     delay(500);
//     Serial.print(".");
//   }

//   Serial.println("\nWiFi connected");
//   Serial.println("IP address: ");
//   Serial.println(WiFi.localIP());
// }

// // MQTT重连
// void reconnect() {
//   while (!client.connected()) {
//     Serial.print("Connecting MQTT...");
//     if (client.connect(device_id, mqtt_user, mqtt_pass)) {
//       Serial.println("connected");
//       client.subscribe(command_topic);
//     } else {
//       Serial.print("failed, rc=");
//       Serial.print(client.state());
//       Serial.println(" retry in 5s");
//       delay(5000);
//     }
//   }
// }

// // MQTT消息回调
// void mqtt_callback(char* topic, byte* payload, unsigned int length) {
//   Serial.print("Message [");
//   Serial.print(topic);
//   Serial.print("] ");
  
//   // 解析JSON
//   JsonDocument doc;
//   deserializeJson(doc, payload, length);


//   // DeserializationError error = deserializeJson(doc, payload, length);
  
//   // if (error) {
//   //   Serial.print("JSON error: ");
//   //   Serial.println(error.c_str());
//   //   return;
//   // }

//   // 命令验证
//   // if (!doc.containsKey("command") || !doc.containsKey("params")) {
//   //   Serial.println("Invalid command format");
//   //   return;
//   // }

//   const char* command = doc["command"];
//   JsonArray params = doc["params"];
  
//   // 命令路由
//   if (strcmp(command, "toggle") == 0) {
//     handle_toggle(params);
//   } else if (strcmp(command, "set_cmd_status") == 0) {
//     handle_set_cmd(params);
//   } else {
//     Serial.println("Unknown command");
//   }
  
//   publish_status();
// }

// // 处理开关命令
// void handle_toggle(JsonArray params) {
//   if (params.size() != 1) {
//     Serial.println("Invalid toggle params");
//     return;
//   }
  
//   const char* state = params[0];
//   current_status.is_working = (strcmp(state, "on") == 0);
  
//   Serial.print("Toggle: ");
//   Serial.println(state);
// }

// // 处理设置命令
// void handle_set_cmd(JsonArray params) {
//   if (params.size() != 2) {
//     Serial.println("Invalid set_cmd params");
//     return;
//   }
  
//   const char* type = params[0];
//   const char* value = params[1];
  
//   // 参数验证
//   if (strcmp(type, "working_model") == 0) {
//     if (strcmp(value, "制冷") && strcmp(value, "制热") && strcmp(value, "除湿")) {
//       Serial.println("Invalid work mode");
//       return;
//     }
//     strncpy(current_status.work_mode, value, sizeof(current_status.work_mode));
//   } 
//   else if (strcmp(type, "temperature") == 0) {
//     int temp = atoi(value);
//     if (temp < 16 || temp > 30) {
//       Serial.println("Invalid temperature");
//       return;
//     }
//     current_status.temperature = temp;
//   }
//   else if (strcmp(type, "wind_model") == 0) {
//     if (strcmp(value, "自动") && strcmp(value, "固定") && strcmp(value, "摇头")) {
//       Serial.println("Invalid wind mode");
//       return;
//     }
//     strncpy(current_status.wind_mode, value, sizeof(current_status.wind_mode));
//   }
//   else {
//     Serial.println("Unknown parameter");
//     return;
//   }
  
//   current_status.is_working = true;
//   Serial.print("Set ");
//   Serial.print(type);
//   Serial.print(" to ");
//   Serial.println(value);
// }

// // 发布状态
// void publish_status() {
//   JsonDocument doc;
//   JsonObject status = doc[device_id].to<JsonObject>();
//   JsonObject cmd_status = doc[device_id].to<JsonObject>();
  
//   // status["is_working"] = current_status.is_working ? "on" : "off";
//   doc["type"] = "ir_remote";
  
//   // JsonObject cmd_status = status.createNestedObject("cmd_status");
//   cmd_status["working_model"] = current_status.work_mode;
//   cmd_status["temperature"] = current_status.temperature;
//   cmd_status["wind_model"] = current_status.wind_mode;

//   char buffer[256];
//   serializeJson(doc, buffer);
  
//   client.publish(status_topic, buffer);
//   Serial.print("Published: "+ String(buffer));
//   Serial.println(buffer);
// }



// void setup() {
//   Serial.begin(115200);
//   Serial.println("Starting");
//   setup_wifi();
//   client.setServer(mqtt_server, mqtt_port);
//   client.setCallback(mqtt_callback);
  
//   // 初始化状态
//   publish_status();
// }

// void loop() {
//   if (!client.connected()) {
//     reconnect();
//   }
//   client.loop();
//   delay(10); // 维持系统稳定性
// }