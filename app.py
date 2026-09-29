from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json

HOST = "0.0.0.0"
PORT = 8080

BASE_DIR = Path(__file__).resolve().parent
WEB_FILE = BASE_DIR / "web" / "index.html"
NOTES_FILE = BASE_DIR / "data" / "notes.json"


def load_notes():
    if not NOTES_FILE.exists():
        return []

    with open(NOTES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as file:
        json.dump(notes, file, ensure_ascii=False, indent=4)


class NoteLabHandler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()

        self.wfile.write(content)

    def send_html(self):
        content = WEB_FILE.read_bytes()

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()

        self.wfile.write(content)

    def do_GET(self):

        if self.path == "/":
            self.send_html()

        elif self.path == "/health":
            self.send_json({
                "status": "ok",
                "project": "NoteLab"
            })

        elif self.path == "/api/notes":
            self.send_json(load_notes())

        else:
            self.send_json({
                "error": "Page not found"
            }, 404)

    def do_POST(self):

        if self.path != "/api/notes":
            self.send_json({
                "error": "Endpoint not found"
            }, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_data = self.rfile.read(length)
            data = json.loads(raw_data.decode("utf-8"))

            text = str(data.get("text", "")).strip()

            if not text:
                self.send_json({
                    "error": "Empty note"
                }, 400)
                return

            notes = load_notes()

            new_id = max(
                [note["id"] for note in notes],
                default=0
            ) + 1

            notes.append({
                "id": new_id,
                "text": text
            })

            save_notes(notes)

            self.send_json({
                "status": "created",
                "id": new_id
            }, 201)

        except Exception as error:
            self.send_json({
                "error": str(error)
            }, 400)


server = ThreadingHTTPServer((HOST, PORT), NoteLabHandler)

print(f"NoteLab запущен на http://{HOST}:{PORT}")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nСервер остановлен.")
finally:
    server.server_close()
