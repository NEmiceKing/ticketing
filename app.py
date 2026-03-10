from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

# Sample event data
EVENTS = [
    {
        "id": 1,
        "title": "周杰伦2026世界巡回演唱会",
        "date": "2026-04-15",
        "venue": "香港红磡体育馆",
        "price": 880,
        "category": "演唱会",
        "emoji": "🎤"
    },
    {
        "id": 2,
        "title": "五月天诺亚方舟演唱会",
        "date": "2026-04-20",
        "venue": "香港中环海滨活动空间",
        "price": 980,
        "category": "演唱会",
        "emoji": "🎸"
    },
    {
        "id": 3,
        "title": "经典原版音乐剧《猫》",
        "date": "2026-05-01",
        "venue": "香港文化艺术中心",
        "price": 680,
        "category": "音乐剧",
        "emoji": "🐱"
    },
    {
        "id": 4,
        "title": "2026香港国际七人榄球赛",
        "date": "2026-04-05",
        "venue": "香港大球场",
        "price": 450,
        "category": "体育赛事",
        "emoji": "🏉"
    },
    {
        "id": 5,
        "title": "芭蕾舞剧《天鹅湖》",
        "date": "2026-05-10",
        "venue": "香港文化中心大剧院",
        "price": 580,
        "category": "舞蹈芭蕾",
        "emoji": "🦢"
    },
    {
        "id": 6,
        "title": "陈奕迅FEAR and DREAMS演唱会",
        "date": "2026-06-01",
        "venue": "香港体育馆",
        "price": 880,
        "category": "演唱会",
        "emoji": "🎤"
    }
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/events')
def get_events():
    category = request.args.get('category', '全部')
    if category == '全部':
        return jsonify(EVENTS)
    return jsonify([e for e in EVENTS if e['category'] == category])

@app.route('/api/event/<int:event_id>')
def get_event(event_id):
    event = next((e for e in EVENTS if e['id'] == event_id), None)
    if event:
        return jsonify(event)
    return jsonify({"error": "Event not found"}), 404

@app.route('/api/order', methods=['POST'])
def create_order():
    data = request.json
    # In production, save to database
    return jsonify({
        "success": True,
        "order_id": f"ORD{1000 + int(os.urandom(2).hex(), 16)}",
        "message": "订单创建成功"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
