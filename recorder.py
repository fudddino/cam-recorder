import os
import subprocess
import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_watchlist():
    if not os.path.exists("models.txt"):
        return []
    with open("models.txt", "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def check_and_record(url):
    print(f"Checking {url}...")
    model_name = url.rstrip("/").split("/")[-1]
    filename = f"{model_name}.mp4"

    # Streamlink checks stream status and captures feed if live
    cmd = ["streamlink", "--output", filename, url, "best", "--force"]
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if process.returncode == 0 and os.path.exists(filename) and os.path.getsize(filename) > 0:
        print(f"Stream captured for {model_name}! Uploading to Telegram...")
        upload_to_telegram(filename, f"🎥 Recorded live show: #{model_name}")
        os.remove(filename)
    else:
        print(f"{model_name} is currently offline.")

def upload_to_telegram(file_path, caption):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    with open(file_path, "rb") as video:
        files = {"video": video}
        data = {"chat_id": CHAT_ID, "caption": caption}
        response = requests.post(telegram_url, data=data, files=files)
        print("Telegram Upload Status:", response.json())

if __name__ == "__main__":
    watchlist = get_watchlist()
    for model in watchlist:
        check_and_record(model)
