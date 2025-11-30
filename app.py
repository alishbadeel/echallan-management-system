from flask import Flask, render_template, request, redirect
from database import get_db, init_db
from datetime import datetime
app = Flask(__name__)
init_db()

@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM challan")
    total = cur.fetchone()[0]

    cur.execute("SELECT SUM(fine) FROM challan")
    fines = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM challan WHERE paid=1")
    paid = cur.fetchone()[0]

    cur.execute("SELECT * FROM challan ORDER BY id DESC LIMIT 10")
    latest = cur.fetchall()

    return render_template("index.html",
        total=total,
        fines=fines,
        paid=paid,
        challans=latest
    )

@app.route("/generate", methods=["GET","POST"])
def generate():
    if request.method == "POST":
        name = request.form["name"]
        vehicle = request.form["vehicle"]
        violation = request.form["violation"]
        fine = request.form["fine"]

        conn = get_db()
        conn.execute("""
        INSERT INTO challan(name, vehicle, fine, violation, issued_at)
        VALUES (?,?,?,?,?)
        """, (name, vehicle, fine, violation,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return redirect("/")
    return render_template("generate.html")

@app.route("/viewall")
def viewall():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM challan ORDER BY id DESC")
    data = cur.fetchall()
    return render_template("viewall.html", challans=data)

@app.route("/markpaid/<int:id>")
def markpaid(id):
    conn = get_db()
    conn.execute("UPDATE challan SET paid=1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/viewall")

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        key = request.form["query"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM challan WHERE
            name LIKE ? OR vehicle LIKE ? OR id LIKE ?
        """, (f"%{key}%", f"%{key}%", f"%{key}%"))
        return render_template("search.html", challans=cur.fetchall())
    
    return render_template("search.html")


if __name__ == "__main__":
    app.run(debug=True)

