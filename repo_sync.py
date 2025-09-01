#!/usr/bin/env python3
import os
import subprocess
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

# ====== CONFIG ======
CLONE_FILE = "repos/clone_repos.txt"
PUSH_FILE = "repos/push_repos.txt"
GITHUB_TOKEN = ""

# Telegram bot settings
TELEGRAM_BOT_TOKEN = "8389557403:AAFqqL6XAoQMmqY-hcTLie7oPK9-MqPualY"
TELEGRAM_CHAT_ID = "-3008886997"  # Replace with your group ID
# =====================


def send_telegram_message(message: str):
    """Send a message to Telegram group."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"⚠️ Telegram send failed: {e}")


def read_file(path):
    """Read repos list from file."""
    repos = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 3 and parts[1] == "branch":
                repos.append((parts[0], parts[2]))
            else:
                print(f"⚠️ Skipping invalid line in {path}: {line}")
    return repos


def get_repo_name(url):
    """Extract repo folder name from Git URL."""
    return url.rstrip("/").split("/")[-1].replace(".git", "")


def get_ist_time():
    """Return current IST datetime and formatted string."""
    tz = ZoneInfo("Asia/Kolkata")
    dt = datetime.now(tz)
    return dt, dt.strftime("%Y-%m-%d %H:%M:%S")


def run_cmd(cmd, cwd=None):
    """Run shell command."""
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, text=True,
                                capture_output=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()


def main():
    # ASCII banner
    banner = r"""
 __  __ _     _   _____   ____   _____           _             
|  \/  (_)   | | |_   _| / __ \ / ____|         | |            
| \  / |_  __| |   | |  | |  | | |     ___  _ __| |_ ___  _ __ 
| |\/| | |/ _` |   | |  | |  | | |    / _ \| '__| __/ _ \| '__|
| |  | | | (_| |  _| |_ | |__| | |___| (_) | |  | || (_) | |   
|_|  |_|_|\__,_| |_____| \____/ \_____\___/|_|   \__\___/|_|   

                  MistOS Cloning tool
    """
    print(banner)
    send_telegram_message("🚀 *MistOS Cloning tool started*")

    start_time, start_str = get_ist_time()
    send_telegram_message(f"🕒 Start Time (IST): `{start_str}`")

    clone_repos = read_file(CLONE_FILE)
    push_repos = read_file(PUSH_FILE)

    if len(clone_repos) != len(push_repos):
        print("❌ Mismatch in number of repos between clone and push lists")
        sys.exit(1)

    summary = []
    for i, ((clone_repo, clone_branch), (push_repo, push_branch)) in enumerate(
        zip(clone_repos, push_repos), 1
    ):
        repo_name = get_repo_name(clone_repo)
        print(f"\n=== [{i}] Processing {repo_name} ===")
        send_telegram_message(f"🔄 Processing *{repo_name}*...")

        if not os.path.exists(repo_name):
            ok, out = run_cmd(["git", "clone", "-b", clone_branch, clone_repo, repo_name])
            if not ok:
                print(f"❌ Clone failed: {out}")
                send_telegram_message(f"❌ Clone failed for *{repo_name}*:\n`{out}`")
                summary.append((repo_name, "Clone Failed"))
                continue
            print(f"✅ Cloned {repo_name} ({clone_branch})")
            send_telegram_message(f"✅ Cloned *{repo_name}* ({clone_branch})")
        else:
            print(f"⚠️ {repo_name} already exists, skipping clone")

        remote_url = f"https://{GITHUB_TOKEN}@github.com/{push_repo}.git"
        ok, out = run_cmd(["git", "remote", "set-url", "origin", remote_url], cwd=repo_name)
        if not ok:
            print(f"❌ Remote set failed: {out}")
            send_telegram_message(f"❌ Remote set failed for *{repo_name}*:\n`{out}`")
            summary.append((repo_name, "Remote Failed"))
            continue

        ok, out = run_cmd(["git", "push", "-f", "origin", f"{clone_branch}:{push_branch}"], cwd=repo_name)
        if not ok:
            print(f"❌ Push failed: {out}")
            send_telegram_message(f"❌ Push failed for *{repo_name}*:\n`{out}`")
            summary.append((repo_name, "Push Failed"))
            continue

        print(f"✅ Pushed {repo_name} ({clone_branch} → {push_branch})")
        send_telegram_message(f"✅ Pushed *{repo_name}* ({clone_branch} → {push_branch})")
        summary.append((repo_name, "Success"))

    end_time, end_str = get_ist_time()
    elapsed = end_time - start_time
    elapsed_str = str(elapsed).split(".")[0]  # HH:MM:SS

    print("\n===== SUMMARY =====")
    table = "\n".join([f"{name}: {status}" for name, status in summary])
    print(table)

    print(f"\n🕒 Start Time: {start_str}")
    print(f"🕒 End Time:   {end_str}")
    print(f"⏳ Duration:   {elapsed_str}")

    summary_msg = (
        "📊 *MistOS Cloning Summary:*\n"
        + "\n".join([f"- {name}: {status}" for name, status in summary])
        + f"\n\n🕒 Start: `{start_str}`\n🕒 End: `{end_str}`\n⏳ Duration: `{elapsed_str}`"
    )
    send_telegram_message(summary_msg)


if __name__ == "__main__":
    main()
