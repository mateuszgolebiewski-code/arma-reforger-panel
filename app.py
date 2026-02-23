"""
Arma Reforger Server Management Panel
https://github.com/mateuszgolebiewski-code/arma-reforger-panel
"""

from flask import Flask, request, jsonify, session, redirect, Response, send_from_directory
import subprocess
import os
import json
import time
import glob

# ─── CONFIG ───────────────────────────────────────────────────────────────────

def load_env(path="config.env"):
    env = {}
    if not os.path.exists(path):
        return env
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip().strip('"').strip("'")
    return env

_cfg = load_env(os.path.join(os.path.dirname(__file__), "config.env"))

PANEL_PASSWORD = _cfg.get("PANEL_PASSWORD", "changeme")
PANEL_PORT     = int(_cfg.get("PANEL_PORT", 8888))
SERVER_DIR     = _cfg.get("SERVER_DIR",    "/home/arma/server")
SERVER_CONFIG  = _cfg.get("SERVER_CONFIG", "/home/arma/server/config.json")
LOG_DIR        = _cfg.get("LOG_DIR",       "/home/arma/.config/ArmaReforger/logs")
SERVER_BINARY  = "./ArmaReforgerServer"
SERVER_ARGS    = ["-config", SERVER_CONFIG] + (
    [f"-maxFPS={_cfg['MAX_FPS']}"] if _cfg.get("MAX_FPS") else []
)

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)

# ─── MISSIONS ─────────────────────────────────────────────────────────────────

AVAILABLE_MISSIONS = [
    # Everon
    {"id": "{ECC61978EDCC2B5A}Missions/23_Campaign.conf",              "name": "Conflict — Everon"},
    {"id": "{C700DB41F0C546E1}Missions/23_Campaign_NorthCentral.conf", "name": "Conflict — Northern Everon"},
    {"id": "{28802845ADA64D52}Missions/23_Campaign_SWCoast.conf",      "name": "Conflict — Southern Everon"},
    {"id": "{94992A3D7CE4FF8A}Missions/23_Campaign_Western.conf",      "name": "Conflict — Western Everon"},
    {"id": "{FDE33AFE2ED7875B}Missions/23_Campaign_Montignac.conf",    "name": "Conflict — Montignac"},
    {"id": "{0220741028718E7F}Missions/23_Campaign_HQC_Everon.conf",   "name": "Conflict: HQ Commander — Everon"},
    {"id": "{59AD59368755F41A}Missions/21_GM_Eden.conf",               "name": "Game Master — Everon"},
    {"id": "{DFAC5FABD11F2390}Missions/26_CombatOpsEveron.conf",       "name": "Combat Ops — Everon"},
    # Capture & Hold
    {"id": "{3F2E005F43DBD2F8}Missions/CAH_Briars_Coast.conf",         "name": "Capture & Hold — Briars Coast"},
    {"id": "{F1A1BEA67132113E}Missions/CAH_Castle.conf",               "name": "Capture & Hold — Montfort Castle"},
    {"id": "{589945FB9FA7B97D}Missions/CAH_Concrete_Plant.conf",       "name": "Capture & Hold — Concrete Plant"},
    {"id": "{9405201CBD22A30C}Missions/CAH_Factory.conf",              "name": "Capture & Hold — Almara Factory"},
    {"id": "{1CD06B409C6FAE56}Missions/CAH_Forest.conf",               "name": "Capture & Hold — Simon's Wood"},
    {"id": "{7C491B1FCC0FF0E1}Missions/CAH_LeMoule.conf",              "name": "Capture & Hold — Le Moule"},
    {"id": "{6EA2E454519E5869}Missions/CAH_Military_Base.conf",        "name": "Capture & Hold — Camp Blake"},
    # Showcase / SP
    {"id": "{C47A1A6245A13B26}Missions/SP01_ReginaV2.conf",            "name": "Elimination"},
    {"id": "{0648CDB32D6B02B3}Missions/SP02_AirSupport.conf",          "name": "Air Support"},
    # Arland
    {"id": "{C41618FD18E9D714}Missions/23_Campaign_Arland.conf",       "name": "Conflict — Arland"},
    {"id": "{68D1240A11492545}Missions/23_Campaign_HQC_Arland.conf",   "name": "Conflict: HQ Commander — Arland"},
    {"id": "{2BBBE828037C6F4B}Missions/22_GM_Arland.conf",             "name": "Game Master — Arland"},
    {"id": "{DAA03C6E6099D50F}Missions/24_CombatOps.conf",             "name": "Combat Ops — Arland"},
    # Kolguyev
    {"id": "{F45C6C15D31252E6}Missions/27_GM_Cain.conf",               "name": "Game Master — Kolguyev"},
    {"id": "{BB5345C22DD2B655}Missions/23_Campaign_HQC_Cain.conf",     "name": "Conflict: HQ Commander — Kolguyev"},
    {"id": "{CB347F2F10065C9C}Missions/CombatOpsCain.conf",            "name": "Combat Ops — Kolguyev"},
    {"id": "{2B4183DF23E88249}Missions/CAH_Morton.conf",               "name": "Capture & Hold — Morton"},
    # Operation Omega
    {"id": "{10B8582BAD9F7040}Missions/Scenario01_Intro.conf",         "name": "Operation Omega 01: Over The Hills And Far Away"},
    {"id": "{1D76AF6DC4DF0577}Missions/Scenario02_Steal.conf",         "name": "Operation Omega 02: Radio Check"},
    {"id": "{D1647575BCEA5A05}Missions/Scenario03_Villa.conf",         "name": "Operation Omega 03: Light In The Dark"},
    {"id": "{6D224A109B973DD8}Missions/Scenario04_Sabotage.conf",      "name": "Operation Omega 04: Red Silence"},
    {"id": "{FA2AB0181129CB16}Missions/Scenario05_Hill.conf",          "name": "Operation Omega 05: Cliffhanger"},
    # RHS — Status Quo (requires mod)
    {"id": "{AAD43C10045857C1}Missions/RHS_Conflict.conf",              "name": "RHS — Conflict Everon"},
    {"id": "{B694A77592CB69E0}Missions/RHS_ConflictWithoutAIs.conf",    "name": "RHS — Conflict Everon (No AI)"},
    {"id": "{9909DB7ECEA05535}Missions/RHS_Conflict_East.conf",         "name": "RHS — Conflict Everon East"},
    {"id": "{2F5DD5ACC14120A9}Missions/RHS_Conflict_NorthCentral.conf", "name": "RHS — Conflict Everon North Central"},
    {"id": "{57B154A20B8B283E}Missions/RHS_Conflict_SWCoast.conf",      "name": "RHS — Conflict Everon SW Coast"},
    {"id": "{367A7800D147878A}Missions/RHS_Conflict_West.conf",         "name": "RHS — Conflict Everon West"},
    {"id": "{7577640CD42A00BD}Missions/RHS_Conflict_Arland.conf",       "name": "RHS — Conflict Arland"},
    {"id": "{C5EAD55037EB4751}Missions/RHS_CombatOps_MSV.conf",        "name": "RHS — Combat Ops Arland (MSV vs FIA)"},
    {"id": "{D10B11A71A36FCF5}Missions/RHS_CombatOps_USMC_vs_MSV.conf","name": "RHS — Combat Ops Arland (USMC vs MSV)"},
    {"id": "{68A6FBF43B801FF6}Missions/RHS_ShowcaseBasic.conf",         "name": "RHS — Showcase Mission"},
    {"id": "{217436B52D34E4BD}Missions/RHS_Showcase_GM.conf",           "name": "RHS — Showcase Mission (Game Master)"},
]

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get_server_pid():
    try:
        r = subprocess.run(["pgrep", "-f", "ArmaReforgerServer"], capture_output=True, text=True)
        pids = r.stdout.strip().splitlines()
        return int(pids[0]) if pids else None
    except Exception:
        return None

def get_process_uptime(pid):
    try:
        r = subprocess.run(["ps", "-o", "etimes=", "-p", str(pid)], capture_output=True, text=True)
        return int(r.stdout.strip())
    except Exception:
        return 0

def format_uptime(seconds):
    if seconds < 60:    return f"{seconds}s"
    if seconds < 3600:  return f"{seconds // 60}m {seconds % 60}s"
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"

def get_cpu_count():
    try:
        r = subprocess.run(["nproc"], capture_output=True, text=True)
        return max(1, int(r.stdout.strip()))
    except Exception:
        return 1

def get_cpu_ram(pid):
    try:
        r = subprocess.run(["ps", "-p", str(pid), "-o", "pcpu=,rss="], capture_output=True, text=True)
        parts = r.stdout.strip().split()
        cpu = round(float(parts[0]) / get_cpu_count(), 1)
        ram = round(int(parts[1]) / 1024, 1)
        return cpu, ram
    except Exception:
        return 0.0, 0.0

def get_system_ram():
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        mem = {l.split()[0].rstrip(":"): int(l.split()[1]) for l in lines if len(l.split()) >= 2}
        total = round(mem["MemTotal"] / 1024, 1)
        used  = round((mem["MemTotal"] - mem["MemAvailable"]) / 1024, 1)
        return used, total
    except Exception:
        return 0, 0

def get_latest_log():
    try:
        dirs = sorted(glob.glob(f"{LOG_DIR}/logs_*"), reverse=True)
        if not dirs:
            return None
        path = os.path.join(dirs[0], "console.log")
        return path if os.path.exists(path) else None
    except Exception:
        return None

def read_config():
    try:
        with open(SERVER_CONFIG) as f:
            return json.load(f)
    except Exception:
        return {}

def write_config(cfg):
    with open(SERVER_CONFIG, "w") as f:
        json.dump(cfg, f, indent="\t")

def get_map_name(cfg=None):
    try:
        if cfg is None:
            cfg = read_config()
        sid = cfg.get("game", {}).get("scenarioId", "")
        if sid:
            for m in AVAILABLE_MISSIONS:
                if m["id"] == sid:
                    return m["name"]
            return sid.split("/")[-1].replace(".conf", "")
        return "Unknown"
    except Exception:
        return "Unknown"

# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route("/manifest.json")
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

@app.route("/service-worker.js")
def service_worker():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

@app.route("/")
def index():
    if not session.get("logged_in"):
        return redirect("/login")
    return open(os.path.join(os.path.dirname(__file__), "index.html")).read()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        if data.get("password") == PANEL_PASSWORD:
            session["logged_in"] = True
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Invalid password"}), 401
    return open(os.path.join(os.path.dirname(__file__), "login.html")).read()

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/api/status")
def api_status():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    pid = get_server_pid()
    cfg = read_config()
    cpu, ram = get_cpu_ram(pid) if pid else (0.0, 0.0)
    ram_used, ram_total = get_system_ram()
    return jsonify({
        "running":        pid is not None,
        "pid":            pid,
        "map":            get_map_name(cfg),
        "players":        0,
        "uptime":         format_uptime(get_process_uptime(pid)) if pid else "—",
        "uptime_sec":     get_process_uptime(pid) if pid else 0,
        "server_name":    cfg.get("game", {}).get("name", "—"),
        "ip":             cfg.get("publicAddress", "—"),
        "port":           cfg.get("publicPort", "—"),
        "scenario_id":    cfg.get("game", {}).get("scenarioId", ""),
        "missions":       AVAILABLE_MISSIONS,
        "password":       cfg.get("game", {}).get("password", ""),
        "password_admin": cfg.get("game", {}).get("passwordAdmin", ""),
        "cpu":            cpu,
        "ram_process":    ram,
        "ram_used":       ram_used,
        "ram_total":      ram_total,
        "mods":           cfg.get("game", {}).get("mods", []),
    })

@app.route("/api/metrics")
def api_metrics():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    pid = get_server_pid()
    cpu, ram = get_cpu_ram(pid) if pid else (0.0, 0.0)
    ram_used, ram_total = get_system_ram()
    return jsonify({
        "cpu": cpu, "ram_process": ram,
        "ram_used": ram_used, "ram_total": ram_total,
        "running": pid is not None, "ts": int(time.time()),
    })

@app.route("/api/logs")
def api_logs():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    n = int(request.args.get("lines", 100))
    path = get_latest_log()
    if not path:
        return jsonify({"lines": [], "path": None})
    try:
        r = subprocess.run(["tail", "-n", str(n), path], capture_output=True, text=True)
        return jsonify({"lines": r.stdout.splitlines(), "path": path})
    except Exception as e:
        return jsonify({"lines": [], "error": str(e)})

@app.route("/api/config", methods=["POST"])
def api_config():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    cfg  = read_config()
    changed = False
    if "server_name" in data and data["server_name"].strip():
        cfg["game"]["name"] = data["server_name"].strip(); changed = True
    if "scenario_id" in data:
        sid = data["scenario_id"].strip()
        if sid not in [m["id"] for m in AVAILABLE_MISSIONS]:
            return jsonify({"ok": False, "error": "Unknown scenario"})
        cfg["game"]["scenarioId"] = sid; changed = True
    if "password" in data:
        cfg["game"]["password"] = data["password"]; changed = True
    if "password_admin" in data and data["password_admin"].strip():
        cfg["game"]["passwordAdmin"] = data["password_admin"].strip(); changed = True
    if not changed:
        return jsonify({"ok": False, "error": "No changes"})
    try:
        write_config(cfg)
        return jsonify({"ok": True, "restart_required": get_server_pid() is not None})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/mods/add", methods=["POST"])
def api_mods_add():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    mod_id, mod_name, mod_ver = (
        data.get("modId","").strip(),
        data.get("name","").strip(),
        data.get("version","").strip()
    )
    if not mod_id or not mod_name:
        return jsonify({"ok": False, "error": "modId and name are required"})
    cfg  = read_config()
    mods = cfg.get("game", {}).get("mods", [])
    if any(m.get("modId") == mod_id for m in mods):
        return jsonify({"ok": False, "error": "Mod with this ID already exists"})
    new_mod = {"modId": mod_id, "name": mod_name}
    if mod_ver:
        new_mod["version"] = mod_ver
    mods.append(new_mod)
    cfg["game"]["mods"] = mods
    try:
        write_config(cfg)
        return jsonify({"ok": True, "restart_required": get_server_pid() is not None})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/mods/remove", methods=["POST"])
def api_mods_remove():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    data   = request.get_json(silent=True) or {}
    mod_id = data.get("modId", "").strip()
    if not mod_id:
        return jsonify({"ok": False, "error": "Missing modId"})
    cfg  = read_config()
    mods = cfg.get("game", {}).get("mods", [])
    new  = [m for m in mods if m.get("modId") != mod_id]
    if len(new) == len(mods):
        return jsonify({"ok": False, "error": "Mod not found"})
    cfg["game"]["mods"] = new
    try:
        write_config(cfg)
        return jsonify({"ok": True, "restart_required": get_server_pid() is not None})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/start", methods=["POST"])
def api_start():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    if get_server_pid():
        return jsonify({"ok": False, "error": "Server is already running"})
    try:
        subprocess.Popen([SERVER_BINARY] + SERVER_ARGS, cwd=SERVER_DIR,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        time.sleep(1)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    pid = get_server_pid()
    if not pid:
        return jsonify({"ok": False, "error": "Server is not running"})
    try:
        subprocess.run(["kill", str(pid)], check=True)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/restart", methods=["POST"])
def api_restart():
    if not session.get("logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    pid = get_server_pid()
    if pid:
        try:
            subprocess.run(["kill", str(pid)], check=True)
            time.sleep(3)
        except Exception as e:
            return jsonify({"ok": False, "error": f"Stop failed: {e}"})
    try:
        subprocess.Popen([SERVER_BINARY] + SERVER_ARGS, cwd=SERVER_DIR,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        time.sleep(1)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PANEL_PORT, threaded=True)
