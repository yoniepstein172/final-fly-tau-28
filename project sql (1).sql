CREATE SCHEMA FLYTAU;

USE FLYTAU;

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
Destination VARCHAR(45),
Airport_Source VARCHAR(45),
primary key (R_ID, Duration));

CREATE TABLE Air_Craft
(AC_ID VARCHAR(45) NOT NULL UNIQUE,
Size ENUM("Large","Small"),
Manufactur ENUM("Boeing","Airbus","Dassault"),
Purchased_DATE DATE,
primary key(AC_ID));

CREATE TABLE Flight
(Flight_Number VARCHAR(45) NOT NULL UNIQUE, 
Departure_Date DATE,
Departure_TIME TIME,
Status VARCHAR(45),
Price_Econemy INT,
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
Stat ENUM("Active","Approved","customer_Cancelation","System_Cancelation"),
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
S_ROW INT,
Letter CHAR(1),
Class ENUM("Business","Economy"),
O_ID VARCHAR(45),
foreign key (AC_ID) references Air_Craft(AC_ID),
foreign key (O_ID) references F_Order(O_ID));

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
(Email VARCHAR(45) NOT NULL UNIQUE,
Phone_Number VARCHAR(45),
primary key (Email, Phone_Number),
foreign key(Email) references NonRegistered_Customer(Email));

CREATE TABLE Phone_Numbers_Registered_Customers
(R_Email VARCHAR(45) NOT NULL UNIQUE,
Phone_Number VARCHAR(45),
primary key (R_Email, Phone_Number),
foreign key(R_Email) references Registered_Customer(R_Email));

