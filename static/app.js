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
        currentFileLines = (data.content || '').split('\n');
        displayFile(data, name);
        selectedLines.clear();
        lastClickedLine = null;
        updateSelectionInfo();
    } catch (e) {
        console.error(e);
    }
}

let currentTexView = 'source';

function displayFile(data, name) {
    const content = document.getElementById('content');
    const isTexFile = name.toLowerCase().endsWith('.tex');

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

    currentTexView = 'source';
    const lines = data.content.split('\n');
    let html = '';

    if (isTexFile) {
        html += `<div class="tex-toolbar">
            <button id="texSourceBtn" class="active" onclick="showTexSource()">Source</button>
            <button id="texRenderBtn" onclick="renderTexFile()">Render PDF</button>
        </div>`;
    }

    html += `<div class="file-preview"><div class="file-name">${name}</div><div id="texContent"><pre><code>`;
    lines.forEach((line, idx) => {
        const lineNum = idx + 1;
        const escapedLine = escapeHtml(line) || '&nbsp;';
        html += `<div class="line" data-line="${lineNum}" onclick="handleLineClick(${lineNum}, event)" style="cursor: pointer;">`;
        html += `<span style="color: #858585; margin-right: 10px; user-select: none;">${lineNum}</span>`;
        html += escapedLine;
        html += '</div>';
    });
    html += '</code></pre></div></div>';
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
    const baseIndent = lineText.match(/^\s*/)[0].length;
    let start = lineNum;
    let end = lineNum;
    while (start > 1) {
        const prev = currentFileLines[start - 2];
        if (prev.trim() === '') {
            start -= 1;
            continue;
        }
        const indent = prev.match(/^\s*/)[0].length;
        if (indent < baseIndent) break;
        start -= 1;
    }
    while (end < currentFileLines.length) {
        const next = currentFileLines[end];
        if (next.trim() === '') {
            end += 1;
            continue;
        }
        const indent = next.match(/^\s*/)[0].length;
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

function showTexSource() {
    if (currentTexView === 'source') return;
    currentTexView = 'source';
    document.getElementById('texSourceBtn').classList.add('active');
    document.getElementById('texRenderBtn').classList.remove('active');
    loadFile(currentFilePath, currentFile);
}

async function renderTexFile() {
    if (currentTexView === 'pdf') return;
    currentTexView = 'pdf';
    document.getElementById('texSourceBtn').classList.remove('active');
    document.getElementById('texRenderBtn').classList.add('active');

    const texContent = document.getElementById('texContent');
    texContent.innerHTML = '<div class="tex-loading">Compiling LaTeX...</div>';

    try {
        const res = await fetch('/api/render-tex/' + currentFilePath);
        const data = await res.json();

        if (data.success) {
            texContent.innerHTML = `<iframe class="preview-frame" src="${data.pdf_url}"></iframe>`;
        } else {
            texContent.innerHTML = `<div class="tex-error">Error compiling LaTeX:\n\n${escapeHtml(data.error)}</div>`;
        }
    } catch (e) {
        texContent.innerHTML = `<div class="tex-error">Error: ${escapeHtml(e.message)}</div>`;
    }
}

async function confirmSelection() {
    if (selectedLines.size === 0) return;

    const lines = Array.from(selectedLines).sort((a, b) => a - b);
    const selectedText = lines.map(ln => currentFileLines[ln - 1] ?? '').join('\n');

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
    bc.innerHTML = '<span onclick="loadFiles(\'\')" style="cursor: pointer;">Root</span>';
    if (path) {
        const parts = path.split('/');
        let acc = '';
        parts.forEach(p => {
            acc += (acc ? '/' : '') + p;
            bc.innerHTML += ` / <span onclick="loadFiles('${acc}')" style="cursor: pointer;">${p}</span>`;
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('confirmBtn').onclick = confirmSelection;
    document.addEventListener('mouseup', () => {
        isDragging = false;
        dragStartLine = null;
    });
    loadFiles();
});
