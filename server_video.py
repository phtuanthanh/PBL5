import asyncio
import websockets
import uuid
import os
import cv2
from natsort import natsorted

HOST = "0.0.0.0"
PORT = 5000
DIRECTORY = "B2"
clients = set()
MAX_IMAGES = 300  # 60 ảnh cho 1 phút video
FPS = 1          # 1 frame mỗi giây
# Tạo thư mục nếu chưa có
os.makedirs(DIRECTORY, exist_ok=True)

async def handle_client(websocket):
    print("[📷] ESP32-CAM connected!")
    clients.add(websocket)
    image_count = 0
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
            
                name_image = str(STT) + ' - B2' + ".jpg"
                STT = STT + 1
                image_path = os.path.join(DIRECTORY, name_image)
                with open(image_path, "wb") as f:
                    f.write(image_data)
                print(f"[📥] Saved image {name_image}")
                image_count += 1

                if image_count >= MAX_IMAGES:
                    print("[📸] Đã nhận đủ ảnh. Tạo video...")
                    # create_video_from_images(DIRECTORY, "esp32cam_video.mp4", fps=FPS)
                    await websocket.send("stop")
                    break

                await asyncio.sleep(1.5)  # Delay giữa mỗi ảnh cho ESP32-CAM kịp xử lý
                await websocket.send("capture")

    except websockets.exceptions.ConnectionClosed:
        print("[❌] ESP32-CAM disconnected")
    finally:
        clients.remove(websocket)

async def main():
    server = await websockets.serve(handle_client, HOST, PORT)
    print(f"[🚀] WebSocket Server running on ws://{HOST}:{PORT}")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
