import asyncio
import websockets
import uuid
import shutil
import os

HOST = "0.0.0.0"  # Chấp nhận kết nối từ mọi IP trong mạng LAN
PORT = 5000       # Cổng lắng nghe
DIRECTORY = "image_esp32cam"
clients = set()  # Danh sách các client đang kết nối

# Tạo thư mục nếu chưa có
os.makedirs(DIRECTORY, exist_ok=True)

async def train_model():
    """Hàm giả lập quá trình train mô hình, trả về True khi đã train xong"""
    await asyncio.sleep(2)  # Giả lập thời gian train (10 giây)
    return True  # Giả sử đã train xong

async def handle_client(websocket):
    """Xử lý kết nối từ ESP32-CAM"""
    print("[📷] ESP32-CAM connected!")
    clients.add(websocket)  # Thêm ESP32-CAM vào danh sách client

    try:
        message = await websocket.recv()

        if isinstance(message, str):  
            print(f"[📩] Received: {message}")

            if message == "Hello Server":
                await websocket.send("Hello ESP32-CAM")  # Phản hồi ESP32-CAM
                await asyncio.sleep(2)
                await websocket.send("capture")  # Yêu cầu chụp ảnh

        while True:
            # Nhận dữ liệu ảnh từ ESP32-CAM
            image_data = await websocket.recv()
            
            if isinstance(image_data, bytes):
                name_image = str(uuid.uuid4()) + ".jpg"
                print(f"[📥] Received image ({len(image_data)} bytes)")

                # Lưu ảnh vào thư mục
                image_path = os.path.join(DIRECTORY, name_image)
                with open(image_path, "wb") as f:
                    f.write(image_data)
                print(f"[💾] Image saved as {image_path}")

                # Kiểm tra xem model đã train xong chưa
                if await train_model():
                    print("[✅] Model training complete! Sending 'stop' signal...")
                    
                    # Gửi tín hiệu "stop" đến tất cả client (bao gồm ESP8266)
                    for client in clients:
                        if client.remote_address[0]=='192.168.137.232':
                            await client.send("stop")
                    
                    break  # Kết thúc vòng lặp khi train xong

                # Tiếp tục yêu cầu ESP32-CAM chụp ảnh
                await asyncio.sleep(2)
                await websocket.send("capture")

    except websockets.exceptions.ConnectionClosed:
        print("[❌] ESP32-CAM disconnected")
    finally:
        clients.remove(websocket)

async def main():
    """Chạy WebSocket Server"""
    server = await websockets.serve(handle_client, HOST, PORT)
    print(f"[🚀] WebSocket Server running on ws://{HOST}:{PORT}")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
