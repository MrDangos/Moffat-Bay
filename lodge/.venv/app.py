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
app.config["SESSION_PERMANENT"] = False    
app.config["SESSION_TYPE"] = "filesystem"  

Session(app)

mysql = MySQL(app)

def create_table():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            userid INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
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

@app.route("/reservation/", methods=["GET", "POST"])
def reservation():
    return render_template("booking/reservation.html")


@app.route('/login/', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM user WHERE email = % s AND password = % s', 
                  (email, password, ))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            message = 'Logged in successfully !'
            return render_template('user/user.html', message=message)
        else:
            message = 'Please enter correct email / password !'
    return render_template('user/login.html', message=message)

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

@app.route('/user')
def user():
    if not session.get("name"):
        return redirect("/login")
    return render_template('user/user.html', name=session['name'])