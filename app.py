# app.py
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def get_db_connection():
    try:
        conn = sqlite3.connect('database/passwords.db')
        conn.row_factory = sqlite3.Row
        logging.debug("Database connection established")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database: {e}")
        raise

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    try:
        passwords = conn.execute('SELECT * FROM passwords WHERE user_id = ?', (session['user_id'],)).fetchall()
        logging.debug("Fetched passwords for user ID %s", session['user_id'])
    except sqlite3.Error as e:
        logging.error(f"Error fetching passwords: {e}")
        passwords = []
    finally:
        conn.close()
    return render_template('index.html', passwords=passwords)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        except sqlite3.Error as e:
            logging.error(f"Error fetching user: {e}")
            user = None
        finally:
            conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']  # Set the 'username' in the session
            logging.info("User %s logged in successfully", username)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
            logging.warning("Invalid login attempt for username %s", username)
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password_hash))
            conn.commit()
            flash('Registration successful. Please login.')
            logging.info("User %s registered successfully", username)
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another.')
            logging.warning("Registration attempt with existing username %s", username)
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        logging.info("User %s logged out", session['username'])
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        website = request.form['website']
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO passwords (user_id, website, username, password) VALUES (?, ?, ?, ?)',
                         (session['user_id'], website, username, password))
            conn.commit()
            logging.info("Password added for user ID %s", session['user_id'])
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            logging.error(f"Error adding password: {e}")
        finally:
            conn.close()

    return render_template('add.html')

if __name__ == '__main__':
    app.run(debug=True)
