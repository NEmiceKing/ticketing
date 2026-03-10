"""
高并发票务系统 - 防超卖
使用Redis分布式锁 + 数据库事务
"""
import os
import time
import threading
import random
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'tickety-concurrent-key-2026'

# 模拟数据库中的票务数据
TICKET_INVENTORY = {
    1: {"total": 100, "sold": 0, "name": "Jay Chou Concert"},
    2: {"total": 50, "sold": 0, "name": "Mayday Concert"},
    3: {"total": 200, "sold": 0, "name": "Cats Musical"},
}

# 模拟Redis锁（生产环境请使用真实Redis）
class LockManager:
    locks = {}
    
    @classmethod
    def acquire(cls, key, timeout=10):
        """获取锁"""
        if key not in cls.locks:
            cls.locks[key] = threading.Lock()
        return cls.locks[key].acquire(timeout=timeout)
    
    @classmethod
    def release(cls, key):
        """释放锁"""
        if key in cls.locks:
            cls.locks[key].release()

# 订单队列
ORDER_QUEUE = []
ORDER_COUNTER = 1

def process_order_queue():
    """后台处理订单队列"""
    global ORDER_COUNTER
    while True:
        if ORDER_QUEUE:
            order = ORDER_QUEUE.pop(0)
            event_id = order['event_id']
            quantity = order['quantity']
            
            # 获取锁
            lock_key = f"event_{event_id}"
            if LockManager.acquire(lock_key):
                try:
                    # 检查库存
                    if TICKET_INVENTORY[event_id]['sold'] + quantity <= TICKET_INVENTORY[event_id]['total']:
                        # 扣减库存
                        TICKET_INVENTORY[event_id]['sold'] += quantity
                        order['status'] = 'success'
                        order['order_id'] = f"ORD-{ORDER_COUNTER:06d}"
                        ORDER_COUNTER += 1
                    else:
                        order['status'] = 'failed'
                        order['reason'] = '票已售罄'
                finally:
                    LockManager.release(lock_key)
        time.sleep(0.1)

# 启动订单处理线程
import threading
order_processor = threading.Thread(target=process_order_queue, daemon=True)
order_processor.start()

@app.route('/')
def index():
    return render_template('concert_index.html')

@app.route('/api/events')
def get_events():
    return jsonify([
        {
            "id": k,
            "name": v["name"],
            "total": v["total"],
            "available": v["total"] - v["sold"],
            "sold": v["sold"]
        }
        for k, v in TICKET_INVENTORY.items()
    ])

@app.route('/api/book', methods=['POST'])
def book_ticket():
    """
    抢票接口 - 使用队列处理高并发
    """
    data = request.json
    event_id = data.get('event_id')
    quantity = data.get('quantity', 1)
    user_id = data.get('user_id', 'anonymous')
    
    # 验证参数
    if event_id not in TICKET_INVENTORY:
        return jsonify({"success": False, "message": "活动不存在"})
    
    if quantity < 1 or quantity > 10:
        return jsonify({"success": False, "message": "限购1-10张"})
    
    # 先检查是否还有票（快速检查，不加锁）
    available = TICKET_INVENTORY[event_id]['total'] - TICKET_INVENTORY[event_id]['sold']
    if available < quantity:
        return jsonify({
            "success": False, 
            "message": f"票已售罄！仅剩 {available} 张"
        })
    
    # 加入订单队列
    order = {
        "event_id": event_id,
        "quantity": quantity,
        "user_id": user_id,
        "status": "pending",
        "timestamp": datetime.now().isoformat()
    }
    ORDER_QUEUE.append(order)
    
    return jsonify({
        "success": True,
        "message": "订单已提交，请稍候...",
        "queue_position": len(ORDER_QUEUE)
    })

@app.route('/api/order/status/<user_id>')
def check_order_status(user_id):
    """查询订单状态"""
    # 模拟查询
    return jsonify({"status": "processing"})

@app.route('/api/queue/stats')
def queue_stats():
    """队列状态（用于监控）"""
    return jsonify({
        "queue_length": len(ORDER_QUEUE),
        "inventory": TICKET_INVENTORY
    })

@app.route('/simulate-rush')
def simulate_rush():
    """模拟抢票高峰 - 用于测试"""
    global ORDER_COUNTER
    results = {"success": 0, "failed": 0, "pending": 0}
    
    # 模拟100个用户同时抢票
    import concurrent.futures
    
    def try_buy(i):
        event_id = random.choice([1, 2, 3])
        quantity = random.randint(1, 3)
        
        available = TICKET_INVENTORY[event_id]['total'] - TICKET_INVENTORY[event_id]['sold']
        if available < quantity:
            return "failed"
        
        order = {
            "event_id": event_id,
            "quantity": quantity,
            "user_id": f"user_{i}",
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        }
        ORDER_QUEUE.append(order)
        return "pending"
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        outcomes = list(executor.map(try_buy, range(100)))
    
    results["success"] = outcomes.count("success")
    results["pending"] = outcomes.count("pending")
    results["failed"] = outcomes.count("failed")
    results["total_events"] = {k: v["sold"] for k, v in TICKET_INVENTORY.items()}
    
    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
