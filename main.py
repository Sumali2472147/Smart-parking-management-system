from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask import Flask, request, jsonify
from flask_cors import CORS
import os


app = Flask(__name__)
import sqlite3


DATABASE = "parking.db"


def create_table():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        parking_name TEXT,

        vehicle TEXT,

        owner TEXT

    )
    """)

    cursor.execute("""
CREATE TABLE IF NOT EXISTS parking(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT,

    total_slots INTEGER,

    available_slots INTEGER

)
""")

    cursor.execute("""
CREATE TABLE IF NOT EXISTS users(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT,

    email TEXT UNIQUE,

    password TEXT

)
""")


    conn.commit()

    conn.close()



create_table()
CORS(app)



def add_parking_data():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()


    cursor.execute(
        "SELECT * FROM parking"
    )

    data = cursor.fetchall()


    if len(data) == 0:

        cursor.execute(
        """
        INSERT INTO parking
        (name,total_slots,available_slots)

        VALUES
        ('City Parking',5,5),
        ('Mall Parking',10,10),
        ('Railway Parking',8,8)
        """
        )


    conn.commit()

    conn.close()



add_parking_data()

@app.route("/park", methods=["POST"])
def park():

    try:

        data = request.get_json()

        vehicle = data["vehicle"]
        owner = data["owner"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()


        # Vehicle already parked check
        cursor.execute("""
            SELECT * FROM bookings
            WHERE vehicle=?
        """, (vehicle,))

        existing = cursor.fetchone()

        if existing:
            conn.close()

            return jsonify({
                "error": "Vehicle already parked"
            })


        # New vehicle add
        cursor.execute("""
            INSERT INTO bookings
            (parking_name, vehicle, owner, entry_time)
            VALUES (?, ?, ?, ?)
        """,
        (
            "Manual Parking",
            vehicle,
            owner,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))


        conn.commit()
        conn.close()


        return jsonify({
            "message": "Vehicle Added"
        })


    except Exception as e:

        print("PARK ERROR:", e)

        return jsonify({
            "error": str(e)
        }),500

@app.route("/status")
def status():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT vehicle, owner
        FROM bookings
    """)

    rows = cursor.fetchall()

    conn.close()

    vehicles = []

    for row in rows:

        vehicles.append({
            "vehicle": row[0],
            "owner": row[1]
        })

    return jsonify(vehicles)
@app.route("/exit", methods=["POST"])
def exit_vehicle():

    data = request.get_json()
    vehicle = data["vehicle"]

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT parking_name, entry_time
        FROM bookings
        WHERE vehicle=?
    """, (vehicle,))

    booking = cursor.fetchone()

    if booking is None:
        conn.close()
        return jsonify({
            "error": "Vehicle not found"
        }), 404

    parking_name = booking[0]
    entry_time = datetime.strptime(
        booking[1],
        "%Y-%m-%d %H:%M:%S"
    )

    exit_time = datetime.now()

    minutes = max(
        1,
        int((exit_time - entry_time).total_seconds() / 60)
    )

    fee = minutes * 2      # ₹2 per minute

    cursor.execute("""
        UPDATE parking
        SET available_slots = available_slots + 1
        WHERE name=?
    """, (parking_name,))

    print("Updated rows:", cursor.rowcount)

    cursor.execute(
    "SELECT name, available_slots FROM parking WHERE name=?",
    (parking_name,)
)

    print("AFTER EXIT:", cursor.fetchone())

    cursor.execute("""
        DELETE FROM bookings
        WHERE vehicle=?
    """, (vehicle,))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Vehicle Exit Successful",
        "vehicle": vehicle,
        "parking": parking_name,
        "minutes": minutes,
        "fee": fee,
        "exit_time": exit_time.strftime("%Y-%m-%d %H:%M:%S")
    })
@app.route("/book", methods=["POST"])
def book():

    try:

        data = request.get_json()

        print(data)

        parking_name = data["parking_name"]
        vehicle = data["vehicle"]
        owner = data["owner"]


        conn = sqlite3.connect(DATABASE)

        cursor = conn.cursor()


        cursor.execute(
"""
INSERT INTO bookings
(parking_name, vehicle, owner, entry_time)
VALUES (?, ?, ?, ?)
""",
(
    parking_name,
    vehicle,
    owner,
    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
)
)


        cursor.execute(
            """
            UPDATE parking

            SET available_slots = available_slots - 1

            WHERE name = ?

            AND available_slots > 0

            """,
            (parking_name,)
        )
        cursor.execute(
         "SELECT name, available_slots FROM parking WHERE name=?",
          (parking_name,)
     )

        print("UPDATED SLOT:", cursor.fetchone())


        conn.commit()
        conn.close()


        return jsonify({
            "message":"Parking Booked Successfully"
        })


    except Exception as e:

        print("BOOK ERROR:",e)

        return jsonify({
            "error":str(e)
        }),500
@app.route("/bookings")
def bookings():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM bookings"
    )

    data = cursor.fetchall()

    conn.close()

    bookings_list = []

    for row in data:
        bookings_list.append({
            "id": row[0],
            "parking_name": row[1],
            "vehicle": row[2],
            "owner": row[3]
        })

    return jsonify(bookings_list)

@app.route("/parking")
def parking():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, total_slots, available_slots FROM parking"
    )

    data = cursor.fetchall()

    conn.close()

    parking_list = []

    locations = {
        "City Parking": (31.3260, 75.5762),
        "Mall Parking": (31.3170, 75.5800),
        "Railway Parking": (31.3255, 75.5790)
    }

    for row in data:

        lat, lon = locations[row[0]]

        parking_list.append({
            "name": row[0],
            "total_slots": row[1],
            "available_slots": row[2],
            "lat": lat,
            "lon": lon
        })

    return jsonify(parking_list)



@app.route("/<path:filename>")
def files(filename):
    return send_from_directory(".", filename)

@app.route("/login")
def login_page():

    return send_from_directory(
        "frontend",
        "login.html"
    )

@app.route("/")
def home():
    return send_from_directory("frontend", "register.html")


@app.route("/dashboard")
def dashboard():
    return send_from_directory(".", "index.html")

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    name = data["name"]
    email = data["email"]
    password = data["password"]

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:

        cursor.execute("""
        INSERT INTO users
        (name,email,password)
        VALUES(?,?,?)
        """,
        (name,email,password))

        conn.commit()
        conn.close()

        return jsonify({
            "message":"Registration Successful"
        })

    except sqlite3.IntegrityError:

        return jsonify({
        "error": "Account already exists. Please login"
    })

@app.route("/login", methods=["POST"])
def login():

    try:

        data = request.get_json()

        email = data["email"]
        password = data["password"]


        conn = sqlite3.connect(
            DATABASE,
            timeout=10
        )

        cursor = conn.cursor()


        cursor.execute("""
            SELECT * FROM users
            WHERE email=? AND password=?
        """,
        (
            email,
            password
        ))


        user = cursor.fetchone()

        conn.close()


        if user:

            return jsonify({
                "message":"Login Successful"
            })

        else:

            return jsonify({
                "error":"Invalid Email or Password"
            })


    except Exception as e:

        print("LOGIN ERROR:", e)

        return jsonify({
            "error":str(e)
        }),500


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )

    
