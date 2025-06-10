import asyncio
import websockets
import uuid
import os
import time
from ultralytics import YOLO
import cv2
from collections import deque
import json

message_queue = deque() 
# ====================== Cấu hình ======================
HOST = "0.0.0.0"  # Cho phép mọi IP kết nối
PORT = 5000
DIRECTORY = "image_esp32cam"
MODEL_PATH = "best (2).pt"
ESP32_IP = "192.168.137.232"
detection_map = {
            "A1": 0,
            "A2": 0,
            "B1": 0,
            "B2": 0
        }
esp32_clients = set()
flutter_clients = set()
esp8266_clients = set()  # Thêm set cho ESP8266 clients

# Hàng đợi FIFO cho các từ khóa
keyword_queue = deque()
is_no_capture = False
# Danh sách các từ khóa hợp lệ
VALID_KEYWORDS = ["A1", "A2", "B1", "B2"]

# Tạo thư mục lưu ảnh nếu chưa có
os.makedirs(DIRECTORY, exist_ok=True)

# ====================== Load model 1 lần ======================
model = YOLO(MODEL_PATH)

# ====================== Hàm Nhận Diện ======================
def detect_board(image):
    try:
        results = model(image, conf=0.3, imgsz=640)
        result = results[0]
        detected_class = None
        if len(result.boxes) > 0:
            class_id = int(result.boxes[0].cls[0])
            detected_class = result.names[class_id]
        return detected_class
    except Exception as e:
        print(f"[❌] Error in detection: {str(e)}")
        return None
# ====================== Gửi tín hiệu dừng đến ESP8266 ======================
async def send_stop_to_esp8266():
    for client in esp8266_clients:
        try:
            await client.send("stop")
        except websockets.exceptions.ConnectionClosed:
            print("ESP8266 client disconnected")
            esp8266_clients.remove(client)
# ====================== Xử Lý ESP32 ======================
async def handle_esp32_client(websocket):
    global is_no_capture
    esp32_clients.add(websocket)
    print("[🔄] New ESP32-CAM client connected")
    # Khởi tạo map với giá trị ban đầu là 0
    start_time = time.time()
    try:
       # await websocket.send("Hello ESP32-CAM")
        
        await websocket.send("capture")
        STT = 1
        while True:
            #print queue
            print(f"[🔄] Current keyword queue: {list(keyword_queue)}")
            if not is_no_capture:
                message = await websocket.recv()
                
                # Xử lý ảnh
                if isinstance(message, bytes):
                    # Lưu ảnh
               
                    filename = str(STT) + ".jpg"
                    filepath = os.path.join(DIRECTORY, filename)
                    STT+=1
                    with open(filepath, "wb") as f:
                        f.write(message)
                    # Nhận diện ảnh
                    detected_class = detect_board(filepath)

                    if detected_class:
                        print(f"[🎯] Detected class: {detected_class}")
                        # Tăng giá trị trong map
                        if detected_class in detection_map:
                            detection_map[detected_class] += 1
                          
                            print(f"[📊] Current map: {detection_map}")
                            
                            if time.time() - start_time > 2.5 and max(detection_map.values()) > 2:   #kieemr tra nen sua hay k
                                # Tìm key có giá trị lớn nhất
                                max_key = max(detection_map.items(), key=lambda x: x[1])[0]
                                max_value = detection_map[max_key]
                                if keyword_queue and max_key == keyword_queue[0] :
                                    print(f"[🛑] Sending stop signal for {max_key}")
                                    await send_stop_to_esp8266()
                                    if keyword_queue:
                                        keyword_queue.popleft()
                                    #send to flutter, current table
                                    for key in detection_map:
                                        detection_map[key] = 0
                                    is_no_capture = True
                                    await notify_flutter_clients(max_key, "stopping")
                                    start_time = time.time()
                                else :
                                    print(f"[⚠️] Detected {max_key} but not in keyword queue or not the first keyword.")
                                    for key in detection_map:
                                        detection_map[key] = 0
                                    is_no_capture = False
                                    start_time = time.time()
                    else:
                        print("[⚠️] No object detected.")

                    # Tiếp tục yêu cầu ảnh mới
                    if not is_no_capture:
                        
                      
                        print("capture....")
                        await websocket.send("capture")
            else:
                print("[⏸️] No capture in progress, waiting...")
                start_time = time.time()
                
                await asyncio.sleep(0.1)  

    except websockets.exceptions.ConnectionClosed:
        print("[❌] ESP32-CAM disconnected")
    finally:
        esp32_clients.remove(websocket)

# ====================== Xử Lý Flutter App ======================
async def handle_flutter_client(websocket):
    flutter_clients.add(websocket)
    try:
        while True:
            message = await websocket.recv()
            if isinstance(message, str):
                try:
                    # Kiểm tra nếu message là một trong các từ khóa hợp lệ
                    if message in VALID_KEYWORDS:
                        # Thêm vào hàng đợi
                        keyword_queue.append(message)
                        # Gửi xác nhận về cho app
                        await websocket.send(json.dumps({
                            "keyword": message,
                            "status": "success",
                        }))
                        print(f"[✅] Received keyword: {message}")
                    else:
                        print(f"[⚠️] Invalid keyword received: {message}")
                except Exception as e:
                    print(f"[❌] Error processing message: {str(e)}")
    except websockets.exceptions.ConnectionClosed:
        print("[❌] Flutter client disconnected")
    finally:
        flutter_clients.remove(websocket)

# ====================== Xử Lý ESP8266 ======================
async def handle_esp8266_client(websocket):
    global is_no_capture
    print("[🔄] New ESP8266 client connected")
    esp8266_clients.add(websocket)
    try:
        await websocket.send("Hello ESP8266")
        while True:
            message = await websocket.recv()
            if message == "renew":
                for key in detection_map:
                    detection_map[key] = 0
                print("renewed")
                is_no_capture = False
                print(f"[DEBUG] is_no_capture set to {is_no_capture}, keyword_queue: {keyword_queue}")
               # await notify_flutter_clients(None, "moving")
                for client in esp32_clients:
                        try:
                            print("[🔄] Sending new capture command to ESP32...")
                            await client.send("capture")
                        except websockets.exceptions.ConnectionClosed:
                            print("[❌] Failed to send capture command - ESP32 disconnected")
                            esp32_clients.remove(client)
                continue
    except websockets.exceptions.ConnectionClosed:
        print("[❌] ESP8266 disconnected")
    finally:
        esp8266_clients.remove(websocket)

# ====================== Xử Lý Client ======================
async def handle_client(websocket):
    try:
        # Đợi message đầu tiên để xác định loại client
        message = await websocket.recv()
        
        if isinstance(message, str):
            if message == "Hello Server":
                await handle_esp32_client(websocket)
            elif message == "flutter":
                await handle_flutter_client(websocket)
            elif message == "esp8266": 
                await handle_esp8266_client(websocket)
            else:
                print(f"[⚠️] Unknown client type: {message}")
                await websocket.close()
    except websockets.exceptions.ConnectionClosed:
        print("[❌] Client disconnected before identification")

# ====================== Server WebSocket ======================
async def main():
    server = await websockets.serve(handle_client, HOST, PORT)
    print(f"[🚀] Server running on ws://{HOST}:{PORT}")
    await server.wait_closed()

async def notify_flutter_clients(keyword, status):
    message = json.dumps({
        "keyword": keyword,
        "car_status": status
    })
    for client in flutter_clients:
        try:
            await client.send(message)
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
