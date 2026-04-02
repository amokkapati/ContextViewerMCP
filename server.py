#!/usr/bin/env python3
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import quote, unquote, urlparse, parse_qs


def _install_missing_latex_packages(error_output: str) -> list[str]:
    """Parse LaTeX error output for missing .sty files and install them via tlmgr."""
    missing = re.findall(r"File `([^']+\.sty)' not found", error_output)
    if not missing:
        return []
    packages = [name[:-4] for name in missing]  # strip .sty
    try:
        subprocess.run(
            ["tlmgr", "install"] + packages,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return packages


class FileServerHandler(SimpleHTTPRequestHandler):
    base_dir = os.getcwd()

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self.get_html().encode("utf-8"))
            return

        if self.path.startswith("/static/"):
            self.handle_static_file()
            return

        if self.path.startswith("/api/files"):
            self.handle_files_api()
            return

        if self.path.startswith("/api/file-content"):
            self.handle_file_content_api()
            return

        if self.path.startswith("/api/render-tex"):
            self.handle_render_tex_api()
            return

        if self.path == "/api/navigation-state":
            self.handle_navigation_state_api()
            return

        if self.path.startswith("/api/file-mtime"):
            self.handle_file_mtime_api()
            return

        if self.path.startswith("/api/annotations"):
            self.handle_annotations_api()
            return

        super().do_GET()

    def do_POST(self):
        if self.path == "/api/confirm-selection":
            self.handle_confirm_selection()
            return

        if self.path == "/api/navigation-executed":
            self.handle_navigation_executed()
            return

        if self.path == "/api/voice-spoken":
            self.handle_voice_spoken()
            return

        if self.path == "/api/delete-annotation":
            self.handle_delete_annotation()
            return

        self.send_response(404)
        self.end_headers()

    def handle_static_file(self):
        try:
            # Remove /static/ prefix and get the file path
            file_path = self.path.replace("/static/", "", 1)
            static_dir = os.path.join(os.path.dirname(__file__), "static")
            full_path = os.path.join(static_dir, file_path)
            full_path = os.path.normpath(full_path)

            # Security check: ensure we're serving from static dir
            if not full_path.startswith(static_dir):
                self.send_error(403)
                return

            if not os.path.isfile(full_path):
                self.send_error(404)
                return

            # Determine content type
            mime_type, _ = mimetypes.guess_type(full_path)
            if mime_type is None:
                mime_type = "application/octet-stream"

            # Read and serve the file
            with open(full_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-type", mime_type)
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception:
            self.send_error(500)

    def handle_files_api(self):
        try:
            path = unquote(self.path.replace("/api/files", "", 1)) or "/"
            full_path = os.path.join(self.base_dir, path.lstrip("/"))
            full_path = os.path.normpath(full_path)

            if not full_path.startswith(self.base_dir):
                self.send_error(403)
                return

            if not os.path.exists(full_path):
                self.send_error(404)
                return

            if os.path.isfile(full_path):
                self.send_error(400)
                return

            items = []
            for item in sorted(os.listdir(full_path)):
                if item.startswith("."):
                    continue
                item_path = os.path.join(full_path, item)
                rel_path = os.path.relpath(item_path, self.base_dir)
                is_dir = os.path.isdir(item_path)
                items.append(
                    {
                        "name": item,
                        "path": quote(rel_path),
                        "is_dir": is_dir,
                        "size": os.path.getsize(item_path) if not is_dir else 0,
                    }
                )

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(items).encode("utf-8"))
        except Exception:
            self.send_error(500)

    def handle_file_content_api(self):
        try:
            path = unquote(self.path.replace("/api/file-content", "", 1)).lstrip("/")
            full_path = os.path.join(self.base_dir, path)
            full_path = os.path.normpath(full_path)

            if not full_path.startswith(self.base_dir):
                self.send_error(403)
                return

            if not os.path.isfile(full_path):
                self.send_error(404)
                return

            mime_type, _ = mimetypes.guess_type(full_path)
            is_text = False
            content = None
            with open(full_path, "rb") as f:
                raw = f.read()
            if b"\x00" not in raw:
                content = raw.decode("utf-8", errors="replace")
                is_text = True

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "content": content,
                        "mime_type": mime_type,
                        "is_text": is_text,
                        "file_url": f"/{quote(path)}",
                    }
                ).encode("utf-8")
            )
        except Exception:
            self.send_error(500)

    def handle_render_tex_api(self):
        try:
            path = unquote(self.path.replace("/api/render-tex", "", 1)).lstrip("/")
            full_path = os.path.join(self.base_dir, path)
            full_path = os.path.normpath(full_path)

            if not full_path.startswith(self.base_dir):
                self.send_json_response({"success": False, "error": "Access denied"})
                return

            if not os.path.isfile(full_path) or not full_path.endswith(".tex"):
                self.send_json_response({"success": False, "error": "Invalid .tex file"})
                return

            tex_dir = os.path.dirname(full_path)
            tex_filename = os.path.basename(full_path)
            pdf_filename = tex_filename.rsplit(".", 1)[0] + ".pdf"
            pdf_path = os.path.join(tex_dir, pdf_filename)

            def _run_pdflatex():
                return subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", tex_filename],
                    cwd=tex_dir,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

            result = _run_pdflatex()

            # If packages are missing, install them and retry once
            if result.returncode != 0:
                combined = result.stderr + result.stdout
                installed = _install_missing_latex_packages(combined)
                if installed:
                    result = _run_pdflatex()

            # Clean up auxiliary files
            for ext in [".aux", ".log"]:
                aux_file = os.path.join(tex_dir, tex_filename.rsplit(".", 1)[0] + ext)
                if os.path.exists(aux_file):
                    os.remove(aux_file)

            if result.returncode != 0 or not os.path.exists(pdf_path):
                # Show the *end* of the LaTeX log, which usually contains the
                # actual error message, instead of only the banner.
                error_msg = result.stderr or result.stdout or "pdflatex compilation failed"
                tail = error_msg[-800:]  # keep last ~800 chars for context
                self.send_json_response({"success": False, "error": tail})
                return

            rel_pdf_path = os.path.relpath(pdf_path, self.base_dir)
            self.send_json_response({
                "success": True,
                "pdf_url": "/" + quote(rel_pdf_path),
            })
        except subprocess.TimeoutExpired:
            self.send_json_response({"success": False, "error": "Compilation timed out"})
        except FileNotFoundError:
            self.send_json_response({"success": False, "error": "pdflatex not found. Please install LaTeX."})
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)})

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def handle_confirm_selection(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode("utf-8"))

        print("\n" + "=" * 60)
        print("SELECTION CONFIRMED")
        print("=" * 60)
        print(f"File: {data.get('file_path', '')}")
        print(f"Lines: {data.get('start_line', '')}-{data.get('end_line', '')}")
        print("-" * 60)
        print(data.get("selected_text", ""))
        print("=" * 60 + "\n")

        # Save selection to state file for MCP server
        import time
        state_file = Path.home() / ".context-viewer-state.json"
        try:
            existing_state = {}
            if state_file.exists():
                with open(state_file, "r") as f:
                    existing_state = json.load(f)

            existing_state["selection"] = {
                "file_path": data.get("file_path", ""),
                "start_line": data.get("start_line", 0),
                "end_line": data.get("end_line", 0),
                "selected_text": data.get("selected_text", ""),
                "voice_query": data.get("voice_query", ""),
                "timestamp": time.time(),
            }

            with open(state_file, "w") as f:
                json.dump(existing_state, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save selection state: {e}")

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))

    def handle_file_mtime_api(self):
        try:
            path = unquote(self.path.replace("/api/file-mtime", "", 1)).lstrip("/")
            full_path = os.path.join(self.base_dir, path)
            full_path = os.path.normpath(full_path)
            if not full_path.startswith(self.base_dir):
                self.send_error(403)
                return
            if not os.path.isfile(full_path):
                self.send_error(404)
                return
            self.send_json_response({"mtime": os.path.getmtime(full_path)})
        except Exception:
            self.send_error(500)

    def handle_navigation_state_api(self):
        """Return current navigation state from state file."""
        state_file = Path.home() / ".context-viewer-state.json"
        try:
            if state_file.exists():
                with open(state_file, "r") as f:
                    state = json.load(f)
            else:
                state = {}

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(state).encode("utf-8"))
        except Exception as e:
            print(f"Error reading navigation state: {e}")
            self.send_json_response({})

    def handle_navigation_executed(self):
        """Mark navigation command as executed."""
        content_length = int(self.headers.get("Content-Length", "0"))
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode("utf-8"))

        state_file = Path.home() / ".context-viewer-state.json"
        try:
            existing_state = {}
            if state_file.exists():
                with open(state_file, "r") as f:
                    existing_state = json.load(f)

            # Mark navigation as executed if timestamps match
            if "navigation" in existing_state:
                if existing_state["navigation"].get("timestamp") == data.get("timestamp"):
                    existing_state["navigation"]["executed"] = True

                    with open(state_file, "w") as f:
                        json.dump(existing_state, f, indent=2)

                    print(f"\nNavigation executed: {existing_state['navigation']['command']} to {existing_state['navigation']['file_path']}\n")

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
        except Exception as e:
            print(f"Error marking navigation as executed: {e}")
            self.send_response(500)
            self.end_headers()

    def handle_voice_spoken(self):
        """Mark voice_response as spoken so the browser doesn't replay it."""
        content_length = int(self.headers.get("Content-Length", "0"))
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode("utf-8"))

        state_file = Path.home() / ".context-viewer-state.json"
        try:
            existing_state = {}
            if state_file.exists():
                with open(state_file, "r") as f:
                    existing_state = json.load(f)

            if "voice_response" in existing_state:
                if existing_state["voice_response"].get("timestamp") == data.get("timestamp"):
                    existing_state["voice_response"]["spoken"] = True
                    with open(state_file, "w") as f:
                        json.dump(existing_state, f, indent=2)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
        except Exception as e:
            print(f"Error marking voice response as spoken: {e}")
            self.send_response(500)
            self.end_headers()

    def handle_annotations_api(self):
        """Return annotations, optionally filtered by file path."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        file_filter = params.get("file", [None])[0]

        state_file = Path.home() / ".context-viewer-state.json"
        try:
            state = {}
            if state_file.exists():
                with open(state_file, "r") as f:
                    state = json.load(f)

            annotations = state.get("annotations", [])

            if file_filter:
                file_filter_decoded = unquote(file_filter)
                annotations = [
                    a for a in annotations
                    if unquote(a.get("file_path", "")) == file_filter_decoded
                ]

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(annotations).encode("utf-8"))
        except Exception:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b"[]")

    def handle_delete_annotation(self):
        """Delete an annotation by id."""
        content_length = int(self.headers.get("Content-Length", "0"))
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode("utf-8"))
        annotation_id = data.get("id")

        state_file = Path.home() / ".context-viewer-state.json"
        try:
            existing_state = {}
            if state_file.exists():
                with open(state_file, "r") as f:
                    existing_state = json.load(f)

            annotations = existing_state.get("annotations", [])
            existing_state["annotations"] = [
                a for a in annotations if a.get("id") != annotation_id
            ]

            with open(state_file, "w") as f:
                json.dump(existing_state, f, indent=2)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
        except Exception as e:
            print(f"Error deleting annotation: {e}")
            self.send_response(500)
            self.end_headers()

    def get_html(self):
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        index_path = os.path.join(static_dir, "index.html")
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "<html><body><h1>Error: index.html not found in static directory</h1></body></html>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("port", nargs="?", type=int, default=8000)
    parser.add_argument("--serve-dir", default=os.getcwd())
    args = parser.parse_args()

    port = args.port
    FileServerHandler.base_dir = os.path.abspath(args.serve_dir)

    server = HTTPServer(("localhost", port), FileServerHandler)
    print(f"Server running at http://localhost:{port}")
    print(f"Serving files from: {FileServerHandler.base_dir}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
