#include <ESP8266WiFi.h>
#include <ArduinoWebsockets.h>

const char *ssid = "Hades";
const char *password = "congchua";
const char *serverUrl = "ws://192.168.137.1:5000"; // Địa chỉ WebSocket Server

using namespace websockets;
WebsocketsClient client;

#define CONTROL_PIN 5       // Chân GPIO cần điều khiển
bool stop_received = false; // Biến đánh dấu nhận được tín hiệu "stop"

void onMessageCallback(WebsocketsMessage message)
{
  Serial.print("Received: ");
  Serial.println(message.data());

  if (message.data() == "stop")
  {
    stop_received = true; // Cập nhật trạng thái nhận lệnh
  }
}

void setup()
{
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi!");

  pinMode(CONTROL_PIN, OUTPUT);

  client.onMessage(onMessageCallback);

  Serial.println("Connecting to WebSocket Server...");
  if (client.connect(serverUrl))
  {
    Serial.println("Connected to Server!");
  }
  else
  {
    Serial.println("WebSocket connection failed.");
  }
}

void loop()
{
  if (client.available())
  {
    client.poll(); // Nhận tin nhắn từ server
  }
  else
  {
    Serial.println("Reconnecting WebSocket...");
    client.connect(serverUrl); // Thử kết nối lại nếu mất kết nối
  }

  if (stop_received)
  {
    digitalWrite(CONTROL_PIN, HIGH); // Bật GPIO 5
    delay(500);
    digitalWrite(CONTROL_PIN, LOW); // Mặc định chân ở mức LOW
  }

  delay(100);
}