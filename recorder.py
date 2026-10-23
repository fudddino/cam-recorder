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
    if not clean_url or clean_url.startswith("#"):
        return

    username = clean_url.split('/')[-1]
    output_filename = f"{username}.mp4"
    print(f"\nChecking: {clean_url} with yt-dlp...")

    # Use yt-dlp which has active Cloudflare bypasses and Stripchat extractors
    cmd = [
        "yt-dlp",
        "--add-header", f"Cookie: {STRIPCHAT_COOKIE}",
        "--add-header", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "--format", "best",
        "--output", output_filename,
        clean_url
    ]

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            # Let it download for exactly the time limit
            stdout, _ = process.communicate(timeout=RECORD_SECONDS)
            print(stdout)
        except subprocess.TimeoutExpired:
            process.terminate()
            print(f"Captured {RECORD_SECONDS}s of {username}.")

        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 100000:
            print("Upload starting...")
            send_telegram_video(output_filename, f"📹 Recorded live stream: {username}")
            os.remove(output_filename)
        else:
            print(f"{username} is offline.")
            if os.path.exists(output_filename):
                os.remove(output_filename)

    except Exception as e:
        print(f"Error processing {clean_url}: {e}")

def main():
    if not os.path.exists(MODELS_FILE):
        return
    with open(MODELS_FILE, "r") as f:
        urls = f.readlines()
    for url in urls:
        check_and_record(url)

if __name__ == "__main__":
    main()
