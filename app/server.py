#!/usr/bin/env python3
"""
Division 2 — DPS Tracker
Serveur local · Interface web · http://localhost:7842
"""
import re, time, threading, json, base64, os, io, sys, glob
from datetime import datetime
from collections import deque
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from flask import Flask, Response, request, jsonify, send_from_directory

# ── Localisation de Tesseract (Windows surtout) ──────────────────────────────
def _find_tesseract():
    # 1) Variable transmise par lancer.bat
    env = os.environ.get("TESSERACT_CMD", "").strip()
    if env and os.path.isfile(env):
        return env
    # 2) Déjà dans le PATH
    import shutil
    found = shutil.which("tesseract")
    if found:
        return found
    # 3) Emplacements Windows courants
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LocalAppData%\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expandvars(r"%LocalAppData%\Tesseract-OCR\tesseract.exe"),
        r"C:\Tesseract-OCR\tesseract.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    # 4) Registre Windows
    try:
        import winreg
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                key = winreg.OpenKey(root, r"SOFTWARE\Tesseract-OCR")
                install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                exe = os.path.join(install_dir, "tesseract.exe")
                if os.path.isfile(exe):
                    return exe
            except Exception:
                pass
    except ImportError:
        pass
    return None

_tess = _find_tesseract()
if _tess:
    pytesseract.pytesseract.tesseract_cmd = _tess

# ── Config par défaut ────────────────────────────────────────────────────────
DEFAULT_CFG = {
    "region": {"x": 0, "y": 730, "w": 400, "h": 350},
    "fps": 8,
    "dps_window": 10,
    "source": "screen",     # "screen" | "video"
    "video_path": "",
    "resolution": "1920x1080"
}

PRESETS = {
    "1920x1080": {"x": 0, "y": 730, "w": 400, "h": 350},
    "2560x1440": {"x": 0, "y": 975, "w": 530, "h": 465},
    "3840x2160": {"x": 0, "y": 1460,"w": 800, "h": 700},
    "1280x720":  {"x": 0, "y": 490, "w": 265, "h": 230},
}

CFG_FILE = Path(__file__).parent / "config.json"

def load_cfg():
    if CFG_FILE.exists():
        try:
            return {**DEFAULT_CFG, **json.loads(CFG_FILE.read_text())}
        except Exception:
            pass
    return dict(DEFAULT_CFG)

def save_cfg(cfg):
    CFG_FILE.write_text(json.dumps(cfg, indent=2))

# ── État global ──────────────────────────────────────────────────────────────
cfg       = load_cfg()
state     = {
    "running":   False,
    "total":     0,
    "hits":      0,
    "peak":      0,
    "avg":       0.0,
    "dps":       0.0,
    "dps_bar":   0,          # 0-100
    "elapsed":   0.0,
    "history":   [],         # [(rel_time, value)]
    "feed":      deque(maxlen=80),  # dernières lignes du log
    "preview_b64": "",       # aperçu de la zone (base64 PNG)
    "status":    "stopped",  # stopped | running | paused | error
    "error_msg": "",
    "video_progress": 0,     # 0-100 pour mode vidéo
}
lock = threading.Lock()
worker_thread = None
stop_event    = threading.Event()

PATTERN = re.compile(r'\[(\d{2}:\d{2})\]DG[T1]S\s*[:\s]\s*(\d{4,8})', re.IGNORECASE)

# ── OCR ──────────────────────────────────────────────────────────────────────
def preprocess(frame):
    big  = cv2.resize(frame, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    hsv  = cv2.cvtColor(big, cv2.COLOR_BGR2HSV)
    m_or = cv2.inRange(hsv, (5,  100, 140), (28, 255, 255))
    m_ye = cv2.inRange(hsv, (25,  80, 160), (40, 255, 255))
    m_wh = cv2.inRange(hsv, (0,    0, 180), (180, 45, 255))
    mask = cv2.bitwise_or(m_or, cv2.bitwise_or(m_ye, m_wh))
    kernel = np.ones((2,2), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    out = np.full_like(big, 255)
    out[mask == 0] = 255
    out[mask  > 0] = 0
    return out

def ocr_frame(crop):
    proc = preprocess(crop)
    text = pytesseract.image_to_string(
        proc,
        config='--psm 6 --oem 1 -c tessedit_char_whitelist=0123456789:[DGTS] '
    )
    hits = []
    for ts, val in PATTERN.findall(text):
        hits.append((ts, int(val)))
    return hits

def frame_to_b64(frame):
    ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    if not ok:
        return ""
    return base64.b64encode(buf).decode()

# ── Capture d'écran ──────────────────────────────────────────────────────────
def get_capture_fn():
    try:
        import mss as _mss
        def _mss_cap(r):
            with _mss.mss() as s:
                mon = {"left":r["x"],"top":r["y"],"width":r["w"],"height":r["h"]}
                shot = s.grab(mon)
                f = np.array(shot)
                return cv2.cvtColor(f, cv2.COLOR_BGRA2BGR)
        return _mss_cap, "mss"
    except ImportError:
        pass
    try:
        from PIL import ImageGrab
        def _pil_cap(r):
            x,y,w,h = r["x"],r["y"],r["w"],r["h"]
            img = ImageGrab.grab(bbox=(x,y,x+w,y+h))
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        return _pil_cap, "PIL.ImageGrab"
    except Exception:
        pass
    if os.system("which scrot > /dev/null 2>&1") == 0:
        def _scrot_cap(r):
            tmp = "/tmp/_d2cap.png"
            os.system(f"scrot -a {r['x']},{r['y']},{r['w']},{r['h']} {tmp} 2>/dev/null")
            return cv2.imread(tmp)
        return _scrot_cap, "scrot"
    return None, None

# ── Worker threads ───────────────────────────────────────────────────────────
def push_hit(ts, val, wall_time, start_time):
    with lock:
        state["total"] += val
        state["hits"]  += 1
        if val > state["peak"]:
            state["peak"] = val
        rel = wall_time - start_time
        state["history"].append((rel, val))
        state["avg"] = state["total"] / state["hits"]
        # DPS fenêtre glissante
        window = cfg["dps_window"]
        cutoff = wall_time - window
        recent = [v for t, v in state["history"] if (start_time + t) >= cutoff]
        state["dps"] = sum(recent) / window if recent else 0.0
        # Barre DPS (0-100) basée sur 3M/s = 100%
        state["dps_bar"] = min(100, int(state["dps"] / 3_000_000 * 100))
        state["elapsed"] = rel
        # Feed
        color = "crit" if val > 800_000 else "normal"
        state["feed"].appendleft({
            "ts": ts, "val": val,
            "fmt": fmt_num(val), "color": color
        })

def fmt_num(n):
    if n >= 1_000_000: return f"{n/1_000_000:.2f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}K"
    return str(n)

def worker_screen():
    cap_fn, backend = get_capture_fn()
    if cap_fn is None:
        with lock:
            state["status"]    = "error"
            state["error_msg"] = ("Aucune librairie de capture disponible.\n"
                                  "Installez mss : pip install mss")
        return

    with lock:
        state["status"] = "running"
        state["error_msg"] = f"Capture via {backend}"

    region    = cfg["region"]
    interval  = 1.0 / cfg["fps"]
    start     = time.time()
    prev_set  = set()
    preview_t = 0

    while not stop_event.is_set():
        t0    = time.time()
        frame = cap_fn(region)

        if frame is None:
            time.sleep(interval)
            continue

        hits       = ocr_frame(frame)
        cur_set    = set(hits)
        new_lines  = cur_set - prev_set
        prev_set   = cur_set

        now = time.time()
        for ts, val in new_lines:
            push_hit(ts, val, now, start)

        # Aperçu ~ 2 fps
        if now - preview_t > 0.5:
            with lock:
                state["preview_b64"] = frame_to_b64(frame)
            preview_t = now

        elapsed = time.time() - t0
        if interval - elapsed > 0:
            time.sleep(interval - elapsed)

    with lock:
        state["status"] = "stopped"

def worker_video(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        with lock:
            state["status"]    = "error"
            state["error_msg"] = f"Impossible d'ouvrir : {path}"
        return

    with lock:
        state["status"] = "running"

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_fps    = cap.get(cv2.CAP_PROP_FPS) or 30
    step         = max(1, int(video_fps / cfg["fps"]))
    region       = cfg["region"]
    x,y,w,h      = region["x"],region["y"],region["w"],region["h"]
    start        = time.time()
    prev_set     = set()
    idx          = 0

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            break
        if idx % step == 0:
            fh, fw = frame.shape[:2]
            cx = min(x, fw);  cw = min(w, fw - cx)
            cy = min(y, fh);  ch = min(h, fh - cy)
            crop    = frame[cy:cy+ch, cx:cx+cw]
            hits    = ocr_frame(crop)
            cur_set = set(hits)
            new_lines = cur_set - prev_set
            prev_set  = cur_set

            # Temps relatif simulé sur la durée vidéo
            sim_time = start + (idx / total_frames) * (total_frames / video_fps)
            for ts, val in new_lines:
                push_hit(ts, val, sim_time, start)

            with lock:
                state["video_progress"] = int(idx / total_frames * 100)
                if idx % (step * 5) == 0:
                    state["preview_b64"] = frame_to_b64(crop)
        idx += 1

    cap.release()
    export_csv()
    with lock:
        state["status"] = "stopped"
        state["video_progress"] = 100

def export_csv():
    fname = datetime.now().strftime("div2_log_%Y%m%d_%H%M%S.csv")
    path  = Path(__file__).parent / fname
    with open(path, "w") as f:
        f.write("timestamp_rel,damage\n")
        for t, v in state["history"]:
            f.write(f"{t:.3f},{v}\n")
    with lock:
        state["error_msg"] = f"Exporté → {fname}"
    return fname

# ── Flask app ────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=str(Path(__file__).parent))

@app.route("/")
def index():
    return send_from_directory(str(Path(__file__).parent), "index.html")

@app.route("/api/state")
def api_state():
    with lock:
        feed = list(state["feed"])
        return jsonify({
            "running":        state["status"] == "running",
            "status":         state["status"],
            "error_msg":      state["error_msg"],
            "total":          state["total"],
            "total_fmt":      fmt_num(state["total"]),
            "hits":           state["hits"],
            "peak":           state["peak"],
            "peak_fmt":       fmt_num(state["peak"]),
            "avg":            state["avg"],
            "avg_fmt":        fmt_num(state["avg"]),
            "dps":            state["dps"],
            "dps_fmt":        fmt_num(state["dps"]),
            "dps_bar":        state["dps_bar"],
            "elapsed":        state["elapsed"],
            "video_progress": state["video_progress"],
            "feed":           feed,
            "preview_b64":    state["preview_b64"],
        })

@app.route("/api/config", methods=["GET"])
def api_cfg_get():
    return jsonify({**cfg, "presets": PRESETS})

@app.route("/api/config", methods=["POST"])
def api_cfg_set():
    global cfg
    data = request.get_json()
    cfg.update(data)
    save_cfg(cfg)
    return jsonify({"ok": True})

@app.route("/api/start", methods=["POST"])
def api_start():
    global worker_thread
    if state["status"] == "running":
        return jsonify({"ok": False, "msg": "Déjà en cours"})

    # Reset
    with lock:
        state.update({
            "total":0,"hits":0,"peak":0,"avg":0.0,
            "dps":0.0,"dps_bar":0,"elapsed":0.0,
            "history":[],"feed":deque(maxlen=80),
            "preview_b64":"","video_progress":0,
            "error_msg":""
        })
    stop_event.clear()

    src = cfg.get("source","screen")
    if src == "video":
        path = cfg.get("video_path","")
        if not path or not Path(path).exists():
            return jsonify({"ok":False,"msg":f"Fichier introuvable : {path}"})
        worker_thread = threading.Thread(target=worker_video, args=(path,), daemon=True)
    else:
        worker_thread = threading.Thread(target=worker_screen, daemon=True)

    worker_thread.start()
    return jsonify({"ok": True})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    stop_event.set()
    fname = export_csv()
    return jsonify({"ok": True, "export": fname})

@app.route("/api/export")
def api_export():
    fname = export_csv()
    return jsonify({"ok": True, "file": fname})

@app.route("/api/videos")
def api_videos():
    exts = ["*.mkv","*.mp4","*.avi","*.mov"]
    files = []
    for ext in exts:
        files += glob.glob(str(Path(__file__).parent / ext))
        files += glob.glob(str(Path.home() / "Videos" / ext))
        files += glob.glob(str(Path.home() / "Desktop" / ext))
    return jsonify({"files": sorted(set(files))})

# ── Lancement ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import webbrowser
    port = 7842
    print(f"\n  Division 2 DPS Tracker")
    print(f"  → http://localhost:{port}\n")
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
