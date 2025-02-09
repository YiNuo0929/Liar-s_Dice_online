import tkinter as tk
from tkinter import scrolledtext
import socket
import threading
import random
import atexit

# 全局變量
connections = []  # 存儲多個客戶端連接
current_player = 0
game_active = False
player_dices = []
all_dice = []
previous_call = None
server_socket = None  # 用於清理伺服器資源
time_left = 30
timer_running = False

# 生成玩家骰子
def generate_dice():
    return [random.randint(1, 6) for _ in range(5)]

# 計算骰子數量
def count_dice(dice_list):
    counts = [0] * 6
    for dice in dice_list:
        if dice != 1:
            counts[dice - 1] += 1
        else:
            for i in range(6):
                counts[i] += 1
    return counts

# 廣播訊息給所有玩家
def broadcast_message(message):
    for conn in connections:
        try:
            conn.sendall(message.encode('utf-8'))
        except Exception as e:
            update_text_area(f"⚠️ 傳送訊息失敗: {e}")

# 更新遊戲訊息
def update_text_area(message):
    text_area.config(state=tk.NORMAL)
    text_area.insert(tk.END, f"{message}\n")
    text_area.config(state=tk.DISABLED)
    text_area.see(tk.END)

# 更新倒數計時標籤
def update_timer_label(message):
    timer_label.config(text=message)

# 倒數計時函數
def start_turn_timer():
    global time_left, timer_running, current_player

    time_left = 30
    timer_running = True
    update_timer_label(f"玩家{current_player + 1}剩餘時間: {time_left}秒")
    broadcast_message(f"timer:{time_left}")

    while time_left > 0 and timer_running:
        time_left -= 1
        update_timer_label(f"玩家{current_player + 1}剩餘時間: {time_left}秒")
        broadcast_message(f"timer:{time_left}")
        root.update()
        root.after(1000)
        if not game_active:
            break

    if time_left == 0 and game_active:
        handle_timeout()

# 處理超時邏輯
def handle_timeout():
    global current_player, game_active

    update_text_area(f"⏰ 玩家{current_player + 1}超時！判定該玩家輸掉遊戲！")
    broadcast_message(f"⏰ 玩家{current_player + 1}超時！玩家{current_player + 1}輸掉遊戲！")

    # 廣播所有玩家的骰子情況
    for i, dices in enumerate(player_dices):
        broadcast_message(f"🎲 玩家{i + 1}的骰子: {dices}")

    # 結束遊戲
    broadcast_message("🏆 遊戲結束！感謝大家參與！")
    game_active = False
    cleanup()

# 開始輪到某位玩家
def start_turn():
    global current_player
    if not game_active:
        return

    broadcast_message(f"👉 輪到玩家{current_player + 1}行動！")
    start_turn_timer()

# 接收玩家行動
def handle_action(action, player_index):
    global current_player, previous_call, game_active, timer_running

    if not action:
        connections[player_index].sendall("⚠️ 請輸入有效指令！\n".encode('utf-8'))
        return

    if action.lower() == "catch":
        # 處理抓謊邏輯...
        return

    try:
        count, value = map(int, action.split())
        # 處理喊話邏輯...
        previous_call = (count, value)
        update_text_area(f"玩家{player_index + 1}喊了 {count} 個 {value}")
        broadcast_message(f"玩家{player_index + 1}喊了 {count} 個 {value}")

        timer_running = False  # 停止倒數
        current_player = (current_player + 1) % len(connections)
        start_turn()
    except ValueError:
        connections[player_index].sendall("⚠️ 輸入格式錯誤！請重新輸入。\n".encode('utf-8'))

# 開始遊戲
def start_game():
    global game_active, player_dices, all_dice, current_player

    player_dices = [generate_dice() for _ in range(3)]
    all_dice = sum(player_dices, [])
    current_player = 0
    game_active = True

    for i, conn in enumerate(connections):
        conn.sendall(f"🎲 你的骰子是: {player_dices[i]}\n".encode('utf-8'))

    update_text_area("✨ 遊戲開始！等待玩家1行動！")
    start_turn()

# 接收玩家連接
def accept_connections():
    global connections
    while len(connections) < 3:
        conn, addr = server_socket.accept()
        connections.append(conn)
        update_text_area(f"✅ 玩家{len(connections)} 已連接: {addr}")
        conn.sendall(f"歡迎玩家{len(connections)}！等待其他玩家加入...\n".encode('utf-8'))

    start_game()

# 清理資源
def cleanup():
    global server_socket, connections, game_active
    update_text_area("⚠️ 遊戲結束，清理資源...")
    game_active = False
    for conn in connections:
        try:
            conn.close()
        except Exception as e:
            update_text_area(f"⚠️ 關閉玩家連線時出錯: {e}")
    connections.clear()
    if server_socket:
        server_socket.close()

# 啟動伺服器
def start_server():
    global server_socket
    HOST = '127.0.0.1'
    PORT = 65430
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    update_text_area("伺服器已啟動，等待連線...")
    threading.Thread(target=accept_connections, daemon=True).start()

# Tkinter 界面設置
root = tk.Tk()
root.title("吹我老二 - 伺服器")

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state=tk.DISABLED, width=50, height=15)
text_area.pack(padx=10, pady=10)

timer_label = tk.Label(root, text="", font=("Arial", 16))
timer_label.pack(pady=10)

atexit.register(cleanup)
start_server()