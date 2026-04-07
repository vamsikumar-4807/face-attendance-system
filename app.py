from flask import Flask, render_template, request, redirect, session, send_file
import subprocess
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "vamsi_secret_key"

# ==============================
# DATABASE SETUP
# ==============================

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first TEXT,
            last TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ==============================
# LOGIN PAGE
# ==============================

@app.route("/")
def login():
    return render_template("login.html")

# ==============================
# REGISTER PAGE
# ==============================

@app.route("/register")
def register():
    return render_template("register.html")

# ==============================
# CREATE ACCOUNT
# ==============================

@app.route("/create", methods=["POST"])
def create_account():
    first = request.form["first"]
    last = request.form["last"]
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO users (first, last, email, password) VALUES (?, ?, ?, ?)",
            (first, last, email, password)
        )
        conn.commit()
        conn.close()
        return redirect("/")
    except:
        conn.close()
        return "Email already exists!"

# ==============================
# LOGIN ACTION
# ==============================

@app.route("/login", methods=["POST"])
def login_post():
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, password)
    )
    user = c.fetchone()
    conn.close()

    if user:
        session["user"] = email
        return redirect("/dashboard")

    return "Invalid Email or Password"

# ==============================
# DASHBOARD
# ==============================

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")

# ==============================
# START ATTENDANCE (Camera + Download)
# ==============================

@app.route("/start")
def start_attendance():

    # Run attendance script (camera opens)
    process = subprocess.Popen(
        ["py", "-3.11", "attendance_30s.py"]
    )

    process.wait()  # Wait until 30 sec capture finishes

    file_path = "attendance.csv"

    if os.path.exists(file_path):
        return send_file(
            file_path,
            as_attachment=True,
            download_name="Attendance_Report.csv"
        )

    return "Attendance file not found!"

# ==============================
# LOGOUT
# ==============================

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# ==============================

if __name__ == "__main__":
    app.run(debug=True)
