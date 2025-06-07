#include <ESP8266WiFi.h>
#include <ArduinoWebsockets.h>

const char *ssid = "Hades";
const char *password = "congchua";
const char *serverUrl = "ws://192.168.137.1:5000"; // Địa chỉ WebSocket Server

using namespace websockets;
WebsocketsClient client;

#define STOP_PIN 5       // Chân GPIO cần điều khiển
bool stop_received = false;

void onMessageCallback(WebsocketsMessage message)
{
  Serial.print("Received: ");
  Serial.println(message.data());

  if (message.data() == "stop")
  {
    stop_received = true; 
  }
}
void sendMessage(const String &message)
{
  if (client.available())
  {
    client.send(message);
    Serial.println("Sent: " + message);
  }
  else
  {
    Serial.println("WebSocket not available for sending messages.");
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

  pinMode(STOP_PIN, OUTPUT);

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
    digitalWrite(STOP_PIN, HIGH); // Bật GPIO 5
    delay(5000);
    digitalWrite(STOP_PIN, LOW); // Mặc định chân ở mức LOW
    stop_received = false;
   sendMessage("renew");
  }

  delay(100);
}