from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'tickety-secret-key-2026'

# In-memory data store (use database in production)
EVENTS = [
    {
        "id": 1,
        "title": "Jay Chou World Tour 2026",
        "date": "Apr 15, 2026",
        "venue": "Hong Kong Coliseum",
        "price": 880,
        "category": "Concerts",
        "emoji": "🎤",
        "status": "active",
        "image": "concert.jpg"
    },
    {
        "id": 2,
        "title": "Mayday Noah's Ark Concert",
        "date": "Apr 20, 2026",
        "venue": "Central Harbourfront",
        "price": 980,
        "category": "Concerts",
        "emoji": "🎸",
        "status": "active",
        "image": "concert.jpg"
    },
    {
        "id": 3,
        "title": "Cats - Original Musical",
        "date": "May 01, 2026",
        "venue": "Hong Kong Arts Centre",
        "price": 680,
        "category": "Theater",
        "emoji": "🐱",
        "status": "active",
        "image": "theater.jpg"
    }
]

ORDERS = []

# Admin credentials (use hashed passwords in production)
ADMIN_USER = "admin"
ADMIN_PASS = "tickety123"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_login():
    if session.get('admin_logged_in'):
        return redirect('/admin/dashboard')
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == ADMIN_USER and password == ADMIN_PASS:
        session['admin_logged_in'] = True
        return redirect('/admin/dashboard')
    return render_template('admin_login.html', error="Invalid credentials")

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    
    # Calculate stats in Python
    active_count = sum(1 for e in EVENTS if e.get('status') == 'active')
    revenue = sum(o.get('total', 0) for o in ORDERS)
    
    return render_template('admin_dashboard.html', 
                          events=EVENTS, 
                          orders=ORDERS,
                          active_count=active_count,
                          revenue=revenue)

# Event Management
@app.route('/admin/event/add', methods=['GET', 'POST'])
def add_event():
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    
    if request.method == 'POST':
        new_event = {
            "id": len(EVENTS) + 1,
            "title": request.form.get('title'),
            "date": request.form.get('date'),
            "venue": request.form.get('venue'),
            "price": int(request.form.get('price')),
            "category": request.form.get('category'),
            "emoji": request.form.get('emoji', '🎫'),
            "status": "active",
            "image": "event.jpg"
        }
        EVENTS.append(new_event)
        return redirect('/admin/dashboard')
    
    return render_template('add_event.html')

@app.route('/admin/event/<int:event_id>/toggle', methods=['POST'])
def toggle_event(event_id):
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    for event in EVENTS:
        if event['id'] == event_id:
            event['status'] = 'inactive' if event['status'] == 'active' else 'active'
            return jsonify({"success": True, "status": event['status']})
    
    return jsonify({"error": "Event not found"}), 404

@app.route('/admin/event/<int:event_id>/delete', methods=['POST'])
def delete_event(event_id):
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    global EVENTS
    EVENTS = [e for e in EVENTS if e['id'] != event_id]
    return jsonify({"success": True})

@app.route('/admin/event/<int:event_id>/edit', methods=['GET', 'POST'])
def edit_event(event_id):
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    
    event = next((e for e in EVENTS if e['id'] == event_id), None)
    if not event:
        return "Event not found", 404
    
    if request.method == 'POST':
        event['title'] = request.form.get('title')
        event['date'] = request.form.get('date')
        event['venue'] = request.form.get('venue')
        event['price'] = int(request.form.get('price'))
        event['category'] = request.form.get('category')
        return redirect('/admin/dashboard')
    
    return render_template('edit_event.html', event=event)

@app.route('/admin/event/<int:event_id>/update-image', methods=['POST'])
def update_event_image(event_id):
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    for event in EVENTS:
        if event['id'] == event_id:
            # In production, save image to disk and update path
            event['emoji'] = request.form.get('emoji', event.get('emoji', '🎫'))
            return jsonify({"success": True, "emoji": event['emoji']})
    
    return jsonify({"error": "Event not found"}), 404

# Smart Pricing
@app.route('/admin/pricing')
def smart_pricing():
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    return render_template('smart_pricing.html', events=EVENTS)

@app.route('/api/scrape-prices', methods=['POST'])
def scrape_prices():
    """Mock price scraping - in production, use real web scraping"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    event_title = data.get('title', '')
    
    # Mock scraped data (in production, scrape real sites)
    mock_prices = {
        "Jay Chou": [
            {"source": "Cityline", "price": 880, "url": "https://cityline.com"},
            {"source": "Ticketflux", "price": 950, "url": "https://ticketflux.com"},
            {"source": "Viagogo", "price": 1200, "url": "https://viagogo.com"}
        ],
        "Mayday": [
            {"source": "Cityline", "price": 980, "url": "https://cityline.com"},
            {"source": "StubHub", "price": 1050, "url": "https://stubhub.com"}
        ],
        "default": [
            {"source": "Cityline", "price": 500, "url": "https://cityline.com"},
            {"source": "Resale", "price": 650, "url": "https://resale.com"}
        ]
    }
    
    # Find matching prices
    prices = []
    for key, data in mock_prices.items():
        if key.lower() in event_title.lower():
            prices = data
            break
    
    if not prices:
        prices = mock_prices["default"]
    
    # Calculate recommended price (average of competitors)
    avg_price = sum(p['price'] for p in prices) // len(prices)
    
    return jsonify({
        "event": event_title,
        "competitor_prices": prices,
        "recommended_price": avg_price,
        "market_analysis": f"Market average: HK${avg_price}. Prices range from HK${min(p['price'] for p in prices)} to HK${max(p['price'] for p in prices)}"
    })

@app.route('/admin/event/<int:event_id>/update-price', methods=['POST'])
def update_event_price(event_id):
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    new_price = request.json.get('price')
    for event in EVENTS:
        if event['id'] == event_id:
            event['price'] = new_price
            return jsonify({"success": True, "price": new_price})
    
    return jsonify({"error": "Event not found"}), 404

# Payment (Mock)
@app.route('/api/order', methods=['POST'])
def create_order():
    data = request.json
    event_id = data.get('event_id')
    ticket_type = data.get('ticket_type', 'Standard')
    quantity = data.get('quantity', 1)
    
    event = next((e for e in EVENTS if e['id'] == event_id), None)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    
    # Calculate price based on type
    multiplier = 1.5 if ticket_type == 'VIP' else (2 if ticket_type == 'Premium' else 1)
    total = event['price'] * multiplier * quantity
    
    order = {
        "id": len(ORDERS) + 1,
        "event_id": event_id,
        "event_title": event['title'],
        "ticket_type": ticket_type,
        "quantity": quantity,
        "total": total,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    ORDERS.append(order)
    
    return jsonify({
        "success": True,
        "order": order,
        "payment_url": f"/payment/{order['id']}"
    })

@app.route('/payment/<int:order_id>')
def payment_page(order_id):
    order = next((o for o in ORDERS if o['id'] == order_id), None)
    if not order:
        return "Order not found", 404
    return render_template('payment.html', order=order)

@app.route('/payment/<int:order_id>/process', methods=['POST'])
def process_payment(order_id):
    order = next((o for o in ORDERS if o['id'] == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    # Mock payment processing
    order['status'] = 'paid'
    order['paid_at'] = datetime.now().isoformat()
    
    return jsonify({
        "success": True,
        "message": "Payment successful!",
        "order": order
    })

# API endpoints for frontend
@app.route('/api/events')
def get_events():
    active_events = [e for e in EVENTS if e['status'] == 'active']
    return jsonify(active_events)

@app.route('/api/event/<int:event_id>')
def get_event(event_id):
    event = next((e for e in EVENTS if e['id'] == event_id), None)
    if event:
        return jsonify(event)
    return jsonify({"error": "Event not found"}), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
