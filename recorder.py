import os
import sys
import subprocess
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

MODELS_FILE = "models.txt"
RECORD_SECONDS = 180  # 3 minutes

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
    print("Telegram upload response:", response.status_code)

def check_and_record(url):
    url = url.strip()
    if not url or url.startswith("#"):
        return

    # Format model name safely
    clean_url = url.rstrip('/')
    model_name = clean_url.split('/')[-1]
    output_filename = f"{model_name}.mp4"

    print(f"\nChecking {url}...")

    # Build streamlink CLI command with browser bypass headers
    cmd = [
        "streamlink",
        "--http-header", "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "--http-header", "Accept-Language=en-US,en;q=0.9",
        "--output", output_filename,
        clean_url,
        "best",
        "--force"
    ]

    try:
        # Run streamlink for up to RECORD_SECONDS
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        try:
            # Wait for recording window
            stdout, _ = process.communicate(timeout=RECORD_SECONDS)
            print(stdout)
        except subprocess.TimeoutExpired:
            # Time reached, stop streamlink cleanly
            process.terminate()
            print(f"Captured {RECORD_SECONDS} seconds of stream for {model_name}.")

        # Check if output file was created and contains data
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 100000:
            print(f"Successfully recorded {output_filename}. Uploading to Telegram...")
            send_telegram_video(output_filename, f"📹 Recorded live stream: {model_name}")
            os.remove(output_filename)
        else:
            print(f"{model_name} was offline or stream could not be captured.")
            if os.path.exists(output_filename):
                os.remove(output_filename)

    except Exception as e:
        print(f"Error processing {url}: {e}")

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
