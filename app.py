from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import hashlib

app = Flask(__name__)
app.secret_key = 'secret123'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '4MU22CS024'
app.config['MYSQL_DB'] = 'students_db'

mysql = MySQL(app)

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = hash_password("admin123")

def init_db():
    cur = mysql.connection.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            username VARCHAR(50) PRIMARY KEY,
            password VARCHAR(255) NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            roll INT UNIQUE NOT NULL,
            marks FLOAT NOT NULL
        )
    """)
    cur.execute("SELECT * FROM admin WHERE username=%s", (ADMIN_USERNAME,))
    if not cur.fetchone():
        cur.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", (ADMIN_USERNAME, ADMIN_PASSWORD))
    mysql.connection.commit()
    cur.close()



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        uname = request.form.get('username', '').strip()
        pw = request.form.get('password', '').strip()

        # Basic validation for empty fields
        if not uname or not pw:
            flash("Please fill in all the required fields.")
            return render_template('signup.html')

        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM admin WHERE username=%s", (uname,))
            if cur.fetchone():
                flash("Username already exists. Please choose another.")
                return render_template('signup.html')
            
            # Insert new user with hashed password
            cur.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", (uname, hash_password(pw)))
            mysql.connection.commit()
            flash("Registration successful! You can now log in.")
            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error during registration: {e}")
            return render_template('signup.html')
        finally:
            cur.close()
    else:
        return render_template('signup.html')


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pw = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (uname, hash_password(pw)))
        result = cur.fetchone()
        cur.close()
        if result:
            session['admin'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials or user not registered')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('login'))
    sort = request.args.get('sort', 'id')
    order = request.args.get('order', 'asc')
    direction = 'ASC' if order == 'asc' else 'DESC'
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * FROM students ORDER BY {sort} {direction}")
    students = cur.fetchall()
    cur.close()
    return render_template('dashboard.html', students=students, sort=sort, order=order)

@app.route('/add', methods=['POST'])
def add():
    if not session.get('admin'):
        return redirect(url_for('login'))
    name = request.form['name']
    roll = request.form['roll']
    marks = request.form['marks']
    cur = mysql.connection.cursor()
    try:
        cur.execute("INSERT INTO students (name, roll, marks) VALUES (%s, %s, %s)", (name, int(roll), float(marks)))
        mysql.connection.commit()
        flash('Added successfully!')
    except Exception as e:
        flash(f'Error: {e}')
        mysql.connection.rollback()
    cur.close()
    return redirect(url_for('dashboard'))

@app.route('/edit/<int:stu_id>', methods=['POST'])
def edit(stu_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    name = request.form['name']
    roll = request.form['roll']
    marks = request.form['marks']
    cur = mysql.connection.cursor()
    try:
        cur.execute("UPDATE students SET name=%s, roll=%s, marks=%s WHERE id=%s", (name, int(roll), float(marks), stu_id))
        mysql.connection.commit()
        flash('Updated successfully!')
    except Exception as e:
        flash(f'Error: {e}')
        mysql.connection.rollback()
    cur.close()
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:stu_id>')
def delete(stu_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM students WHERE id=%s", (stu_id,))
        mysql.connection.commit()
        flash('Deleted successfully!')
    except Exception as e:
        flash(f'Error: {e}')
        mysql.connection.rollback()
    finally:
        cur.close()
    return redirect(url_for('dashboard'))

@app.route('/view_students')
def view_students():
    if not session.get('admin'):
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()  # fetch all rows
    cur.close()
    return render_template('view_students.html', students=students)


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)

