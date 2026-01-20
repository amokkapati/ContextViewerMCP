#!/usr/bin/env python3
import json
import mimetypes
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import quote, unquote


class FileServerHandler(SimpleHTTPRequestHandler):
    base_dir = os.getcwd()

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self.get_html().encode("utf-8"))
            return

        if self.path.startswith("/api/files"):
            self.handle_files_api()
            return

        if self.path.startswith("/api/file-content"):
            self.handle_file_content_api()
            return

        super().do_GET()

    def do_POST(self):
        if self.path == "/api/confirm-selection":
            self.handle_confirm_selection()
            return

        self.send_response(404)
        self.end_headers()

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

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))

    def get_html(self):
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Context Viewer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, sans-serif; background: #1e1e1e; color: #e0e0e0; }
        .container { display: flex; height: 100vh; }
        .sidebar { width: 280px; flex: 0 0 280px; background: #252526; border-right: 1px solid #3e3e42; overflow-y: auto; padding: 10px; }
        .main { flex: 1; display: flex; flex-direction: column; }
        .toolbar { background: #2d2d30; padding: 10px; border-bottom: 1px solid #3e3e42; display: flex; gap: 10px; align-items: center; }
        .toolbar button { background: #007acc; color: white; border: none; padding: 8px 16px; cursor: pointer; border-radius: 4px; }
        .toolbar button:hover { background: #0098ff; }
        .toolbar button:disabled { background: #555; cursor: not-allowed; }
        .content { flex: 1; overflow: auto; padding: 20px; }
        .file-item { padding: 8px; cursor: pointer; margin: 2px 0; border-radius: 4px; display: flex; align-items: center; gap: 8px; }
        .file-item:hover { background: #3e3e42; }
        .file-item.active { background: #007acc; }
        .folder-icon::before { content: "📁"; margin-right: 4px; }
        .file-icon::before { content: "📄"; margin-right: 4px; }
        .breadcrumb { padding: 10px; background: #2d2d30; border-bottom: 1px solid #3e3e42; display: flex; gap: 5px; flex-wrap: wrap; }
        .breadcrumb span { cursor: pointer; padding: 5px 10px; border-radius: 4px; }
        .breadcrumb span:hover { background: #3e3e42; }
        .hint { padding: 8px 10px; color: #888; font-size: 12px; }
        pre { background: #1e1e1e; padding: 15px; border-radius: 4px; overflow-x: auto; }
        code { font-family: 'Consolas', 'Monaco', monospace; font-size: 14px; }
        .line { display: block; padding: 0 10px; }
        .line.selected { background: #264f78; }
        .file-preview { margin-top: 20px; }
        .file-name { font-weight: bold; padding: 10px 0; }
        .binary-file { text-align: center; color: #888; padding: 40px; }
        .confirmation-bar { background: #0e639c; padding: 15px; border-top: 1px solid #3e3e42; display: none; }
        .confirmation-bar.show { display: flex; gap: 10px; align-items: center; }
        .preview-frame { width: 100%; height: 80vh; border: none; background: #1e1e1e; }
        img.preview-image { max-width: 100%; height: auto; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div style="font-weight: bold; margin-bottom: 10px; color: #007acc;">Files</div>
            <div id="fileTree"></div>
        </div>
        <div class="main">
            <div class="breadcrumb" id="breadcrumb"></div>
            <div class="toolbar">
                <button id="confirmBtn" disabled>✓ Confirm Selection</button>
                <button id="clearBtn" onclick="clearSelection()">✕ Clear Selection</button>
                <span id="selectionInfo" style="flex: 1; color: #888;"></span>
            </div>
            <div class="hint">
                Click to toggle line, shift-click to select a range, drag to select a block.
                Double-click selects a paragraph. Option/Alt-click selects an indent block.
            </div>
            <div class="content" id="content">
                <div style="color: #888; text-align: center; margin-top: 40px;">Select a file to view</div>
            </div>
            <div class="confirmation-bar" id="confirmationBar">
                <span>Selection confirmed and printed to terminal</span>
            </div>
        </div>
    </div>

    <script>
        let currentPath = '';
        let currentFile = '';
        let currentFilePath = '';
        let currentFileLines = [];
        let selectedLines = new Set();
        let isDragging = false;
        let dragStartLine = null;
        let lastClickedLine = null;

        async function loadFiles(path = '') {
            try {
                const res = await fetch('/api/files' + (path ? '/' + path : '/'));
                const files = await res.json();
                const tree = document.getElementById('fileTree');
                tree.innerHTML = '';
                files.forEach(f => {
                    const div = document.createElement('div');
                    div.className = 'file-item';
                    div.innerHTML = `<span class="${f.is_dir ? 'folder-icon' : 'file-icon'}"></span>${f.name}`;
                    if (f.is_dir) {
                        div.onclick = () => loadFiles(f.path);
                    } else {
                        div.onclick = () => loadFile(f.path, f.name);
                    }
                    tree.appendChild(div);
                });
                updateBreadcrumb(path);
                currentPath = path;
            } catch (e) {
                console.error(e);
            }
        }

        async function loadFile(path, name) {
            try {
                const res = await fetch('/api/file-content/' + path);
                const data = await res.json();
                currentFile = name;
                currentFilePath = path;
                currentFileLines = (data.content || '').split('\\n');
                displayFile(data, name);
                selectedLines.clear();
                lastClickedLine = null;
                updateSelectionInfo();
            } catch (e) {
                console.error(e);
            }
        }

        function displayFile(data, name) {
            const content = document.getElementById('content');
            if (!data.is_text) {
                const mime = data.mime_type || '';
                if (mime.startsWith('image/')) {
                    content.innerHTML = `<div class="file-name">${name}</div><img class="preview-image" src="${data.file_url}" alt="${name}">`;
                } else if (mime === 'application/pdf') {
                    content.innerHTML = `<div class="file-name">${name}</div><iframe class="preview-frame" src="${data.file_url}"></iframe>`;
                } else {
                    content.innerHTML = `<div class="file-name">${name}</div><div class="binary-file">Preview not supported. <a href="${data.file_url}" style="color:#4aa3ff;">Download</a></div>`;
                }
                return;
            }

            if (!data.content) {
                content.innerHTML = `<div class="file-name">${name}</div><div class="binary-file">Empty file or unable to read</div>`;
                return;
            }

            const lines = data.content.split('\\n');
            let html = `<div class="file-preview"><div class="file-name">${name}</div><pre><code>`;
            lines.forEach((line, idx) => {
                const lineNum = idx + 1;
                const escapedLine = escapeHtml(line) || '&nbsp;';
                html += `<div class="line" data-line="${lineNum}" onclick="handleLineClick(${lineNum}, event)" style="cursor: pointer;">`;
                html += `<span style="color: #858585; margin-right: 10px; user-select: none;">${lineNum}</span>`;
                html += escapedLine;
                html += '</div>';
            });
            html += '</code></pre></div>';
            content.innerHTML = html;

            const lineEls = content.querySelectorAll('.line');
            lineEls.forEach(el => {
                el.addEventListener('mousedown', (e) => {
                    const lineNum = parseInt(el.dataset.line, 10);
                    if (Number.isNaN(lineNum)) return;
                    if (!e.shiftKey && !e.metaKey && !e.ctrlKey && !e.altKey) {
                        clearSelection();
                    }
                    isDragging = true;
                    dragStartLine = lineNum;
                    setRangeSelection(lineNum, lineNum, true);
                    e.preventDefault();
                });
                el.addEventListener('mouseover', () => {
                    if (!isDragging || dragStartLine === null) return;
                    const lineNum = parseInt(el.dataset.line, 10);
                    if (Number.isNaN(lineNum)) return;
                    setRangeSelection(dragStartLine, lineNum, true);
                });
            });
        }

        function handleLineClick(lineNum, event) {
            event.stopPropagation();
            if (event.altKey) {
                selectIndentBlock(lineNum);
                lastClickedLine = lineNum;
                return;
            }
            if (event.detail === 2) {
                selectParagraph(lineNum);
                lastClickedLine = lineNum;
                return;
            }
            if (event.shiftKey && lastClickedLine !== null) {
                setRangeSelection(lastClickedLine, lineNum, false);
            } else {
                toggleLine(lineNum);
            }
            lastClickedLine = lineNum;
            updateSelectionInfo();
        }

        function escapeHtml(text) {
            if (typeof hljs !== 'undefined' && hljs.utils && hljs.utils.escapeHtml) {
                return hljs.utils.escapeHtml(text);
            }
            return text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }

        function toggleLine(lineNum) {
            const lineEl = document.querySelector(`[data-line="${lineNum}"]`);
            if (!lineEl) return;
            if (selectedLines.has(lineNum)) {
                selectedLines.delete(lineNum);
                lineEl.classList.remove('selected');
            } else {
                selectedLines.add(lineNum);
                lineEl.classList.add('selected');
            }
        }

        function setRangeSelection(start, end, replace) {
            const from = Math.min(start, end);
            const to = Math.max(start, end);
            if (replace) {
                clearSelection();
            }
            for (let ln = from; ln <= to; ln++) {
                const lineEl = document.querySelector(`[data-line="${ln}"]`);
                if (lineEl) {
                    selectedLines.add(ln);
                    lineEl.classList.add('selected');
                }
            }
            updateSelectionInfo();
        }

        function selectParagraph(lineNum) {
            if (!currentFileLines.length) return;
            let start = lineNum;
            let end = lineNum;
            while (start > 1 && currentFileLines[start - 2].trim() !== '') {
                start -= 1;
            }
            while (end < currentFileLines.length && currentFileLines[end].trim() !== '') {
                end += 1;
            }
            setRangeSelection(start, end, true);
        }

        function selectIndentBlock(lineNum) {
            if (!currentFileLines.length) return;
            const lineText = currentFileLines[lineNum - 1] || '';
            if (lineText.trim() === '') return;
            const baseIndent = lineText.match(/^\\s*/)[0].length;
            let start = lineNum;
            let end = lineNum;
            while (start > 1) {
                const prev = currentFileLines[start - 2];
                if (prev.trim() === '') {
                    start -= 1;
                    continue;
                }
                const indent = prev.match(/^\\s*/)[0].length;
                if (indent < baseIndent) break;
                start -= 1;
            }
            while (end < currentFileLines.length) {
                const next = currentFileLines[end];
                if (next.trim() === '') {
                    end += 1;
                    continue;
                }
                const indent = next.match(/^\\s*/)[0].length;
                if (indent < baseIndent) break;
                end += 1;
            }
            setRangeSelection(start, end, true);
        }

        function updateSelectionInfo() {
            const btn = document.getElementById('confirmBtn');
            const info = document.getElementById('selectionInfo');
            if (selectedLines.size === 0) {
                btn.disabled = true;
                info.textContent = '';
            } else {
                btn.disabled = false;
                const sorted = Array.from(selectedLines).sort((a, b) => a - b);
                info.textContent = `${selectedLines.size} line(s) selected (${sorted[0]}-${sorted[sorted.length - 1]})`;
            }
        }

        function clearSelection() {
            selectedLines.forEach(ln => {
                const el = document.querySelector(`[data-line="${ln}"]`);
                if (el) el.classList.remove('selected');
            });
            selectedLines.clear();
            lastClickedLine = null;
            updateSelectionInfo();
        }


        async function confirmSelection() {
            if (selectedLines.size === 0) return;

            const lines = Array.from(selectedLines).sort((a, b) => a - b);
            const selectedText = lines.map(ln => currentFileLines[ln - 1] ?? '').join('\\n');

            await fetch('/api/confirm-selection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file_path: currentFilePath || currentFile,
                    start_line: lines[0],
                    end_line: lines[lines.length - 1],
                    selected_text: selectedText
                })
            });

            const bar = document.getElementById('confirmationBar');
            bar.classList.add('show');
            setTimeout(() => bar.classList.remove('show'), 3000);
        }

        function updateBreadcrumb(path) {
            const bc = document.getElementById('breadcrumb');
            bc.innerHTML = '<span onclick="loadFiles(\\'\\')" style="cursor: pointer;">Root</span>';
            if (path) {
                const parts = path.split('/');
                let acc = '';
                parts.forEach(p => {
                    acc += (acc ? '/' : '') + p;
                    bc.innerHTML += ` / <span onclick="loadFiles(\\'${acc}\\')" style="cursor: pointer;">${p}</span>`;
                });
            }
        }

        document.getElementById('confirmBtn').onclick = confirmSelection;
        document.addEventListener('mouseup', () => {
            isDragging = false;
            dragStartLine = null;
        });
        loadFiles();
    </script>
</body>
</html>"""


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    FileServerHandler.base_dir = os.getcwd()

    server = HTTPServer(("localhost", port), FileServerHandler)
    print(f"Server running at http://localhost:{port}")
    print(f"Serving files from: {FileServerHandler.base_dir}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
