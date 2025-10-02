import os
import requests
import logging
import coloredlogs
from flask import Flask, jsonify, request, send_from_directory, send_file

app = Flask(__name__, static_folder="static")
seen_ips = set()

# Setup logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='INFO', logger=logger, fmt='%(asctime)s - %(levelname)s - %(message)s')

@app.before_request
def log_request_info():
    if "X-Forwarded-For" in request.headers:
        ip_address = request.headers["X-Forwarded-For"].split(",")[0].strip()
    else:
        ip_address = request.remote_addr

    if ip_address not in seen_ips and request.path == '/':
        url = f"http://ip-api.com/json/{ip_address}"
        try:
            response = requests.get(url)
            data = response.json()
            city = data.get("city", "Unknown")
            region = data.get("regionName", "Unknown")
            country = data.get("country", "Unknown")
            lat = data.get("lat", "Unknown")
            lon = data.get("lon", "Unknown")
            user_agent = request.headers.get('User-Agent')
            
            logger.info(f"New user connected: {ip_address}")
            logger.info(f"  Location: {city}, {region}, {country} ({lat}, {lon})")
            logger.info(f"  User-Agent: {user_agent}")
            
            seen_ips.add(ip_address)
        except Exception as e:
            logger.error(f"Could not get location for {ip_address}. Error: {e}")
    else:
        logger.info(f"Activity from {ip_address}: {request.method} {request.path}")

BASE_PATH = os.path.expanduser("~/MediaFTP")
UPDATED_DIR = os.path.join(BASE_PATH, ".cache/updated")
BOOKMARK_FILE = os.path.join(BASE_PATH, ".cache/bookmark/bookmark.txt")

# Ensure directories exist
os.makedirs(UPDATED_DIR, exist_ok=True)
os.makedirs(os.path.dirname(BOOKMARK_FILE), exist_ok=True)
open(BOOKMARK_FILE, "a").close()


def list_folders(search_query):
    """Read .db files and filter based on search query."""
    db_files = [os.path.join(UPDATED_DIR, f) for f in os.listdir(UPDATED_DIR) if f.endswith(".db")]
    folders = []
    for db in db_files:
        with open(db) as f:
            for line in f:
                line = line.strip()
                if line:
                    rel = os.path.relpath(line, BASE_PATH)
                    if search_query in rel.lower() or search_query in line.lower():
                        folders.append({
                            "name": os.path.basename(line),
                            "path": line,
                            "display_path": rel
                        })
    return sorted(folders, key=lambda x: x['name'])


def list_bookmarks(search_query):
    """Load bookmarks and filter based on search query."""
    bookmarks = []
    with open(BOOKMARK_FILE) as f:
        for line in f:
            parts = line.strip().split("\t", 1)
            if len(parts) == 2:
                name, path = parts[0], parts[1]
                if search_query in name.lower() or search_query in path.lower():
                    bookmarks.append({
                        "name": name,
                        "path": path,
                        "display_path": os.path.relpath(path, BASE_PATH)
                    })
    return bookmarks


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/folders")
def folders():
    search = request.args.get('search')
    if not search:
        return jsonify([])
    return jsonify(list_folders(search.lower()))


@app.route("/bookmarks")
def bookmarks():
    search = request.args.get('search', '')
    return jsonify(list_bookmarks(search.lower()))


@app.route("/bookmark/add", methods=["POST"])
def add_bookmark():
    data = request.json
    name, path = data["name"], data["path"]
    with open(BOOKMARK_FILE, "a") as f:
        f.write(f"{name}\t{path}\n")
    return jsonify({"status": "ok"})


@app.route("/bookmark/remove", methods=["POST"])
def remove_bookmark():
    path = request.json["path"]
    with open(BOOKMARK_FILE) as f:
        lines = f.readlines()
    with open(BOOKMARK_FILE, "w") as f:
        for line in lines:
            if not line.strip().endswith(path):
                f.write(line)
    return jsonify({"status": "ok"})


@app.route("/files")
def list_files():
    path = request.args.get("path")
    if not path or not os.path.exists(path):
        return jsonify({"error": "Path not found"}), 400
    
    if not os.path.abspath(path).startswith(os.path.abspath(BASE_PATH)):
        return jsonify({"error": "Forbidden"}), 403

    media_files = []
    for root, _, files in os.walk(path):
        for f in files:
            if f.lower().endswith((".mp4", ".mkv", ".avi", ".mov", ".mp3", ".flac", ".wav", ".m4a")):
                full_path = os.path.join(root, f)
                media_files.append({
                    "path": full_path,
                    "name": os.path.relpath(full_path, path)
                })

    return jsonify(sorted(media_files, key=lambda x: x['name']))


@app.route("/stream")
def stream():
    path = request.args.get("path")
    if not path or not os.path.abspath(path).startswith(os.path.abspath(BASE_PATH)):
        return "Forbidden", 403
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)
