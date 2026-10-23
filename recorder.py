import os
import sys
import subprocess
import requests
import streamlink

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

MODELS_FILE = "models.txt"
RECORD_SECONDS = 180  # 3-minute test recording per run

def send_telegram_video(video_path, caption=""):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram token or chat ID missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    print(f"Sending {video_path} to Telegram...")
    with open(video_path, "rb") as video_file:
        response = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
            files={"video": video_file}
        )
    print("Telegram response:", response.status_code)

def check_and_record(url):
    url = url.strip()
    if not url or url.startswith("#"):
        return

    print(f"Checking {url}...")
    
    # Configure Streamlink session with custom headers to bypass Cloudflare
    session = streamlink.Streamlink()
    session.set_option("http-headers", {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    try:
        streams = session.streams(url)
        if not streams:
            print(f"Offline or stream unresolvable: {url}")
            return
        
        # Pick best available stream quality
        stream_url = streams['best'].to_url()
        model_name = url.rstrip('/').split('/')[-1]
        output_filename = f"{model_name}_recording.mp4"
        
        print(f"🔴 {model_name} IS LIVE! Recording {RECORD_SECONDS}s...")
        
        # Record stream segment via FFmpeg
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-headers", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n",
            "-i", stream_url,
            "-t", str(RECORD_SECONDS),
            "-c", "copy",
            output_filename
        ]
        
        subprocess.run(ffmpeg_cmd, check=True)
        
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
            send_telegram_video(output_filename, f"📹 Recorded live stream: {model_name}")
            os.remove(output_filename)
        else:
            print("Recording file empty or failed.")

    except Exception as e:
        print(f"Error checking/recording {url}: {e}")

def main():
    if not os.path.exists(MODELS_FILE):
        print("models.txt not found.")
        return

    with open(MODELS_FILE, "r") as f:
        urls = f.readlines()

    for url in urls:
        check_and_record(url)

if __name__ == "__main__":
    main()
