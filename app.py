from flask import Flask, render_template, request, jsonify,session
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
# Enable sessions by setting a secret key (change this to a random string)
app.secret_key = "super_secret_safespace_key_12345" 

# Support credentials sharing across origins for admin sessions
CORS(app, supports_credentials=True)

DATABASE = "database/safespace.db"

# 🔐 CHOOSE YOUR ADMIN PASSWORD HERE
ADMIN_PASSWORD = "Lilith111@@" 

# --- DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vent_id INTEGER,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vent_id) REFERENCES vents (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'available',
            room_link TEXT DEFAULT NULL,
            customer_email TEXT,
            customer_phone TEXT,
            utr TEXT,
            payment_status TEXT DEFAULT 'payment_pending'
        )
    ''')

    new_columns = [
        ("customer_email", "TEXT"),
        ("customer_phone", "TEXT"),
        ("utr", "TEXT"),
        ("payment_status", "TEXT DEFAULT 'payment_pending'")
    ]

    for column_name, column_type in new_columns:
        try:
            cursor.execute(
                f"ALTER TABLE bookings ADD COLUMN {column_name} {column_type}"
            )
        except sqlite3.OperationalError:
            pass

    cursor.execute("SELECT COUNT(*) FROM bookings")

    if cursor.fetchone()[0] == 0:
        default_slots = [
            ("Today", "4:00 PM"),
            ("Today", "6:00 PM"),
            ("Today", "8:00 PM"),
            ("Tomorrow", "10:00 AM"),
            ("Tomorrow", "2:00 PM")
        ]

        cursor.executemany(
            "INSERT INTO bookings (date, time, status) VALUES (?, ?, 'available')",
            default_slots
        )

    conn.commit()
    conn.close()


# --- ADMIN SECURITY CHECK UTILITY ---
def is_admin_authenticated():
    return session.get('is_admin') == True

# --- ADMIN AUTHENTICATION API ---
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    password = data.get('password')
    if password == ADMIN_PASSWORD:
        session['is_admin'] = True
        return jsonify({"status": "success", "message": "Authenticated successfully"}), 200
    return jsonify({"error": "Invalid password"}), 401

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('is_admin', None)
    return jsonify({"status": "success"}), 200

@app.route('/api/admin/check', methods=['GET'])
def admin_check():
    if is_admin_authenticated():
        return jsonify({"authenticated": True}), 200
    return jsonify({"authenticated": False}), 401

# --- ADMIN DELETION ENDPOINTS ---

# Delete a Vent (and all of its replies)
@app.route('/api/admin/vents/<int:vent_id>', methods=['DELETE'])
def delete_vent(vent_id):
    if not is_admin_authenticated():
        return jsonify({"error": "Unauthorized"}), 403
        
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Delete child replies first to maintain relational database integrity
    cursor.execute("DELETE FROM replies WHERE vent_id = ?", (vent_id,))
    cursor.execute("DELETE FROM vents WHERE id = ?", (vent_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"}), 200

# Reset a booked slot back to 'available'
@app.route('/api/admin/slots/<int:slot_id>/reset', methods=['POST'])
def reset_slot(slot_id):
    if not is_admin_authenticated():
        return jsonify({"error": "Unauthorized"}), 403
        
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status = 'available', room_link = NULL WHERE id = ?", (slot_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "reset"}), 200

# Delete a slot entirely from the schedule
@app.route('/api/admin/slots/<int:slot_id>', methods=['DELETE'])
def delete_slot(slot_id):
    if not is_admin_authenticated():
        return jsonify({"error": "Unauthorized"}), 403
        
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookings WHERE id = ?", (slot_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"}), 200

# Add a brand-new slot to the schedule manually
@app.route('/api/admin/slots', methods=['POST'])
def add_slot():
    if not is_admin_authenticated():
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.get_json()
    date = data.get('date')
    time = data.get('time')
    
    if not date or not time:
        return jsonify({"error": "Missing date or time"}), 400
        
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO bookings (date, time, status) VALUES (?, ?, 'available')", (date, time))
    conn.commit()
    conn.close()
    return jsonify({"status": "created"}), 201

# --- PUBLIC ROUTINES (KEEP EXISTING BACKEND FUNCTIONALITY) ---
@app.route('/api/vents', methods=['GET'])
def get_vents():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, content FROM vents ORDER BY id DESC")
    vents = cursor.fetchall()
    
    result = []
    for vent in vents:
        vent_id, content = vent
        cursor.execute("SELECT content FROM replies WHERE vent_id = ? ORDER BY id ASC", (vent_id,))
        replies = [{"content": r[0]} for r in cursor.fetchall()]
        result.append({
            "id": vent_id,
            "content": content,
            "replies": replies
        })
    conn.close()
    return jsonify(result), 200

@app.route('/api/vents', methods=['POST'])
def post_vent():
    data = request.get_json()
    content = data.get('content', '').strip()
    if not content:
        return jsonify({"error": "Content cannot be empty"}), 400
        
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO vents (content) VALUES (?)", (content,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 201

@app.route('/api/vents/<int:vent_id>/reply', methods=['POST'])
def post_reply(vent_id):
    data = request.get_json()
    content = data.get('content', '').strip()
    if not content:
        return jsonify({"error": "Reply cannot be empty"}), 400
        
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO replies (vent_id, content) VALUES (?, ?)", (vent_id, content))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 201

@app.route('/api/slots', methods=['GET'])
def get_slots():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, time, status, room_link FROM bookings")
    slots = cursor.fetchall()
    conn.close()
    
    result = []
    for s in slots:
        result.append({
            "id": s[0],
            "date": s[1],
            "time": s[2],
            "status": s[3],
            "room_link": s[4]
        })
    return jsonify(result), 200

@app.route('/api/book-session', methods=['POST'])
def book_session():

    data = request.get_json()

    slot_id = data.get("slot_id")
    email = data.get("email")
    phone = data.get("phone")
    utr = data.get("utr")

    if not email or not phone or not utr:
        return jsonify({"error": "Please complete all fields."}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT status FROM bookings WHERE id=?",
        (slot_id,)
    )

    slot = cursor.fetchone()

    if not slot:
        conn.close()
        return jsonify({"error":"Slot not found."}),404

    if slot[0] == "booked":
        conn.close()
        return jsonify({"error":"This slot has already been booked."}),400

    cursor.execute("""
        UPDATE bookings
        SET
            status='booked',
            customer_email=?,
            customer_phone=?,
            utr=?,
            payment_status='verification_pending'
        WHERE id=?
    """,
    (
        email,
        phone,
        utr,
        slot_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "status":"success"
    }),200


    
# Serve the main homepage
@app.route('/')
def home():
    return render_template("index.html")

# Serve the private admin panel
@app.route('/admin')
def admin_panel():
    return render_template("admin.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

import os

if __name__ == '__main__':
    init_db()  
    # Tells Flask to listen on the port Render assigns, defaulting to 5000 locally
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)