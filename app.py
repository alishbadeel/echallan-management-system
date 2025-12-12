from flask import Flask, render_template, request, redirect, session, url_for
from database import get_db, init_db
from datetime import datetime
import hashlib
app = Flask(__name__)
app.secret_key = "supersecretkey"
# Initialize DB
init_db()
# Violation to fine mapping
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
# ---------------- AUTH ----------------
app = Flask(__name__)
app.secret_key = "supersecretkey"
@app.route("/", methods=["GET"])
def auth():
    if "user_id" in session:
        return redirect("/dashboard")
    # Always pass error variables, even if empty
    return render_template("auth.html", login_error="", signup_error="")
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
        return render_template("auth.html", signup_error="Email already registered!", login_error="")
    cur.execute(
        "INSERT INTO users(name, email, password) VALUES (?, ?, ?)",
        (name, email, hashed_password)
    )
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
    cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, hashed_password))
    user = cur.fetchone()
    conn.close()
    if user:
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect("/dashboard")
    else:
        # Pass the error to the template, don't return plain string
        return render_template("auth.html", login_error="Invalid credentials!", signup_error="")
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    user_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()
    # Total challans for the user
    cur.execute("SELECT COUNT(*) FROM challan WHERE user_id=?", (user_id,))
    total = cur.fetchone()[0]
    # Sum of fines for the user
    cur.execute("SELECT SUM(fine) FROM challan WHERE user_id=?", (user_id,))
    fines = cur.fetchone()[0] or 0
    # Latest 1 challan
    cur.execute("SELECT * FROM challan WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,))
    latest = cur.fetchall()
    conn.close()
    return render_template(
        "dashboard.html",
        total=total,
        fines=fines,
        challans=latest
    )
# ---------------- GENERATE CHALLAN ----------------
@app.route("/generate", methods=["GET", "POST"])
def generate():
    if "user_id" not in session:
        return redirect("/")
    if request.method == "POST":
        name = request.form["name"]
        vehicle = request.form["vehicle number"]
        violation = request.form["violation"]
        fine = VIOLATION_FINE.get(violation, 0)
        issued_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_id = session["user_id"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO challan(user_id, name, vehicle, fine, violation, issued_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, name, vehicle, fine, violation, issued_time))
        conn.commit()
        challan_id = cur.lastrowid
        conn.close()
        # Redirect to receipt page
        return redirect(f"/receipt/{challan_id}")
    return render_template("generate.html", violations=VIOLATION_FINE.keys())
# ---------------- RECEIPT PAGE ----------------
@app.route('/receipt/<int:challan_id>')
def receipt(challan_id):
    if "user_id" not in session:
        return redirect("/")
    user_id = session["user_id"]
    db = get_db()
    cur = db.cursor()
    # Fetch only the challan for this user
    cur.execute("SELECT * FROM challan WHERE id=? AND user_id=?", (challan_id, user_id))
    challan = cur.fetchone()
    if challan is None:
        return "Challan not found", 404
    return render_template("receipt.html", data=challan)
# ---------------- VIEW ALL CHALLANS ----------------
from datetime import datetime
@app.route("/viewall")
def viewall():
    if "user_id" not in session:
        return redirect("/")
    user_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM challan WHERE user_id=? ORDER BY id DESC", (user_id,))
    challans = cur.fetchall()
    # Format issued_at date for each challan
    formatted_challans = []
    for c in challans:
        c_dict = dict(c)
        dt = datetime.strptime(c_dict['issued_at'], "%Y-%m-%d %H:%M:%S")
        c_dict['issued_at'] = dt.strftime("%d-%m-%Y")  # Format: DD-MM-YYYY
        formatted_challans.append(c_dict)
    conn.close()
    return render_template("viewall.html", challans=formatted_challans)
# ---------------- SEARCH CHALLANS ----------------
from datetime import datetime
@app.route("/search", methods=["GET", "POST"])
def search():
    if "user_id" not in session:
        return redirect("/")
    results = []
    if request.method == "POST":
        key = request.form["query"]
        user_id = session["user_id"]
        conn = get_db()
        cur = conn.cursor()
        # Search by challan ID (exact match) and ensure it belongs to the logged-in user
        cur.execute("""
            SELECT * FROM challan 
            WHERE user_id=? AND id=?
        """, (user_id, key))
        results = cur.fetchall()
        # Format issued_at date
        formatted_results = []
        for c in results:
            c_dict = dict(c)
            dt = datetime.strptime(c_dict['issued_at'], "%Y-%m-%d %H:%M:%S")
            c_dict['issued_at'] = dt.strftime("%d-%m-%Y")  # Format: DD-MM-YYYY
            formatted_results.append(c_dict)
        conn.close()
        results = formatted_results
    return render_template("search.html", challans=results)
if __name__ == "__main__":
    app.run(debug=True)  # PythonAnywhere uses WSGI, so this is fine for local testing






