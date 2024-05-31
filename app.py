from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import serial

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
users = {'admin': 'pass'}

#MySQL database credentials
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'rfid_library',
}

# Function to execute SQL queries
def execute_query(query, data=None, fetchall=True):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    try:
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
        result = cursor.fetchall()
        connection.commit()
        return result
    finally:
        cursor.close()
        connection.close()

#Function to scan UID
def scan_uid(serial_port='COM5', baud_rate=9600):
    ser = serial.Serial(serial_port, baud_rate)

    try:
        uid = ser.readline().decode('utf-8').strip()
        print(uid)
        return uid

    except Exception as e:
        print(f"Error scanning UID: {e}")
        return None

    finally:
        ser.close()

def get_total_books():
    query = "SELECT COUNT(*) AS total_books FROM books"
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    connection.commit()
    return result[0] if result != tuple() else 0


def get_total_issued_books():
    query = "SELECT COUNT(*) AS total_issued_books FROM books WHERE isIssued = 1"
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    connection.commit()
    return result[0] if result != tuple() else 0

@app.route('/')
def login():
    if 'username' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

# Route to display the options
@app.route('/index')
def index():
    if 'username' not in session:
        flash('Please log in first', 'error')
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'], total_books=get_total_books(), total_issued_books=get_total_issued_books())

#Route to display the login page
@app.route('/login', methods=['POST'])
def authenticate():
    username = request.form.get('username')
    password = request.form.get('password')

    if username in users and password == users[username]:
        session['username'] = username
        return redirect(url_for('index'))
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))

#Route for logout procedure
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logout successful!', 'success')
    return redirect(url_for('login'))


# Route to add a book to the database
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        uid = scan_uid()
        bookID = request.form['bookID']
        name = request.form['name']
        publisher = request.form['publisher']
        isbn = request.form['isbn']

        query = "INSERT IGNORE INTO books (uid, bookID, name, publisher, isbn, isIssued) VALUES (%s, %s, %s, %s, %s, 0)"
        data = (uid, bookID, name, publisher, isbn)
        execute_query(query, data)

        return redirect(url_for('add_book'))

    return render_template('add_book.html')

# Route to remove a book from the database
@app.route('/remove_book', methods=['GET', 'POST'])
def remove_book():
    if request.method == 'POST':
        bookID_to_remove = request.form['bookID']

        # Check if the book ID exists in the database
        query_select = "SELECT * FROM books WHERE bookID = %s"
        data_select = (bookID_to_remove,)
        result = execute_query(query_select, data_select)

        if result:
            query_delete = "DELETE FROM books WHERE bookID = %s"
            data_delete = (bookID_to_remove,)
            execute_query(query_delete, data_delete)

            return redirect(url_for('index', success_message='Book removed successfully'))

        else:
            # Book not found
            error_message = 'Book not found. Please check the book ID.'
            return render_template('remove_book.html', error_message=error_message)

    return render_template('remove_book.html')

# Route to issue/return a book
@app.route('/issue_return_book', methods=['GET', 'POST'])
def issue_return_book():
    if request.method == 'POST':
        uid = scan_uid()

        if uid:
            query_select = "SELECT isIssued FROM books WHERE uid = %s"
            data_select = (uid,)
            result = execute_query(query_select, data_select)

            if result:
                current_status = result[0]['isIssued']
                new_status = 1 - current_status

                query_update = "UPDATE books SET isIssued = %s WHERE uid = %s"
                data_update = (new_status, uid)
                execute_query(query_update, data_update)

                if new_status == 1:
                    flash('Book issued successfully', 'success')
                else:
                    flash('Book returned successfully', 'success')

            else:
                flash('UID not found in the database', 'error')

            return redirect(url_for('issue_return_book'))

    return render_template('issue_return_book.html')

if __name__ == '__main__':
    app.run(debug=True)
