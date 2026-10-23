import os
import subprocess
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STRIPCHAT_COOKIE = os.environ.get("STRIPCHAT_COOKIE", "")

MODELS_FILE = "models.txt"
RECORD_SECONDS = 180  # 3 minutes

def send_telegram_video(video_path, caption=""):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    print(f"Uploading {video_path} to Telegram...")
    with open(video_path, "rb") as video_file:
        requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
            files={"video": video_file}
        )

def check_and_record(raw_url):
    clean_url = raw_url.strip().rstrip('/')
    if not clean_url or clean_url.startswith("#"): return
    username = clean_url.split('/')[-1]
    output_filename = f"{username}.mp4"
    
    print(f"\nQuerying API for {username}...")
    api_url = f"https://stripchat.com/api/front/v2/models/username/{username}/cam"
    
    try:
        r = requests.get(api_url, headers={"Cookie": STRIPCHAT_COOKIE}, timeout=10)
        stream_name = r.json().get("cam", {}).get("streamName")
        
        if stream_name:
            hls_url = f"https://b-hls-01.strpcdn.com/hls/{stream_name}/master/{stream_name}.m3u8"
            print("Live stream found! Recording...")
            
            cmd = ["yt-dlp", hls_url, "-o", output_filename]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            try:
                process.communicate(timeout=RECORD_SECONDS)
            except subprocess.TimeoutExpired:
                process.terminate()
            
            if os.path.exists(output_filename) and os.path.getsize(output_filename) > 100000:
                send_telegram_video(output_filename, f"📹 Recorded: {username}")
                os.remove(output_filename)
        else:
            print("Model offline or stream hidden from datacenter IP.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    if not os.path.exists(MODELS_FILE):
        return
    with open(MODELS_FILE, "r") as f:
        urls = f.readlines()
    for url in urls:
        check_and_record(url)

if __name__ == "__main__":
    main()
