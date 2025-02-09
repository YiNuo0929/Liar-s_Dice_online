import tkinter as tk
from tkinter import scrolledtext
import socket
import threading
import random

# 玩家骰子生成
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

# 處理玩家行動
def handle_action(action):
    global current_player, previous_call, conn, game_active

    if not action:
        update_text_area("⚠️ 請輸入有效指令！")
        if current_player == 1:
            root.after(100, enable_input)  # 延遲啟用輸入框
        return

    if action.lower() == "catch":
        if not previous_call:
            update_text_area("⚠️ 無法抓，因為尚無喊話紀錄。")
            if current_player == 1:
                root.after(100, enable_input)
            elif current_player == 2:
                threading.Thread(target=send_message, args=("⚠️ 無法抓，因為尚無喊話紀錄。\n",), daemon=True).start()
            return

        total_dice = count_dice(all_dice)
        count, value = previous_call
        if total_dice[value - 1] < count:
            result = f"🎉 玩家{current_player}抓對了！對方說謊！玩家{current_player}獲勝！"
        else:
            result = f"😔 玩家{current_player}抓錯了！對方沒有說謊！玩家{3 - current_player}獲勝！"

        final_message = (
            f"{result}\n"
            f"🎲 玩家1的骰子: {player1_dice}\n"
            f"🎲 玩家2的骰子: {player2_dice}\n"
        )
        update_text_area(final_message)
        threading.Thread(target=send_message, args=(final_message,), daemon=True).start()
        game_active = False
        return

    try:
        count, value = map(int, action.split())
        if value < 1 or value > 6 or (previous_call and (count < previous_call[0] or (count == previous_call[0] and value <= previous_call[1]))):
            update_text_area("⚠️ 喊話必須往上！請重新輸入。")
            if current_player == 1:
                root.after(100, enable_input)
            elif current_player == 2:
                threading.Thread(target=send_message, args=("⚠️ 喊話必須往上！請重新輸入。\n",), daemon=True).start()
            return

        previous_call = (count, value)
        message = f"玩家{current_player}喊了 {count} 個 {value}"
        update_text_area(message)
        threading.Thread(target=send_message, args=(f"{message}\n",), daemon=True).start()
        current_player = 3 - current_player
        if current_player == 2:
            threading.Thread(target=send_message, args=("👉 輪到你行動，請輸入（數字＋空格＋數字 或 catch）：\n",), daemon=True).start()
        else:
            threading.Thread(target=send_message, args=("⏳ 等待玩家1行動...\n",), daemon=True).start()
    except ValueError:
        update_text_area("⚠️ 輸入格式錯誤！請重新輸入。")
        if current_player == 1:
            root.after(100, enable_input)
        elif current_player == 2:
            threading.Thread(target=send_message, args=("⚠️ 輸入格式錯誤！請重新輸入。\n",), daemon=True).start()

# 發送訊息（子線程執行）
def send_message(message):
    try:
        conn.sendall(message.encode('utf-8'))
    except Exception as e:
        update_text_area(f"⚠️ 傳送訊息失敗: {e}")

# 遊戲主循環
def game_loop():
    global current_player, conn, game_active
    while game_active:
        if current_player == 1:
            root.after(100, enable_input)
        else:
            root.after(100, disable_input)
            update_text_area("⏳ 等待玩家2行動...")
            try:
                action = conn.recv(1024).decode('utf-8')
                handle_action(action)
            except ConnectionResetError:
                update_text_area("⚠️ 玩家2斷線，遊戲結束。")
                break

# 開始遊戲
def start_game():
    global conn, current_player, game_active, player1_dice, player2_dice, all_dice, previous_call
    player1_dice = generate_dice()
    player2_dice = generate_dice()
    all_dice = player1_dice + player2_dice
    current_player = 1
    previous_call = None
    game_active = True
    update_text_area(f"🎲 玩家1的骰子是: {player1_dice}")
    threading.Thread(target=send_message, args=(f"🎲 你的骰子是: {player2_dice}\n✨ 遊戲開始！輪到玩家1行動！\n",), daemon=True).start()
    update_text_area("✨ 遊戲開始！輪到玩家1行動！")
    threading.Thread(target=game_loop, daemon=True).start()

# 啟用輸入框
def enable_input():
    input_field.config(state=tk.NORMAL)
    submit_button.config(state=tk.NORMAL)

# 禁用輸入框
def disable_input():
    input_field.config(state=tk.DISABLED)
    submit_button.config(state=tk.DISABLED)

# 提交動作
def submit_action():
    global current_player
    action = input_field.get().strip()
    input_field.delete(0, tk.END)
    disable_input()
    threading.Thread(target=handle_action, args=(action,), daemon=True).start()

# 啟動伺服器
def start_server():
    HOST = '127.0.0.1'
    PORT = 65432
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    update_text_area("🔄 伺服器正在等待連線...")
    global conn
    conn, addr = server_socket.accept()
    update_text_area(f"✅ 已連接到 {addr}")
    start_game()

# Tkinter 界面
root = tk.Tk()
root.title("骰子吹牛遊戲 - 伺服器")

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state=tk.DISABLED, width=50, height=20)
text_area.pack(padx=10, pady=10)

input_field = tk.Entry(root, width=40, state=tk.DISABLED)
input_field.pack(pady=5)

submit_button = tk.Button(root, text="提交", command=submit_action, state=tk.DISABLED)
submit_button.pack()

threading.Thread(target=start_server, daemon=True).start()

root.mainloop()