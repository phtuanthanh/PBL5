#include <eloquent_esp32cam.h>
#include <ArduinoWebsockets.h>
#include <WiFi.h>

const char *ssid = "Hades";
const char *password = "congchua";                               // Enter WiFi password
const char *websockets_server_host = "ws://192.168.137.1:5000/"; // Enter WebSocket server address

using namespace websockets;
using eloq::camera;

WebsocketsClient client;

void connectToWiFi();
void connectToWebSocket();
void handleMessage(WebsocketsMessage message);
void captureImage();

void setup()
{
    Serial.begin(115200);
    delay(3000);
    Serial.println("___ESP32 CAM with WebSocket___");
    connectToWiFi();
    connectToWebSocket();

    // Setup camera
    camera.pinout.aithinker(); // Adjust according to your camera model
    camera.brownout.disable();
    camera.resolution.hd();
    camera.quality.high();

    // Initialize camera
    while (!camera.begin().isOk())
        Serial.println(camera.exception.toString());

    Serial.println("Camera OK");
    Serial.println("Enter 'capture' (without quotes) to capture an image or send 'capture' command via WebSocket.");
}

void loop()
{
    // Check WiFi and WebSocket connection
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("WiFi disconnected. Reconnecting...");
        connectToWiFi();
    }

    if (!client.available())
    {
        Serial.println("WebSocket disconnected. Reconnecting...");
        connectToWebSocket();
    }

    // Handle commands from Serial Monitor
    if (Serial.available() && Serial.readStringUntil('\n') == "capture")
    {
        captureImage();
    }

    // Listen for messages from WebSocket server
    client.poll();
    delay(100);
}

// Function to connect to WiFi
void connectToWiFi()
{
    Serial.print("Connecting to WiFi...");
    WiFi.begin(ssid, password);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 10)
    {
        Serial.print(".");
        delay(1000);
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED)
    {
        Serial.println("Connected to WiFi");
    }
    else
    {
        Serial.println("Failed to connect to WiFi");
    }
}

// Function to connect to WebSocket server
void connectToWebSocket()
{
    Serial.println("Connecting to WebSocket server...");
    bool connected = client.connect(websockets_server_host);

    if (connected)
    {
        Serial.println("Connected to WebSocket server!");
        client.send("esp32cam");
        client.onMessage(handleMessage);
    }
    else
    {
        Serial.println("Failed to connect to WebSocket server. Retrying in 5 seconds...");
        delay(5000);
        connectToWebSocket();
    }
}

// Function to handle messages from WebSocket server
void handleMessage(WebsocketsMessage message)
{
    Serial.print("Got Message: ");
    Serial.println(message.data());

    if (message.data() == "capture")
    {
        captureImage();
    }
}

// Function to capture image and send it
void captureImage()
{
    Serial.println("Capturing image...");

    if (!camera.capture().isOk())
    {
        Serial.println(camera.exception.toString());
        return;
    }

    camera_fb_t *fb = camera.frame;
    client.sendBinary((const char *)fb->buf, fb->len);

    Serial.printf(
        "JPEG size in bytes: %d. Width: %dpx. Height: %dpx.\n",
        camera.getSizeInBytes(),
        camera.resolution.getWidth(),
        camera.resolution.getHeight());

    Serial.println("Enter 'capture' (without quotes) to capture another image or send 'capture' command via WebSocket.");
}
