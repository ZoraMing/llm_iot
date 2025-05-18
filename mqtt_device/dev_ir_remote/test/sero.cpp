// #include <ESP8266WiFi.h>
// #include <PubSubClient.h>
// #include <ArduinoJson.h>
// #include <Servo.h>

// // WiFi配置
// const char *ssid = "103";
// const char *password = "15821570898";

// // MQTT配置
// const char *mqtt_server = "47.237.21.234";
// const int mqtt_port = 1884;
// const char *mqtt_user = "testuser1";
// const char *mqtt_pass = "zora666";

// // 设备配置
// const char *device_id = "servo666";
// const char *command_topic = "devices/command/servo666";
// const char *status_topic = "devices/status/servo666";

// // 硬件配置
// const int servo_pin = D4;     // GPIO2 (D4)


// Servo servo;
// WiFiClient espClient;
// PubSubClient client(espClient);

// // 全局变量
// int current_angle = 0;
// int target_angle = 0;
// int init_angle = 0;
// bool is_moving = false;

// // 函数声明
// void setup_wifi();
// void callback(char *topic, byte *payload, unsigned int length);
// void handle_movement();
// void publish_status();
// void reconnect();



// // 连接到WiFi网络
// void setup_wifi()
// {
//   delay(10);
//   Serial.println();
//   Serial.print("Connecting to: ");
//   Serial.println(ssid);

//   WiFi.begin(ssid, password);

//   while (WiFi.status() != WL_CONNECTED)
//   {
//     delay(500);
//     Serial.print(".");
//   }

//   Serial.println("");
//   Serial.println("WiFi connected");
//   Serial.println("IP address: ");
//   Serial.println(WiFi.localIP());
//   // 启用电源管理
//   WiFi.setSleepMode(WIFI_LIGHT_SLEEP);
// }

// // 重新连接到MQTT服务器
// void reconnect()
// {
//   while (!client.connected())
//   {
//     Serial.print("Attempting MQTT connection...");
//     if (client.connect(device_id, mqtt_user, mqtt_pass))
//     {
//       Serial.println("connected");
//       client.subscribe(command_topic);
//     }
//     else
//     {
//       Serial.print("failed, rc=");
//       Serial.print(client.state());
//       Serial.println(" retrying in 5 seconds");
//       delay(5000);
//     }
//   }
// }

// // 转动参数
// const int STEP_DELAY = 10; // 每度转动间隔(ms)
// const int MIN_ANGLE = 0;
// unsigned long last_step = 0;
// const int MAX_ANGLE = 180;

// void handle_movement()
// {
//   if (current_angle == target_angle)
//   {
//     if (is_moving)
//     {
//       is_moving = false;
//       publish_status();
//     }
//     return;
//   }

//   if (millis() - last_step >= STEP_DELAY)
//   {
//     last_step = millis();
//     is_moving = true;

//     current_angle += (target_angle > current_angle) ? 1 : -1;
//     current_angle = constrain(current_angle, MIN_ANGLE, MAX_ANGLE);

//     servo.write(current_angle);
//     // Serial.printf("Moving: %d° -> %d°\n", current_angle, target_angle);

//     if (current_angle == target_angle)
//     {
//       publish_status();
//     }
//   }
// }

// // 处理MQTT消息回调
// void callback(char *topic, byte *payload, unsigned int length)
// {
//   Serial.print("Message arrived [");
//   Serial.print(topic);
//   Serial.println("] ");

//   JsonDocument doc;
//   deserializeJson(doc, payload, length);
//   Serial.println("Received JSON: ");
//   serializeJson(doc, Serial);
//   Serial.println();

//   String cmd_type = doc["command"];
//   int cmd_value = doc["params"][0].as<int>();

//   Serial.println("Command received: " + cmd_type + " : " + String(cmd_value));
//   if (cmd_type == "rest")
//   {

//     // 立即停止运动
//     target_angle = init_angle;
//     is_moving = false;

//     // 直接写入目标角度
//     servo.write(target_angle);
//     publish_status();
//     return;
//   }

//   if (cmd_type == "set_angle")
//   {
//     Serial.println("Set_angle: " + String(cmd_value));
//     target_angle = cmd_value;

//     return;
//   }
// }

// // void set_angle(int angle) {
// //   is_moving = true;
// //   publish_status();
// //   target_angle = angle;
// //   servo.write(target_angle);
// //   is_moving = false;
// //   current_angle = target_angle;
// //   publish_status();
// // }

// // 发布设备状态到MQTT服务器
// void publish_status()
// {
//   JsonDocument doc;
//   JsonObject status = doc[device_id].to<JsonObject>();

//   status["type"] = "servo";
//   JsonObject status_obj = status["status"].to<JsonObject>();
//   status_obj["is_working"] = is_moving ? "on" : "off";
//   status_obj["angle"] = current_angle;

//   char buffer[256];
//   serializeJson(doc, buffer);
//   client.publish(status_topic, buffer);
//   Serial.println("Status published: " + String(buffer));
// }



// void setup()
// {
//   Serial.begin(115200);
//   // 调整舵机脉冲范围
//   servo.attach(servo_pin, 500, 2400); // SG90标准脉冲范围
//   servo.write(init_angle);

//   setup_wifi();
//   ESP.wdtEnable(5000);                // 启用看门狗
//   WiFi.setSleepMode(WIFI_NONE_SLEEP); // 禁用WiFi睡眠
//   client.setServer(mqtt_server, mqtt_port);
//   client.setCallback(callback);
//   Serial.println("setup complete-----");
// }

// void loop() {
//   if (!client.connected()) reconnect();
//   client.loop();
//   handle_movement();
//   delay(10); // 添加小延迟以避免过度占用CPU
// }
