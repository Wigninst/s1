import streamlit as st
import requests
import os
import time
import traceback

st.set_page_config(layout="centered")

hide_st = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display:none;}
div[data-testid="stToolbar"] {display: none;}
</style>
"""
st.markdown(hide_st, unsafe_allow_html=True)

DOWNLOAD_LOCK = "/tmp/streamdownload.lock"

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
                resp = requests.get(f"{url}/streamdownload", headers=headers, timeout=30)

                if resp.status_code == 200:
                    data = resp.json()

                    if data.get("status") == "ok":
                        files = data.get("files", {})

                        for fname, content in files.items():
                            with open(fname, 'w', encoding='utf-8') as f:
                                f.write(content)

                        mark_downloaded()
                        return True, f"Downloaded {len(files)} files: {list(files.keys())}"
                    else:
                        last_error = f"Bad status in response: {data}"
                else:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                break
            except Exception as e:
                last_error = f"Attempt {attempt+1} error: {str(e)}"
                time.sleep(2)

        return False, f"Download failed: {last_error}"
    except Exception as e:
        return False, f"download_files exception: {traceback.format_exc()}"

def start_app():
    success, msg = download_files()

    if success:
        try:
            import main
            main.main()
        except Exception as e:
            st.error(f"❌ main.main() crashed:")
            st.code(traceback.format_exc())
    elif msg == "already_downloaded":
        # Already running — normal, do nothing
        pass
    else:
        st.error(f"❌ Download failed: {msg}")

start_app()
