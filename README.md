# FLY-TAU-28
FLYTAU - Airline Flight Management & Ticketing System
**OVERVIEW**
The FLYTAU Information System is a web-based airline platform that allows customers to search and purchase flight tickets, and enables managers to control operational activities such as flight creation, cancellation, and staff assignment.

This README describes the functionality, user flows, technology stack, and deployment instructions for the web application.

### SYSTEM FEATURES

**Customer Interface**

Available to both guest users and registered customers:

- Search flights by date, origin, and destination
- View available seats per flight
- Purchase tickets and complete orders
- Receive a unique order code for later retrieval
- Cancel orders
- View flight tickets

Registered customers additionally can:
- Log in with email + password
- Automatically fill personal details when ordering
- View full order history with status filtering

**Manager / Admin Interface**

Accessible to system managers after login:

- Create and publish new flights
- Create new routes
- Assign aircraft and crew
- Cancel existing flights
- View all flight board 
- View operational statistics & business reports
- Add pilots and attendants (as employees)
- Add purchased aricrafts


### USER ROLES

The system supports three types of users:

**Guest** -	Search & purchase flights, cancel order via email + code <br>
**Registered Customer** -	All guest capabilities + login + history view <br>
**Manager (Admin)** -	Full operational control panel <br>


### CORE BUSINESS RULES IMPLEMENTED

- Managers cannot purchase tickets
- Guests and registered customers may cancel orders
- Order cancellation up to 36 hours before flight refunds 95% of the original cost (5% fee)
- Flight cancellation by manager triggers full refund
- Long flights (>6h) require certified crew
- Aircraft size determines seat classes and crew size
- Flight cannot be created if no aircraft or crew is available
- Aircraft types: Boeing / Airbus / Dassault
- Aircraft sizes: Small / Large


### MAIN USER FLOWS

**Purchase Flow -** <br>
1. User selects flight from flight board or by searching date and route <br>
2. System displays available seats <br>
3. User selects seat(s) <br>
4. User confirms order details <br>
5. System saves order & returns unique order code <br>

**Login / Registration -** <br>
1. Registration requires: name, email, password, phone number, birth date, passport number <br>
2. Login requires: email + password<br>

**Manager Flight Creation** <br>
1. Manager logs in <br>
2. Selects date, time, route<br>
3. System checks aircraft availability<br>
4. System checks crew availability & qualifications<br>
5. Manager assigns aircraft + staff<br>
6. Flight becomes “open” to public<br>

**Manager Reports & Monitoring** <br>
1. The manager dashboard includes business reporting


### SCREEN / UI PAGES

Common screens include:

- Flight search page - guest and registered
- Flight board - for costumers, only active flights
- Seat selection page
- Order summary page
- Order confirmation page
- Login / Registration
- Manager dashboard
- Flight creation - assigning aircraft, aircrew, pricing
- Reports / statistics screen
- Aircraft purchase documentaion
- Aircrew creation
- Flight cancelation
- Route creation
- Extended flight board - search and filters
