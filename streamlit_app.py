import streamlit as st
import requests
import os
import time
import traceback
import sys
import io

DOWNLOAD_LOCK = "/tmp/streamdownload.lock"

# ── Live logger — captures all print() calls and shows on page ──
log_area = st.empty()
_log_lines = []

class StreamlitLogger(io.TextIOBase):
    def write(self, msg):
        if msg.strip():
            _log_lines.append(msg.rstrip())
            # Keep last 200 lines
            if len(_log_lines) > 200:
                _log_lines.pop(0)
            log_area.code("\n".join(_log_lines))
        return len(msg)
    def flush(self):
        pass

# Redirect stdout so all print() goes to page
sys.stdout = StreamlitLogger()

def is_downloaded():
    return os.path.exists(DOWNLOAD_LOCK)

def mark_downloaded():
    try:
        with open(DOWNLOAD_LOCK, 'w') as f:
            f.write(str(os.getpid()))
    except:
        pass

def download_files():
    if is_downloaded():
        return False, "already_downloaded"

    try:
        url = st.secrets.get("downloaderurl", "")
        streamuser = st.secrets.get("streamuser", "")
        downloaderkey = st.secrets.get("downloaderkey", "")

        if not url or not streamuser or not downloaderkey:
            return False, f"Missing secrets: url={bool(url)} streamuser={bool(streamuser)} key={bool(downloaderkey)}"

        headers = {
            "X-Streamuser": streamuser,
            "X-Downloaderkey": downloaderkey
        }

        last_error = ""
        for attempt in range(3):
            try:
                print(f"📥 Download attempt {attempt+1}...")
                resp = requests.get(f"{url}/streamdownload", headers=headers, timeout=30)

                if resp.status_code == 200:
                    data = resp.json()

                    if data.get("status") == "ok":
                        files = data.get("files", {})

                        for fname, content in files.items():
                            with open(fname, 'w', encoding='utf-8') as f:
                                f.write(content)
                            print(f"✅ Saved: {fname}")

                        mark_downloaded()
                        return True, f"Downloaded {len(files)} files"
                    else:
                        last_error = f"Bad status: {data}"
                else:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                break
            except Exception as e:
                last_error = f"Attempt {attempt+1} error: {str(e)}"
                time.sleep(2)

        return False, f"Download failed: {last_error}"
    except Exception as e:
        return False, f"Exception: {traceback.format_exc()}"

def start_app():
    print("🚀 streamlit_app.py starting...")

    success, msg = download_files()

    if success:
        print(f"✅ {msg}")
        print("▶️ Starting main.main()...")
        try:
            import main
            main.main()
        except Exception as e:
            print(f"❌ main.main() crashed: {traceback.format_exc()}")
    elif msg == "already_downloaded":
        print("⚠️ Already downloaded (lock exists) — main may already be running")
    else:
        print(f"❌ {msg}")

start_app()
