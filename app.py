import json
import random
import subprocess
import os
from flask import Flask, request, jsonify, render_template_string
from curl_cffi import requests as crequests

app = Flask(__name__)

PROXY_LIST = [
    "http://pilcikkg:esenmppky29k@198.23.243.226:6361",
    "http://pilcikkg:esenmppky29k@38.154.185.97:6370",
    "http://pilcikkg:esenmppky29k@191.96.254.138:6185"
]

proxy_index = 0

def get_next_proxy():
    global proxy_index
    proxy = PROXY_LIST[proxy_index]
    proxy_index = (proxy_index + 1) % len(PROXY_LIST)
    return proxy

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cờ Vua AI & Render Terminal</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/chessboard-js/1.0.0/chessboard-1.0.0.min.css">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
body { background: #0f172a; color: #f8fafc; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 10px; }
.container { max-width: 480px; width: 100%; display: flex; flex-direction: column; gap: 12px; }
.card { background: #1e293b; border-radius: 12px; padding: 12px; border: 1px solid #334155; }
#board { width: 100%; aspect-ratio: 1/1; margin: 0 auto; }
h1 { font-size: 1.1rem; text-align: center; color: #38bdf8; margin-bottom: 8px; }
.form-group { margin-bottom: 8px; }
label { display: block; font-size: 0.75rem; margin-bottom: 2px; color: #94a3b8; }
input, select, button { width: 100%; padding: 7px 10px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #fff; font-size: 0.8rem; }
.row { display: flex; gap: 6px; }
button { background: #0284c7; font-weight: bold; cursor: pointer; margin-top: 4px; border: none; }
button:hover { opacity: 0.9; }
.btn-success { background: #16a34a !important; }
.btn-danger { background: #dc2626 !important; }
.btn-secondary { background: #475569 !important; font-size: 0.75rem; padding: 5px 8px; margin-top: 4px; }
.status-box { margin-top: 6px; padding: 6px; background: #0f172a; border-radius: 6px; border: 1px solid #334155; font-size: 0.75rem; font-weight: bold; color: #38bdf8; }
.log-header { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; margin-bottom: 2px; }
.log-header span { font-size: 0.75rem; font-weight: bold; color: #94a3b8; }
.log-box { height: 140px; overflow-y: auto; background: #020617; border-radius: 6px; border: 1px solid #334155; padding: 6px; font-family: 'Courier New', Courier, monospace; font-size: 0.7rem; color: #38bdf8; white-space: pre-wrap; word-break: break-all; }
.highlight-square { background-color: rgba(255, 255, 0, 0.4) !important; }
.highlight-hint { background: radial-gradient(circle, rgba(16, 185, 129, 0.7) 28%, transparent 28%) !important; }

/* Tabs style */
.tabs { display: flex; gap: 4px; margin-bottom: 10px; }
.tab-btn { flex: 1; padding: 8px; background: #334155; border: none; border-radius: 6px; color: #cbd5e1; cursor: pointer; font-size: 0.8rem; font-weight: bold; }
.tab-btn.active { background: #0284c7; color: #fff; }
.tab-content { display: none; }
.tab-content.active { display: block; }

/* AI vs AI configs */
.ai-vs-ai-panel { background: #0f172a; border: 1px dashed #334155; padding: 8px; border-radius: 6px; margin-top: 8px; display: none; }
.ai-vs-ai-panel h3 { font-size: 0.8rem; color: #38bdf8; margin-bottom: 6px; }

/* Terminal style */
.terminal-box { height: 280px; overflow-y: auto; background: #000; border-radius: 6px; border: 1px solid #334155; padding: 8px; font-family: 'Courier New', Courier, monospace; font-size: 0.75rem; color: #22c55e; white-space: pre-wrap; word-break: break-all; margin-bottom: 6px; }
.terminal-input-row { display: flex; gap: 6px; }
.terminal-input-row input { flex: 1; background: #020617; }
</style>
</head>
<body>

<div class="container">
    <h1>Cờ Vua AI & Render Terminal</h1>
    
    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('game')">🎮 Ván Cờ AI</button>
        <button class="tab-btn" onclick="switchTab('terminal')">💻 Render Terminal</button>
    </div>

    <!-- TAB 1: CỜ VUA -->
    <div id="tab-game" class="tab-content active">
        <div class="card"><div id="board"></div></div>
        <div class="card">
            <div class="form-group">
                <label>Tên Provider (Nhà cung cấp)</label>
                <input type="text" id="providerName" value="OpenAI / Claude Hub">
            </div>
            <div class="form-group">
                <label>API Endpoint</label>
                <input type="text" id="apiEndpoint" value="https://api.openai.com/v1">
            </div>
            <div class="row">
                <div class="form-group" style="flex: 2;">
                    <label>API Key</label>
                    <input type="password" id="apiKey" placeholder="Dán API Key...">
                </div>
                <div class="form-group" style="flex: 1;">
                    <label>Auth Type</label>
                    <select id="authType">
                        <option value="Bearer">Bearer</option>
                        <option value="x-api-key">x-api-key</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label>Tên Model AI Trắng</label>
                <input type="text" id="modelInput" value="gpt-4o">
            </div>
            <div class="row">
                <button class="btn-success" onclick="fetchModels()" style="flex: 1;">Lấy Model (Auto)</button>
                <button onclick="testConnection()" style="flex: 1; background: #0d9488;">Test Connect</button>
            </div>
            <div class="row" style="margin-top: 6px;">
                <div class="form-group" style="flex: 1;">
                    <label>Chế độ ván đấu</label>
                    <select id="gameMode" onchange="toggleAiVsAiPanel()">
                        <option value="player_vs_ai">Người vs AI</option>
                        <option value="ai_vs_ai">🤖 AI vs AI (Tự động)</option>
                    </select>
                </div>
                <div class="form-group" id="playerColorGroup" style="flex: 1;">
                    <label>Bạn cầm quân</label>
                    <select id="playerColor">
                        <option value="w">Trắng</option>
                        <option value="b">Đen</option>
                    </select>
                </div>
            </div>

            <!-- Panel cấu hình riêng cho AI vs AI (2 API độc lập) -->
            <div id="aiVsAiPanel" class="ai-vs-ai-panel">
                <h3>⚙️ Cấu hình AI Đen (Quân Đen)</h3>
                <div class="form-group">
                    <label>Endpoint AI Đen</label>
                    <input type="text" id="blackEndpoint" value="https://api.openai.com/v1">
                </div>
                <div class="row">
                    <div class="form-group" style="flex: 2;">
                        <label>API Key AI Đen</label>
                        <input type="password" id="blackApiKey" placeholder="Để trống nếu dùng chung Key chính">
                    </div>
                    <div class="form-group" style="flex: 1;">
                        <label>Auth Type</label>
                        <select id="blackAuthType">
                            <option value="Bearer">Bearer</option>
                            <option value="x-api-key">x-api-key</option>
                        </select>
                    </div>
                </div>
                <div class="form-group" style="margin-bottom:0;">
                    <label>Model AI Đen</label>
                    <input type="text" id="blackModelInput" value="gpt-4o">
                </div>
            </div>

            <button id="startBtn" onclick="startGame()" style="margin-top: 8px;">Bắt Đầu Ván Mới</button>
            <button id="stopBtn" class="btn-danger" onclick="stopGame()" style="display: none; margin-top: 8px;">Dừng Trận Đấu</button>
            <div class="status-box" id="statusBox">Trạng thái: Sẵn sàng</div>
            <div class="log-header">
                <span>DEBUG LOG</span>
                <div>
                    <button class="btn-secondary" onclick="copyLog('logBox')">Copy</button>
                    <button class="btn-secondary" onclick="$('#logBox').empty()">Xóa</button>
                </div>
            </div>
            <div class="log-box" id="logBox"></div>
        </div>
    </div>

    <!-- TAB 2: TERMINAL RENDER -->
    <div id="tab-terminal" class="tab-content">
        <div class="card">
            <div class="log-header" style="margin-top: 0; margin-bottom: 6px;">
                <span style="color: #38bdf8;">Render Free Tier (0.1 CPU / 512MB RAM)</span>
                <div>
                    <button class="btn-secondary" onclick="copyLog('termOutput')">Copy Log</button>
                    <button class="btn-secondary" onclick="$('#termOutput').html('Terminal Ready.\\n')">Xóa Log</button>
                </div>
            </div>
            <div class="terminal-box" id="termOutput">Terminal Ready. Gõ lệnh bash (vd: pip install ..., df -h, ls -la)...\\n</div>
            <div class="terminal-input-row">
                <input type="text" id="termCmd" placeholder="Nhập lệnh bash..." onkeydown="if(event.key==='Enter') executeTerminalCommand()">
                <button onclick="executeTerminalCommand()" style="width: 80px; margin-top:0;">Gửi</button>
            </div>
        </div>
    </div>
</div>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.3/chess.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chessboard-js/1.0.0/chessboard-1.0.0.min.js"></script>
<script>
let board = null;
let game = new Chess();
let isRunning = false;
let aiTimeout = null;
let selectedSquare = null;

function switchTab(tabName) {
    $('.tab-btn').removeClass('active');
    $('.tab-content').removeClass('active');
    if(tabName === 'game') {
        $('.tab-btn:eq(0)').addClass('active');
        $('#tab-game').addClass('active');
        if(board) board.resize();
    } else {
        $('.tab-btn:eq(1)').addClass('active');
        $('#tab-terminal').addClass('active');
    }
}

function toggleAiVsAiPanel() {
    let mode = $('#gameMode').val();
    if(mode === 'ai_vs_ai') {
        $('#aiVsAiPanel').show();
        $('#playerColorGroup').hide();
    } else {
        $('#aiVsAiPanel').hide();
        $('#playerColorGroup').show();
    }
}

function chessDotComPieceTheme(piece) {
    const color = piece.charAt(0);
    const type = piece.charAt(1).toLowerCase();
    return `https://images.chesscomfiles.com/chess-themes/pieces/neo/150/${color}${type}.png`;
}

function log(type, msg) {
    const time = new Date().toLocaleTimeString();
    const logBox = $('#logBox');
    logBox.append(`[${time}] [${type}] ${msg}\\n`);
    logBox.scrollTop(logBox[0].scrollHeight);
}

function copyLog(elementId) { navigator.clipboard.writeText($('#' + elementId).text()).then(() => alert('Đã copy nội dung!')); }
function updateStatus(msg) { $('#statusBox').text('Trạng thái: ' + msg); }
function removeHighlights() { $('#board .square-55d63').removeClass('highlight-square highlight-hint'); }

function formatEndpoint(url) {
    url = url.trim().replace(/\/+$/, '');
    if (!url.endsWith('/chat/completions')) {
        if (url.endsWith('/v1')) url += '/chat/completions';
        else if (!url.includes('/v1')) url += '/v1/chat/completions';
        else url += '/chat/completions';
    }
    return url;
}

async function fetchModels() {
    let endpoint = formatEndpoint($('#apiEndpoint').val().trim());
    let apiKey = $('#apiKey').val().trim();
    let authType = $('#authType').val();

    if (!apiKey) { alert('Vui lòng nhập API Key trước!'); return; }
    
    log('SYS', 'Đang tự động quét model qua các Provider nổi tiếng (Ưu tiên OpenAI & Anthropic)...');

    try {
        const res = await fetch('/api/models', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_endpoint: endpoint, api_key: apiKey, auth_type: authType })
        });
        const data = await res.json();
        
        if (res.ok && data.models && data.models.length > 0) {
            let modelIds = data.models;
            $('#modelInput').val(modelIds[0]);
            log('SUCCESS', `Tìm thấy ${modelIds.length} models từ [${data.provider_used}]. Model đầu tiên: ${modelIds[0]}`);
            alert(`Lấy thành công qua ${data.provider_used}!\nĐã chọn model: ${modelIds[0]}`);
        } else {
            throw new Error(data.error || 'Không tìm thấy model nào từ các endpoint.');
        }
    } catch (err) {
        log('ERROR', `Lỗi lấy models: ${err.message}`);
        alert('Lỗi: ' + err.message);
    }
}

async function testConnection() {
    let endpoint = formatEndpoint($('#apiEndpoint').val().trim());
    let apiKey = $('#apiKey').val().trim();
    let authType = $('#authType').val();
    let model = $('#modelInput').val().trim();

    if (!apiKey || !endpoint) { alert('Nhập đủ API Key và Endpoint!'); return; }
    try {
        const res = await fetch('/api/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_endpoint: endpoint, api_key: apiKey, auth_type: authType, model: model })
        });
        if (res.ok) alert('Kết nối thành công qua Proxy!');
        else alert('Kết nối thất bại.');
    } catch (err) { alert('Lỗi: ' + err.message); }
}

function handleSquareClick(square) {
    let mode = $('#gameMode').val();
    if (mode === 'ai_vs_ai') return;

    if (!isRunning || game.game_over()) return;
    const playerColor = $('#playerColor').val();
    if ((game.turn() === 'w' && playerColor !== 'w') || (game.turn() === 'b' && playerColor !== 'b')) return;

    if (selectedSquare === null) {
        const piece = game.get(square);
        if (piece && piece.color === playerColor) {
            selectedSquare = square;
            removeHighlights();
            $('#board .square-' + square).addClass('highlight-square');
            game.moves({ square: square, verbose: true }).forEach(m => $('#board .square-' + m.to).addClass('highlight-hint'));
        }
    } else {
        const move = game.move({ from: selectedSquare, to: square, promotion: 'q' });
        removeHighlights();
        selectedSquare = null;
        if (move !== null) {
            board.position(game.fen());
            log('MOVE', `Bạn đi: ${move.san}`);
            if (isRunning && !game.game_over()) setTimeout(triggerAiMove, 300);
        } else {
            const piece = game.get(square);
            if (piece && piece.color === playerColor) handleSquareClick(square);
        }
    }
}

function startGame() {
    let mode = $('#gameMode').val();
    let endpoint = formatEndpoint($('#apiEndpoint').val().trim());
    let apiKey = $('#apiKey').val().trim();
    let model = $('#modelInput').val().trim();

    if (!apiKey || !endpoint || !model) { alert('Vui lòng điền đủ thông tin cấu hình AI Trắng!'); return; }

    if (mode === 'ai_vs_ai') {
        let bModel = $('#blackModelInput').val().trim();
        if (!bModel) { alert('Vui lòng nhập model cho AI Đen!'); return; }
    }

    game.reset();
    isRunning = true;
    selectedSquare = null;
    removeHighlights();

    if (mode === 'player_vs_ai') {
        const playerColor = $('#playerColor').val();
        board.orientation(playerColor === 'b' ? 'black' : 'white');
    } else {
        board.orientation('white');
    }

    board.position(game.fen());
    board.resize();
    $('#startBtn').hide();
    $('#stopBtn').show();
    $('#logBox').empty();
    
    let provider = $('#providerName').val().trim();
    log('SYSTEM', `--- Bắt đầu ván đấu (${mode === 'ai_vs_ai' ? 'AI vs AI' : provider}) ---`);
    updateStatus('Đang trong trận đấu');

    if (mode === 'ai_vs_ai') {
        setTimeout(triggerAiVsAiMove, 500);
    } else {
        const playerColor = $('#playerColor').val();
        if (playerColor === 'b') triggerAiMove();
    }
}

function stopGame() {
    isRunning = false;
    if (aiTimeout) clearTimeout(aiTimeout);
    removeHighlights();
    selectedSquare = null;
    $('#startBtn').show();
    $('#stopBtn').hide();
    log('SYSTEM', 'Đã dừng ván đấu');
    updateStatus('Đã dừng');
}

async function triggerAiMove() {
    if (!isRunning || game.game_over()) return;
    let endpoint = formatEndpoint($('#apiEndpoint').val().trim());
    let apiKey = $('#apiKey').val().trim();
    let authType = $('#authType').val();
    let model = $('#modelInput').val().trim();

    updateStatus(`AI (${model}) đang suy nghĩ...`);
    const possibleMoves = game.moves();
    const promptText = `You are playing chess. Current FEN: ${game.fen()}. Legal moves: ${possibleMoves.join(', ')}. Choose the best move in SAN format (e.g. e4, Nf3). Reply with ONLY the move notation.`;

    log('API_REQ', `Model: ${model} | Gửi request...`);
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: model,
                messages: [{ role: 'user', content: promptText }],
                temperature: 0.2,
                target_endpoint: endpoint,
                api_key: apiKey,
                auth_type: authType
            })
        });
        const text = await res.text();
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${text}`);
        const data = JSON.parse(text);
        
        let aiMoveStr = data.choices[0].message.content.trim().replace(/['"`]/g, '');
        let move = game.move(aiMoveStr);
        if (!move) {
            let matched = game.moves({verbose:true}).find(m => m.san.toLowerCase() === aiMoveStr.toLowerCase() || m.lan.toLowerCase() === aiMoveStr.toLowerCase());
            if (matched) move = game.move(matched);
            else move = game.move(game.moves()[0]);
        }

        board.position(game.fen());
        log('MOVE', `AI đi: ${move.san}`);
        
        if (game.in_checkmate()) { updateStatus('Chiếu bí!'); stopGame(); }
        else if (game.in_draw()) { updateStatus('Hòa!'); stopGame(); }
        else if (isRunning) { updateStatus('Đến lượt bạn'); }
    } catch (err) {
        log('ERROR', `Lỗi: ${err.message}`);
        stopGame();
    }
}

async function triggerAiVsAiMove() {
    if (!isRunning || game.game_over()) return;
    
    let turn = game.turn();
    let endpoint, apiKey, authType, model;

    if (turn === 'w') {
        endpoint = formatEndpoint($('#apiEndpoint').val().trim());
        apiKey = $('#apiKey').val().trim();
        authType = $('#authType').val();
        model = $('#modelInput').val().trim();
    } else {
        endpoint = formatEndpoint($('#blackEndpoint').val().trim());
        apiKey = $('#blackApiKey').val().trim() || $('#apiKey').val().trim();
        authType = $('#blackAuthType').val();
        model = $('#blackModelInput').val().trim();
    }

    updateStatus(`AI ${turn === 'w' ? 'Trắng' : 'Đen'} (${model}) đang suy nghĩ...`);
    const possibleMoves = game.moves();
    const promptText = `You are playing chess as ${turn === 'w' ? 'White' : 'Black'}. Current FEN: ${game.fen()}. Legal moves: ${possibleMoves.join(', ')}. Choose the best move in SAN format (e.g. e4, Nf3). Reply with ONLY the move notation.`;

    log('API_REQ', `AI ${turn === 'w' ? 'Trắng' : 'Đen'} [Model: ${model}] | Gửi request...`);
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: model,
                messages: [{ role: 'user', content: promptText }],
                temperature: 0.2,
                target_endpoint: endpoint,
                api_key: apiKey,
                auth_type: authType
            })
        });
        const text = await res.text();
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${text}`);
        const data = JSON.parse(text);
        
        let aiMoveStr = data.choices[0].message.content.trim().replace(/['"`]/g, '');
        let move = game.move(aiMoveStr);
        if (!move) {
            let matched = game.moves({verbose:true}).find(m => m.san.toLowerCase() === aiMoveStr.toLowerCase() || m.lan.toLowerCase() === aiMoveStr.toLowerCase());
            if (matched) move = game.move(matched);
            else move = game.move(game.moves()[0]);
        }

        board.position(game.fen());
        log('MOVE', `AI ${turn === 'w' ? 'Trắng' : 'Đen'} đi: ${move.san}`);
        
        if (game.in_checkmate()) { updateStatus('Chiếu bí!'); stopGame(); }
        else if (game.in_draw()) { updateStatus('Hòa!'); stopGame(); }
        else if (isRunning) {
            aiTimeout = setTimeout(triggerAiVsAiMove, 600);
        }
    } catch (err) {
        log('ERROR', `Lỗi AI vs AI: ${err.message}`);
        // Thử lại nước đi sau 3 giây nếu lỗi tạm thời từ mạng hoặc timeout thay vì dừng hẳn ván
        if (isRunning) {
            log('SYSTEM', 'Thử lại lượt đi sau 3 giây...');
            aiTimeout = setTimeout(triggerAiVsAiMove, 3000);
        }
    }
}

async function executeTerminalCommand() {
    const cmd = $('#termCmd').val().trim();
    if (!cmd) return;

    let isDownloadCmd = cmd.includes('pip install') || cmd.includes('apt-get') || cmd.includes('wget') || cmd.includes('curl') || cmd.includes('git clone');
    if (isDownloadCmd) {
        let estimatedMB = (Math.random() * 40 + 10).toFixed(1);
        let confirmAction = confirm(`⚠️ CẢNH BÁO TẢI TỆP/GÓI TRÊN RENDER:\\nBạn chuẩn bị chạy lệnh tải dung lượng ước tính khoảng ~${estimatedMB} MB trên gói Free (512MB RAM).\\n\\nBạn có muốn tiếp tục (YES) hay Hủy (NO)?`);
        if (!confirmAction) {
            $('#termOutput').append(`\\n$ ${cmd}\\n[HỦY BỎ] Đã dừng lệnh tải theo yêu cầu người dùng.\\n`);
            $('#termCmd').val('');
            return;
        }
    }

    $('#termOutput').append(`\\n$ ${cmd}\\n[Đang thực thi...]\\n`);
    $('#termCmd').val('');
    const termOut = document.getElementById('termOutput');
    termOut.scrollTop = termOut.scrollHeight;

    try {
        const res = await fetch('/api/terminal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: cmd })
        });
        const data = await res.json();
        if (res.ok) {
            $('#termOutput').append(data.output + `\\n[Hoàn thành - Exit Code: ${data.exit_code}]\\n`);
        } else {
            $('#termOutput').append(`[LỖI] ${data.error}\\n`);
        }
    } catch (err) {
        $('#termOutput').append(`[LỖI KẾT NỐI] ${err.message}\\n`);
    }
    termOut.scrollTop = termOut.scrollHeight;
}

$(document).ready(function() {
    board = Chessboard('board', { draggable: false, position: 'start', pieceTheme: chessDotComPieceTheme });
    $('#board').on('click', '.square-55d63', function() {
        const square = $(this).attr('data-square');
        if (square) handleSquareClick(square);
    });
    setTimeout(() => board.resize(), 300);
});
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

def build_auth_header(auth_type, api_key):
    if auth_type == 'x-api-key':
        return {"x-api-key": api_key, "Content-Type": "application/json"}
    else:
        bearer = api_key if api_key.startswith('Bearer ') else f"Bearer {api_key}"
        return {"Authorization": bearer, "Content-Type": "application/json"}

@app.route('/api/models', methods=['POST'])
def api_models():
    try:
        data = request.get_json()
        target_url = data.get('target_endpoint', '').strip()
        api_key = data.get('api_key', '')
        auth_type = data.get('auth_type', 'Bearer')

        base_urls = []
        if target_url:
            cleaned = target_url.replace('/chat/completions', '').replace('/models', '').rstrip('/')
            base_urls.append(cleaned)

        popular_providers = [
            "https://api.openai.com/v1",
            "https://api.anthropic.com/v1",
            "https://openrouter.ai/api/v1",
            "https://api.deepseek.com/v1",
            "https://generativelanguage.googleapis.com/v1beta/openai",
            target_url
        ]
        
        for url in popular_providers:
            if url and url not in base_urls:
                base_urls.append(url)

        headers = build_auth_header(auth_type, api_key)
        headers["User-Agent"] = "claude-cli/1.0.0 (external, cli)"
        chosen_proxy = get_next_proxy()
        proxies = {"http": chosen_proxy, "https": chosen_proxy}

        last_error = ""
        for base in base_urls:
            models_url = f"{base.rstrip('/')}/models"
            try:
                response = crequests.get(models_url, headers=headers, proxies=proxies, impersonate="chrome120", timeout=15, allow_redirects=False)
                if response.status_code == 200:
                    res_json = response.json()
                    model_list = []
                    
                    raw_data = res_json.get('data', res_json.get('models', res_json))
                    if isinstance(raw_data, list):
                        for item in raw_data:
                            if isinstance(item, dict):
                                m_id = item.get('id') or item.get('name') or item.get('model')
                                if m_id: model_list.append(str(m_id))
                            elif isinstance(item, str):
                                model_list.append(item)
                    elif isinstance(raw_data, dict):
                        for k, v in raw_data.items():
                            if isinstance(v, str): model_list.append(v)
                            elif isinstance(v, dict):
                                m_id = v.get('id') or v.get('name')
                                if m_id: model_list.append(str(m_id))

                    if model_list:
                        return jsonify({"models": model_list, "provider_used": base}), 200
            except Exception as e:
                last_error = str(e)
                continue

        return jsonify({"error": f"Không thể lấy model từ bất kỳ Provider nào. Lỗi gần nhất: {last_error}"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test', methods=['POST'])
def api_test():
    try:
        data = request.get_json()
        target_url = data.get('target_endpoint', '').strip()
        api_key = data.get('api_key')
        auth_type = data.get('auth_type', 'Bearer')
        model = data.get('model', 'gpt-4o')

        headers = build_auth_header(auth_type, api_key)
        headers["User-Agent"] = "claude-cli/1.0.0 (external, cli)"
        payload = {"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
        chosen_proxy = get_next_proxy()
        proxies = {"http": chosen_proxy, "https": chosen_proxy}

        response = crequests.post(target_url, headers=headers, json=payload, proxies=proxies, impersonate="chrome120", timeout=20, allow_redirects=False)
        if response.status_code in [200, 400, 404, 422]:
            return jsonify({"status": "ok", "code": response.status_code}), 200
        return response.text, response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def proxy_chat():
    try:
        payload = request.get_json()
        target_url = payload.pop('target_endpoint', '').strip()
        api_key = payload.pop('api_key', '').strip()
        auth_type = payload.pop('auth_type', 'Bearer')
        payload.pop('provider', None)

        if not target_url:
            return jsonify({"error": "Thiếu API Endpoint"}), 400

        headers = build_auth_header(auth_type, api_key)
        headers["User-Agent"] = "claude-cli/1.0.0 (external, cli)"
        chosen_proxy = get_next_proxy()
        proxies = {"http": chosen_proxy, "https": chosen_proxy}

        # Tăng timeout lên 60 giây để Claude / các model nặng có thời gian suy nghĩ
        response = crequests.post(target_url, headers=headers, json=payload, proxies=proxies, impersonate="chrome120", timeout=60, allow_redirects=False)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({"error": f"Lỗi HTTP {response.status_code}: {response.text[:200]}"}), 500
    except Exception as e:
        return jsonify({"error": f"Lỗi Gateway: {str(e)}"}), 500

@app.route('/api/terminal', methods=['POST'])
def api_terminal():
    try:
        data = request.get_json()
        command = data.get('command', '')

        if not command:
            return jsonify({"error": "Thiếu câu lệnh!"}), 400

        process = subprocess.Popen(
            command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        stdout, stderr = process.communicate(timeout=40)
        exit_code = process.returncode

        full_output = ""
        if stdout: full_output += stdout
        if stderr:
            if full_output: full_output += "\n--- STDERR / WARNINGS ---\n"
            full_output += stderr
        
        if not full_output: full_output = "Lệnh đã chạy xong nhưng không trả về dữ liệu text."

        return jsonify({"output": full_output, "exit_code": exit_code}), 200

    except subprocess.TimeoutExpired:
        return jsonify({"output": "⚠️ Lỗi: Tiến trình chạy quá thời gian giới hạn (>40s).", "exit_code": -1}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
