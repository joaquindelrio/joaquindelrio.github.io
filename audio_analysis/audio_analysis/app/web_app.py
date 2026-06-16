import json
import os
import posixpath
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from main import process_wav_folder
from report_generator import analyze_folder_and_generate_report

APP_DIR = os.path.abspath(os.path.dirname(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.join(APP_DIR, "..", "..", ".."))
WEB_ROOT = os.path.join(APP_DIR, "web")


def normalize_path(path):
    if not path:
        return WORKSPACE_ROOT
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.abspath(os.path.join(WORKSPACE_ROOT, path))
    return os.path.abspath(path)


def is_allowed_path(path):
    path = os.path.abspath(path)
    return path.startswith(WORKSPACE_ROOT)


def list_directory_entries(path):
    entries = []
    try:
        with os.scandir(path) as it:
            for entry in sorted(it, key=lambda e: (not e.is_dir(), e.name.lower())):
                entries.append(
                    {
                        "name": entry.name,
                        "path": os.path.join(path, entry.name),
                        "is_dir": entry.is_dir(),
                        "is_file": entry.is_file(),
                    }
                )
    except PermissionError:
        pass
    return entries


def list_results(folder_path):
    parent_dir = os.path.dirname(folder_path)
    results_dir = os.path.join(parent_dir, "resultados")
    files = []
    if os.path.isdir(results_dir):
        for entry in sorted(os.listdir(results_dir)):
            full_path = os.path.join(results_dir, entry)
            if os.path.isfile(full_path):
                files.append({"name": entry, "path": full_path})
    return files


class AudioWebHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urllib.parse.urlparse(path)
        if parsed.path.startswith("/api"):
            return super().translate_path("/")
        if parsed.path.startswith("/"):
            requested = parsed.path.lstrip("/")
            potential = os.path.join(WEB_ROOT, requested)
            if os.path.exists(potential):
                return potential
        return os.path.join(WEB_ROOT, "index.html")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/list":
            query = urllib.parse.parse_qs(parsed.query)
            raw_path = query.get("path", [""])[0]
            folder = normalize_path(raw_path)
            if not is_allowed_path(folder) or not os.path.isdir(folder):
                return self.send_json({"error": "Ruta no válida o carpeta no accesible."}, status=400)

            entries = list_directory_entries(folder)
            return self.send_json({"folder": folder, "entries": entries, "workspace_root": WORKSPACE_ROOT})

        if parsed.path == "/api/results":
            query = urllib.parse.parse_qs(parsed.query)
            raw_path = query.get("folder", [""])[0]
            folder = normalize_path(raw_path)
            if not is_allowed_path(folder) or not os.path.isdir(folder):
                return self.send_json({"error": "Ruta no válida o carpeta no accesible."}, status=400)
            return self.send_json({"results": list_results(folder)})

        if parsed.path == "/api/download":
            query = urllib.parse.parse_qs(parsed.query)
            raw_path = query.get("folder", [""])[0]
            filename = query.get("file", [""])[0]
            folder = normalize_path(raw_path)
            if not is_allowed_path(folder) or not os.path.isdir(folder):
                return self.send_json({"error": "Ruta no válida o carpeta no accesible."}, status=400)
            parent_dir = os.path.dirname(folder)
        results_dir = os.path.join(parent_dir, "resultados")
        safe_name = os.path.basename(filename)
        file_path = os.path.abspath(os.path.join(results_dir, safe_name))
        if not file_path.startswith(results_dir) or not os.path.isfile(file_path):
            return self.send_json({"error": "Archivo no encontrado."}, status=404)
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f"attachment; filename=\"{os.path.basename(file_path)}\"")
            self.send_header("Content-Length", str(os.path.getsize(file_path)))
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/api/run-analysis":
            return super().do_POST()

        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            return self.send_json({"error": "JSON inválido."}, status=400)

        raw_folder = payload.get("folder", "")
        folder = normalize_path(raw_folder)
        if not is_allowed_path(folder) or not os.path.isdir(folder):
            return self.send_json({"error": "Ruta no válida o carpeta no accesible."}, status=400)

        window_seconds = float(payload.get("window", 20.0))
        band_freqs = payload.get("band_freqs", "63,125,2000")
        try:
            band_frequencies = tuple(float(x.strip()) for x in band_freqs.split(",") if x.strip())
        except ValueError:
            return self.send_json({"error": "Frecuencias de banda inválidas."}, status=400)

        try:
            pdf_path = analyze_folder_and_generate_report(
                folder,
                pdf_path=None,
                centers=None,
                band_frequencies=band_frequencies,
                window_seconds=window_seconds,
                hop_seconds=None,
                band_window_seconds=window_seconds,
                nperseg=1024,
                noverlap=None,
                cmap="viridis",
                p_ref=20e-6,
                verbose=True,
            )
        except Exception as exc:
            return self.send_json({"error": str(exc)}, status=500)

        return self.send_json({"success": True, "pdf_path": pdf_path, "results": list_results(folder)})

    def send_json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run(host="127.0.0.1", port=8000):
    os.chdir(WEB_ROOT)
    server = ThreadingHTTPServer((host, port), AudioWebHandler)
    print(f"Servidor web iniciado en http://{host}:{port}")
    print(f"Workspace root: {WORKSPACE_ROOT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
