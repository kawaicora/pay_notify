#!/usr/bin/env python3
"""
SpyMoneyAlipayPlayer - 间谍偷钱支付宝语音播报
TCP server: 127.0.0.1:39247
Protocol: SPY_MONEY_EVENT {"amount":N,"direction":"gain"/"lose","frame":N}
"""
import socket
import threading
import json
import os
import sys
import time
from pathlib import Path

# Try to use winsound for WAV playback on Windows
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# Try to use pygame for MP3 playback
try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

HOST = "127.0.0.1"
PORT = 39247

# Audio directory
if getattr(sys, 'frozen', False):
    # Running as compiled exe - audio bundled inside, extracted to temp
    BASE_DIR = Path(sys.executable).parent
    # PyInstaller extracts bundled data to sys._MEIPASS
    if hasattr(sys, '_MEIPASS'):
        AUDIO_DIR = Path(sys._MEIPASS) / "audio"
    else:
        AUDIO_DIR = BASE_DIR / "audio"
else:
    BASE_DIR = Path(__file__).parent
    AUDIO_DIR = BASE_DIR / "audio"


def get_audio_path(name: str) -> Path:
    """Get audio file path, prefer WAV over MP3."""
    wav = AUDIO_DIR / f"{name}.wav"
    if wav.exists():
        return wav
    return AUDIO_DIR / f"{name}.mp3"


def play_audio(name: str):
    """Play an audio file and wait until finished."""
    path = get_audio_path(name)
    if not path.exists():
        print(f"[WARN] Audio not found: {path}")
        return

    if HAS_WINSOUND and path.suffix.lower() == ".wav":
        # winsound.PlaySound: SND_FILENAME | SND_SYNC plays synchronously
        winsound.PlaySound(str(path), 0x00020000 | 0x0000)
    elif HAS_PYGAME:
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    else:
        print(f"[WARN] No audio backend available, would play: {path}")
        time.sleep(0.5)


def amount_to_clips(amount) -> list:
    """Convert amount to list of audio clip names.
    Example: 1241182 -> ['tts_1','tts_hundred','tts_2','tts_ten','tts_4',
                          'tts_ten_thousand','tts_1','tts_thousand','tts_1',
                          'tts_hundred','tts_8','tts_ten','tts_2']
    Supports float amounts for jiao/fen (角/分).
    """
    if amount <= 0:
        return []

    clips = []
    amount = float(amount)
    int_part = int(amount)
    decimal_part = round((amount - int_part) * 100)  # in fen

    # Handle integer part
    if int_part > 0:
        # Handle 亿 (100,000,000)
        if int_part >= 100000000:
            yi = int_part // 100000000
            rest_after_yi = int_part % 100000000
            clips.extend(number_to_clips(yi))
            clips.append("tts_ten_million")  # 亿
            if rest_after_yi > 0:
                # Handle 万 (10,000)
                if rest_after_yi >= 10000:
                    wan = rest_after_yi // 10000
                    rest = rest_after_yi % 10000
                    clips.extend(number_to_clips(wan))
                    clips.append("tts_ten_thousand")
                    if rest > 0:
                        clips.extend(number_to_clips(rest))
                else:
                    clips.extend(number_to_clips(rest_after_yi))
        # Handle 万 (10,000)
        elif int_part >= 10000:
            wan = int_part // 10000
            rest = int_part % 10000
            clips.extend(number_to_clips(wan))
            clips.append("tts_ten_thousand")
            if rest > 0:
                clips.extend(number_to_clips(rest))
        else:
            clips.extend(number_to_clips(int_part))

    # Handle decimal part (jiao/fen)
    if decimal_part > 0:
        jiao = decimal_part // 10
        fen = decimal_part % 10
        clips.append("tts_dot")  # 小数点
        if jiao > 0:
            clips.append(f"tts_{jiao}")
        if fen > 0:
            clips.append(f"tts_{fen}")

    return clips


def number_to_clips(n: int) -> list:
    """Convert a number < 10000 to audio clip names."""
    clips = []
    if n >= 1000:
        thousand = n // 1000
        clips.append(f"tts_{thousand}")
        clips.append("tts_thousand")
        n = n % 1000

    if n >= 100:
        hundred = n // 100
        clips.append(f"tts_{hundred}")
        clips.append("tts_hundred")
        n = n % 100

    if n >= 10:
        ten = n // 10
        clips.append(f"tts_{ten}")
        clips.append("tts_ten")
        n = n % 10
    elif n > 0 and (clips and not clips[-1] in ("tts_hundred", "tts_thousand", "tts_ten_thousand")):
        # Only add zero if we're in the middle of a number
        pass

    if n > 0:
        clips.append(f"tts_{n}")

    return clips


def handle_event(data: str):
    """Handle a SPY_MONEY_EVENT."""
    try:
        # Parse: SPY_MONEY_EVENT {"amount":N,"direction":"gain","frame":N}
        if not data.startswith("SPY_MONEY_EVENT "):
            return
        json_str = data[len("SPY_MONEY_EVENT "):].strip()
        event = json.loads(json_str)
        amount = event.get("amount", 0)
        direction = event.get("direction", "gain")

        if amount <= 0:
            return

        # Build clip list
        clips = ["tts_success"]
        clips.extend(amount_to_clips(amount))
        clips.append("tts_yuan")

        print(f"[player] 播放到账 {amount} ({len(clips)} 段)")

        # Play all clips synchronously
        for clip in clips:
            play_audio(clip)

    except Exception as e:
        print(f"[ERROR] {e}")


def handle_client(conn: socket.socket, addr):
    """Handle a client connection."""
    print(f"[server] 游戏已连接 from {addr}", flush=True)
    try:
        buffer = ""
        while True:
            data = conn.recv(1024).decode("utf-8")
            if not data:
                break
            print(f"[server] received: {data.strip()}", flush=True)
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line:
                    handle_event(line)
    except Exception as e:
        print(f"[server] Connection error: {e}", flush=True)
    finally:
        conn.close()


def main():
    print("=" * 50)
    print("间谍偷钱支付宝语音 — 监听中")
    print(f"程序目录: {BASE_DIR}")
    print("请先保持本窗口打开，再启动尤里复仇。关闭窗口即停止。")
    print("=" * 50)

    # Initialize pygame if available
    if HAS_PYGAME:
        pygame.mixer.init()

    # Start TCP server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[server] 监听中: {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
