# Moffat Bay Lodge

## Collaborators
- Hugo Ramirez Jr.
- Maria Michaels

---

## Requirements
- Python 3.x
- MySQL (LocalHost:3306)
- pip dependencies: `pip install -r requirements.txt`
- pip install python-dotenv

This project uses a `.env` file to store sensitive credentials. This file is not included in the repository for security reasons.

To get started:
1. Copy `.env.example` and rename it to `.env`
2. Open `.env` and fill in your MySQL credentials and secret key
3. Save the file and run the project as normal
---

## Running the Project
   
The project will run as-is. Run the app with:

```bash
python app.py
```

On first launch, Flask will automatically create the required database schema, tables, and seed the rooms table with the four room types and pricing.

> Note: Use `python app.py` instead of `flask run` to ensure the database tables are created correctly on startup.

**Default MySQL settings:**
| Setting | Value |
|---------|-------|
| Host | localhost:3306 |
| User | root |
| Password | root |

> If your MySQL settings are different, update lines 11–13 in `lodge/app.py`.

---

## Manual Database Setup

If Flask fails to create the tables on first run, execute the following in MySQL Workbench or your MySQL terminal:

```sql
CREATE DATABASE IF NOT EXISTS user_table;
USE user_table;

CREATE TABLE IF NOT EXISTS user (
    userid   INT          AUTO_INCREMENT PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    email    VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS rooms (
    roomid       INT           AUTO_INCREMENT PRIMARY KEY,
    room_type    VARCHAR(20)   NOT NULL,
    room_name    VARCHAR(50)   NOT NULL,
    nightly_rate DECIMAL(10,2) NOT NULL
);

INSERT INTO rooms (room_type, room_name, nightly_rate) VALUES
('DFBed', 'Double Full Bed',  120.00),
('queen', 'Queen',            135.00),
('DQBed', 'Double Queen Bed', 150.00),
('king',  'King',             160.00);

CREATE TABLE IF NOT EXISTS reservations (
    reservationid INT       AUTO_INCREMENT PRIMARY KEY,
    userid        INT       NOT NULL,
    roomid        INT       NOT NULL,
    num_guests    INT       NOT NULL,
    checkin       DATE      NOT NULL,
    checkout      DATE      NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userid) REFERENCES user(userid),
    FOREIGN KEY (roomid) REFERENCES rooms(roomid)
);
```

---

## Features

- Public access to all lodge pages without requiring an account
- User registration and login with session management
- Lodge reservation booking with room selection, guest count, and date validation
- Reservation summary page with confirm and edit options
- Reservation history viewable on the user account page
- Reservation lookup by reservation ID or email address

---

## Known Issues

- Passwords are currently stored as plain text. bcrypt hashing is planned for a future update.
- No reservation button in the navigation bar. Users must navigate to the reservation page manually.

---

## Troubleshooting / Can't Get the Project Running?

If you are unable to get the project running as-is, the [Flask Tutorial for VS Code](https://code.visualstudio.com/docs/python/tutorial-flask) is a good step-by-step guide for setting up a new Flask project from scratch. It is written for VS Code but works as a general Flask setup guide regardless of your editor. As a last resort you can create a fresh Flask project following that guide and copy over the files from this project into the new folder.
