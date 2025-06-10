#include <ESP8266WiFi.h>
#include <ArduinoWebsockets.h>

const char *ssid = "Hades";
const char *password = "congchua";
const char *serverUrl = "ws://192.168.137.1:5000"; // Địa chỉ WebSocket Server

using namespace websockets;
WebsocketsClient client;
#define STOP_PIN 14
#define STOP_DURATION 5000  
#define RECONNECT_DELAY 5000  
#define LOOP_DELAY 100



bool stop_received = false;
unsigned long last_reconnect_attempt = 0;
void onMessageCallback(WebsocketsMessage message) {
    Serial.print("Received: ");
    Serial.println(message.data());

    if (message.data() == "stop") {
        stop_received = true;
    }
}

void sendMessage(const String &message) {
    if (client.available()) {
        client.send(message);
        Serial.println("Sent: " + message);
    } else {
        Serial.println("WebSocket not available for sending messages.");
    }
}
void setup() {
    Serial.begin(115200);
    
    // Khởi tạo GPIO
    pinMode(STOP_PIN, OUTPUT);
    digitalWrite(STOP_PIN, LOW);  // Đảm bảo trạng thái mặc định là LOW
    
    // Kết nối WiFi
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nConnected to WiFi!");

    // Cấu hình WebSocket
    client.onMessage(onMessageCallback);
    
    // Kết nối WebSocket
    Serial.println("Connecting to WebSocket Server...");
    if (client.connect(serverUrl)) {
        Serial.println("Connected to Server!");
        sendMessage("esp8266");  // Gửi tin nhắn phân loại client
    } else {
        Serial.println("WebSocket connection failed.");
    }
}


void loop() {
    // Xử lý WebSocket
    if (client.available()) {
        client.poll();
    } else {
        // Thử kết nối lại sau mỗi RECONNECT_DELAY
        unsigned long current_time = millis();
        if (current_time - last_reconnect_attempt >= RECONNECT_DELAY) {
            Serial.println("Reconnecting WebSocket...");
            if (client.connect(serverUrl)) {
                Serial.println("Reconnected!");
                sendMessage("esp8266");  // Gửi lại tin nhắn phân loại
            }
            last_reconnect_attempt = current_time;
        }
    }

    // Xử lý tín hiệu dừng
    if (stop_received) {
        digitalWrite(STOP_PIN, HIGH);
        delay(STOP_DURATION);
        digitalWrite(STOP_PIN, LOW);
        stop_received = false;
        sendMessage("renew");
    }

    delay(LOOP_DELAY);
}