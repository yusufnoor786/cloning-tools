import os
import subprocess
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# ===== CONFIG =====
CLONE_FILE = "repos/clone_repos.txt"
PUSH_FILE = "repos/push_repos.txt"
WORKDIR = "workspace"
GITHUB_TOKEN = ""
TELEGRAM_BOT_TOKEN = "8389557403:AAFqqL6XAoQMmqY-hcTLie7oPK9-MqPualY"
TELEGRAM_CHAT_ID = -1003008886997  # replace with your group chat id

# ===== BANNER =====
BANNER = r"""
  __  __ _     _    ____   _____ 
 |  \/  (_)   | |  / __ \ / ____|
 | \  / |_ ___| |_| |  | | (___  
 | |\/| | / __| __| |  | |\___ \ 
 | |  | | \__ \ |_| |__| |____) |
 |_|  |_|_|___/\__|\____/|_____/ 

             🚀 MistOS Cloning tool 🚀
"""

# ===== HELPER FUNCS =====
def send_telegram_message(text):
    """Send message to Telegram with safety checks."""
    if not text or not text.strip():
        text = "ℹ️ No details provided."
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        r = requests.post(url, data=payload)
        if not r.json().get("ok"):
            print("⚠️ Telegram error:", r.json())
    except Exception as e:
        print(f"⚠️ Failed to send Telegram message: {e}")

def get_ist_time():
    tz = ZoneInfo("Asia/Kolkata")
    dt = datetime.now(tz)
    return dt, dt.strftime("%Y-%m-%d %H:%M:%S")

def parse_line(line):
    """Parse repo line: supports '<url> <branch>' or '<url> branch <branch>'"""
    parts = line.strip().split()
    if len(parts) == 2:
        return parts[0], parts[1]
    elif len(parts) == 3 and parts[1].lower() == "branch":
        return parts[0], parts[2]
    return None, None

def read_file(path):
    repos = []
    with open(path, "r") as f:
        for line in f:
            if not line.strip() or line.strip().startswith("#"):
                continue
            url, branch = parse_line(line)
            if url and branch:
                repos.append((url, branch))
            else:
                print(f"⚠️ Skipping invalid line in {path}: {line.strip()}")
    return repos

def run_cmd(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return result.returncode, result.stdout
    except Exception as e:
        return 1, str(e)

# ===== MAIN =====
def main():
    print(BANNER)

    start_dt, start_str = get_ist_time()
    send_telegram_message(f"🚀 MistOS Cloning tool started at {start_str} IST")

    clone_repos = read_file(CLONE_FILE)
    push_repos = read_file(PUSH_FILE)

    summary = []
    os.makedirs(WORKDIR, exist_ok=True)

    for i, ((clone_repo, clone_branch), (push_repo, push_branch)) in enumerate(zip(clone_repos, push_repos), 1):
        repo_name = os.path.splitext(os.path.basename(clone_repo))[0]
        repo_dir = os.path.join(WORKDIR, repo_name)

        send_telegram_message(f"🔄 [{i}] Processing {repo_name} ({clone_branch} → {push_branch})")

        # Clone or skip if exists
        if not os.path.exists(repo_dir):
            code, out = run_cmd(["git", "clone", "-b", clone_branch, clone_repo, repo_name], cwd=WORKDIR)
            if code != 0:
                summary.append((repo_name, "❌ Clone failed"))
                send_telegram_message(f"❌ Clone failed: {repo_name}\n{out}")
                continue
        else:
            print(f"ℹ️ Skipping clone, {repo_name} already exists")
            send_telegram_message(f"ℹ️ Skipping clone, {repo_name} already exists")

        # Push
        remote_url = push_repo.replace("https://", f"https://{GITHUB_TOKEN}@")
        run_cmd(["git", "remote", "remove", "dest"], cwd=repo_dir)  # cleanup if exists
        run_cmd(["git", "remote", "add", "dest", remote_url], cwd=repo_dir)
        code, out = run_cmd(["git", "push", "-f", "dest", f"{clone_branch}:{push_branch}"], cwd=repo_dir)

        if code == 0:
            summary.append((repo_name, "✅ Success"))
            send_telegram_message(f"✅ Pushed {repo_name} ({clone_branch} → {push_branch})")
        else:
            summary.append((repo_name, "❌ Push failed"))
            send_telegram_message(f"❌ Push failed: {repo_name}\n{out}")

    # Summary
    end_dt, end_str = get_ist_time()
    elapsed = end_dt - start_dt
    elapsed_h, rem = divmod(elapsed.total_seconds(), 3600)
    elapsed_m, _ = divmod(rem, 60)

    summary_text = ["\n📊 Final Summary:"]
    if summary:
        for repo, status in summary:
            summary_text.append(f"- {repo}: {status}")
    else:
        summary_text.append("- ℹ️ No repos processed")

    summary_text.append(f"\n⏱️ Started: {start_str} IST")
    summary_text.append(f"🏁 Completed: {end_str} IST")
    summary_text.append(f"⌛ Duration: {int(elapsed_h)}h {int(elapsed_m)}m")

    send_telegram_message("\n".join(summary_text))
    print("\n".join(summary_text))

if __name__ == "__main__":
    main()
