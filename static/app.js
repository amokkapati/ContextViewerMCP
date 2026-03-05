let currentPath = '';
let currentFile = '';
let currentFilePath = '';
let currentFileLines = [];
let selectedLines = new Set();
let isDragging = false;
let dragStartLine = null;
let lastClickedLine = null;
let activeTreePath = '';
let activeTreeIsDir = false;
let lastNavigationTimestamp = 0;
let navigationPollInterval = null;
let currentIsPdf = false;

function getFileBadge(name, isDir) {
    if (isDir) {
        return { label: 'DIR', color: '#3a3a40', text: '#f7f7f8' };
    }
    const ext = (name.split('.').pop() || '').toLowerCase();
    const map = {
        js: { label: 'JS', color: '#f7df1e', text: '#111' },
        jsx: { label: 'JSX', color: '#61dafb', text: '#0b233a' },
        ts: { label: 'TS', color: '#3178c6', text: '#f5f7fb' },
        tsx:{ label: 'TSX', color: '#3178c6', text: '#f5f7fb' },
        py: { label: 'PY', color: '#3572a5', text: '#f8fbff' },
        rb: { label: 'RB', color: '#cc342d', text: '#fff' },
        java:{ label: 'JAVA', color: '#ed8b00', text: '#111' },
        go: { label: 'GO', color: '#00acd7', text: '#0b1c24' },
        rs: { label: 'RS', color: '#dea584', text: '#1e120a' },
        php:{ label: 'PHP', color: '#8892bf', text: '#0d0d15' },
        cs: { label: 'CS', color: '#9b4f96', text: '#fff' },
        cpp:{ label: 'C++', color: '#00599c', text: '#e9f2ff' },
        c:  { label: 'C', color: '#00599c', text: '#e9f2ff' },
        h:  { label: 'H', color: '#6a737d', text: '#fff' },
        html:{ label: 'HTML', color: '#e44d26', text: '#fff' },
        css:{ label: 'CSS', color: '#264de4', text: '#fff' },
        scss:{ label: 'SCSS', color: '#c6538c', text: '#fff' },
        json:{ label: 'JSON', color: '#f0ad4e', text: '#111' },
        yml:{ label: 'YML', color: '#6f42c1', text: '#fff' },
        yaml:{ label: 'YML', color: '#6f42c1', text: '#fff' },
        md: { label: 'MD', color: '#4f4f4f', text: '#fff' },
        txt:{ label: 'TXT', color: '#4f4f4f', text: '#fff' },
        sh: { label: 'SH', color: '#3c873a', text: '#f5fff4' },
        bash:{ label: 'SH', color: '#3c873a', text: '#f5fff4' },
        zsh:{ label: 'SH', color: '#3c873a', text: '#f5fff4' },
        sql:{ label: 'SQL', color: '#336791', text: '#f8fbff' },
        pdf:{ label: 'PDF', color: '#d32f2f', text: '#fff' },
        png:{ label: 'IMG', color: '#607d8b', text: '#fff' },
        jpg:{ label: 'IMG', color: '#607d8b', text: '#fff' },
        jpeg:{ label: 'IMG', color: '#607d8b', text: '#fff' },
        gif:{ label: 'IMG', color: '#607d8b', text: '#fff' },
        svg:{ label: 'SVG', color: '#ffb300', text: '#111' },
        tex:{ label: 'TEX', color: '#5c6bc0', text: '#f8f9ff' },
    };
    return map[ext] || { label: ext ? ext.toUpperCase().slice(0,4) : 'FILE', color: '#444', text: '#fff' };
}

function setActiveTreeItem(path, isDir) {
    activeTreePath = path || '';
    activeTreeIsDir = !!isDir;

    document.querySelectorAll('#fileTree .file-item').forEach(el => {
        const elPath = el.dataset.path || '';
        const elIsDir = el.dataset.isDir === '1';
        const isActive = elPath === activeTreePath && elIsDir === activeTreeIsDir;
        el.classList.toggle('active', isActive);
        el.classList.toggle('open', isActive && elIsDir);
    });
}

async function loadFiles(path = '') {
    try {
        const res = await fetch('/api/files' + (path ? '/' + path : '/'));
        const files = await res.json();
        const tree = document.getElementById('fileTree');
        tree.innerHTML = '';
        files.forEach(f => {
            const badge = getFileBadge(f.name, f.is_dir);
            const div = document.createElement('div');
            div.className = 'file-item';
            div.dataset.path = f.path;
            div.dataset.isDir = f.is_dir ? '1' : '0';
            if (f.is_dir) {
                div.innerHTML = `<span class="folder-icon">▸</span><span class="name">${f.name}</span>`;
            } else {
                div.innerHTML = `<span class="file-badge" style="background:${badge.color};color:${badge.text};border:1px solid ${badge.color}">${badge.label}</span><span class="name">${f.name}</span>`;
            }
            if (f.is_dir) {
                div.onclick = () => {
                    setActiveTreeItem(f.path, true);
                    loadFiles(f.path);
                };
            } else {
                div.onclick = () => {
                    setActiveTreeItem(f.path, false);
                    loadFile(f.path, f.name);
                };
            }
            tree.appendChild(div);
        });
        updateBreadcrumb(path);
        currentPath = path;

        if (path) setActiveTreeItem(path, true);
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
let pdfJsLoaded = false;

async function ensurePdfJs() {
    if (pdfJsLoaded) return;
    await new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
    pdfjsLib.GlobalWorkerOptions.workerSrc =
        'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    pdfJsLoaded = true;
}

function getLanguageFromFilename(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const langMap = {
        'js': 'javascript',
        'jsx': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        'py': 'python',
        'rb': 'ruby',
        'java': 'java',
        'c': 'c',
        'cpp': 'cpp',
        'cc': 'cpp',
        'cxx': 'cpp',
        'h': 'c',
        'hpp': 'cpp',
        'cs': 'csharp',
        'php': 'php',
        'go': 'go',
        'rs': 'rust',
        'swift': 'swift',
        'kt': 'kotlin',
        'scala': 'scala',
        'sh': 'bash',
        'bash': 'bash',
        'zsh': 'bash',
        'fish': 'bash',
        'ps1': 'powershell',
        'sql': 'sql',
        'html': 'xml',
        'htm': 'xml',
        'xml': 'xml',
        'css': 'css',
        'scss': 'scss',
        'sass': 'sass',
        'less': 'less',
        'json': 'json',
        'yaml': 'yaml',
        'yml': 'yaml',
        'toml': 'toml',
        'ini': 'ini',
        'md': 'markdown',
        'markdown': 'markdown',
        'tex': 'latex',
        'latex': 'latex',
        'r': 'r',
        'R': 'r',
        'm': 'objectivec',
        'mm': 'objectivec',
        'pl': 'perl',
        'pm': 'perl',
        'lua': 'lua',
        'vim': 'vim',
        'dockerfile': 'dockerfile',
        'makefile': 'makefile',
        'mk': 'makefile',
        'cmake': 'cmake',
        'diff': 'diff',
        'patch': 'diff',
    };
    return langMap[ext] || null;
}

function displayFile(data, name) {
    const content = document.getElementById('content');
    const isTexFile = name.toLowerCase().endsWith('.tex');
    currentIsPdf = false;

    if (!data.is_text) {
        const mime = data.mime_type || '';
        if (mime.startsWith('image/')) {
            content.innerHTML = `<div class="file-name">${name}</div><img class="preview-image" src="${data.file_url}" alt="${name}">`;
        } else if (mime === 'application/pdf') {
            displayPdf(name, data.file_url);
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

    const language = getLanguageFromFilename(name);
    let highlightedCode = '';

    if (typeof hljs !== 'undefined') {
        try {
            if (language) {
                const highlighted = hljs.highlight(data.content, { language: language });
                highlightedCode = highlighted.value;
            } else {
                const highlighted = hljs.highlightAuto(data.content);
                highlightedCode = highlighted.value;
            }
        } catch (e) {
            try {
                const highlighted = hljs.highlightAuto(data.content);
                highlightedCode = highlighted.value;
            } catch (e2) {
                highlightedCode = escapeHtml(data.content);
            }
        }
    } else {
        highlightedCode = escapeHtml(data.content);
    }

    const highlightedLines = highlightedCode.split('\n');

    html += `<div class="file-preview"><div class="file-name">${name}</div><div id="texContent" style="background: #151515; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 10px 30px rgba(0,0,0,0.4); overflow: hidden;">`;
    highlightedLines.forEach((line, idx) => {
        const lineNum = idx + 1;
        const displayLine = line || '';
        html += `<div class="line" data-line="${lineNum}" onclick="handleLineClick(${lineNum}, event)" style="cursor: pointer;"><span class="line-number">${lineNum}</span><span class="line-content">${displayLine}</span></div>`;
    });
    html += '</div></div>';
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

// ─── PDF viewer ───────────────────────────────────────────────────────────────

async function displayPdf(name, fileUrl) {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="file-name">${name}</div>
        <div class="tex-toolbar">
            <button id="pdfPreviewBtn" class="active" onclick="showPdfPreview()">Preview</button>
            <button id="pdfLinesBtn" onclick="showPdfLines()">Select Lines</button>
        </div>
        <div id="pdfBody"></div>`;

    // stash url/name for tab switching
    content.dataset.pdfUrl  = fileUrl;
    content.dataset.pdfName = name;

    _renderPdfIframe(fileUrl);
}

function showPdfPreview() {
    const content = document.getElementById('content');
    document.getElementById('pdfPreviewBtn').classList.add('active');
    document.getElementById('pdfLinesBtn').classList.remove('active');
    clearSelection();
    const sel = window.getSelection ? window.getSelection() : null;
    if (sel && sel.removeAllRanges) sel.removeAllRanges();
    currentIsPdf = false;
    _renderPdfIframe(content.dataset.pdfUrl);
}

async function showPdfLines() {
    const content = document.getElementById('content');
    document.getElementById('pdfLinesBtn').classList.add('active');
    document.getElementById('pdfPreviewBtn').classList.remove('active');

    const pdfBody = document.getElementById('pdfBody');
    pdfBody.innerHTML = '<div class="tex-loading">Rendering PDF… (text-selectable)</div>';

    try {
        await ensurePdfJs();
        const pdf = await pdfjsLib.getDocument(content.dataset.pdfUrl).promise;

        pdfBody.innerHTML = '';

        const scale = 1.5;

        for (let p = 1; p <= pdf.numPages; p++) {
            const page = await pdf.getPage(p);
            const viewport = page.getViewport({ scale });

            const pageWrapper = document.createElement('div');
            pageWrapper.className = 'pdf-page-wrapper';
            pageWrapper.style.width = viewport.width + 'px';
            pageWrapper.style.height = viewport.height + 'px';

            const canvas = document.createElement('canvas');
            canvas.className = 'pdf-canvas';
            canvas.width = viewport.width;
            canvas.height = viewport.height;

            const textLayer = document.createElement('div');
            textLayer.className = 'pdf-text-layer';
            textLayer.style.width = viewport.width + 'px';
            textLayer.style.height = viewport.height + 'px';

            pageWrapper.appendChild(canvas);
            pageWrapper.appendChild(textLayer);
            pdfBody.appendChild(pageWrapper);

            const ctx = canvas.getContext('2d');
            await page.render({ canvasContext: ctx, viewport }).promise;

            const textContent = await page.getTextContent();
            // Use pdf.js text layer helper if available to create a proper
            // selectable text layer that tracks the rendered PDF.
            if (pdfjsLib.renderTextLayer) {
                pdfjsLib.renderTextLayer({
                    textContent,
                    container: textLayer,
                    viewport,
                    textDivs: [],
                });
            } else {
                // Fallback: simple paragraphs, still selectable but without
                // precise positioning.
                textContent.items.forEach(item => {
                    if (!item.str || !item.str.trim()) return;
                    const span = document.createElement('span');
                    span.textContent = item.str + ' ';
                    textLayer.appendChild(span);
                });
            }
        }

        currentIsPdf = true;
        selectedLines.clear();
        lastClickedLine = null;
        const btn  = document.getElementById('confirmBtn');
        const info = document.getElementById('selectionInfo');
        if (btn) btn.disabled = true;
        if (info) info.textContent = '';

    } catch (e) {
        pdfBody.innerHTML = `<div class="tex-error">Failed to render PDF: ${escapeHtml(e.message)}</div>`;
    }
}


function _renderPdfIframe(url) {
    document.getElementById('pdfBody').innerHTML =
        `<iframe class="preview-frame" src="${url}"></iframe>`;
}

// ─── Line interaction ─────────────────────────────────────────────────────────

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
    const to   = Math.max(start, end);
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
    let end   = lineNum;
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
    let end   = lineNum;
    while (start > 1) {
        const prev = currentFileLines[start - 2];
        if (prev.trim() === '') { start -= 1; continue; }
        if (prev.match(/^\s*/)[0].length < baseIndent) break;
        start -= 1;
    }
    while (end < currentFileLines.length) {
        const next = currentFileLines[end];
        if (next.trim() === '') { end += 1; continue; }
        if (next.match(/^\s*/)[0].length < baseIndent) break;
        end += 1;
    }
    setRangeSelection(start, end, true);
}

function updateSelectionInfo() {
    const btn  = document.getElementById('confirmBtn');
    const info = document.getElementById('selectionInfo');
    if (selectedLines.size === 0) {
        btn.disabled    = true;
        info.textContent = '';
    } else {
        btn.disabled    = false;
        const sorted    = Array.from(selectedLines).sort((a, b) => a - b);
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

// ─── LaTeX viewer ─────────────────────────────────────────────────────────────

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
        const res  = await fetch('/api/render-tex/' + currentFilePath);
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

// ─── Confirm / send selection ─────────────────────────────────────────────────

async function confirmSelection() {
    const isPdf = currentIsPdf;
    let selectedText = '';
    let startLine = null;
    let endLine = null;

    if (isPdf) {
        // Use the browser's native text selection for PDFs rendered with a
        // text layer. This gives the most natural selection UX.
        const sel = window.getSelection ? window.getSelection() : null;
        selectedText = sel ? sel.toString() : '';
        if (!selectedText.trim()) return;
    } else {
        if (selectedLines.size === 0) return;
        const lines = Array.from(selectedLines).sort((a, b) => a - b);
        selectedText = lines.map(ln => currentFileLines[ln - 1] ?? '').join('\n');
        startLine = lines[0];
        endLine = lines[lines.length - 1];
    }

    const payload = {
        file_path:     currentFilePath || currentFile,
        selected_text: selectedText,
        start_line:    startLine,
        end_line:      endLine,
    };

    await fetch('/api/confirm-selection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    // Temporary debug: show confirmed text in the UI
    try {
        const dbg = document.getElementById('debugSelection');
        if (dbg) {
            dbg.textContent = selectedText || '';
        }
        console.log('[ContextViewer] Confirmed selection:', {
            file: payload.file_path,
            start_line: payload.start_line,
            end_line: payload.end_line,
            text_preview: (selectedText || '').slice(0, 200)
        });
    } catch (e) {
        // Debug-only; ignore errors
    }

    const bar = document.getElementById('confirmationBar');
    bar.classList.add('show');
    setTimeout(() => bar.classList.remove('show'), 3000);
}

// ─── Breadcrumb ───────────────────────────────────────────────────────────────

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

// ─── Bidirectional navigation polling ────────────────────────────────────────

async function pollNavigationCommands() {
    try {
        const res   = await fetch('/api/navigation-state');
        const state = await res.json();

        if (state.navigation && !state.navigation.executed && state.navigation.timestamp > lastNavigationTimestamp) {
            lastNavigationTimestamp = state.navigation.timestamp;
            await executeNavigationCommand(state.navigation);
        }
    } catch (e) {
        console.error('Navigation polling error:', e);
    }
}

async function executeNavigationCommand(nav) {
    console.log('Executing navigation command:', nav);

    const filePath = nav.file_path;
    const fileName = filePath.split('/').pop();

    if (currentFilePath !== filePath) {
        await loadFile(filePath, fileName);
        await new Promise(resolve => setTimeout(resolve, 100));
    }

    let targetLine = null;

    switch (nav.command) {
        case 'goto_line':
            targetLine = nav.target;
            break;
        case 'search_text':
            targetLine = findTextInFile(nav.target);
            break;
        case 'find_function':
            targetLine = findFunctionInFile(nav.target);
            break;
    }

    if (targetLine) {
        navigateToLine(targetLine);

        await fetch('/api/navigation-executed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ timestamp: nav.timestamp })
        });
    } else {
        console.warn('Navigation target not found:', nav);
    }
}

function navigateToLine(lineNum) {
    const lineEl = document.querySelector(`[data-line="${lineNum}"]`);
    if (!lineEl) return;

    clearSelection();

    selectedLines.add(lineNum);
    lineEl.classList.add('selected');
    lineEl.scrollIntoView({ behavior: 'smooth', block: 'center' });

    lineEl.style.animation = 'none';
    setTimeout(() => {
        lineEl.style.animation = 'flash 1s ease-in-out';
    }, 10);

    updateSelectionInfo();
}

function findTextInFile(searchText) {
    const searchLower = searchText.toLowerCase();
    for (let i = 0; i < currentFileLines.length; i++) {
        if (currentFileLines[i].toLowerCase().includes(searchLower)) {
            return i + 1;
        }
    }
    return null;
}

function findFunctionInFile(funcName) {
    const patterns = [
        new RegExp(`^\\s*def\\s+${funcName}\\s*\\(`, 'i'),
        new RegExp(`^\\s*class\\s+${funcName}\\s*[(:{\n]`, 'i'),
        new RegExp(`^\\s*function\\s+${funcName}\\s*\\(`, 'i'),
        new RegExp(`^\\s*const\\s+${funcName}\\s*=.*=>`, 'i'),
        new RegExp(`^\\s*async\\s+function\\s+${funcName}\\s*\\(`, 'i'),
    ];

    for (let i = 0; i < currentFileLines.length; i++) {
        const line = currentFileLines[i];
        for (const pattern of patterns) {
            if (pattern.test(line)) {
                return i + 1;
            }
        }
    }
    return null;
}

function startNavigationPolling() {
    if (navigationPollInterval) return;
    navigationPollInterval = setInterval(pollNavigationCommands, 1000);
}

function stopNavigationPolling() {
    if (navigationPollInterval) {
        clearInterval(navigationPollInterval);
        navigationPollInterval = null;
    }
}

// ─── Init ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('confirmBtn').onclick = confirmSelection;
    document.addEventListener('mouseup', () => {
        isDragging    = false;
        dragStartLine = null;
    });
    // For PDFs, watch native text selection so we can enable/disable the
    // confirm button when the user highlights text on the page.
    document.addEventListener('selectionchange', () => {
        if (!currentIsPdf) return;
        const btn  = document.getElementById('confirmBtn');
        const info = document.getElementById('selectionInfo');
        if (!btn || !info) return;
        const sel = window.getSelection ? window.getSelection() : null;
        const hasText = sel && sel.toString().trim().length > 0;
        btn.disabled = !hasText;
        info.textContent = hasText
            ? 'PDF text selected (no line numbers available)'
            : '';
    });
    loadFiles();
    startNavigationPolling();
});