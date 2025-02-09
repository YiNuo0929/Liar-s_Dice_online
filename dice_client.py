import tkinter as tk
from tkinter import scrolledtext
import socket
import threading
import atexit
from PIL import Image, ImageTk  # 用於處理圖片
import os

# 創建Tkinter主窗口
root = tk.Tk()
root.title("吹牛 - 客戶端")

# 載入骰子圖片
dice_images = {}
dice_folder = "dice_images"  # 圖片資料夾路徑
for i in range(1, 7):
    image_path = os.path.join(dice_folder, f"dice{i}.png")
    dice_images[i] = ImageTk.PhotoImage(Image.open(image_path).resize((50, 50)))  # 調整圖片大小

# 更新文字區域，帶有分隔線美化
def update_text_area(message):
    text_area.config(state=tk.NORMAL)
    text_area.insert(tk.END, f"—" * 50 + "\n")
    text_area.insert(tk.END, message + "\n")
    text_area.insert(tk.END, f"—" * 50 + "\n")
    text_area.config(state=tk.DISABLED)
    text_area.see(tk.END)

def update_dice_images(dice_list):
    for i, dice_value in enumerate(dice_list):
        if dice_value in dice_images:
            player_dice_labels[i].config(image=dice_images[dice_value])  # 更新圖片
            player_dice_labels[i].image = dice_images[dice_value]  # 防止垃圾回收

# 接收伺服器消息
def receive_messages():
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            # 更新UI顯示伺服器消息
            root.after(0, update_text_area, data)

            if data.startswith("🎲 你的骰子是:"):
                # 解析骰子數據
                dice_list = list(map(int, data.split(":")[1].strip().strip("[]").split(", ")))
                # 更新骰子圖片
                root.after(0, update_dice_images, dice_list)

            # 根據伺服器消息啟用或禁用輸入框
            if "輪到你行動" in data:
                root.after(0, enable_input)
            elif "等待玩家" in data:
                root.after(0, disable_input)
            elif "請重新輸入" in data:
                root.after(0, enable_input)
        except ConnectionResetError:
            root.after(0, update_text_area, "⚠️ 連線中斷，遊戲結束。")
            break
    cleanup_connection()

# 發送玩家的行動到伺服器
def send_action():
    action = input_field.get().strip()
    input_field.delete(0, tk.END)
    disable_input()  # 禁用輸入框，等待伺服器處理
    if action:
        try:
            threading.Thread(target=send_to_server, args=(action,), daemon=True).start()
        except Exception as e:
            root.after(0, update_text_area, f"⚠️ 發送動作時出錯: {e}")
            root.after(0, enable_input)

# 使用子線程發送數據到伺服器
def send_to_server(action):
    try:
        client_socket.sendall(action.encode('utf-8'))
        root.after(0, update_text_area, f"✅ 你發送了動作: {action}")
    except Exception as e:
        root.after(0, update_text_area, f"⚠️ 傳送失敗: {e}")
        root.after(0, enable_input)

# 啟用輸入框和提交按鈕
def enable_input():
    input_field.config(state=tk.NORMAL)
    send_button.config(state=tk.NORMAL)

# 禁用輸入框和提交按鈕
def disable_input():
    input_field.config(state=tk.DISABLED)
    send_button.config(state=tk.DISABLED)

# 連接到伺服器並啟動接收消息的子線程
def connect_to_server():
    try:
        client_socket.connect((HOST, PORT))
        threading.Thread(target=receive_messages, daemon=True).start()
        root.after(0, update_text_area, "✅ 已連接到伺服器，等待其他玩家加入...")
    except Exception as e:
        root.after(0, update_text_area, f"⚠️ 無法連接伺服器: {e}")

# 清理連接資源
def cleanup_connection():
    try:
        client_socket.close()
        update_text_area("✅ 已關閉連線。")
    except Exception as e:
        update_text_area(f"⚠️ 關閉連線失敗: {e}")

# 程式退出時清理資源
atexit.register(cleanup_connection)

# 配置伺服器信息
HOST = '127.0.0.1'
PORT = 65430
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 滾動文字顯示框
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state=tk.DISABLED, width=50, height=20)
text_area.pack(padx=10, pady=10)

# 添加用於顯示骰子圖片的框架
dice_frame = tk.Frame(root)
dice_frame.pack(pady=10)

# 創建 5 個標籤，用於顯示骰子圖片
player_dice_labels = [tk.Label(dice_frame) for _ in range(5)]
for label in player_dice_labels:
    label.pack(side=tk.LEFT, padx=5)

# 輸入框和提交按鈕
input_frame = tk.Frame(root)
input_field = tk.Entry(input_frame, width=40, state=tk.DISABLED)
input_field.pack(side=tk.LEFT, padx=5)
send_button = tk.Button(input_frame, text="提交", command=send_action, state=tk.DISABLED)
send_button.pack(side=tk.LEFT)
input_frame.pack(pady=10)

# 連接到伺服器
connect_to_server()

# 啟動Tkinter主循環
root.mainloop()