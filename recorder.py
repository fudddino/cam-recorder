import os
import sys
import subprocess
import requests

# Fetch Telegram credentials and Stripchat authenticated cookie from GitHub Secrets
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
STRIPCHAT_COOKIE = os.environ.get("STRIPCHAT_COOKIE", "")

MODELS_FILE = "models.txt"
RECORD_SECONDS = 180  # Duration per model per run (3 minutes)

def send_telegram_video(video_path, caption=""):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing in GitHub Secrets.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    print(f"Uploading {video_path} to Telegram channel...")
    
    with open(video_path, "rb") as video_file:
        response = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
            files={"video": video_file}
        )
    print("Telegram upload status code:", response.status_code)

def check_and_record(raw_url):
    clean_url = raw_url.strip().rstrip('/')
    if not clean_url or clean_url.startswith("#"):
        return

    model_name = clean_url.split('/')[-1]
    output_filename = f"{model_name}.mp4"

    print(f"\n----------------------------------------")
    print(f"Checking model stream: {clean_url}")

    # Streamlink CLI execution array with Chrome browser identity + Session Cookie
    cmd = [
        "streamlink",
        "--http-header", "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "--http-header", "Accept-Language=en-US,en;q=0.9",
        "--http-header", f"Cookie={STRIPCHAT_COOKIE}",
        "--output", output_filename,
        clean_url,
        "best",
        "--force"
    ]

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        try:
            # Wait for recording window
            stdout, _ = process.communicate(timeout=RECORD_SECONDS)
            print(stdout)
        except subprocess.TimeoutExpired:
            # Reached recording timeout, terminate process to finalize video file
            process.terminate()
            print(f"Captured {RECORD_SECONDS} seconds of stream for {model_name}.")

        # Verify output video file exists and is valid (greater than 100 KB)
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 100000:
            print(f"Recording successful ({os.path.getsize(output_filename)} bytes). Uploading...")
            send_telegram_video(output_filename, f"📹 Recorded live stream: {model_name}")
            os.remove(output_filename)
        else:
            print(f"Result: {model_name} is offline or stream capture was blocked.")
            if os.path.exists(output_filename):
                os.remove(output_filename)

    except Exception as e:
        print(f"Error processing {clean_url}: {e}")

def main():
    if not os.path.exists(MODELS_FILE):
        print(f"Error: {MODELS_FILE} not found.")
        return

    with open(MODELS_FILE, "r") as f:
        urls = f.readlines()

    for url in urls:
        check_and_record(url)

if __name__ == "__main__":
    main()
