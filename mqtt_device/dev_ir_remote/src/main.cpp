#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <IRremoteESP8266.h>

#include "ir_storage.h"
#include "mqtt_tools.h"

// 设备配置
const char *device_id = "ir_remote666";
const char *command_topic = "devices/command/ir_remote666";
const char *status_topic = "devices/status/ir_remote666";

// 硬件配置
const int led_pin = D2;
const int recv_pin = D5;

// 函数声明
void handle_movement();
void publish_status();
void callback(char *topic, byte *payload, unsigned int length);

IRStorage irStorage;

void ir_send(char *cmd_type, char *cmd_params)
{
  // 发送IR信号
  Serial.printf("Ir send command %s : %s \n", cmd_type, cmd_params);
}

void ir_learn(char *cmd_info)
{
  // 10秒内输入或无输入时，结束学习模式
  Serial.println("IR learning mode");

  // 将接收的信号填写到EEPROM
  IRCommand cmd;
  if (irStorage.getCommand(cmd_info, &cmd))
  {
    Serial.println("Command already exists, updating it");
    irStorage.updateCommand(cmd_info, cmd);
  }
  else
  {
    Serial.println("Command does not exist, adding it");
    cmd.dataType = 1;
    strncpy(cmd.cmdInfo, cmd_info, sizeof(cmd.cmdInfo) - 1); // 安全拷贝
    cmd.cmdInfo[sizeof(cmd.cmdInfo) - 1] = '\0';             // 确保终止符
    cmd.dataCode = 0xABCD;
    cmd.address = 0x1234;
    memcpy(cmd.rawData, (uint16_t[]){12, 421, 42, 14, 21, 214, 4, 1, 1532, 432}, sizeof(cmd.rawData));
    cmd.rawLength = 10;

    irStorage.addCommand(cmd);
    irStorage.commit();
  }
}

void eeprom_init()
{
  // 初始化EEPROM
}

// 回调函数，处理接收到的MQTT消息
void callback(char *topic, byte *payload, unsigned int length)
{
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

  if (cmd_type == "toggle")
  {
    // 处理开关机功能
    if (cmd_type.indexOf("on") != -1)
    {
      Serial.println("Turning on the device");
    }
    else if (cmd_type.indexOf("off") != -1)
    {
      Serial.println("Turning off the device");
    }
    ir_send("toggle", "on");
  }

  if (cmd_type == "learn")
  {
    // 处理学习功能
    Serial.println("Learning IR command");

    ir_learn("cmd_info");
  }

  if (cmd_type == "clear_cmd")
  {
    // 清理所有EEPROM中的红外命令
    irStorage.formatEEPROM();
    publish_status();
    Serial.println("Cleared all IR commands, you should restart the device to take effect");
  }

  // 处理set_cmd_status功能
  if (cmd_type == "set_cmd_status")
  {
    // 处理工作模式设置
    if (cmd_type.indexOf("working_mode"))
    {
      Serial.println("Setting working mode to cooling");
    }
    else if (cmd_type.indexOf("制热") != -1)
    {
      Serial.println("Setting working mode to heating");
    }
    else if (cmd_type.indexOf("除湿") != -1)
    {
      Serial.println("Setting working mode to dehumidification");
    }

    if (cmd_type.indexOf("temperature") != -1)
    {
      // 处理温度设置
      int start = cmd_type.indexOf("temperature") + 13;
      int end = cmd_type.indexOf(",", start);
      if (end == -1)
      {
        end = cmd_type.indexOf("}", start);
      }
      String temperature = cmd_type.substring(start, end);
      int temperature = tempStr.toInt();
      if (temperature >= 16 && temperature <= 30)
      {
        Serial.print("Setting temperature to ");
        Serial.println(temperature);
      }
      else
      {
        Serial.println("Invalid temperature value");
      }
    }

    if (cmd_type.indexOf("wind_model") != -1)
    {
      // 处理吹风模式设置
      if (cmd_type.indexOf("上下") != -1)
      {
        Serial.println("Setting wind mode to 上下");
      }
      else if (cmd_type.indexOf("摇头") != -1)
      {
        Serial.println("Setting wind mode to 摇头");
      }
      else if (cmd_type.indexOf("固定") != -1)
      {
        Serial.println("Setting wind mode to 固定");
      }
    }
  }
}

// 发布设备状态到MQTT服务器
void publish_status()
{

}

void setup()
{
  Serial.begin(115200);

  setupWiFi();                        // 初始化WiFi
  setupMQTT();                        // 初始化MQTT
  ESP.wdtEnable(5000);                // 启用看门狗
  WiFi.setSleepMode(WIFI_NONE_SLEEP); // 禁用WiFi睡眠

  Serial.println("setup complete-----");
}

void loop()
{

  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.printf("WIFI disconnect,try reconnecting [WiFi] SSID: %s\n", ssid);
    setupWiFi();
  }

  if (!mqttClient.connected())
    reconnect();
  mqttClient.loop(); // 处理MQTT消息
  handle_movement();
  delay(10);
}