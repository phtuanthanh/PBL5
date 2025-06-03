import asyncio
import websockets
import uuid
import os
from ultralytics import YOLO
import cv2

# ====================== Cấu hình ======================
HOST = "0.0.0.0"  # Cho phép mọi IP kết nối
PORT = 5000
DIRECTORY = "image_esp32cam"
MODEL_PATH = "best (2).pt"
ESP32_IP = "192.168.137.232"

clients = set()

# Tạo thư mục lưu ảnh nếu chưa có
os.makedirs(DIRECTORY, exist_ok=True)

# ====================== Load model 1 lần ======================
model = YOLO(MODEL_PATH)

# ====================== Hàm Nhận Diện ======================
def detect_board(image):
 
    model = YOLO("best (2).pt")
   
    results = model(image, conf=0.3, imgsz=640)
   
    result = results[0]
   
    detected_class = None
    if len(result.boxes) > 0:
        class_id = int(result.boxes[0].cls[0])
        detected_class = result.names[class_id]
   
    return detected_class

# ====================== Xử Lý ESP32 ======================
async def handle_client(websocket):
    clients.add(websocket)

    try:
        message = await websocket.recv()
        if isinstance(message, str) and message == "Hello Server":
            await websocket.send("Hello ESP32-CAM")
            await asyncio.sleep(1)
            await websocket.send("capture")
        STT = 1
        while True:
            image_data = await websocket.recv()
            if isinstance(image_data, bytes):
                # Lưu ảnh
                filename = str(STT) + ".jpg"
                filepath = os.path.join(DIRECTORY, filename)
                STT+=1
                with open(filepath, "wb") as f:
                    f.write(image_data)
                # Nhận diện ảnh
                detected_class = detect_board(filepath)

                if detected_class:
                    print(f"[🎯] Detected class: {detected_class}")
                else:
                    print("[⚠️] No object detected.")

                # Tiếp tục yêu cầu ảnh mới
                await asyncio.sleep(1)
                await websocket.send("capture")

    except websockets.exceptions.ConnectionClosed:
        print("[❌] ESP32-CAM disconnected")
    finally:
        clients.remove(websocket)

# ====================== Server WebSocket ======================
async def main():
    server = await websockets.serve(handle_client, HOST, PORT)
    print(f"[🚀] Server running on ws://{HOST}:{PORT}")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
