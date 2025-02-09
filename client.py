import tkinter as tk
from tkinter import scrolledtext
import socket
import threading

def update_text_area(message):
    """更新文字區域，加入分隔線與美化"""
    text_area.config(state=tk.NORMAL)
    text_area.insert(tk.END, f"—" * 50 + "\n")
    text_area.insert(tk.END, message + "\n")
    text_area.insert(tk.END, f"—" * 50 + "\n")
    text_area.config(state=tk.DISABLED)
    text_area.see(tk.END)

def receive_messages():
    """接收服务器消息并根据轮次更新UI"""
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            # 更新消息到UI
            root.after(0, update_text_area, data)

            # 根据服务器消息启用或禁用输入框
            if "輪到你行動" in data:
                root.after(0, enable_input)
            elif "等待玩家1行動" in data:
                root.after(0, disable_input)
            elif "請重新輸入" in data:
                root.after(0, enable_input)
        except ConnectionResetError:
            root.after(0, update_text_area, "⚠️ 連線中斷，遊戲結束。")
            break

def send_action():
    """发送玩家的行动到服务器"""
    action = input_field.get().strip()
    input_field.delete(0, tk.END)
    disable_input()  # 禁用输入框和按钮，等待服务器处理
    if action:
        try:
            threading.Thread(target=send_to_server, args=(action,), daemon=True).start()
        except Exception as e:
            root.after(0, update_text_area, f"⚠️ 發送動作時出錯: {e}")
            root.after(0, enable_input)

def send_to_server(action):
    """通过子线程发送数据到服务器"""
    try:
        client_socket.sendall(action.encode('utf-8'))
        root.after(0, update_text_area, f"✅ 你發送了動作: {action}")
    except Exception as e:
        root.after(0, update_text_area, f"⚠️ 傳送失敗: {e}")
        root.after(0, enable_input)

def enable_input():
    """启用输入框和提交按钮"""
    input_field.config(state=tk.NORMAL)
    send_button.config(state=tk.NORMAL)

def disable_input():
    """禁用输入框和提交按钮"""
    input_field.config(state=tk.DISABLED)
    send_button.config(state=tk.DISABLED)

def connect_to_server():
    """連接到伺服器並啟動接收消息的子线程"""
    try:
        client_socket.connect((HOST, PORT))
        threading.Thread(target=receive_messages, daemon=True).start()
        root.after(0, update_text_area, "✅ 已連接到伺服器，等待遊戲開始...")
    except Exception as e:
        root.after(0, update_text_area, f"⚠️ 無法連接伺服器: {e}")

# 配置伺服器信息
HOST = '127.0.0.1'
PORT = 65432
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 创建Tkinter主窗口
root = tk.Tk()
root.title("骰子吹牛遊戲 - 客戶端")

# 添加滚动文字显示框
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state=tk.DISABLED, width=50, height=20)
text_area.pack(padx=10, pady=10)

# 添加输入框和提交按钮
input_frame = tk.Frame(root)
input_field = tk.Entry(input_frame, width=40, state=tk.DISABLED)
input_field.pack(side=tk.LEFT, padx=5)
send_button = tk.Button(input_frame, text="提交", command=send_action, state=tk.DISABLED)
send_button.pack(side=tk.LEFT)
input_frame.pack(pady=10)

# 连接到伺服器
connect_to_server()

# 启动Tkinter主循环
root.mainloop()