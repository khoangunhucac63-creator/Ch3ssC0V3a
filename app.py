from flask import Flask, render_template_string, request, jsonify
from curl_cffi import requests as crequests
import json

app = Flask(__name__)

@app.route('/api/chat', methods=['POST'])
def proxy_chat():
    try:
        auth_header = request.headers.get('Authorization', '')
        payload = request.get_json()

        target_url = payload.pop('target_endpoint', '').strip()
        if not target_url:
            return jsonify({"error": "Thiếu API Endpoint"}), 400

        headers = {
            "Content-Type": "application/json",
            "Authorization": auth_header,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # Sử dụng curl_cffi để giả mạo trình duyệt Chrome, vượt qua Cloudflare
        response = crequests.post(
            target_url,
            headers=headers,
            json=payload,
            impersonate="chrome120",
            timeout=25
        )

        if response.status_code == 200:
            try:
                response.json() # Kiểm tra xem có phải JSON chuẩn không
                return response.text, 200, [('Content-Type', 'application/json')]
            except json.JSONDecodeError:
                snippet = response.text[:300].replace('\n', ' ')
                return jsonify({"error": f"TabiToken trả về Non-JSON: {snippet}"}), 500

        return jsonify({"error": f"TabiToken trả về lỗi HTTP {response.status_code}: {response.text[:200]}"}), 500

    except Exception as e:
        return jsonify({"error": f"Lỗi Gateway: {str(e)}"}), 500

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cờ Vua AI - Render</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/chessboard-js/1.0.0/chessboard-1.0.0.min.css">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
body { background: #0f172a; color: #f8fafc; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 10px; }
.container { max-width: 480px; width: 100%; display: flex; flex-direction: column; gap: 12px; }
.card { background: #1e293b; border-radius: 12px; padding: 12px; border: 1px solid #334155; }
#board { width: 100%; aspect-ratio: 1/1; margin: 0 auto; }
h1 { font-size: 1.2rem; text-align: center; color: #38bdf8; margin-bottom: 8px; }
.form-group { margin-bottom: 8px; }
label { display: block; font-size: 0.8rem; margin-bottom: 3px; color: #94a3b8; }
input, select, button { width: 100%; padding: 8px 10px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #fff; font-size: 0.85rem; }
button { background: #0284c7; font-weight: bold; cursor: pointer; margin-top: 5px; border: none; }
.btn-danger { background: #dc2626 !important; }
.btn-secondary { background: #475569 !important; font-size: 0.75rem; padding: 5px 8px; margin-top: 4px; }
.status-box { margin-top: 8px; padding: 6px; background: #0f172a; border-radius: 6px; border: 1px solid #334155; font-size: 0.8rem; font-weight: bold; color: #38bdf8; }

.log-header { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; margin-bottom: 4px; }
.log-header span { font-size: 0.8rem; font-weight: bold; color: #94a3b8; }
.log-box { height: 200px; overflow-y: auto; background: #020617; border-radius: 6px; border: 1px solid #334155; padding: 8px; font-family: 'Courier New', Courier, monospace; font-size: 0.72rem; color: #38bdf8; white-space: pre-wrap; word-break: break-all; }

.highlight-square { background-color: rgba(255, 255, 0, 0.4) !important; }
.highlight-hint { background: radial-gradient(circle, rgba(16, 185, 129, 0.7) 28%, transparent 28%) !important; }
</style>
</head>
<body>

<div class="container">
    <h1>Cờ Vua AI (Render Server)</h1>

    <div class="card">
        <div id="board"></div>
    </div>

    <div class="card">
        <div class="form-group">
            <label>API Endpoint</label>
            <input type="text" id="apiEndpoint" value="https://tabitoken.com/v1/chat/completions">
        </div>

        <div class="form-group">
            <label>API Key (sk-...)</label>
            <input type="text" id="apiKey" placeholder="Dán API Key...">
        </div>

        <div class="form-group">
            <label>Chế độ chơi</label>
            <select id="gameMode" onchange="handleModeChange()">
                <option value="pvai">Người vs AI</option>
                <option value="aivai">AI vs AI (4.8 vs 5)</option>
            </select>
        </div>

        <div id="pvaiSettings">
            <div class="form-group">
                <label>Chọn Model AI</label>
                <select id="singleAiModel">
                    <option value="claude-opus-5">claude-opus-5</option>
                    <option value="claude-opus-4.8">claude-opus-4.8</option>
                </select>
            </div>
            <div class="form-group">
                <label>Bạn cầm quân</label>
                <select id="playerColor">
                    <option value="w">Trắng</option>
                    <option value="b">Đen</option>
                </select>
            </div>
        </div>

        <div id="aivaiSettings" style="display: none;">
            <div class="form-group">
                <label>Cấu hình Trắng / Đen</label>
                <select id="aiAssignment">
                    <option value="48_vs_5">Trắng: claude-opus-4.8 | Đen: claude-opus-5</option>
                    <option value="5_vs_48">Trắng: claude-opus-5 | Đen: claude-opus-4.8</option>
                </select>
            </div>
        </div>

        <button id="startBtn" onclick="startGame()">Bắt Đầu Ván Mới</button>
        <button id="stopBtn" class="btn-danger" onclick="stopGame()" style="display: none;">Dừng Trận Đấu</button>

        <div class="status-box" id="statusBox">Trạng thái: Sẵn sàng</div>

        <div class="log-header">
            <span>FULL DEBUG LOG</span>
            <div>
                <button class="btn-secondary" onclick="copyLog()">Copy Log</button>
                <button class="btn-secondary" onclick="clearLog()">Xóa Log</button>
            </div>
        </div>
        <div class="log-box" id="logBox"></div>
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

function chessDotComPieceTheme(piece) {
    const color = piece.charAt(0);
    const type = piece.charAt(1).toLowerCase();
    return `https://images.chesscomfiles.com/chess-themes/pieces/neo/150/${color}${type}.png`;
}

function handleModeChange() {
    const mode = $('#gameMode').val();
    if (mode === 'pvai') {
        $('#pvaiSettings').show();
        $('#aivaiSettings').hide();
    } else {
        $('#pvaiSettings').hide();
        $('#aivaiSettings').show();
    }
}

function log(type, msg) {
    const time = new Date().toLocaleTimeString();
    const logBox = $('#logBox');
    logBox.append(`[${time}] [${type}] ${msg}\\n`);
    logBox.scrollTop(logBox[0].scrollHeight);
}

function clearLog() { $('#logBox').empty(); }

function copyLog() {
    navigator.clipboard.writeText($('#logBox').text()).then(() => alert('Đã copy Log!'));
}

function updateStatus(msg) { $('#statusBox').text('Trạng thái: ' + msg); }

function removeHighlights() {
    $('#board .square-55d63').removeClass('highlight-square highlight-hint');
}

function handleSquareClick(square) {
    if (!isRunning || $('#gameMode').val() === 'aivai' || game.game_over()) return;

    const playerColor = $('#playerColor').val();
    if ((game.turn() === 'w' && playerColor !== 'w') || (game.turn() === 'b' && playerColor !== 'b')) return;

    if (selectedSquare === null) {
        const piece = game.get(square);
        if (piece && piece.color === playerColor) {
            selectedSquare = square;
            removeHighlights();
            $('#board .square-' + square).addClass('highlight-square');

            const moves = game.moves({ square: square, verbose: true });
            moves.forEach(m => $('#board .square-' + m.to).addClass('highlight-hint'));
        }
    } else {
        const move = game.move({ from: selectedSquare, to: square, promotion: 'q' });
        removeHighlights();
        selectedSquare = null;

        if (move !== null) {
            board.position(game.fen());
            log('MOVE', `Bạn đi: ${move.san} | FEN mới: ${game.fen()}`);
            checkGameState();
            if (isRunning && !game.game_over()) setTimeout(triggerAiMove, 300);
        } else {
            const piece = game.get(square);
            if (piece && piece.color === playerColor) handleSquareClick(square);
        }
    }
}

function checkGameState() {
    if (game.in_checkmate()) { log('GAME', 'Kết thúc: CHIẾU BÍ'); updateStatus('Chiếu bí!'); stopGame(); }
    else if (game.in_draw()) { log('GAME', 'Kết thúc: HÒA'); updateStatus('Hòa!'); stopGame(); }
}

function startGame() {
    let apiKey = $('#apiKey').val().trim();
    let endpoint = $('#apiEndpoint').val().trim();

    if (!apiKey) { alert('Vui lòng nhập API Key!'); return; }
    if (!endpoint) { alert('Vui lòng nhập Endpoint!'); return; }

    localStorage.setItem('tabi_api_key', apiKey);
    localStorage.setItem('tabi_endpoint', endpoint);

    game.reset();
    isRunning = true;
    selectedSquare = null;
    removeHighlights();

    const mode = $('#gameMode').val();
    const playerColor = $('#playerColor').val();
    board.orientation(mode === 'pvai' && playerColor === 'b' ? 'black' : 'white');
    board.position(game.fen());
    board.resize();

    $('#startBtn').hide();
    $('#stopBtn').show();
    clearLog();
    log('SYSTEM', '--- Bắt đầu ván đấu mới ---');
    log('SYSTEM', `Chế độ: ${mode} | FEN: ${game.fen()}`);
    updateStatus('Đang trong trận đấu');

    if (mode === 'aivai' || (mode === 'pvai' && playerColor === 'b')) triggerAiMove();
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
    let apiKey = $('#apiKey').val().trim();
    let endpoint = $('#apiEndpoint').val().trim();
    const mode = $('#gameMode').val();

    let modelName = mode === 'pvai' ? $('#singleAiModel').val() :
        (game.turn() === 'w' ? ($('#aiAssignment').val() === '48_vs_5' ? 'claude-opus-4.8' : 'claude-opus-5') :
                               ($('#aiAssignment').val() === '48_vs_5' ? 'claude-opus-5' : 'claude-opus-4.8'));

    const turnName = game.turn() === 'w' ? 'Trắng' : 'Đen';
    updateStatus(`${turnName} (${modelName}) đang suy nghĩ...`);
    const possibleMoves = game.moves();

    const promptText = `Trạng thái FEN: "${game.fen()}". Nước hợp lệ: [${possibleMoves.join(', ')}]. Chọn 1 nước đi tốt nhất dạng SAN (vd: e4, Nf3). Chỉ trả lời duy nhất mã nước đi.`;

    let authHeaderValue = apiKey.startsWith('Bearer ') ? apiKey : `Bearer ${apiKey}`;

    log('API_REQ', `Model: ${modelName} | Gửi request...`);

    try {
        const payload = {
            target_endpoint: endpoint,
            model: modelName,
            messages: [{ role: 'user', content: promptText }],
            temperature: 0.2
        };

        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': authHeaderValue
            },
            body: JSON.stringify(payload)
        });

        const text = await res.text();
        log('API_RES', `HTTP status: ${res.status}`);

        if (!res.ok) throw new Error(`HTTP ${res.status}: ${text}`);

        const data = JSON.parse(text);
        let aiMoveStr = data.choices[0].message.content.trim().replace(/['"`]/g, '');
        log('AI_PARSED_MOVE', `Nước đi AI chọn: "${aiMoveStr}"`);

        let move = game.move(aiMoveStr);
        if (!move) {
            const match = possibleMoves.find(m => m.toLowerCase() === aiMoveStr.toLowerCase());
            if (match) move = game.move(match);
        }
        
        if (!move) {
            log('WARN', `Nước không hợp lệ (${aiMoveStr}), chọn ngẫu nhiên.`);
            move = game.move(possibleMoves[Math.floor(Math.random() * possibleMoves.length)]);
        }

        board.position(game.fen());
        log('MOVE', `${turnName} (${modelName}): ${move.san} | FEN mới: ${game.fen()}`);
        checkGameState();

        if (isRunning && !game.game_over()) {
            if (mode === 'aivai') aiTimeout = setTimeout(triggerAiMove, 800);
            else updateStatus('Đến lượt bạn');
        }
    } catch (err) {
        log('ERROR', `Lỗi: ${err.message}`);
        stopGame();
    }
}

$(document).ready(function() {
    const savedKey = localStorage.getItem('tabi_api_key');
    const savedEndpoint = localStorage.getItem('tabi_endpoint');
    if (savedKey) $('#apiKey').val(savedKey);
    if (savedEndpoint) $('#apiEndpoint').val(savedEndpoint);

    board = Chessboard('board', {
        draggable: false,
        position: 'start',
        pieceTheme: chessDotComPieceTheme
    });

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

if __name__ == '__main__':
    app.run()
