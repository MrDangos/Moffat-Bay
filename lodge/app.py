from datetime import datetime
from flask import *
from flask_session import Session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from dotenv import load_dotenv
import os
from flask_bcrypt import Bcrypt


app = Flask(__name__)
bcrypt = Bcrypt(app)

load_dotenv()

app.secret_key = os.getenv('SECRET_KEY')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config["SESSION_PERMANENT"] = False    # session will not be lost if the browser is closed
app.config["SESSION_TYPE"] = "filesystem"  # session is store in the filesystem

Session(app)

mysql = MySQL(app)


def create_table():
    cursor = mysql.connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            userid   INT          AUTO_INCREMENT PRIMARY KEY,
            name     VARCHAR(100) NOT NULL,
            email    VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            roomid       INT          AUTO_INCREMENT PRIMARY KEY,
            room_type    VARCHAR(20)  NOT NULL,
            room_name    VARCHAR(50)  NOT NULL,
            nightly_rate DECIMAL(10,2) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            reservationid INT AUTO_INCREMENT PRIMARY KEY,
            userid        INT NOT NULL,
            roomid        INT NOT NULL,
            num_guests    INT NOT NULL,
            checkin       DATE NOT NULL,
            checkout      DATE NOT NULL,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (userid) REFERENCES user(userid),
            FOREIGN KEY (roomid) REFERENCES rooms(roomid)
        )
    """)

    # seed rooms only if the table is empty
    cursor.execute("SELECT COUNT(*) FROM rooms")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO rooms (room_type, room_name, nightly_rate) VALUES
            ('DFBed', 'Double Full Bed',  120.00),
            ('queen', 'Queen',            135.00),
            ('DQBed', 'Double Queen Bed', 150.00),
            ('king',  'King',             160.00)
        """)

    mysql.connection.commit()
    cursor.close()


with app.app_context():
    create_table()
    
@app.route("/")
def home():
    return render_template("base/home.html")

@app.route("/about/")
def about():
    return render_template("base/about.html")

@app.route("/contact/")
def contact():
    return render_template("base/contact.html")

@app.route("/attractions/")
def attractions():
    return render_template("base/attractions.html")

# resrevation page, get user input and save it in session, then redirect to summary page
@app.route("/reservation/", methods=["GET", "POST"])
def reservation():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == 'POST':
        roomid = request.form['roomid']
        checkin = request.form['checkin']
        checkout = request.form['checkout']
        num_guests = request.form['numGuests']
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

        cursor.execute("SELECT * FROM rooms")
        rooms = cursor.fetchall()
        today_str = today.strftime("%Y-%m-%d")

        # check for empty fields first before trying to parse dates
        if not checkin or not checkout or not num_guests:
            error = "Please fill out all fields."
            return render_template("booking/reservation.html", rooms=rooms, error=error, today=today_str)

        checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
        checkout_date = datetime.strptime(checkout, "%Y-%m-%d")
        
        if checkin_date < today:
            error = "Check-in date cannot be in the past."
            return render_template("booking/reservation.html", rooms=rooms, error=error, today=today_str)

        if checkout_date <= checkin_date:
            error = "Check-out date must be after check-in date."
            return render_template("booking/reservation.html", rooms=rooms, error=error, today=today_str)

        cursor.execute("SELECT * FROM rooms WHERE roomid = %s", (roomid,))
        room = cursor.fetchone()
        nights = (checkout_date - checkin_date).days

        session['pending_reservation'] = {
            'roomid': roomid,
            'room_name': room['room_name'],
            'nightly_rate': float(room['nightly_rate']),
            'num_guests': num_guests,
            'checkin': checkin,
            'checkout': checkout,
            'nights': nights,
            'total_cost': nights * float(room['nightly_rate'])
        }
        return redirect(url_for('summary'))

    today = datetime.today().strftime("%Y-%m-%d")
    cursor.execute("SELECT * FROM rooms")
    rooms = cursor.fetchall()
    cursor.close()
    return render_template("booking/reservation.html", rooms=rooms, today=today)

#summary page, displays reservation deatils
@app.route("/reservation/summary", methods=["GET"])
def summary():
    reservation = session.get('pending_reservation')
    if not reservation:
        return redirect(url_for('reservation'))
    return render_template('booking/summary.html', reservation=reservation)

#allows user edit reservation details before confirming
@app.route("/reservation/edit")
def edit_reservation():
    if not session.get("name"):
        return redirect("/login")
    pending = session.get('pending_reservation')
    if not pending:
        return redirect(url_for('reservation'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM rooms")
    rooms = cursor.fetchall()
    cursor.close()

    today = datetime.today().strftime("%Y-%m-%d")
    return render_template("booking/reservation.html", rooms=rooms, today=today, pending=pending)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        user = cursor.fetchone()
        if user and bcrypt.check_password_hash(user['password'], password):
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            return redirect(url_for('user'))
        else:
            message = 'Please enter correct email / password!'
    return render_template('user/login.html', message=message)

# Logs user out and clear sessoin data/cookies
@app.route('/logout')
def logout():
    session["name"] = None
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))

# Singup page 
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            message = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$', password):
            message = 'Password must be at least 8 characters and include one uppercase letter, one lowercase letter, and one number.'
        elif not userName or not email:
            message = 'Please fill out the form!'
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            cursor.execute(
                'INSERT INTO user VALUES (NULL, %s, %s, %s)',
                (userName, email, hashed_password,))
            mysql.connection.commit()
            message = 'You have successfully registered!'
    elif request.method == 'POST':
        message = 'Please fill out the form!'
    return render_template('user/signup.html', message=message)

# user account page, only displays if user is logged in and display all of users reservations
@app.route('/user')
def user():
    if not session.get("name"):
        return redirect("/login")
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT 
            r.reservationid,
            r.num_guests,
            r.checkin,
            r.checkout,
            ro.room_name,
            ro.nightly_rate,
            DATEDIFF(r.checkout, r.checkin) AS nights,
            DATEDIFF(r.checkout, r.checkin) * ro.nightly_rate  AS total_cost
        FROM reservations r
        JOIN rooms ro ON r.roomid = ro.roomid
        WHERE r.userid = %s
    """, (session['userid'],))
    reservations = cursor.fetchall()
    cursor.close()
    
    return render_template('user/user.html', name=session['name'], reservations=reservations)

# cancel reservation
@app.route('/cancel/<int:reservation_id>', methods=['GET', 'POST'])
def cancel_reservation(reservation_id):
    if not session.get("name"):
        return redirect("/login")
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT r.reservationid, ro.room_name, r.checkin, r.checkout
        FROM reservations r
        JOIN rooms ro ON r.roomid = ro.roomid
        WHERE r.reservationid = %s AND r.userid = %s
    """, (reservation_id, session['userid']))
    reservation = cursor.fetchone()
    cursor.close()

    if not reservation:
        return redirect(url_for('user'))

    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM reservations WHERE reservationid = %s", (reservation_id,))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('user'))

    return render_template('booking/cancel.html', reservation_id=reservation_id)

# live search
@app.route('/search_reservations', methods=['POST', 'GET'])
def search_reservations():
    if not session.get("name"):
        return redirect("/login")

    reservation_id = request.form['reservation_id']
    user_id = session.get("userid")

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = """
        SELECT 
            r.reservationid,
            r.num_guests,
            r.checkin,
            r.checkout,
            ro.room_name,
            ro.nightly_rate,
            DATEDIFF(r.checkout, r.checkin) AS nights,
            DATEDIFF(r.checkout, r.checkin) * ro.nightly_rate AS total_cost
        FROM reservations r
        JOIN rooms ro ON r.roomid = ro.roomid
        WHERE r.userid = %s
        AND CAST(r.reservationid AS CHAR) LIKE %s
    """
    cursor.execute(query, (user_id, f'%{reservation_id}%'))
    result = cursor.fetchall()
    cursor.close()

    return jsonify(result)

# confirm reservation and save it to sql db so user can see it on account page
@app.route("/confirm/", methods=["POST"])
def confirm():
    if not session.get("name"):
        return redirect("/login")
    r = session.get('pending_reservation')
    if not r:
        return redirect(url_for('reservation'))

    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO reservations (userid, roomid, num_guests, checkin, checkout)
        VALUES (%s, %s, %s, %s, %s)
    """, (session['userid'], r['roomid'], r['num_guests'], r['checkin'], r['checkout']))
    mysql.connection.commit()
    cursor.close()

    session.pop('pending_reservation', None)
    return redirect(url_for('user'))


if __name__ == "__main__":
    app.run(debug=True)