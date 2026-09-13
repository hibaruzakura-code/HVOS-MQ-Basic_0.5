"""
HVOS Base Edition (MQ) - メインスクリプト

0.1 MQ【公開】260908
0.2 MQ→PC【修正】260908 
0.3 PC【追加・修正】260911
0.5 PC→MQ【高速化対応】260913
 Meta Quest版をPC版v0.5相当の高速処理へアップデート。
 画面部分キャプチャの最適化およびメモリ上での画像処理、生成速度の高速化を反映。
"""

import sys
import io

# 標準出力をUTF-8に変更（Windows環境でのUnicodeEncodeErrorを防止）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
import time
import socket
import threading
from datetime import datetime
from flask import Flask, render_template_string, jsonify
import pyautogui
import keyboard
import pygetwindow as gw
from PIL import Image
from google import genai

# ==========================================
# 🔑 APIキー設定
# ==========================================
GEMINI_API_KEY = "ここに取得したAPIキーを入れる"

app = Flask(__name__)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

IMAGE_SAVE_DIR = "saved_captures"
if not os.path.exists(IMAGE_SAVE_DIR):
    os.makedirs(IMAGE_SAVE_DIR)

latest_result = {
    "title": "HVOS Base Edition (MQ v0.5) - スタンバイ完了",
    "gemini_content": "【HVOS (MQ v0.5) スタンバイOK！】\nキーボードの【1】を押すと、高速撮影＆解析を実行します。",
    "timestamp": ""
}

is_processing = False
processing_lock = threading.Lock()

def bring_meta_cast_to_front():
    try:
        all_wins = gw.getAllWindows()
        target_win = None
        for win in all_wins:
            title_lower = win.title.lower()
            if any(k in title_lower for k in ["meta casting", "casting", "oculus", "meta"]):
                target_win = win
                break

        if target_win:
            if target_win.isMinimized:
                target_win.restore()
                time.sleep(0.05)
            pyautogui.press('alt')
            target_win.activate()
            time.sleep(0.1)
            return target_win
    except Exception as e:
        print(f"⚠️ ウィンドウ制御エラー: {e}")
    return None

def execute_analysis():
    global latest_result, is_processing

    with processing_lock:
        if is_processing:
            print("⚠️ 解析処理中のためスキップします。")
            return
        is_processing = True

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    latest_result["title"] = "解析中..."
    latest_result["gemini_content"] = "画像を分析しています...数秒お待ちください。"
    latest_result["timestamp"] = now_str

    try:
        cast_win = bring_meta_cast_to_front()
        
        # 領域指定キャプチャによる高速化
        if cast_win and cast_win.width > 0 and cast_win.height > 0:
            left, top = max(0, cast_win.left), max(0, cast_win.top)
            width, height = cast_win.width, cast_win.height
            # Meta Questのキャスト領域切りだし
            crop_left = left + int(width * 0.02)
            crop_top = top + int(height * 0.08)
            crop_width = int(width * 0.96)
            crop_height = int(height * 0.90)
            cropped_img = pyautogui.screenshot(region=(crop_left, crop_top, crop_width, crop_height))
        else:
            screenshot = pyautogui.screenshot()
            w, h = screenshot.size
            cropped_img = screenshot.crop((int(w * 0.05), int(h * 0.05), int(w * 0.95), int(h * 0.95)))

        # バックグラウンドで非同期保存（レスポンス待ち時間を短縮）
        saved_img_path = os.path.join(IMAGE_SAVE_DIR, f"cap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        threading.Thread(target=cropped_img.save, args=(saved_img_path,)).start()

        prompt = (
            "あなたは最高のバーチャルツアーガイドです。このVR画像に写っている景色・場所について、以下の構成で600文字程度で魅力的に解説してください。\n\n"
            "1. 【場所の特定と概要】：ここがどこか、何という施設・景色か\n"
            "2. 【歴史と背景】：この場所にまつわる深い歴史やストーリー、建築のこだわりなど\n"
            "3. 【ここだけの魅力・おすすめポイント】：訪れた人が『ワクワクする』豆知識や見どころ\n"
            "4. 【周囲のおすすめ・楽しみ方】：もし実際にここを歩くなら立ち寄るべき周辺スポットや楽しみ方\n\n"
            "語り口は親しみやすく、聞いているだけで旅に出たくなるようなワクワクする文章でまとめてください。文末には必ず『（文字数：〇〇文字）』と実際に生成した文字数を記載してください。"
        )

        response = gemini_client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[prompt, cropped_img]
        )

        latest_result["title"] = "HVOS ガイド解説 (v0.5)"
        latest_result["gemini_content"] = response.text

    except Exception as e:
        print(f"❌ エラー発生: {e}")
        latest_result["title"] = "エラー発生"
        latest_result["gemini_content"] = f"処理エラー: {e}"

    finally:
        with processing_lock:
            is_processing = False

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: sans-serif; padding: 15px; margin: 0; }
        .header { font-size: 1rem; font-weight: bold; color: #818cf8; border-bottom: 1px solid #334155; padding-bottom: 6px; display: flex; justify-content: space-between; }
        .card { background: #1e293b; border-radius: 8px; padding: 15px; margin-top: 12px; border-top: 4px solid #38bdf8; }
        .content { font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap; }
    </style>
    <script>
        setInterval(async () => {
            try {
                const res = await fetch('/api/data');
                const data = await res.json();
                document.getElementById('ui-title').innerText = data.title;
                document.getElementById('ui-timestamp').innerText = data.timestamp;
                document.getElementById('ui-gemini').innerText = data.gemini_content;
            } catch (e) {}
        }, 500);
    </script>
</head>
<body>
    <div class="header">
        <span id="ui-title">{{ title }}</span>
        <span id="ui-timestamp" style="font-size:0.75rem; color:#64748b;">{{ timestamp }}</span>
    </div>
    <div class="card">
        <div id="ui-gemini" class="content">{{ gemini_content }}</div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, title=latest_result["title"], timestamp=latest_result["timestamp"], gemini_content=latest_result["gemini_content"])

@app.route('/api/data')
def get_data():
    return jsonify(latest_result)

def start_keyboard_listener():
    print("▶ 【1】キーの監視を開始しました。(v0.5 高速化版)")
    last_execution_time = 0
    cooldown_seconds = 3.0  # レスポンス向上に伴いクールダウンを3秒に短縮

    while True:
        if keyboard.is_pressed("1") or keyboard.is_pressed("num 1"):
            current_time = time.time()
            if current_time - last_execution_time > cooldown_seconds:
                last_execution_time = current_time
                if not is_processing:
                    threading.Thread(target=execute_analysis).start()
            
            while keyboard.is_pressed("1") or keyboard.is_pressed("num 1"):
                time.sleep(0.02)

        time.sleep(0.02)

if __name__ == '__main__':
    threading.Thread(target=start_keyboard_listener, daemon=True).start()

    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"

    print(f"\n==========================================")
    print(f"=== HVOS Base Edition (MQ v0.5) 稼働中 ===")
    print(f"・Questブラウザ用URL: http://{local_ip}:5000")
    print(f"==========================================\n")

    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)