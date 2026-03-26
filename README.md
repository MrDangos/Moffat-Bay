# Moffat Bay Lodge

## Collaborators
- Hugo Ramirez Jr.
- Maria Michaels

---

## Requirements
- Python 3.x
- MySQL (LocalHost:3306)
- pip dependencies: `pip install -r requirements.txt`

---

## Running the Project

The project will run as-is. On first launch, Flask will automatically create the required database schema and tables in MySQL.

**Default MySQL settings:**
| Setting | Value |
|---------|-------|
| Host | localhost:3306 |
| User | root |
| Password | root |

> If your MySQL settings are different, update lines 11–13 in `lodge/app.py`.

---

## Manual Database Setup

If Flask fails to create the tables on first run, execute the following code in MySQL Workbench or your MySQL terminal to create the tables:
```sql
CREATE DATABASE IF NOT EXISTS user_table;
USE user_table;

CREATE TABLE IF NOT EXISTS user (
    userid INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS reservations (
    reservationid INT AUTO_INCREMENT PRIMARY KEY,
    userid INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    num_guests INT NOT NULL,
    room_type VARCHAR(20) NOT NULL,
    checkin DATE NOT NULL,
    checkout DATE NOT NULL,
    total_cost DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userid) REFERENCES user(userid)
);
```

---

## Troubleshooting / Can't Get the Project Running?

If you are unable to get the project running as-is, the [Flask Tutorial for VS Code](https://code.visualstudio.com/docs/python/tutorial-flask) is a good step-by-step guide for setting up a new Flask project from scratch. It is written for VS Code but works as a general Flask setup guide regardless of your editor. As a last resort you can create a fresh Flask project following that guide and copy over the files from this project into the new folder.