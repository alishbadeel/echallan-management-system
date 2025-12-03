from flask import Flask, render_template, request, redirect, session, url_for
from database import get_db, init_db
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = "supersecretkey"
init_db()

# Violation → Fine Mapping
VIOLATION_FINE = {
    "Overspeeding": 15000,
    "Signal break": 20000,
    "No license": 40000,
    "Drunk driving": 20000,
    "No Helmet": 10000,
    "No seatbelt": 10000,
    "Driving without insurance": 30000,
    "Overloading passengers": 150000,
    "Wrong turn": 20000,
    "Triple riding on two wheelers": 25000,
    "Using mobilephone while driving": 15000,
    "Riding without registration number plate": 40000,
    "Causing obstruction to traffic": 30000,
    "Parking in no parking zone": 25000,
    "Speeding in public roads": 10000,
    "Driving defective vehicle": 35000
}

# ===== AUTH ROUTES =====
@app.route("/", methods=["GET"])
def auth():
    if "user_id" in session:
        return redirect("/dashboard")
    return render_template("auth.html")

@app.route("/signup", methods=["POST"])
def signup():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    if cur.fetchone():
        conn.close()
        return "Email already registered!"
    
    cur.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)", (name,email,hashed_password))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email,hashed_password))
    user = cur.fetchone()
    conn.close()

    if user:
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect("/dashboard")
    else:
        return "Invalid credentials!"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ===== DASHBOARD =====
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM challan WHERE user_id=?", (user_id,))
    total = cur.fetchone()[0]

    cur.execute("SELECT SUM(fine) FROM challan WHERE user_id=?", (user_id,))
    fines = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM challan WHERE paid=1 AND user_id=?", (user_id,))
    paid = cur.fetchone()[0]

    cur.execute("SELECT * FROM challan WHERE user_id=? ORDER BY id DESC LIMIT 10", (user_id,))
    latest = cur.fetchall()
    conn.close()

    return render_template("dashboard.html", total=total, fines=fines, paid=paid, challans=latest)

@app.route("/generate", methods=["GET", "POST"])
def generate():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        name = request.form["name"]
        vehicle = request.form["vehicle"]
        violation = request.form["violation"]
        fine = VIOLATION_FINE.get(violation, 0)
        user_id = session["user_id"]

        conn = get_db()
        cur = conn.cursor()

        # Insert challan into database
        cur.execute("""
            INSERT INTO challan(user_id, name, vehicle, fine, violation, issued_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, name, vehicle, fine, violation, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        # Redirect directly to dashboard
        return redirect("/dashboard")

    # GET request → show form
    return render_template("generate.html", violations=VIOLATION_FINE.keys())

# ===== VIEW ALL CHALLANS =====
@app.route("/viewall")
def viewall():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM challan WHERE user_id=? ORDER BY id DESC", (user_id,))
    data = cur.fetchall()
    conn.close()
    return render_template("viewall.html", challans=data)
# ===== SEARCH CHALLANS =====
@app.route("/search", methods=["GET","POST"])
def search():
    if "user_id" not in session:
        return redirect("/")

    results = []
    if request.method == "POST":
        key = request.form["query"]
        user_id = session["user_id"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""SELECT * FROM challan 
                       WHERE user_id=? AND (name LIKE ? OR vehicle LIKE ? OR CAST(id AS TEXT) LIKE ?)""",
                    (user_id, f"%{key}%", f"%{key}%", f"%{key}%"))
        results = cur.fetchall()
        conn.close()

    return render_template("search.html", challans=results)

if __name__ == "__main__":
    app.run(debug=True)





