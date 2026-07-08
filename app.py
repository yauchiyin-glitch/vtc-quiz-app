from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import qrcode
import io
import base64
import socket

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vtc-training-2026'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ── 題目資料 ──────────────────────────────────────────────
QUESTIONS = [
    {
        "id": 1,
        "session": "morning",
        "type": "quiz",
        "question": "全球第一個喺西洋棋打敗世界冠軍嘅AI叫咩名？",
        "options": ["A. Deep Blue", "B. AlphaGo", "C. Watson", "D. HAL 9000"],
        "answer": 0,
        "fun_fact": "1997年，IBM嘅Deep Blue擊敗世界棋王Garry Kasparov，係AI史上重要里程碑！"
    },
    {
        "id": 2,
        "session": "morning",
        "type": "quiz",
        "question": "\"ChatGPT\"入面嘅GPT係咩嘅簡寫？",
        "options": ["A. General Purpose Tool", "B. Generative Pre-trained Transformer", "C. Global Processing Technology", "D. Guided Prompt Training"],
        "answer": 1,
        "fun_fact": "GPT = Generative Pre-trained Transformer，係一種用海量文字訓練出嚟嘅語言模型架構！"
    },
    {
        "id": 3,
        "session": "morning",
        "type": "quiz",
        "question": "AI「一本正經噏假嘢」嘅現象，行內正式叫咩名？",
        "options": ["A. Bug", "B. Glitch", "C. Hallucination", "D. Error 404"],
        "answer": 2,
        "fun_fact": "AI Hallucination（幻覺）係指AI自信地生成不存在或錯誤嘅資訊，用AI時要小心核實！"
    },
    {
        "id": 4,
        "session": "morning",
        "type": "quiz",
        "question": "你有冇用過任何生成式AI工具？（例如ChatGPT、Copilot、Gemini等）",
        "options": ["A. 從未用過", "B. 試過幾次", "C. 間中使用", "D. 經常使用"],
        "answer": None,
        "fun_fact": None
    },
    {
        "id": 5,
        "session": "morning",
        "type": "scale",
        "question": "你對「Prompt（提詞）」呢個概念嘅熟悉程度？",
        "options": ["1 - 完全唔識", "2 - 略有所聞", "3 - 一般了解", "4 - 比較熟悉", "5 - 非常熟悉"],
        "answer": None,
        "fun_fact": None
    },
    {
        "id": 6,
        "session": "morning",
        "type": "quiz",
        "question": "你喺Word、Excel、PowerPoint或Outlook入面，有冇見過或用過Copilot功能？",
        "options": ["A. 用過，很有幫助", "B. 用過，但未知點用", "C. 見過但未試過", "D. 完全冇留意"],
        "answer": None,
        "fun_fact": None
    },
    {
        "id": 7,
        "session": "morning",
        "type": "quiz",
        "question": "Copilot有三種主要入口：Copilot Chat、各Office App內、同Agents，你之前知唔知？",
        "options": ["A. 全部都知", "B. 知一兩種", "C. 聽過但唔清楚", "D. 完全唔知"],
        "answer": None,
        "fun_fact": None
    },
    {
        "id": 8,
        "session": "morning",
        "type": "quiz",
        "question": "你有冇聽過或試過用「Agent Builder」自己整AI助手？",
        "options": ["A. 用過", "B. 聽過未試", "C. 今日先聽到", "D. 未聽過"],
        "answer": None,
        "fun_fact": None
    },
    {
        "id": 9,
        "session": "morning",
        "type": "scale",
        "question": "你覺得而家AI/Copilot對你「教學準備」工作幫到幾多？",
        "options": ["1 - 完全冇幫", "2 - 少少幫助", "3 - 一般", "4 - 頗有幫助", "5 - 非常有幫助"],
        "answer": None,
        "fun_fact": None
    },
    {
        "id": 10,
        "session": "morning",
        "type": "quiz",
        "question": "今日你最想透過訓練解決嘅痛點係咩？",
        "options": ["A. 教學準備太花時間", "B. 行政文書太多", "C. 唔識點開始用AI", "D. 想深入了解Copilot功能"],
        "answer": None,
        "fun_fact": None
    },
    {
        "id": 11,
        "session": "afternoon",
        "type": "wordcloud",
        "question": "用一個詞形容你今日上午對AI／Copilot嘅新發現或感受",
        "options": [],
        "answer": None,
        "fun_fact": None
    },
    {
        "id": 12,
        "session": "afternoon",
        "type": "wordcloud",
        "question": "你最想你自己科目嘅AI Bot幫你做到啲咩？（一個詞或短語）",
        "options": [],
        "answer": None,
        "fun_fact": None
    }
]

# ── 全域狀態 ──────────────────────────────────────────────
state = {
    "current_question": 0,
    "responses": {i: {} for i in range(len(QUESTIONS))},
    "participants": {},
    "show_results": False
}

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def generate_qr(url):
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

# ── Routes ────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('join.html')

@app.route('/join')
def join():
    return render_template('join.html')

@app.route('/participant')
def participant():
    return render_template('participant.html')

@app.route('/host')
def host():
    base_url = request.host_url.rstrip('/')
    join_url = f"{base_url}/join"
    qr_data = generate_qr(join_url)
    return render_template('host.html', qr_data=qr_data, join_url=join_url, questions=QUESTIONS)

# ── Socket Events ─────────────────────────────────────────
@socketio.on('join_session')
def on_join(data):
    name = data.get('name', 'Anonymous')
    sid = request.sid
    state['participants'][sid] = name
    emit('session_joined', {
        'name': name,
        'current_question': state['current_question'],
        'show_results': state['show_results']
    })
    emit('participant_count', {'count': len(state['participants'])}, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    if sid in state['participants']:
        del state['participants'][sid]
    emit('participant_count', {'count': len(state['participants'])}, broadcast=True)

@socketio.on('submit_answer')
def on_answer(data):
    q_idx = data.get('question_index')
    answer = data.get('answer')
    sid = request.sid
    name = state['participants'].get(sid, 'Anonymous')
    if q_idx is not None and answer is not None:
        state['responses'][q_idx][sid] = {'name': name, 'answer': answer}
        emit('answer_update', {
            'question_index': q_idx,
            'responses': get_response_summary(q_idx)
        }, broadcast=True)

@socketio.on('next_question')
def on_next(data):
    if state['current_question'] < len(QUESTIONS) - 1:
        state['current_question'] += 1
        state['show_results'] = False
        emit('question_changed', {
            'current_question': state['current_question'],
            'show_results': False
        }, broadcast=True)

@socketio.on('prev_question')
def on_prev(data):
    if state['current_question'] > 0:
        state['current_question'] -= 1
        state['show_results'] = False
        emit('question_changed', {
            'current_question': state['current_question'],
            'show_results': False
        }, broadcast=True)

@socketio.on('show_results')
def on_show_results(data):
    state['show_results'] = True
    q_idx = state['current_question']
    emit('results_shown', {
        'question_index': q_idx,
        'responses': get_response_summary(q_idx)
    }, broadcast=True)

@socketio.on('reset_question')
def on_reset(data):
    q_idx = state['current_question']
    state['responses'][q_idx] = {}
    state['show_results'] = False
    emit('question_reset', {'question_index': q_idx}, broadcast=True)

@socketio.on('get_state')
def on_get_state(data):
    q_idx = state['current_question']
    emit('full_state', {
        'current_question': q_idx,
        'show_results': state['show_results'],
        'responses': get_response_summary(q_idx),
        'participant_count': len(state['participants'])
    })

def get_response_summary(q_idx):
    q = QUESTIONS[q_idx]
    responses = state['responses'].get(q_idx, {})
    if q['type'] == 'wordcloud':
        words = [r['answer'] for r in responses.values()]
        word_count = {}
        for w in words:
            w = w.strip()
            if w:
                word_count[w] = word_count.get(w, 0) + 1
        return {'type': 'wordcloud', 'words': word_count, 'total': len(responses)}
    else:
        counts = [0] * len(q['options'])
        for r in responses.values():
            try:
                idx = int(r['answer'])
                if 0 <= idx < len(counts):
                    counts[idx] += 1
            except:
                pass
        return {'type': 'bar', 'counts': counts, 'total': len(responses)}

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
