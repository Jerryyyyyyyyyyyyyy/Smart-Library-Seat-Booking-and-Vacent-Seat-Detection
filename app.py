from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key")
socketio = SocketIO(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# MySQL connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("DB_PASS", "yourpassword"),
    database="library"
)
cursor = conn.cursor(dictionary=True)

class User(UserMixin):
    def __init__(self, student_id):
        self.id = student_id

@login_manager.user_loader
def load_user(student_id):
    cursor.execute("SELECT student_id FROM Students WHERE student_id=%s", (student_id,))
    user = cursor.fetchone()
    return User(user['student_id']) if user else None

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.json
        student_id = data.get("student_id")
        cursor.execute("SELECT student_id FROM Students WHERE student_id=%s", (student_id,))
        user = cursor.fetchone()
        if user:
            login_user(User(student_id))
            return jsonify({"success": True, "message": "Logged in"})
        return jsonify({"success": False, "message": "Invalid student ID"})
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = request.json
        try:
            cursor.execute(
                "INSERT INTO Students (student_id, name, email) VALUES (%s, %s, %s)",
                (data['student_id'], data['name'], data['email'])
            )
            conn.commit()
            return jsonify({"success": True, "message": "Registered successfully"})
        except mysql.connector.Error as e:
            return jsonify({"success": False, "message": str(e)})
    return render_template("register.html")  # Handle GET request

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"success": True, "message": "Logged out"})

@app.route("/map")
@login_required
def seat_map():
    return render_template("index.html")

@app.route("/seats")
def get_seats():
    cursor.execute("SELECT seat_id, status, x1, y1, x2, y2 FROM Seats")
    seats = cursor.fetchall()
    return jsonify(seats)

@app.route("/seat_count")
def seat_count():
    cursor.execute("SELECT COUNT(*) as count FROM Seats WHERE status='Vacant'")
    vacant_seats = cursor.fetchone()['count']
    return jsonify({"vacant_seats": vacant_seats})

@app.route("/user_booking")
@login_required
def user_booking():
    cursor.execute("SELECT seat_id FROM Bookings WHERE student_id=%s AND end_time > NOW()", (current_user.id,))
    booking = cursor.fetchone()
    return jsonify({"seat_id": booking['seat_id'] if booking else None})

@app.route("/book", methods=["POST"])
@login_required
def book_seat():
    data = request.json
    seat_id = data['seat_id']
    student_id = data['student_id']

    cursor.execute("SELECT status FROM Seats WHERE seat_id=%s", (seat_id,))
    seat = cursor.fetchone()

    if seat is None:
        return jsonify({"success": False, "message": "Seat not found"})
    if seat['status'] != "Vacant":
        return jsonify({"success": False, "message": "Seat not available"})

    start_time = datetime.now()
    end_time = start_time + timedelta(hours=2)

    cursor.execute(
        "INSERT INTO Bookings (seat_id, student_id, start_time, end_time) VALUES (%s,%s,%s,%s)",
        (seat_id, student_id, start_time, end_time)
    )
    cursor.execute("UPDATE Seats SET status='Booked' WHERE seat_id=%s", (seat_id,))
    conn.commit()

    socketio.emit('update_seats', {'seat_id': seat_id, 'status': 'Booked'})
    return jsonify({"success": True, "message": "Seat booked"})

def run_app():
    port = 5000
    print(f"🚀 Running on http://127.0.0.1:{port}/")
    socketio.run(app, debug=True, port=port)

if __name__ == "__main__":
    run_app()