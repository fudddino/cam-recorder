import os
import subprocess
from curl_cffi import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STRIPCHAT_COOKIE = os.environ.get("STRIPCHAT_COOKIE", "")
MODELS_FILE = "models.txt"
RECORD_SECONDS = 180

def send_telegram_video(video_path, caption=""):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    print(f"Uploading {video_path} to Telegram...")
    with open(video_path, "rb") as video_file:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption}, files={"video": video_file})

def check_and_record(raw_url):
    clean_url = raw_url.strip().rstrip('/')
    if not clean_url or clean_url.startswith("#"): return
    username = clean_url.split('/')[-1]
    output_filename = f"{username}.mp4"
    
    print(f"\nQuerying API for {username}...")
    api_url = f"https://stripchat.com/api/front/v2/models/username/{username}/cam"
    
    try:
        # curl_cffi perfectly mimics Chrome's TLS fingerprint to bypass Cloudflare
        r = requests.get(api_url, impersonate="chrome", headers={"Cookie": STRIPCHAT_COOKIE}, timeout=15)
        
        if "application/json" not in r.headers.get("Content-Type", ""):
            print("Failed: Cloudflare intercepted the request.")
            return
            
        stream_name = r.json().get("cam", {}).get("streamName")
        
        if stream_name:
            hls_url = f"https://b-hls-01.strpcdn.com/hls/{stream_name}/master/{stream_name}.m3u8"
            print("Live stream found! Recording with FFmpeg...")
            
            # FFmpeg natively downloads the stream without triggering bot protections
            cmd = ["ffmpeg", "-y", "-i", hls_url, "-t", str(RECORD_SECONDS), "-c", "copy", output_filename]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(output_filename) and os.path.getsize(output_filename) > 100000:
                send_telegram_video(output_filename, f"📹 Recorded: {username}")
                os.remove(output_filename)
            else:
                print("Failed to capture video data.")
        else:
            print("Model offline or stream unavailable.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    if not os.path.exists(MODELS_FILE): return
    with open(MODELS_FILE, "r") as f:
        urls = f.readlines()
    for url in urls:
        check_and_record(url)

if __name__ == "__main__":
    main()
