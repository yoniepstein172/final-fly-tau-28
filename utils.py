from datetime import datetime, time, timedelta, date
from flask import flash, redirect, session
from functools import wraps
from zoneinfo import ZoneInfo #israel time zone


def complete_orders_for_finished_flight(cursor, flight_number): #Move all orders from Approved → Completed once the flight date has passed
    cursor.execute("""
        UPDATE F_Order
        SET Stat = 'Completed'
        WHERE Flight_Number = %s
          AND Stat = 'Approved'
    """, (flight_number,))


def get_cities(cursor): #from the db getting the cities so customer can choose
    cursor.execute("""
            SELECT DISTINCT Airport_Source AS city FROM Route
            UNION
            SELECT DISTINCT Destination AS city FROM Route
        """)
    results = cursor.fetchall()
    return [row["city"] for row in results]

def create_seats_for_aircraft(cursor, ac_id):

    cursor.execute("""
        SELECT Capacity_Business, Capacity_Economy, Size, Manufactur
        FROM Air_Craft
        WHERE AC_ID = %s
    """, (ac_id,))
    result = cursor.fetchone()

    if not result:
        raise Exception("Aircraft not found")

    business_cap = result["Capacity_Business"]
    economy_cap = result["Capacity_Economy"]
    size = result["Size"]
    manufacturer = result["Manufactur"]

    #  layout rules by manufacturer + size
    layout = {
        ("Boeing", "Small"):    {"Business": 4, "Economy": 6},
        ("Boeing", "Large"):    {"Business": 6, "Economy": 8},
        ("Airbus", "Small"):    {"Business": 4, "Economy": 6},
        ("Airbus", "Large"):    {"Business": 6, "Economy": 8},
        ("Dassault", "Small"):  {"Business": 2, "Economy": 4},
        ("Dassault", "Large"):  {"Business": 4, "Economy": 6},
    }

    # fallback (safety)
    columns = layout.get(
        (manufacturer, size),
        {"Business": 4, "Economy": 6}
    )

    def letters(n):
        return [chr(ord("A") + i) for i in range(n)]

    business_letters = letters(columns["Business"])
    economy_letters  = letters(columns["Economy"])

    row = 1

    # -------- Business --------
    created = 0
    while created < business_cap:
        for letter in business_letters:
            if created >= business_cap:
                break
            cursor.execute("""
                INSERT INTO Seat (AC_ID, S_Row, Letter, Class)
                VALUES (%s, %s, %s, 'Business')
            """, (ac_id, row, letter))
            created += 1
        row += 1

    # -------- Economy --------
    created = 0
    while created < economy_cap:
        for letter in economy_letters:
            if created >= economy_cap:
                break
            cursor.execute("""
                INSERT INTO Seat (AC_ID, S_Row, Letter, Class)
                VALUES (%s, %s, %s, 'Economy')
            """, (ac_id, row, letter))
            created += 1
        row += 1



def build_rows(seats):
    rows = {}

    for seat in seats:
        row_num = seat["row"]
        rows.setdefault(row_num, []).append(seat)

    structured_rows = []

    for row_num in sorted(rows.keys()):
        row_seats = sorted(rows[row_num], key=lambda s: s["letter"])

        total_cols = len(row_seats)
        left_count = total_cols // 2

        structured_rows.append({
            "left": row_seats[:left_count],
            "right": row_seats[left_count:]
        })

    return structured_rows

def build_seats(capacity, letters, seat_class, start_row):
    seats = []
    row = start_row
    count = 0

    while count < capacity:
        for letter in letters:
            if count >= capacity:
                break
            seats.append({
                "row": int(row),
                "letter": letter,
                "class": seat_class
            })
            count += 1
        row += 1

    return seats


    return seats


def update_status(cursor, flight_number): #update flight status after date has passed
    now_in_israel= datetime.now(ZoneInfo("Asia/Jerusalem")).replace(tzinfo=None)
    cursor.execute("""
        SELECT Status,Departure_Date,Departure_Time, Arrival_Date, Arrival_Time, AC_ID
        FROM Flight
        WHERE Flight_Number = %s
    """, (flight_number,))
    flight = cursor.fetchone()

    if not flight or flight["Status"] == "Canceled":
        return

    now = datetime.now()
    arrival_time = flight["Arrival_Time"]

    if isinstance(arrival_time, timedelta):
        total_seconds = int(arrival_time.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        arrival_time = time(hours, minutes, seconds)

    dep_time = flight["Departure_Time"]


    if isinstance(dep_time, timedelta):
        total_seconds = int(dep_time.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        dep_time = time(hours, minutes, seconds)

    departure_dt = datetime.combine(
        flight["Departure_Date"],
        dep_time)

    one_hour_before_departure = departure_dt - timedelta(hours=1)
    if now_in_israel >= one_hour_before_departure:
        cursor.execute("""
            UPDATE Flight
            SET Status = 'Completed'
            WHERE Flight_Number = %s""", (flight_number,))
        complete_orders_for_finished_flight(cursor, flight_number)
        return

    cursor.execute("""
        SELECT COUNT(*) AS total_seats
        FROM Seat
        WHERE AC_ID = %s
    """, (flight["AC_ID"],))
    total_seats = cursor.fetchone()["total_seats"]

    cursor.execute("""
        SELECT COUNT(*) AS taken_seats
        FROM Order_seat OS
        JOIN F_Order O ON O.O_ID = OS.O_ID
        WHERE O.Flight_Number = %s
          AND O.Stat IN ('Approved','Completed')
    """, (flight_number,))
    taken_seats = cursor.fetchone()["taken_seats"]

    if taken_seats >= total_seats and total_seats > 0:
        cursor.execute("""
            UPDATE Flight
            SET Status = 'Full_Flight'
            WHERE Flight_Number = %s
        """, (flight_number,))
    else:
        cursor.execute("""
            UPDATE Flight
            SET Status = 'Active'
            WHERE Flight_Number = %s
        """, (flight_number,))

def update_all_flights_status(cursor):
        cursor.execute("""
            SELECT Flight_Number
            FROM Flight""")
        flights = cursor.fetchall()
        for f in flights:
            update_status(cursor, f["Flight_Number"])

def check_valid_date(dep_date, dep_time): 

    if isinstance(dep_date, str):
        dep_date = datetime.strptime(dep_date, "%Y-%m-%d").date()

    if isinstance(dep_time, str):
        dep_time = datetime.strptime(dep_time, "%H:%M").time()

    dep_datetime = datetime.combine(dep_date, dep_time)
    return dep_datetime <= datetime.now()

def block_manager(f): #in use in any route not under manager features
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") == "manager":
            flash(
                "Managers are not allowed to purchase flights.",
                "error")
            return redirect("/manager/home")
        return f(*args, **kwargs)
    return wrapper


def login_required(role=None): #in use in any route required logging in
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "role" not in session:
                flash("Please login to continue.", "error")
                return redirect("/login")

            if role and session["role"] != role:
                flash("You do not have permission to access this page.", "error")
                return redirect("/")

            return f(*args, **kwargs)
        return wrapper
    return decorator
