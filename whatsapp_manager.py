"""
whatsapp_manager.py - Client interface to local WhatsApp Bridge.
Runs non-blocking async background sending of bills and PDF attachments.
Provides QR status checking and auto-starts the local bridge service.
"""

import os
import sys
import json
import time
import subprocess
import threading
import urllib.request
import urllib.error

BRIDGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bridge")
STATUS_URL = "http://127.0.0.1:5001/status"
SEND_URL = "http://127.0.0.1:5001/send-bill"
LOGOUT_URL = "http://127.0.0.1:5001/logout"
PAIRING_URL = "http://127.0.0.1:5001/request-pairing-code"

bridge_process = None

def is_bridge_running() -> bool:
    """Checks if the local WhatsApp bridge HTTP service is answering."""
    try:
        req = urllib.request.Request(STATUS_URL, headers={"User-Agent": "JewelryApp"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False

def ensure_bridge_running():
    """Auto-starts the Node.js bridge in the background if not already active."""
    global bridge_process
    if is_bridge_running():
        return True

    server_script = os.path.join(BRIDGE_DIR, "server.js")
    if not os.path.exists(server_script):
        return False

    try:
        # Hide command window completely on Windows
        creationflags = 0
        if sys.platform == "win32":
            # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
            creationflags = 0x00000008 | 0x00000200 | 0x08000000

        bridge_process = subprocess.Popen(
            ["node", "server.js"],
            cwd=BRIDGE_DIR,
            creationflags=creationflags,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        
        # Wait up to 5 seconds for it to start listening
        for _ in range(10):
            time.sleep(0.5)
            if is_bridge_running():
                return True
        return False
    except Exception as e:
        print(f"[WhatsApp Manager] Could not start bridge: {e}")
        return False

def get_whatsapp_status() -> dict:
    """Returns { status: 'connected'|'qr_ready'|'connecting'|'disconnected'|'offline', qr: 'data:...', user: {...} }"""
    try:
        req = urllib.request.Request(STATUS_URL, headers={"User-Agent": "JewelryApp"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        pass
    return {"status": "offline", "qr": None, "user": None, "error": "Bridge not running"}

def send_bill_sync(phone: str, message: str = "", pdf_path: str = None) -> dict:
    """Synchronous send (used internally by worker threads)."""
    if not phone:
        return {"success": False, "error": "No phone number provided."}

    payload = {
        "phone": phone,
        "message": message,
        "pdfPath": pdf_path if (pdf_path and os.path.exists(pdf_path)) else None
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            SEND_URL,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "JewelryApp"}
        )
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
            return {"success": False, "error": err_body.get("error", str(e))}
        except Exception:
            return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_bill_async(phone: str, message: str = "", pdf_path: str = None, callback=None):
    """
    Sends WhatsApp message and PDF in the background without blocking the UI.
    Calls optional callback(result_dict) on completion.
    """
    def _worker():
        res = send_bill_sync(phone, message, pdf_path)
        if callback:
            try:
                callback(res)
            except Exception as e:
                print(f"[WhatsApp Manager] Callback error: {e}")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread

def logout_whatsapp() -> bool:
    """Logs out and clears session on the bridge."""
    try:
        req = urllib.request.Request(
            LOGOUT_URL,
            data=b"{}",
            headers={"Content-Type": "application/json", "User-Agent": "JewelryApp"}
        )
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            return resp.status == 200
    except Exception:
        return False

def request_pairing_code(phone: str) -> dict:
    """
    Requests an 8-digit pairing code from Baileys for camera-less linking.
    Returns: {"success": True, "code": "ABCD-1234"} or {"success": False, "error": "..."}
    """
    if not phone:
        return {"success": False, "error": "કૃપા કરીને મોબાઇલ નંબર દાખલ કરો."}

    ensure_bridge_running()

    payload = {"phone": phone}
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            PAIRING_URL,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "JewelryApp"}
        )
        with urllib.request.urlopen(req, timeout=12.0) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
            return {"success": False, "error": err_body.get("error", str(e))}
        except Exception:
            return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}
