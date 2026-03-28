from datetime import datetime
from flask import *
from flask_session import Session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re


app = Flask(__name__)
app.secret_key = 'stundent'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'   
app.config['MYSQL_DB'] = 'user_table'
app.config["SESSION_PERMANENT"] = False    # session will not be lost if the browser is closed
app.config["SESSION_TYPE"] = "filesystem"  # session is store in the filesystem

Session(app)

mysql = MySQL(app)

ROOM_PRICES = {
    'DFBed': 120,
    'queen': 135,
    'DQBed': 150,
    'king': 160
}

ROOM_NAMES = {
    'DFBed': 'Double Full Bed',
    'queen': 'Queen',
    'DQBed': 'Double Queen Bed',
    'king': 'King'
}


def create_table():
    cursor = mysql.connection.cursor()
    # user table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            userid INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        )
    """)
    # reservations table
    cursor.execute("""
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
        )
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
    if request.method == 'POST':
        room = request.form['room']
        checkin = request.form['checkin']
        checkout = request.form['checkout']

        checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
        checkout_date = datetime.strptime(checkout, "%Y-%m-%d")
        nights = (checkout_date - checkin_date).days

        session['pending_reservation'] = {
            'name': request.form['name'],
            'email': request.form['email'],
            'numGuests': request.form['numGuests'],
            'room': room,
            'room_name': ROOM_NAMES[room],
            'checkin': checkin,
            'checkout': checkout,
            'nights': nights,
            'total_cost': nights * ROOM_PRICES[room]
        }
        return redirect(url_for('summary'))
    return render_template("booking/reservation.html") 

#summary page, displays reservation deatils
@app.route("/reservation/summary", methods=["GET"])
def summary():
    reservation = session.get('pending_reservation')
    if not reservation:
        return redirect(url_for('reservation'))
    return render_template('booking/summary.html', reservation=reservation)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    message = ''
    # Check if "email" and "password" exist
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM user WHERE email = % s AND password = % s', 
                  (email, password, ))
        user = cursor.fetchone()
        # If account exists user in logged in and session in save in cookies
        if user:
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            message = 'Logged in successfully !'
            return redirect(url_for('user'))
        else:
            message = 'Please enter correct email / password !'
    return render_template('user/login.html', message=message)

# Logs user out and clear sessoin data/cookies
@app.route('/logout')
def logout():
    session["name"] = None
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    message = ''
    # Check if "name", "password" and "email" exist before creating account
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = % s', (email, ))
        account = cursor.fetchone()
        if account:
            message = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address !'
        elif not userName or not password or not email:
            message = 'Please fill out the form !'
        else:
            cursor.execute(
                'INSERT INTO user VALUES (NULL, % s, % s, % s)', 
                      (userName, email, password, ))
            mysql.connection.commit()
            message = 'You have successfully registered !'
    elif request.method == 'POST':
        message = 'Please fill out the form !'
    return render_template('user/signup.html', message=message)

# user account page, only displays if user is logged in and display all of users reservations
@app.route('/user')
def user():
    if not session.get("name"):
        return redirect("/login")
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT * FROM reservations 
        WHERE userid = %s
    """, (session['userid'],))
    reservations = cursor.fetchall()
    cursor.close()
    
    return render_template('user/user.html', name=session['name'], reservations=reservations)

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
        INSERT INTO reservations 
        (userid, name, email, num_guests, room_type, checkin, checkout, total_cost)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (session['userid'], r['name'], r['email'], r['numGuests'],
          r['room'], r['checkin'], r['checkout'], r['total_cost']))
    mysql.connection.commit()
    cursor.close()

    session.pop('pending_reservation', None)
    return redirect(url_for('user'))

if __name__ == "__main__":
    app.run(debug=True)