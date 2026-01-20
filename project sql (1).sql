-- =============================================
-- 1. CLEANUP: Delete old tables in correct order
-- =============================================
DROP TABLE IF EXISTS Order_seat;
DROP TABLE IF EXISTS Assigned_Attendant;
DROP TABLE IF EXISTS Assigned_Pilot;
DROP TABLE IF EXISTS Seat;
DROP TABLE IF EXISTS F_Order;
DROP TABLE IF EXISTS Flight;
DROP TABLE IF EXISTS Phone_Numbers_Registered_Customers;
DROP TABLE IF EXISTS Phone_Numbers_NonRegistered_Customers;
DROP TABLE IF EXISTS Air_Craft;
DROP TABLE IF EXISTS Route;
DROP TABLE IF EXISTS Registered_Customer;
DROP TABLE IF EXISTS NonRegistered_Customer;
DROP TABLE IF EXISTS Manager;
DROP TABLE IF EXISTS Pilot;
DROP TABLE IF EXISTS Flight_Attendant;

-- =============================================
-- 2. CREATE TABLES
-- =============================================

CREATE TABLE Flight_Attendant
( FA_ID VARCHAR(45) NOT NULL UNIQUE,
First_Name_H VARCHAR(45),
Last_Name_H VARCHAR(45),
Phone_Number VARCHAR(45),
Started_Working_Date DATE,
Address_City VARCHAR(45),
Address_Street VARCHAR(45),
Address_Number INT,
Is_Qualified boolean,
primary key(FA_ID));

CREATE TABLE Pilot
( P_ID VARCHAR(45) NOT NULL UNIQUE,
First_Name_H VARCHAR(45),
Last_Name_H VARCHAR(45),
Phone_Number VARCHAR(45),
Started_Working_Date DATE,
Address_City VARCHAR(45),
Address_Street VARCHAR(45),
Address_Number INT,
Is_Qualified BOOL,
primary key(P_ID));

CREATE TABLE Manager
( M_ID VARCHAR(45) NOT NULL UNIQUE,
First_Name_H VARCHAR(45),
Last_Name_H VARCHAR(45),
Phone_Number VARCHAR(45),
Started_Working_Date DATE,
Address_City VARCHAR(45),
Address_Street VARCHAR(45),
Address_Number INT,
M_Password VARCHAR(45),
primary key(M_ID));

CREATE TABLE NonRegistered_Customer
( Email VARCHAR(45) NOT NULL UNIQUE,
First_Name_E VARCHAR(45),
Last_Name_E VARCHAR(45),
primary key( Email));

CREATE TABLE Registered_Customer
( R_Email VARCHAR(45) NOT NULL UNIQUE,
First_Name_E VARCHAR(45),
Last_Name_E VARCHAR(45),
Passport_Num VARCHAR(45),
Register_Date DATE,
Birth_Date DATE,
C_Password VARCHAR(45),
primary key(R_Email));

CREATE TABLE Route
(R_ID VARCHAR(45) NOT NULL UNIQUE,
Duration TIME NOT NULL,
Airport_Source VARCHAR(45),
Destination VARCHAR(45),
primary key (R_ID, Duration));

CREATE TABLE Air_Craft
(AC_ID VARCHAR(45) NOT NULL UNIQUE,
Size ENUM("Large","Small"),
Manufactur ENUM("Boeing","Airbus","Dassault"),
Capacity_Business INT,
Capacity_Economy INT,
Purchased_DATE DATE,
primary key(AC_ID));

CREATE TABLE Flight
(Flight_Number VARCHAR(45) NOT NULL UNIQUE,
Departure_Date DATE,
Departure_TIME TIME,
Status ENUM("Active", "Full_Flight","Completed","Canceled"),
Price_Economy INT,
Price_Business INT,
R_ID VARCHAR(45),
Duration TIME,
Arrival_Date DATE,
Arrival_Time TIME,
AC_ID VARCHAR(45),
primary key (Flight_Number),
foreign key(R_ID,Duration) references Route(R_ID,Duration),
foreign key(AC_ID) references Air_Craft(AC_ID));

CREATE TABLE F_Order
(O_ID VARCHAR(45) NOT NULL UNIQUE,
Stat ENUM("Completed","Approved","Customer_Cancelation","System_Cancelation"),
User_Type ENUM("NonRegistered_Customers","Registered_Customers"),
Order_Date Date,
Price INT,
Email VARCHAR(45),
R_Email VARCHAR(45),
Flight_Number VARCHAR(45),
PRIMARY KEY (O_ID),
FOREIGN KEY (Email) REFERENCES NonRegistered_Customer(Email),
FOREIGN KEY (R_Email) REFERENCES Registered_Customer(R_Email),
FOREIGN KEY (Flight_Number) REFERENCES Flight(Flight_Number));

CREATE TABLE Seat
(AC_ID VARCHAR(45),
S_Row INT,
Letter CHAR(1),
Class ENUM("Business","Economy"),
primary key (AC_ID,S_Row, Letter),
foreign key (AC_ID) references Air_Craft(AC_ID));

CREATE TABLE Assigned_Pilot
(P_ID VARCHAR(45),
Flight_Number VARCHAR(45),
primary key (P_ID, Flight_Number),
foreign key (P_ID) references Pilot(P_ID),
foreign key(Flight_Number) references Flight( Flight_Number));

CREATE TABLE Assigned_Attendant
(FA_ID VARCHAR(45),
Flight_Number VARCHAR(45),
primary key (FA_ID, Flight_Number),
foreign key (FA_ID) references Flight_Attendant(FA_ID),
foreign key(Flight_Number) references Flight( Flight_Number));

CREATE TABLE Phone_Numbers_NonRegistered_Customers
(Email VARCHAR(45) NOT NULL,
Phone_Number VARCHAR(45),
primary key (Email, Phone_Number),
foreign key(Email) references NonRegistered_Customer(Email));

CREATE TABLE Phone_Numbers_Registered_Customers
(R_Email VARCHAR(45) NOT NULL,
Phone_Number VARCHAR(45),
primary key (R_Email, Phone_Number),
foreign key(R_Email) references Registered_Customer(R_Email));

CREATE TABLE Order_seat
(AC_ID VARCHAR(45),
S_Row INT,
Letter CHAR(1),
O_ID VARCHAR(45),
PRIMARY KEY (S_Row, Letter,O_ID,AC_ID),
foreign key (AC_ID,S_Row, Letter) references Seat(AC_ID,S_Row, Letter),
foreign key (O_ID) references F_Order(O_ID));

-- =============================================
-- 3. INSERT DATA
-- =============================================

-- Managers
INSERT INTO Manager VALUES
('M1','דנה','לוי','0501000001','2019-01-01','תל אביב','דיזנגוף',10,'pass1'),
('M2','רון','כהן','0501000002','2020-02-01','רמת גן','ביאליק',5,'pass2');

-- Customers
INSERT INTO NonRegistered_Customer VALUES
('guest1@mail.com','John','Doe'),
('guest2@mail.com','Jane','Smith');

INSERT INTO Registered_Customer VALUES
('reg1@mail.com','Alice','Brown','P123','2022-01-01','1995-05-05','pw1'),
('reg2@mail.com','Bob','Green','P456','2021-06-01','1990-03-03','pw2'),
('reg3@mail.com','Charlie','White','P789','2023-03-01','1998-09-09','pw3');

-- Phone numbers
INSERT INTO Phone_Numbers_NonRegistered_Customers VALUES
('guest1@mail.com','0509000001'),
('guest2@mail.com','0509000002');

INSERT INTO Phone_Numbers_Registered_Customers VALUES
('reg1@mail.com','0509000101'),
('reg2@mail.com','0509000102'),
('reg3@mail.com','0509000103');

-- Workers
INSERT INTO Pilot VALUES
('P1','יואב','כהן','0503000001','2017-01-01','תל אביב','השלום',1,1),
('P2','רן','לוי','0503000002','2017-02-01','חולון','הרצל',2,1),
('P3','דן','פרץ','0503000003','2018-03-01','רמת גן','ביאליק',3,1),
('P4','אורי','שחר','0503000004','2019-04-01','גבעתיים','כצנלסון',4,1);

INSERT INTO Flight_Attendant VALUES
('FA1','נועה','כהן','0502000001','2018-01-01','תל אביב','אלנבי',1,1),
('FA2','שיר','לוי','0502000002','2018-01-01','תל אביב','אלנבי',2,1),
('FA3','מאיה','פרץ','0502000003','2018-01-01','חולון','הרצל',3,1),
('FA4','נועה','רז','0502000004','2018-01-01','חולון','הרצל',4,1),
('FA5','אור','כהן','0502000005','2018-01-01','רמת גן','ביאליק',5,1),
('FA6','דנה','ברק','0502000006','2018-01-01','רמת גן','ביאליק',6,1),
('FA7','טל','שחר','0502000007','2018-01-01','גבעתיים','כצנלסון',7,1),
('FA8','רוני','בר','0502000008','2018-01-01','גבעתיים','כצנלסון',8,1),
('FA9','שני','לב','0502000009','2018-01-01','חיפה','מוריה',9,1),
('FA10','עדי','רום','0502000010','2018-01-01','חיפה','מוריה',10,1),
('FA11','נועה','שקד','0502000011','2018-01-01','חיפה','מוריה',11,1),
('FA12','מאיה','חן','0502000012','2018-01-01','נתניה','הרצל',12,1),
('FA13','לירון','טל','0502000013','2018-01-01','נתניה','הרצל',13,1),
('FA14','שירה','בן דוד','0502000014','2018-01-01','כפר סבא','ויצמן',14,1),
('FA15','מור','אלון','0502000015','2018-01-01','כפר סבא','ויצמן',15,1),
('FA16','איילת','כהן','0502000016','2018-01-01','רחובות','הרצל',16,1),
('FA17','שחר','זיו','0502000017','2018-01-01','רחובות','הרצל',17,1),
('FA18','שיר','מור','0502000018','2018-01-01','ראשון','רוטשילד',18,1),
('FA19','נועה','זיו','0502000019','2018-01-01','ראשון','רוטשילד',19,1),
('FA20','רוני','פלד','0502000020','2018-01-01','ראשון','רוטשילד',20,1);

-- Routes
INSERT INTO Route VALUES
('R1','02:30:00','LONDON-LHR','TEL AVIV-TLV'),
('R2','05:00:00','PARIS-CDG','TEL AVIV-TLV'),
('R3','09:30:00','NYC-JFK','TEL AVIV-TLV'),
('R4','04:00:00','ROME-FCO','TEL AVIV-TLV'),
('R5','09:00:00','BANGKOK-BKK','TEL AVIV-TLV');

-- Air Craft
INSERT INTO Air_Craft VALUES
('AC1','Small','Boeing',0,80,'2018-01-01'),
('AC2','Large','Airbus',20,200,'2019-01-01'),
('AC3','Large','Boeing',30,250,'2020-01-01'),
('AC4','Small','Dassault',0,120,'2021-01-01'),
('AC5','Large','Airbus',25,220,'2017-01-01'),
('AC6','Small','Boeing',0,100,'2022-01-01');



