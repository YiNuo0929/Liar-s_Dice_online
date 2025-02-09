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

# 更新文字區域
def update_text_area(message):
    text_area.config(state=tk.NORMAL)
    text_area.insert(tk.END, f"—" * 50 + "\n")
    text_area.insert(tk.END, message + "\n")
    text_area.insert(tk.END, f"—" * 50 + "\n")
    text_area.config(state=tk.DISABLED)
    text_area.see(tk.END)

# 廣播訊息給所有玩家
def broadcast_message(message):
    for conn in connections:
        try:
            conn.sendall(message.encode('utf-8'))
        except Exception as e:
            update_text_area(f"⚠️ 傳送訊息失敗: {e}")

# 處理玩家行動
def handle_action(action, player_index):
    global current_player, previous_call, game_active

    if not action:
        connections[player_index].sendall("⚠️ 請輸入有效指令！\n".encode('utf-8'))
        return

    if action.lower() == "catch":
        if not previous_call:
            connections[player_index].sendall("⚠️ 無法抓，因為尚無喊話紀錄。\n".encode('utf-8'))
            return

        total_dice = count_dice(all_dice)
        count, value = previous_call
        if total_dice[value - 1] < count:
            result = f"🎉 玩家{player_index + 1}抓對了！對方說謊！玩家{player_index + 1}獲勝！"
        else:
            result = f"😔 玩家{player_index + 1}抓錯了！對方沒有說謊！其他玩家獲勝！"

        final_message = (
            f"{result}\n"
            + "\n".join([f"🎲 玩家{i + 1}的骰子: {player_dices[i]}" for i in range(3)])
        )
        update_text_area(final_message)
        broadcast_message(final_message)
        game_active = False
        cleanup()
        return

    try:
        count, value = map(int, action.split())
        if value < 1 or value > 6 or (previous_call and (count < previous_call[0] or (count == previous_call[0] and value <= previous_call[1]))):
            connections[player_index].sendall("⚠️ 喊話必須往上！請重新輸入。\n".encode('utf-8'))
            return

        previous_call = (count, value)
        message = f"玩家{player_index + 1}喊了 {count} 個 {value}"
        update_text_area(message)
        broadcast_message(message)

        current_player = (current_player + 1) % 3  # 循環切換到下一位玩家
        broadcast_message(f"👉 輪到玩家{current_player + 1}行動！")
    except ValueError:
        connections[player_index].sendall("⚠️ 輸入格式錯誤！請重新輸入。\n".encode('utf-8'))

# 遊戲主循環
def game_loop():
    global current_player, game_active
    while game_active:
        try:
            conn = connections[current_player]
            conn.sendall("\n".encode('utf-8'))  # 發送一行空白
            conn.sendall("👾輪到你行動，請輸入（數字＋空格＋數字 或 catch）：\n".encode('utf-8'))
            action = conn.recv(1024).decode('utf-8').strip()
            handle_action(action, current_player)
        except ConnectionResetError:
            update_text_area(f"⚠️ 玩家{current_player + 1}斷線，遊戲結束。")
            game_active = False
            cleanup()
            break

# 開始遊戲
def start_game():
    global current_player, game_active, player_dices, all_dice, previous_call

    player_dices = [generate_dice() for _ in range(3)]
    all_dice = sum(player_dices, [])
    current_player = 0
    previous_call = None
    game_active = False

    for i, conn in enumerate(connections):
        conn.sendall(f"🎲 你的骰子是: {player_dices[i]}\n".encode('utf-8'))

    update_text_area("✨ 等待玩家準備...")
    # 延遲 2000 毫秒（2 秒）
    root.after(2000, start_game_after_delay)


def start_game_after_delay():
    global game_active
    # 在伺服器 UI 上顯示遊戲開始訊息
    update_text_area("✨ 遊戲開始！等待玩家1行動！")
    # 向所有客戶端廣播遊戲開始訊息
    broadcast_message("✨ 遊戲開始！等待玩家1行動！")
    game_active = True
    threading.Thread(target=game_loop, daemon=True).start()

# 接收玩家連接
def accept_connections():
    global connections
    while len(connections) < 3:
        conn, addr = server_socket.accept()
        connections.append(conn)
        update_text_area(f"✅ 玩家{len(connections)} 已連接到 {addr}")
        conn.sendall(f"歡迎玩家{len(connections)}！等待其他玩家加入...\n".encode('utf-8'))

    # 開始遊戲
    start_game()

# 清理資源
def cleanup():
    global server_socket, connections
    update_text_area("⚠️ 遊戲結束，清理資源...")
    for conn in connections:
        try:
            conn.close()
            update_text_area("✅ 已關閉玩家連線。")
        except Exception as e:
            update_text_area(f"⚠️ 關閉玩家連線時出錯: {e}")
    connections.clear()

    try:
        if server_socket:
            server_socket.close()
            update_text_area("✅ 已關閉伺服器。")
    except Exception as e:
        update_text_area(f"⚠️ 關閉伺服器時出錯: {e}")

# 啟動伺服器
def start_server():
    global server_socket
    HOST = '127.0.0.1'
    PORT = 65430
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    update_text_area("🔄 伺服器正在等待連線...")
    threading.Thread(target=accept_connections, daemon=True).start()

# Tkinter 界面設置
root = tk.Tk()
root.title("吹牛 - 伺服器")

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state=tk.DISABLED, width=50, height=20)
text_area.pack(padx=10, pady=10)

# 確保程式退出時清理資源
atexit.register(cleanup)

start_server()

root.mainloop()