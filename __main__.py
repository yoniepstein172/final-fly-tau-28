from flask import Flask, request, redirect,session, render_template, flash
import mysql.connector as mdb
from contextlib import contextmanager
from functools import wraps
import uuid #import that will make up order id
import math
from datetime import date, datetime, timedelta, time
from flask_session import Session
from utils import *


app=Flask(__name__)
app.secret_key = "flytau-secret-key"

app.config.update(
    SESSION_TYPE= 'filesystem',
    SESSION_FILE_DIR= '/flask_session_data',
    SESSION_PERMANENT= True,
    PERMANENT_SESSION_LIFETIME= timedelta(minutes=10),
    SESSION_REFRESH_EACH_REQUEST=True,
    SESSION_COOKIE_SECURE=True)

Session(app)

@app.errorhandler(404)
def page_not_found(e):
    flash("You were redirected to the home page because the page you tried to access does not exist.", "error")
    return redirect("/")

@app.errorhandler(403)
def forbidden(e):
    flash("You do not have permission to access that page. You were redirected to the home page.", "error")
    return redirect("/")

@app.errorhandler(500)
def internal_error(e):
    flash("Something went wrong. You were redirected to the home page.", "error")
    return redirect("/")




@contextmanager
def db_cursor():
    conn = mdb.connect(
        host="localhost",
        user="root",
        password="root",
        database="FLYTAU")
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
        conn.commit()
    except mdb.Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

@app.route("/") #home page, customer clicking if in registered/not
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
@block_manager
def register():
    if request.method == "POST":
        email = request.form["email"]
        first = request.form["first_name"]
        last = request.form["last_name"]
        passport = request.form["passport"]
        password = request.form["password"]
        phones = request.form.getlist("phones[]")
        birth = request.form["birth_date"]
        try:
            with db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO Registered_Customer
                    (R_Email, First_Name_E, Last_Name_E,
                     Passport_Num, Register_Date,
                     Birth_Date, C_Password)
                    VALUES (%s,%s,%s,%s,CURDATE(),%s,%s)""",(email, first, last, passport, birth, password))
                for phone in phones:
                    phone = phone.strip()
                    if phone:
                        cursor.execute("""
                            INSERT INTO Phone_Numbers_Registered_Customers (R_Email, Phone_Number)
                            VALUES (%s, %s)""", (email, phone))
            session.clear()
            session["user"] = email
            session["role"] = "customer"
            return redirect("/customer/home")
        except mdb.Error as e:
            return render_template("register.html", error="Registration failed")

    return render_template("register.html",today=date.today()) #if method=get

@app.route("/login", methods=["GET", "POST"])
@block_manager
def login():
    if request.method == "POST":
        identifier = request.form["email"]
        password = request.form["password"]

        with db_cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM Manager
                WHERE M_ID = %s AND M_Password = %s
            """, (identifier, password))
            manager = cursor.fetchone()

            if manager:
                session["user"] = identifier
                session["role"] = "manager"
                return redirect("/manager/home")

            cursor.execute("""
                SELECT *
                FROM Registered_Customer
                WHERE R_Email = %s AND C_Password = %s
            """, (identifier, password))
            customer = cursor.fetchone()

            if customer:
                session.clear()
                session["user"] = identifier
                session["role"] = "customer"
                return redirect("/customer/home")
        return render_template("login.html", error="Invalid email or password")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect("/")

@app.route("/guest") #if customer ig only guest
@block_manager
def guest_login():
    session["role"] = "guest"
    return redirect("/choose-flights")



@app.route("/choose-flights") #entering wanted details of flight
@block_manager
def choose_flight():
    with db_cursor() as cursor:
        cities = get_cities(cursor)
    return render_template("choose_flights.html", cities=cities)
@app.route("/flights-results")
@block_manager
def flight_results():

    date = request.args.get("date")
    from_city = request.args.get("from_city")
    to_city = request.args.get("to_city")

    with db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                F.Flight_Number,
                R.Airport_Source,
                R.Destination,
                F.Status,
                F.Departure_Date,
                F.Departure_TIME,
                F.Price_Economy,
                F.Price_Business
            FROM Flight F
            JOIN Route R 
              ON F.R_ID = R.R_ID AND F.Duration = R.Duration
            WHERE R.Airport_Source = %s
              AND R.Destination = %s
              AND F.Status = 'Active'
              AND TIMESTAMP(F.Departure_Date, F.Departure_Time) 
                  > DATE_ADD(NOW(), INTERVAL 1 HOUR)
              AND F.Departure_Date = %s
        """, (from_city, to_city, date))

        flights = cursor.fetchall()

    return render_template("flights_results.html", flights=flights)

@app.route("/guest/my-order", methods=["GET", "POST"])
def guest_my_order():
    error = None
    order = None
    if request.method == "POST":
        order_id = request.form["order_id"].strip()
        email = request.form["email"].strip()

        with db_cursor() as cursor:
            cursor.execute("""SELECT 
                    O.O_ID,
                    O.Order_Date,
                    O.Stat,
                    O.Price,
                    F.Flight_Number,
                    F.Departure_Date,
                    R.Airport_Source,
                    R.Destination
                FROM F_Order O
                JOIN Flight F ON O.Flight_Number = F.Flight_Number
                JOIN Route R ON F.R_ID = R.R_ID 
                WHERE O.O_ID = %s
                  AND (
                       (O.User_Type = 'NonRegistered_Customers' AND O.Email = %s)
                    OR (O.User_Type = 'Registered_Customers' AND O.R_Email = %s)
                  )
            """, (order_id, email, email))
            order = cursor.fetchone()

        if not order:
            error="Order not found. Please check your details."

    return render_template(
        "guest_my_order.html",order=order,error=error)

@app.route("/flight-board")
@block_manager
def flight_board():
    with db_cursor() as cursor:
        update_all_flights_status(cursor)
        cursor.execute("""
            SELECT 
                F.Flight_Number,
                R.Airport_Source,
                R.Destination,
                F.Departure_Date,
                F.Departure_Time,
                F.Arrival_Time,
                F.Status
            FROM Flight F
            JOIN Route R
              ON F.R_ID = R.R_ID AND F.Duration = R.Duration
              WHERE F.Status="Active"
            ORDER BY F.Departure_Date, F.Departure_Time
        """)
        flights = cursor.fetchall()

    return render_template("flight_board.html", flights=flights)

@app.route("/customer/home")
@block_manager
@login_required("customer")
def customer_home():
    with db_cursor() as cursor:
        update_all_flights_status(cursor)
    email = session["user"]
    status = request.args.get("status")

    query = """
        SELECT 
            O.O_ID,
            O.Order_Date,
            O.Stat,
            O.Price,
            F.Flight_Number,
            F.Departure_Date,
            R.Airport_Source,
            R.Destination
        FROM F_Order O
        JOIN Flight F ON O.Flight_Number = F.Flight_Number
        JOIN Route R ON F.R_ID = R.R_ID AND F.Duration = R.Duration
        WHERE( O.R_Email = %s AND O.User_Type = 'Registered_Customers')
        OR (O.User_Type = 'NonRegistered_Customers' AND O.Email = %s)
        
    """

    params = [email,email]

    if status:
        query += " AND O.Stat = %s"
        params.append(status)

    query += " ORDER BY O.Order_Date DESC"

    with db_cursor() as cursor:
        cursor.execute(query, params)
        orders = cursor.fetchall()

    return render_template(
        "customer_home.html",
        orders=orders,
        selected_status=status)


@app.route("/flight/<flight_number>/seats", methods=["GET", "POST"])
@block_manager
def seat_selection(flight_number):

    if session.get("current_flight") != flight_number:
        session["current_flight"] = flight_number
        session.pop("selected_seats", None)
        session["selected_seats"] = []

    if "selected_seats" not in session:
        session["selected_seats"] = []

    if request.method == "POST":
        seat = {
            "row": int(request.form["row"]),
            "letter": request.form["letter"],
            "class": request.form["class"]
        }
        if seat in session["selected_seats"]:
            session["selected_seats"].remove(seat)
        else:
            session["selected_seats"].append(seat)
        session.modified = True

    with db_cursor() as cursor:
        update_all_flights_status(cursor)

        # Flight info
        cursor.execute("""
            SELECT F.Flight_Number, R.Airport_Source, R.Destination
            FROM Flight F
            JOIN Route R
              ON F.R_ID = R.R_ID AND F.Duration = R.Duration
            WHERE F.Flight_Number = %s
        """, (flight_number,))
        flight_info = cursor.fetchone()

        # Aircraft
        cursor.execute("""
            SELECT AC.AC_ID, AC.Capacity_Business, AC.Capacity_Economy,
                   F.Price_Economy, F.Price_Business
            FROM Flight F
            JOIN Air_Craft AC ON F.AC_ID = AC.AC_ID
            WHERE F.Flight_Number = %s
        """, (flight_number,))
        aircraft = cursor.fetchone()
        session["aircraft_id"] = aircraft["AC_ID"]

        # Create seats if needed
        cursor.execute("""
            SELECT COUNT(*) AS cnt FROM Seat WHERE AC_ID = %s
        """, (aircraft["AC_ID"],))
        if cursor.fetchone()["cnt"] == 0:
            create_seats_for_aircraft(cursor, aircraft["AC_ID"])

        # Taken seats
        cursor.execute("""
            SELECT OS.S_Row, OS.Letter, S.Class
            FROM Order_seat OS
            JOIN F_Order O ON O.O_ID = OS.O_ID
            JOIN Seat S
              ON S.AC_ID = OS.AC_ID
             AND S.S_Row = OS.S_Row
             AND S.Letter = OS.Letter
            WHERE O.Flight_Number = %s
        """, (flight_number,))

        taken_seats = [{
            "row": int(s["S_Row"]),
            "letter": s["Letter"],
            "class": s["Class"]
        } for s in cursor.fetchall()]
        taken_set = {(s["row"], s["letter"]) for s in taken_seats}

        # All seats from DB
        cursor.execute("""
            SELECT S_Row, Letter, Class
            FROM Seat
            WHERE AC_ID = %s
            ORDER BY S_Row, Letter
        """, (aircraft["AC_ID"],))
        all_seats = cursor.fetchall()

    # build rows
    business_seats = []
    economy_seats = []

    for s in all_seats:
        seat = {
            "row": int(s["S_Row"]),
            "letter": s["Letter"],
            "class": s["Class"]
        }
        if s["Class"] == "Business":
            business_seats.append(seat)
        else:
            economy_seats.append(seat)

    business_rows = build_rows(business_seats)
    economy_rows = build_rows(economy_seats)

    return render_template(
        "seat_selection.html",
        flight_number=flight_number,
        flight_info=flight_info,
        aircraft=aircraft,
        selected_seats=session["selected_seats"],
        taken_seats=taken_seats,
        taken_set=taken_set,
        business_rows=business_rows,
        economy_rows=economy_rows)


@app.route("/flight/<flight_number>/order-summary", methods=["GET"])
@block_manager
def order_summary(flight_number):
    selected_seats = session.get("selected_seats", [])
    if not selected_seats:
        return redirect(f"/flight/{flight_number}/seats")

    with db_cursor() as cursor:
        # Flight info
        cursor.execute("""
            SELECT 
                F.Flight_Number,
                R.Airport_Source,
                R.Destination,
                F.Price_Economy,
                F.Price_Business
            FROM Flight F
            JOIN Route R
              ON F.R_ID = R.R_ID
             AND F.Duration = R.Duration
            WHERE F.Flight_Number = %s
        """, (flight_number,))
        flight_info = cursor.fetchone()
        session["current_flight"] = flight_number

    # Price calculation
    economy_count = sum(1 for s in selected_seats if s["class"] == "Economy")
    business_count = sum(1 for s in selected_seats if s["class"] == "Business")

    total_price = (
        economy_count * flight_info["Price_Economy"] +
        business_count * flight_info["Price_Business"])
    session["total_price"] = total_price

    return render_template(
        "order_summary.html",
        flight_info=flight_info,
        selected_seats=selected_seats,
        economy_count=economy_count,
        business_count=business_count,
        total_price=total_price)

@app.route("/Confirmation")
@block_manager
def confirmation():
    role = session.get("role")
    if role == "guest":
        return redirect("/guest-details")
    elif role == "customer":
        return redirect("/purchase")

@app.route("/guest-details", methods=["GET", "POST"])
@block_manager
def guest_details():

    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        phones = request.form.getlist("phones[]")
        with db_cursor() as cursor:
            cursor.execute("""
                            SELECT 1
                            FROM NonRegistered_Customer
                            WHERE Email = %s
                        """, (email,))
            exists = cursor.fetchone()
            if not exists:
                cursor.execute("""
                     INSERT INTO NonRegistered_Customer
                     (Email, First_Name_E, Last_Name_E)
                     VALUES (%s, %s, %s)
                 """, (email, first_name, last_name))
                for phone in phones:
                    phone = phone.strip()
                    if not phone:
                        continue
                    cursor.execute("""
                        SELECT 1
                        FROM Phone_Numbers_NonRegistered_Customers
                        WHERE Email = %s AND Phone_Number = %s
                    """, (email, phone))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO Phone_Numbers_NonRegistered_Customers
                            (Email, Phone_Number)
                            VALUES (%s, %s)
                        """, (email, phone))
        session["guest_info"]= {"email":email, "first_name":first_name, "last_name":last_name, "phones":phones}
        session["user"]=email
        session["role"]="guest"
        return redirect("/purchase")

    return render_template("guest_details.html")


@app.route("/purchase")
@block_manager
def purchase():
    selected_seats = session.get("selected_seats", [])
    flight_number = session.get("current_flight")
    role = session.get("role")

    if not selected_seats or not flight_number:
        return redirect("/")

    with (db_cursor() as cursor):
        order_id = str(uuid.uuid4())

        if role == "customer":
            email = session["user"]

            cursor.execute("""
                INSERT INTO F_Order
                (O_ID, Stat, Order_Date, Price, User_Type, R_Email, Flight_Number)
                VALUES (%s, 'Approved', CURDATE(), %s, 'Registered_Customers', %s, %s)
            """, (order_id, session["total_price"], email, flight_number))
        else:
            guest = session.get("guest_info")
            if not guest:
                return redirect("/guest-details")

            # check if guest already exists
            cursor.execute("""
                SELECT 1
                FROM NonRegistered_Customer
                WHERE Email = %s
            """, (guest["email"],))

            exists = cursor.fetchone()
            if not exists:
                cursor.execute("""
                    INSERT INTO NonRegistered_Customer
                    (Email, First_Name_E, Last_Name_E)
                    VALUES (%s, %s, %s)
                """, (guest["email"], guest["first_name"], guest["last_name"]))

            for phone in guest["phones"]:
                cursor.execute("""
                    SELECT 1
                    FROM Phone_Numbers_NonRegistered_Customers
                    WHERE Email = %s AND Phone_Number = %s
                """, (guest["email"], phone))

                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO Phone_Numbers_NonRegistered_Customers
                        (Email, Phone_Number)
                        VALUES (%s, %s)
                    """, (guest["email"], phone))

            cursor.execute("""
                INSERT INTO F_Order
                (O_ID, Stat, Order_Date, Price, User_Type, Email, Flight_Number)
                VALUES (%s, 'Approved', CURDATE(), %s, 'NonRegistered_Customers', %s, %s)
            """, (order_id, session["total_price"], guest["email"], flight_number))

#איפה משתמשים בזה?
        for seat in selected_seats:
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM Seat WHERE AC_ID = %s",
                (session["aircraft_id"],))
            count= cursor.fetchone()

            cursor.execute("""
                INSERT INTO Order_seat
                (O_ID, AC_ID, S_Row, Letter)
                VALUES (%s, %s, %s, %s)
            """, (order_id, session["aircraft_id"], seat["row"], seat["letter"]))
        session["order_id"] = order_id

        if role == "customer":
            email = session["user"]
            cursor.execute("""
                SELECT First_Name_E
                FROM Registered_Customer
                WHERE R_Email = %s
            """, (email,))
            customer = cursor.fetchone()

            session["customer_name"] = customer["First_Name_E"]
        else:
            session["customer_name"] = guest["first_name"]

        return redirect("/order-confirmation")

@app.route("/order-confirmation")
@block_manager
def order_confirmation():
    order_id = session.get("order_id")
    customer_name = session.get("customer_name")

    if not order_id or not customer_name:
        return redirect("/")

    return render_template(
        "order_confirmation.html",
        order_id=order_id,
        customer_name=customer_name)


@app.route("/manager-login", methods=["GET", "POST"])
def manager_login():
    if request.method == "POST":
        manager_id = request.form["manager_id"]
        password = request.form["password"]

        with db_cursor() as cursor:
            cursor.execute("""
                SELECT M_ID
                FROM Manager
                WHERE M_ID = %s AND M_Password = %s
            """, (manager_id, password))

            manager = cursor.fetchone()

        if manager:
            session.clear()
            session["user"] = manager_id
            session["role"] = "manager"
            return redirect("/manager/home")
        return render_template("manager_login.html",error="Invalid manager ID or password")
    return render_template("manager_login.html",error="Invalid manager credentials")

@app.route("/manager/home")
@login_required("manager")
def manager_home():
    manager_id = session.get("user")
    return render_template("manager_home.html", manager_id=manager_id)

@app.route("/manager/add-flight", methods=["GET", "POST"])
@login_required("manager")
def add_flight():
    step = request.form.get("step", "1")

    with db_cursor() as cursor:
        if request.method == "GET":
            cursor.execute("""
                SELECT R_ID, Airport_Source, Destination, Duration
                FROM Route
                ORDER BY Airport_Source, Destination
            """)
            routes = cursor.fetchall()

            return render_template("manager_add_flight.html",step="1",routes=routes)

        if step == "1":

            r_id = request.form["r_id"]
            dep_date = request.form["departure_date"]      # yyyy-mm-dd
            dep_time = request.form["departure_time"]      # HH:MM

            if check_valid_date(dep_date, dep_time):
                flash("You cannot create a flight in the past.", "error")
                return redirect("/manager/add-flight")
            # Route info
            cursor.execute("""
                SELECT Airport_Source, Destination, Duration
                FROM Route
                WHERE R_ID = %s
            """, (r_id,))
            route = cursor.fetchone()

            duration = route["Duration"]  # TIME
            dep_datetime = datetime.strptime(
                f"{dep_date} {dep_time}", "%Y-%m-%d %H:%M" )

            # arrival = departure + duration
            hours, minutes, seconds = map(int, str(duration).split(":"))
            arrival_datetime = dep_datetime + timedelta(
                hours=hours, minutes=minutes, seconds=seconds)
            rest_before = dep_datetime - timedelta(days=5)
            rest_after = arrival_datetime + timedelta(days=5)

            # long flight = מעל 6 שעות
            long_flight = hours > 6
            need_qualified= 1 if long_flight else 0


            aircraft_query = """
            SELECT AC.*
            FROM Air_Craft AC
            WHERE
            NOT EXISTS (
                SELECT 1
                FROM Flight F
                WHERE F.AC_ID = AC.AC_ID
                  AND NOT (
                      TIMESTAMP(F.Arrival_Date, F.Arrival_Time) <= %s
                      OR
                      TIMESTAMP(F.Departure_Date, F.Departure_TIME) >= %s
                  )
            )
            AND (
                -- no flights at all
                NOT EXISTS (
                    SELECT 1
                    FROM Flight F0
                    WHERE F0.AC_ID = AC.AC_ID
                )
                OR (
                    -- previous flight arrives at new source
                    EXISTS (
                        SELECT 1
                        FROM Flight F_prev
                        JOIN Route R_prev
                          ON F_prev.R_ID = R_prev.R_ID
                         AND F_prev.Duration = R_prev.Duration
                        WHERE F_prev.AC_ID = AC.AC_ID
                          AND TIMESTAMP(F_prev.Arrival_Date, F_prev.Arrival_Time) < %s
                          AND R_prev.Destination = %s
                          AND TIMESTAMP(F_prev.Arrival_Date, F_prev.Arrival_Time) = (
                              SELECT MAX(TIMESTAMP(F1.Arrival_Date, F1.Arrival_Time))
                              FROM Flight F1
                              WHERE F1.AC_ID = AC.AC_ID
                                AND TIMESTAMP(F1.Arrival_Date, F1.Arrival_Time) < %s
                          )
                    )
                    AND NOT EXISTS (
                        SELECT 1
                        FROM Flight F_next
                        JOIN Route R_next
                          ON F_next.R_ID = R_next.R_ID
                         AND F_next.Duration = R_next.Duration
                        WHERE F_next.AC_ID = AC.AC_ID
                          AND TIMESTAMP(F_next.Departure_Date, F_next.Departure_TIME) > %s
                          AND R_next.Airport_Source <> %s
                          AND TIMESTAMP(F_next.Departure_Date, F_next.Departure_TIME) = (
                              SELECT MIN(TIMESTAMP(F2.Departure_Date, F2.Departure_TIME))
                              FROM Flight F2
                              WHERE F2.AC_ID = AC.AC_ID
                                AND TIMESTAMP(F2.Departure_Date, F2.Departure_TIME) > %s
                          )
                    )
                )
            )
            """
            if long_flight:
                aircraft_query = aircraft_query.replace(
                    "WHERE\n",
                    "WHERE AC.Size = 'Large'\nAND ")
            cursor.execute(
                aircraft_query,
                (
                    rest_before,
                    rest_after,
                    dep_datetime,
                    route["Airport_Source"],
                    dep_datetime,
                    dep_datetime,
                    route["Destination"],
                    dep_datetime
                ))

            available_aircrafts = cursor.fetchall()


            min_rest_date =dep_datetime.date() - timedelta(days=5)


            # pilots
            cursor.execute("""
            SELECT P.*
            FROM Pilot P
            WHERE (%s = 0 OR P.Is_Qualified = 1)
            AND NOT EXISTS (
                SELECT 1
                FROM Assigned_Pilot AP
                JOIN Flight F ON F.Flight_Number = AP.Flight_Number
                WHERE AP.P_ID = P.P_ID
                  AND NOT (
                      TIMESTAMP(F.Arrival_Date, F.Arrival_Time) <= %s
                      OR
                      TIMESTAMP(F.Departure_Date, F.Departure_TIME) >= %s
                  )
            )
           AND (
    NOT EXISTS (
        SELECT 1
        FROM Assigned_Pilot AP0
        WHERE AP0.P_ID = P.P_ID)

    OR EXISTS (
        SELECT 1
        FROM Assigned_Pilot AP_prev
        JOIN Flight F_prev ON F_prev.Flight_Number = AP_prev.Flight_Number
        JOIN Route R_prev ON F_prev.R_ID = R_prev.R_ID AND F_prev.Duration = R_prev.Duration
        WHERE AP_prev.P_ID = P.P_ID
          AND TIMESTAMP(F_prev.Arrival_Date, F_prev.Arrival_Time) < %s
          AND R_prev.Destination = %s
          AND TIMESTAMP(F_prev.Arrival_Date, F_prev.Arrival_Time) = (
              SELECT MAX(TIMESTAMP(F1.Arrival_Date, F1.Arrival_Time))
              FROM Assigned_Pilot AP1
              JOIN Flight F1 ON F1.Flight_Number = AP1.Flight_Number
              WHERE AP1.P_ID = P.P_ID
                AND TIMESTAMP(F1.Arrival_Date, F1.Arrival_Time) < %s))

    AND NOT EXISTS (
        SELECT 1
        FROM Assigned_Pilot AP_next
        JOIN Flight F_next ON F_next.Flight_Number = AP_next.Flight_Number
        JOIN Route R_next ON F_next.R_ID = R_next.R_ID AND F_next.Duration = R_next.Duration
        WHERE AP_next.P_ID = P.P_ID
          AND TIMESTAMP(F_next.Departure_Date, F_next.Departure_TIME) > %s
          AND R_next.Airport_Source <> %s
          AND TIMESTAMP(F_next.Departure_Date, F_next.Departure_TIME) = (
              SELECT MIN(TIMESTAMP(F2.Departure_Date, F2.Departure_TIME))
              FROM Assigned_Pilot AP2
              JOIN Flight F2 ON F2.Flight_Number = AP2.Flight_Number
              WHERE AP2.P_ID = P.P_ID
                AND TIMESTAMP(F2.Departure_Date, F2.Departure_TIME) > %s
          )
    )
)
            """, (
                need_qualified,
                rest_before,
                rest_after,
                dep_datetime,
                route["Airport_Source"],
                dep_datetime,
                dep_datetime,
                route["Destination"],
                dep_datetime
            ))
            pilots = cursor.fetchall()

            # attendants
            cursor.execute("""
            SELECT FA.*
            FROM Flight_Attendant FA
            WHERE (%s = 0 OR FA.Is_Qualified = 1)
            AND NOT EXISTS (
                SELECT 1
                FROM Assigned_Attendant AA
                JOIN Flight F ON F.Flight_Number = AA.Flight_Number
                WHERE AA.FA_ID = FA.FA_ID
                  AND NOT (
                      TIMESTAMP(F.Arrival_Date, F.Arrival_Time) <= %s
                      OR
                      TIMESTAMP(F.Departure_Date, F.Departure_TIME) >= %s
                  )
            )
AND (
    NOT EXISTS (
        SELECT 1
        FROM Assigned_Attendant AA0
        WHERE AA0.FA_ID = FA.FA_ID
    )

    OR EXISTS (
        SELECT 1
        FROM Assigned_Attendant AA_prev
        JOIN Flight F_prev ON F_prev.Flight_Number = AA_prev.Flight_Number
        JOIN Route R_prev ON F_prev.R_ID = R_prev.R_ID AND F_prev.Duration = R_prev.Duration
        WHERE AA_prev.FA_ID = FA.FA_ID
          AND TIMESTAMP(F_prev.Arrival_Date, F_prev.Arrival_Time) < %s
          AND R_prev.Destination = %s
          AND TIMESTAMP(F_prev.Arrival_Date, F_prev.Arrival_Time) = (
              SELECT MAX(TIMESTAMP(F1.Arrival_Date, F1.Arrival_Time))
              FROM Assigned_Attendant AA1
              JOIN Flight F1 ON F1.Flight_Number = AA1.Flight_Number
              WHERE AA1.FA_ID = FA.FA_ID
                AND TIMESTAMP(F1.Arrival_Date, F1.Arrival_Time) < %s
          )
    )

    AND NOT EXISTS (
        SELECT 1
        FROM Assigned_Attendant AA_next
        JOIN Flight F_next ON F_next.Flight_Number = AA_next.Flight_Number
        JOIN Route R_next ON F_next.R_ID = R_next.R_ID AND F_next.Duration = R_next.Duration
        WHERE AA_next.FA_ID = FA.FA_ID
          AND TIMESTAMP(F_next.Departure_Date, F_next.Departure_TIME) > %s
          AND R_next.Airport_Source <> %s
          AND TIMESTAMP(F_next.Departure_Date, F_next.Departure_TIME) = (
              SELECT MIN(TIMESTAMP(F2.Departure_Date, F2.Departure_TIME))
              FROM Assigned_Attendant AA2
              JOIN Flight F2 ON F2.Flight_Number = AA2.Flight_Number
              WHERE AA2.FA_ID = FA.FA_ID
                AND TIMESTAMP(F2.Departure_Date, F2.Departure_TIME) > %s
          )
    )
)

            """, (
                need_qualified,
                rest_before,
                rest_after,
                dep_datetime,
                route["Airport_Source"],
                dep_datetime,
                dep_datetime,
                route["Destination"],
                dep_datetime
            ))
            attendants = cursor.fetchall()

            return render_template(
                "manager_add_flight.html",
                step="2",
                route=route,
                r_id=r_id,
                dep_datetime=dep_datetime,
                arrival_datetime=arrival_datetime,
                aircrafts=available_aircrafts,
                pilots=pilots,
                attendants=attendants)

        if step == "2":
            duration = request.form["duration"]
            flight_number = str(uuid.uuid4())
            r_id = request.form["r_id"]
            ac_id = request.form["ac_id"]
            # get aircraft size
            cursor.execute("""
                SELECT Size
                FROM Air_Craft
                WHERE AC_ID = %s
            """, (ac_id,))
            aircraft = cursor.fetchone()

            if aircraft["Size"] == "Large":
                pilot_count = 3
                fa_count = 6
            else:
                pilot_count = 2
                fa_count = 3

            dep_datetime = datetime.fromisoformat(request.form["dep_datetime"])
            arr_datetime = datetime.fromisoformat(request.form["arr_datetime"])

            cursor.execute("""
                SELECT Capacity_Business
                FROM Air_Craft
                WHERE AC_ID = %s
            """, (ac_id,))
            aircraft = cursor.fetchone()
            price_economy = int(request.form["price_economy"])
            if aircraft["Capacity_Business"] == 0:
                price_business = 0
            else:
                price_business = int(request.form["price_business"])

            pilots = request.form.getlist("pilots")
            attendants = request.form.getlist("attendants")
            if len(pilots) != pilot_count:
                flash(f"You must select exactly {pilot_count} pilots.", "error")
                return redirect("/manager/add-flight")

            if len(attendants) != fa_count:
                flash(f"You must select exactly {fa_count} attendants.", "error")
                return redirect("/manager/add-flight")

            cursor.execute("""
                INSERT INTO Flight
                (Flight_Number, R_ID, Duration, AC_ID,
                 Departure_Date, Departure_Time,
                 Arrival_Date,Arrival_Time, Status,
                 Price_Economy, Price_Business)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Active',%s,%s)""",
            (flight_number,
                r_id,
                duration,
                ac_id,
                dep_datetime.date(),
                dep_datetime.time(),
                arr_datetime.date(),
                arr_datetime.time(),
                price_economy,
                price_business
            ))

            # Assign pilots
            for p in pilots:
                cursor.execute("""
                    INSERT INTO Assigned_Pilot ( P_ID,Flight_Number)
                    VALUES (%s,%s)
                """, (p,flight_number))

            # Assign attendants
            for fa in attendants:
                cursor.execute("""
                    INSERT INTO Assigned_Attendant (FA_ID,Flight_Number)
                    VALUES (%s,%s)
                """, (fa,flight_number))

            flash("Flight added successfully!", "success")
            return redirect("/manager/home")



@app.route("/manager/add-route",methods=["GET", "POST"])
@login_required("manager")
def add_route():
    if request.method == "POST":
        # R_ID by using uuid
        r_id = str(uuid.uuid4())
        duration = request.form["duration"]
        airport_source = request.form["airport_source"]
        destination = request.form["destination"]
        try:
            with db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO Route (R_ID, Duration, Airport_Source, Destination)
                    VALUES (%s, %s, %s, %s)
                """, (r_id, duration, airport_source, destination))

            flash("Route added successfully ", "success")
            return redirect("/manager/home")

        except Exception as e:
            flash("Failed to add route", "error")

    return render_template("add_route.html")


@app.route("/manager/cancel-flight", methods=["GET", "POST"])
@login_required("manager")
def cancel_flight():
    error = None
    success = None
    flights = []
    with db_cursor() as cursor:

        if request.method == "GET":
            cursor.execute("""
                SELECT Flight_Number, Departure_Date, Departure_Time
                FROM Flight
                WHERE Status = 'Active'
                ORDER BY Departure_Date, Departure_Time""")
            flights = cursor.fetchall()
            return render_template( "manager_cancel_flight.html",flights=flights)

        flight_number = request.form["flight_number"]
        cursor.execute("""
            SELECT Departure_Date, Departure_Time, Status
            FROM Flight
            WHERE Flight_Number = %s
        """, (flight_number,))
        flight = cursor.fetchone()
        if not flight:
            error = "Flight not found."
        elif flight["Status"] != "Active":
            error = "Only active flights can be canceled."
        else:
            dep_time = (datetime.min + flight["Departure_Time"]).time()
            dep_datetime = datetime.combine(flight["Departure_Date"], dep_time)
            now=datetime.now()
            if dep_datetime - now < timedelta(hours=72):
                error = "Flights can only be canceled at least 72 hours before departure."
            else:
                cursor.execute("""
                    UPDATE Flight
                    SET Status = 'Canceled'
                    WHERE Flight_Number = %s
                """, (flight_number,))

                cursor.execute("""
                    UPDATE F_Order
                    SET Stat = 'System_Cancelation',
                        Price = 0
                    WHERE Flight_Number = %s
                """, (flight_number,))

                # remove crew from flight
                cursor.execute("""
                    DELETE FROM Assigned_Pilot
                    WHERE Flight_Number = %s
                """, (flight_number,))

                cursor.execute("""
                    DELETE FROM Assigned_Attendant
                    WHERE Flight_Number = %s
                """, (flight_number,))

                success = "Flight was successfully canceled."

        # reload flights list
        cursor.execute("""
            SELECT Flight_Number, Departure_Date, Departure_Time
            FROM Flight
            WHERE Status = 'Active'
            ORDER BY Departure_Date, Departure_Time
        """)
        flights = cursor.fetchall()

    return render_template("manager_cancel_flight.html",flights=flights,error=error,success=success)


@app.route("/manager/search-board", methods=["GET", "POST"])
@login_required("manager")
def search_board():
    flights = []

    source = request.form.get("source")
    destination = request.form.get("destination")
    date = request.form.get("date")
    status = request.form.get("status")

    query = """
        SELECT 
            F.Flight_Number,
            R.Airport_Source,
            R.Destination,
            F.Departure_Date,
            F.Departure_Time,
            F.Arrival_Time,
            F.Status
        FROM Flight F
        JOIN Route R
          ON F.R_ID = R.R_ID
         AND F.Duration = R.Duration
         WHERE 1=1 """

    params = []

    if source:
        query += " AND R.Airport_Source LIKE %s"
        params.append(f"%{source}%")

    if destination:
        query += " AND R.Destination LIKE %s"
        params.append(f"%{destination}%")

    if date:
        query += " AND F.Departure_Date = %s"
        params.append(date)

    if status:
        query += " AND F.Status = %s"
        params.append(status)
    query += " ORDER BY F.Departure_Date, F.Departure_Time"
    with db_cursor() as cursor:
        cursor.execute(query, params)
        flights = cursor.fetchall()

    return render_template("search_board.html", flights=flights)


@app.route("/manager/add-crew", methods=["GET", "POST"])
@login_required("manager")
def add_crew():
    error = None
    success = None
    if request.method == "POST":
        emp_type = request.form["employee_type"]
        emp_id = request.form["emp_id"]
        first = request.form["first_name"]
        last = request.form["last_name"]
        phone = request.form["phone"]
        start_date = request.form["start_date"]
        city = request.form["city"]
        street = request.form["street"]
        number = request.form["number"]
        is_qualified = True if request.form.get("is_qualified") else False
        try:
            with db_cursor() as cursor:
                if emp_type == "Flight_Attendant":
                    cursor.execute("""
                        INSERT INTO Flight_Attendant
                        (FA_ID, First_Name_H, Last_Name_H, Phone_Number,
                         Started_Working_Date, Address_City,
                         Address_Street, Address_Number, Is_Qualified)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (emp_id, first, last, phone, start_date,
                          city, street, number, is_qualified))
                elif emp_type == "Pilot":
                    cursor.execute("""
                        INSERT INTO Pilot
                        (P_ID, First_Name_H, Last_Name_H, Phone_Number,
                         Started_Working_Date, Address_City,
                         Address_Street, Address_Number, Is_Qualified)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (emp_id, first, last, phone, start_date,
                          city, street, number, is_qualified))
            success = "Crew member added successfully"
        except mdb.Error:
            error = "Failed to add crew member. ID may already exist."
    return render_template("add_crew.html",error=error,success=success)

@app.route("/manager/add-aircraft", methods=["GET", "POST"])
@login_required("manager")
def add_aircraft():
    error = None
    success = None

    if request.method == "POST":
        ac_id = request.form["ac_id"]
        size = request.form["size"]
        manufactur = request.form["manufactur"]
        cap_economy = request.form["capacity_economy"]
        if size=="Small":
            cap_business=0
        else:
            cap_business = int(request.form["capacity_business"])
        cap_economy = request.form["capacity_economy"]
        purchased_date = request.form["purchased_date"]

        try:
            with db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO Air_Craft
                    (AC_ID, Size, Manufactur, Capacity_Business, Capacity_Economy, Purchased_DATE)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (
                    ac_id,
                    size,
                    manufactur,
                    cap_business,
                    cap_economy,
                    purchased_date))

            success = "Aircraft added successfully."

        except Exception:
            error = "Failed to add aircraft. Aircraft ID may already exist."

    return render_template( "add_ac.html", error=error,success=success)

@app.route("/manager/reports")
@login_required("manager")
def manager_reports():

    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    with db_cursor() as cursor:

        # =========================
        # 1. Revenue by Month
        # =========================
        revenue_query = """
            SELECT 
                YEAR(Order_Date) AS year,
                MONTH(Order_Date) AS month,
                SUM(Price) AS total_revenue,
                COUNT(*) AS orders_count
            FROM F_Order
            WHERE Stat IN ('Approved','Active')
        """

        params = []

        if year and month:
            revenue_query += " AND YEAR(Order_Date) = %s AND MONTH(Order_Date) = %s"
            params.extend([year, month])

        revenue_query += """
            GROUP BY YEAR(Order_Date), MONTH(Order_Date)
            ORDER BY year DESC, month DESC
        """

        cursor.execute(revenue_query, params)
        revenue_report = cursor.fetchall()

        # =========================
        # 2. Popular Routes
        # =========================
        popular_routes_query = """
            SELECT 
                R.Airport_Source,
                R.Destination,
                COUNT(O.O_ID) AS orders_count
            FROM Route R
            JOIN Flight F ON F.R_ID = R.R_ID
            LEFT JOIN F_Order O
              ON O.Flight_Number = F.Flight_Number
             AND O.Stat IN ('Approved','Active')
        """
        params = []

        if year and month:
            popular_routes_query += """
                WHERE YEAR(F.Departure_Date) = %s
                  AND MONTH(F.Departure_Date) = %s
            """
            params.extend([year, month])

        popular_routes_query += """
            GROUP BY R.Airport_Source, R.Destination
            ORDER BY orders_count DESC
        """
        cursor.execute(popular_routes_query, params)
        popular_routes = cursor.fetchall()

        # =========================
        # 3. Cancellations Report
        # =========================
        cancel_query = """
            SELECT 
                YEAR(Order_Date) AS year,
                MONTH(Order_Date) AS month,
                COUNT(*) AS canceled_orders
            FROM F_Order
            WHERE Stat = 'Customer_Cancelation'
        """

        params = []
        if year and month:
            cancel_query += " AND YEAR(Order_Date) = %s AND MONTH(Order_Date) = %s"
            params.extend([year, month])

        cancel_query += " GROUP BY YEAR(Order_Date), MONTH(Order_Date)"

        cursor.execute(cancel_query, params)
        cancellations_report = cursor.fetchall()

        # =========================
        # 4. Orders by User Type
        # =========================
        user_type_query = """
            SELECT 
                User_Type,
                COUNT(*) AS orders_count
            FROM F_Order
        """
        params = []

        if year and month:
            user_type_query += " WHERE YEAR(Order_Date) = %s AND MONTH(Order_Date) = %s"
            params.extend([year, month])

        user_type_query += " GROUP BY User_Type"

        cursor.execute(user_type_query, params)
        orders_by_user_type = cursor.fetchall()

        # =========================
        # 5. Seat Utilization
        # =========================
        seat_query = """
            SELECT 
                F.Flight_Number,
                COUNT(OS.S_Row) AS taken_seats,
                COUNT(S.S_Row) AS total_seats,
                ROUND(COUNT(OS.S_Row) / COUNT(S.S_Row) * 100, 1) AS utilization_percent
            FROM Flight F
            JOIN Seat S ON S.AC_ID = F.AC_ID
            LEFT JOIN Order_Seat OS
              ON OS.AC_ID = S.AC_ID
             AND OS.S_Row = S.S_Row
             AND OS.Letter = S.Letter
        """

        params = []

        if year and month:
            seat_query += """
                WHERE YEAR(F.Departure_Date) = %s
                  AND MONTH(F.Departure_Date) = %s
            """
            params.extend([year, month])

        seat_query += """
            GROUP BY F.Flight_Number
            ORDER BY utilization_percent DESC
        """

        cursor.execute(seat_query, params)
        seat_utilization = cursor.fetchall()

    return render_template(
        "manager_reports.html",
        revenue_report=revenue_report,
        popular_routes=popular_routes,
        cancellations_report=cancellations_report,
        orders_by_user_type=orders_by_user_type,
        seat_utilization=seat_utilization,
        selected_year=year,
        selected_month=month
    )

@app.route("/cancel-order/<order_id>", methods=["POST"])
def cancel_order(order_id):

    with db_cursor() as cursor:
        cursor.execute("""
            SELECT 
                O.O_ID,
                O.Price,
                O.Stat,
                O.User_Type,
                F.Departure_Date,
                F.Departure_Time
            FROM F_Order O
            JOIN Flight F ON O.Flight_Number = F.Flight_Number
            WHERE O.O_ID = %s
        """, (order_id,))
        order = cursor.fetchone()

        if not order or order["Stat"] not in ("Approved", "Active"):
            flash("This order cannot be canceled.", "error")
            return redirect("/")

        dep_datetime = datetime.strptime(
            f"{order['Departure_Date']} {order['Departure_Time']}",
            "%Y-%m-%d %H:%M:%S")
        now = datetime.now()

        if dep_datetime - now >= timedelta(hours=36):
            new_price = round(order["Price"] * 0.05, 2)
            flash(
                f"Your order was canceled successfully. Cancellation fee: {new_price}$ (5%).",
                "success")
        else:
            new_price = order["Price"]
            flash(
                f"Your order was canceled successfully. Due to late cancellation, the full price was charged:{new_price}$.",
                "error")

        cursor.execute("""
            UPDATE F_Order
            SET Stat = 'Customer_Cancelation',
                Price = %s
            WHERE O_ID = %s
        """, (new_price, order_id))

        cursor.execute("""
            DELETE FROM Order_Seat
            WHERE O_ID = %s
        """, (order_id,))

        update_all_flights_status(cursor)

        if order["User_Type"] == "Registered_Customers":
            return redirect("/customer/home")
        else:
            return redirect("/guest/my-order")

if __name__=="__main__":
    app.run(debug=True)
