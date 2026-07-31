from flask import session
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "repairsystem123"

# ==========================
# Path ของโปรเจกต์
# ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database
DB_PATH = os.path.join(BASE_DIR, "database.db")
print("BASE_DIR =", BASE_DIR)
print("DB_PATH =", DB_PATH)

# Upload Folder
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# สร้างโฟลเดอร์ uploads ถ้ายังไม่มี
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==========================
# ฟังก์ชันเชื่อมต่อฐานข้อมูล
# ==========================
def get_db():
    print("กำลังเชื่อมต่อฐานข้อมูล:", DB_PATH)
    return sqlite3.connect(DB_PATH)


# ==========================
# Login
# ==========================
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT username, role
        FROM users
        WHERE username=? AND password=?
        """, (username, password))

        user = cursor.fetchone()

        conn.close()

        if user:

            session["username"] = user[0]
            session["role"] = user[1]

            if user[1] == "admin":
                return redirect(url_for("dashboard_admin"))
            else:
                return redirect(url_for("dashboard_user"))

        else:
            return "<h2>Username หรือ Password ไม่ถูกต้อง</h2><a href='/'>กลับ</a>"

    return render_template("login.html")


# ==========================
# Dashboard
# ==========================
## @app.route("/dashboard") 
# def dashboard():
 #   return render_template("dashboard.html")

@app.route("/dashboard_admin")
def dashboard_admin():

    if session.get("role") != "admin":
        return "ไม่มีสิทธิ์"

    return render_template("dashboard_admin.html")

@app.route("/dashboard_user")
def dashboard_user():

    if session.get("role") != "user":
        return "ไม่มีสิทธิ์"

    return render_template("dashboard_user.html")


# ==========================
# แจ้งซ่อม
# ==========================
@app.route("/repair", methods=["GET", "POST"])
def repair():

    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        fullname = request.form["fullname"]
        department = request.form["department"]
        equipment = request.form["equipment"]
        problem = request.form["problem"]

        # รับรูปหลายรูป
        images = request.files.getlist("images")
        print("จำนวนรูป =", len(images))

        for image in images:
            print(image.filename)

        # รับวิดีโอ
        video = request.files.get("video")
        video_filename = ""

        if video and video.filename != "":
            video_filename = secure_filename(video.filename)
            video.save(
                os.path.join(app.config["UPLOAD_FOLDER"], video_filename)
            )

        conn = get_db()
        cursor = conn.cursor()

        # เพิ่มข้อมูลแจ้งซ่อม
        cursor.execute("""
        INSERT INTO repairs
        (username, fullname, department, equipment, problem, video)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["username"],
            fullname,
            department,
            equipment,
            problem,
            video_filename
        ))

        repair_id = cursor.lastrowid

        # บันทึกรูปทั้งหมด
        for image in images:

            if image and image.filename != "":

                filename = secure_filename(image.filename)

                image.save(
                    os.path.join(app.config["UPLOAD_FOLDER"], filename)
                )

                cursor.execute("""
                INSERT INTO repair_images
                (repair_id, filename)
                VALUES (?, ?)
                """, (
                    repair_id,
                    filename
                ))

        conn.commit()
        conn.close()

        # -------------------------
        # รับไฟล์วิดีโอ
        # -------------------------
        video = request.files.get("video")

        video_filename = ""

        if video and video.filename != "":
            video_filename = secure_filename(video.filename)
            video.save(os.path.join(app.config["UPLOAD_FOLDER"], video_filename))

        conn = get_db()
        cursor = conn.cursor()

        username = session["username"]

        cursor.execute("""
        INSERT INTO repairs
        (username, fullname, department, equipment, problem, video)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
        session["username"],
        fullname,
        department,
        equipment,
        problem,
        video_filename
        ))
        conn.commit()
        conn.close()

        return redirect(url_for("repair_list"))

    return render_template("repair.html")


# ==========================
# รายการแจ้งซ่อม
# ==========================
@app.route("/list")
def repair_list():

    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    if session["role"] == "admin":
        cursor.execute("SELECT * FROM repairs")
    else:
        cursor.execute(
            "SELECT * FROM repairs WHERE username=?",
            (session["username"],)
        )

    repairs = cursor.fetchall()

    repair_data = []

    for repair in repairs:

        cursor.execute("""
            SELECT filename
            FROM repair_images
            WHERE repair_id=?
        """, (repair[0],))

        images = [row[0] for row in cursor.fetchall()]

        repair_data.append({
            "repair": repair,
            "images": images
        })

    conn.close()

    return render_template(
        "list.html",
        repairs=repair_data
    )       
# ==========================
# เปลี่ยนสถานะ
# ==========================
@app.route("/status/<int:id>", methods=["GET", "POST"]) 
def status(id):

    if session.get("role") != "admin":
        return "ไม่มีสิทธิ์"
    
    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":

        new_status = request.form["status"]

        cursor.execute(
            "UPDATE repairs SET status=? WHERE id=?",
            (new_status, id)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("repair_list"))

    cursor.execute("SELECT * FROM repairs WHERE id=?", (id,))
    repair = cursor.fetchone()

    conn.close()

    return render_template("status.html", repair=repair)


# ==========================
# แสดงรูปภาพ
# ==========================
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ==========================
# ลบรายการ
# ==========================
@app.route("/delete/<int:id>")
def delete():

    if session.get("role") != "admin":
        return "ไม่มีสิทธิ์"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT filename FROM repair_images WHERE repair_id=?",
        (id,)
    )

    images = cursor.fetchall()

    for img in images:

        path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            img[0]
        )

        if os.path.exists(path):
            os.remove(path)

    cursor.execute(
        "DELETE FROM repair_images WHERE repair_id=?",
        (id,)
    )

    cursor.execute(
        "DELETE FROM repairs WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("repair_list"))


# ==========================
# Logout
# ==========================
@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("login"))


# ==========================
# Run
# ==========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)