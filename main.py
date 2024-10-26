from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

class LibraryApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = "library"
        self.app.config['MYSQL_HOST'] = 'localhost'
        self.app.config['MYSQL_USER'] = 'root'
        self.app.config['MYSQL_PASSWORD'] = ''
        self.app.config['MYSQL_DB'] = 'library'
        self.mysql = MySQL(self.app)

        #Application routes
        self._setup_routes()

    def get_db_connection(self):
            return self.mysql.connection

    def _setup_routes(self):
        #Home page route
        @self.app.route("/")
        def index():
            return render_template("index.html")

        #User registration form route
        @self.app.route("/signin", methods=['GET', 'POST'])
        def signin():
            if request.method == "POST":
                #Gather user data from the form
                name = request.form['name']
                course = request.form['course']
                year = request.form['year']
                email = request.form['email']
                password = request.form['password']
                repassword = request.form['repassword']

                cursor = self.mysql.connection.cursor()
                cursor.execute('SELECT COUNT(*) FROM users WHERE Email = %s', (email,))
                email_count = cursor.fetchone()[0]

                if email_count > 0:
                    flash('Email is already in use.')
                    return redirect(url_for('signin'))
                if password != repassword:
                    flash('Passwords do not match.')
                    return redirect(url_for('signin'))

                hashed_password = generate_password_hash(password)
                cursor.execute('INSERT INTO users (Name, Course, Year, Email, Password) VALUES (%s, %s, %s, %s, %s)',
                               (name, course, year, email, hashed_password))
                self.mysql.connection.commit()
                cursor.close()

                flash('Successfully registered! Please log in.')
                return redirect(url_for('login'))

            return render_template('signin.html')

        #User login route
        @self.app.route("/login", methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                email = request.form['email']
                password = request.form['password']

                cursor = self.mysql.connection.cursor()
                cursor.execute("SELECT Id, Password FROM users WHERE Email = %s", (email,))
                user = cursor.fetchone()
                cursor.close()

                if user and check_password_hash(user[1], password):
                    session['id'] = user[0]
                    flash('Successfully logged in!')
                    return redirect(url_for('home'))
                else:
                    flash('Login failed. Please check your credentials.')

            return render_template('login.html')

        #User dashboard route
        @self.app.route("/home", methods=['GET', 'POST'])
        def home():
            user_id = session.get('id')
            if not user_id:
                flash('Please log in first.')
                return redirect(url_for('login'))

            cursor = self.mysql.connection.cursor()
            cursor.execute("SELECT Name FROM users WHERE Id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                flash('User not found.')
                return redirect(url_for('login'))

            #Fetch all available books
            cursor.execute("SELECT Id, ISBN, Title FROM books WHERE status = 'available'")
            available_books = cursor.fetchall()
            cursor.close()

            if request.method == "POST":
                book_id = request.form.get("book_id")
                borrow_date = request.form.get("borrow_date")
                return_date = request.form.get("return_date")

                if not all([book_id, borrow_date, return_date]):
                    flash('All fields are required.')
                    return redirect(url_for('home'))

                cursor = self.mysql.connection.cursor()
                cursor.execute("""INSERT INTO borrowed_books (user_id, book_id, borrow_date, return_date, status)
                                  VALUES (%s, %s, %s, %s, 'approved')""",
                               (user_id, book_id, borrow_date, return_date))
                cursor.execute("UPDATE books SET status = 'borrowed' WHERE Id = %s", (book_id,))
                self.mysql.connection.commit()
                cursor.close()

                flash('Book borrowed successfully!')
                return redirect(url_for('home'))

            return render_template('home.html', user=user, available_books=available_books)

        #User profile route
        @self.app.route("/profile")
        def profile():
            user_id = session.get('id')
            if not user_id:
                flash('Please log in first.')
                return redirect(url_for('login'))

            cursor = self.mysql.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE Id = %s", (user_id,))
            user = cursor.fetchone()
            cursor.close()

            if user:
                user_data = {
                    'id': user[0],
                    'name': user[1],
                    'course': user[2],
                    'year': user[3],
                    'email': user[4]
                }
                return render_template('profile.html', user=user_data)
            else:
                flash('User not found.')
                return redirect(url_for('login'))

        #Update user profile route
        @self.app.route("/update_profile", methods=['GET', 'POST'])
        def update_profile():
            user_id = session.get('id')
            if not user_id:
                flash('Please log in first.')
                return redirect(url_for('login'))

            with self.mysql.connection.cursor() as cursor:
                cursor.execute("SELECT Name, Course, Year, Email FROM users WHERE Id = %s", (user_id,))
                user = cursor.fetchone()

                if not user:
                    flash('User not found.')
                    return redirect(url_for('profile'))

                if request.method == 'POST':
                    name = request.form['name']
                    course = request.form['course']
                    year = request.form['year']
                    email = request.form['email']
                    print(f"Debug: Name: {name}, Course: {course}, Year: {year}, Email: {email}")

                    if not all([name, course, year, email]):
                        flash('All fields are required.')
                        return redirect(url_for('update_profile'))

                    try:
                        cursor.execute("""UPDATE users 
                                        SET Name = %s, Course = %s, Year = %s, Email = %s 
                                        WHERE Id = %s""",
                                    (name, course, year, email, user_id))
                        self.mysql.connection.commit()
                        flash('Profile updated successfully.')
                        return redirect(url_for('profile'))
                    except Exception as e:
                        flash(f'An error occurred while updating the profile: {str(e)}')
                        return redirect(url_for('update_profile'))

            return render_template('update_profile.html', user={
                'name': user[0],
                'course': user[1],
                'year': user[2],
                'email': user[3]
            })

        #Borrowing a book route
        @self.app.route("/borrow_book", methods=['POST'])
        def borrow_book():
            user_id = session.get('id')
            if not user_id:
                flash('Please log in first.')
                return redirect(url_for('login'))

            book_id = request.form['book_id']
            borrow_date = request.form['borrow_date']
            return_date = request.form['return_date']

            cursor = self.mysql.connection.cursor()
            cursor.execute("""INSERT INTO borrowed_books (user_id, book_id, borrow_date, return_date, status)
                              VALUES (%s, %s, %s, %s, 'pending')""",
                           (user_id, book_id, borrow_date, return_date))
            cursor.execute("UPDATE books SET status = 'borrowed' WHERE Id = %s", (book_id,))
            self.mysql.connection.commit()
            cursor.close()

            flash('Book borrowed successfully! Approval required.')
            return redirect(url_for('home'))

        #View borrowed books route
        @self.app.route("/borrow")
        def borrow():
            user_id = session.get('id')
            if not user_id:
                flash('Please log in first.')
                return redirect(url_for('login'))

            cursor = self.mysql.connection.cursor()
            try:
                #Fetch user information
                cursor.execute("SELECT Name FROM users WHERE Id = %s", (user_id,))
                user = cursor.fetchone()

                if not user:
                    flash('User not found.')
                    return redirect(url_for('login'))

                #Fetch borrowed books for the user
                cursor.execute("""SELECT b.id, b.ISBN, b.Title, bb.borrow_date, bb.return_date 
                  FROM borrowed_books bb
                  JOIN books b ON bb.book_id = b.id
                  WHERE bb.user_id = %s AND bb.status = 'approved'""", (user_id,))
                borrowed_books = cursor.fetchall()
            except Exception as e:
                flash(f'An error occurred: {str(e)}')
                return redirect(url_for('home'))
            finally:
                cursor.close()

            return render_template("borrow.html", user=user, borrowed_books=borrowed_books)

        #Approval for borrowing a book route
        @self.app.route('/approval')
        def approval():
            return render_template('approval.html')

        #Updating a borrowed book route
        @self.app.route("/update/<int:book_id>", methods=["GET", "POST"])
        def update_book(book_id):
            user_id = session.get('id')
            if not user_id:
                flash('Please log in first.')
                return redirect(url_for('login'))

            if request.method == "POST":
                new_book_id = request.form.get('new_book_id')

                with self.get_db_connection().cursor() as cursor:
                    # Check if the selected book is available
                    cursor.execute("SELECT COUNT(*) FROM books WHERE Id = %s AND status = 'available'", (new_book_id,))
                    available_count = cursor.fetchone()[0]

                    if available_count == 0:
                        flash('The selected book is not available.')
                        return redirect(url_for('update_book', book_id=book_id))

                    # Update the borrowed book
                    cursor.execute("""UPDATE borrowed_books 
                                    SET book_id = %s 
                                    WHERE id = %s AND user_id = %s""",
                                (new_book_id, book_id, user_id))
                    self.mysql.connection.commit()

                flash('Book changed successfully!')
                return redirect(url_for('borrow'))

            # Fetch the current book and available books for the form
            with self.get_db_connection().cursor() as cursor:
                cursor.execute("""SELECT b.Id, b.Title, bb.return_date 
                                FROM borrowed_books bb 
                                JOIN books b ON bb.book_id = b.Id 
                                WHERE bb.id = %s AND bb.user_id = %s""", (book_id, user_id))
                current_book = cursor.fetchone()

                cursor.execute("SELECT Id, Title FROM books WHERE status = 'available'")
                available_books = cursor.fetchall()

            if not current_book:
                flash('No borrowed book found.')
                return redirect(url_for('borrow'))

            return render_template("update_book.html", current_book=current_book, available_books=available_books)

        #Deleting a borrowed book route
        @self.app.route("/delete/<int:book_id>", methods=["POST"])
        def delete_book(book_id):
            user_id = session.get('id')
            if not user_id:
                flash('Please log in first.')
                return redirect(url_for('login'))

            with self.mysql.connection.cursor() as cursor:
                cursor.execute("""DELETE FROM borrowed_books 
                                  WHERE book_id = %s AND user_id = %s""", (book_id, user_id))
                cursor.execute("UPDATE books SET status = 'available' WHERE Id = %s", (book_id,))
                self.mysql.connection.commit()

            flash('Book deleted successfully!')
            return redirect(url_for('borrow'))

        #User log out route
        @self.app.route("/logout")
        def logout():
            session.clear()
            flash('Successfully logged out.')
            return redirect(url_for('index'))

        #Admin login route
        @self.app.route('/admin_login', methods=['GET', 'POST'])
        def admin_login():
            if request.method == 'POST':
                Email = request.form['Email']
                Password = request.form['Password']

                if Email == 'admin@gmail.com' and Password == 'admin':
                    session['admin_login'] = True
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Incorrect email or password. Please check your credentials')

            return render_template('admin_login.html')

        #Admin dashboard route
        @self.app.route('/admin_dashboard')
        def admin_dashboard():
            user_id = session.get('id')
            if not user_id:
                flash('Please log in first.')
                return redirect(url_for('login'))

            if not session.get('admin_login'):
                flash('Access denied: Admins only.')
                return redirect(url_for('home'))

            cursor = self.mysql.connection.cursor()
            cursor.execute("SELECT Id, Name, Email, Course, Year FROM users")
            users = cursor.fetchall()

            cursor.execute("""SELECT books.id, books.ISBN, books.Title, 
                      COUNT(DISTINCT borrowed_books.user_id) AS borrower_count
                      FROM books
                      LEFT JOIN borrowed_books ON books.id = borrowed_books.book_id
                      GROUP BY books.id""")
            books_with_borrowers = cursor.fetchall()

            cursor.execute("""SELECT users.Id, users.Name, books.Title AS book_name, borrowed_books.borrow_date, borrowed_books.return_date, borrowed_books.status
                              FROM borrowed_books
                              JOIN users ON borrowed_books.user_id = users.Id
                              JOIN books ON borrowed_books.book_id = books.id
                              ORDER BY borrowed_books.borrow_date DESC""")
            borrowed_books = cursor.fetchall()
            cursor.close()

            return render_template(
                'admin_dashboard.html',
                users=users,
                books=books_with_borrowers,
                borrowed_books=borrowed_books
            )

        #Managing borrow requests route
        @self.app.route("/admin/borrow-requests", methods=['GET', 'POST'])
        def borrow_requests():
            if not session.get('admin_login'):
                flash('Access denied: Admins only.')
                return redirect(url_for('index'))

            cursor = self.mysql.connection.cursor()
            cursor.execute("""SELECT bb.id, bb.user_id, b.ISBN, u.Name, bb.borrow_date, bb.return_date, bb.status
                            FROM borrowed_books bb
                            JOIN users u ON bb.user_id = u.Id
                            JOIN books b ON bb.book_id = b.id
                            WHERE bb.status = 'pending'""")
            requests = cursor.fetchall()

            if request.method == 'POST':
                request_id = request.form['request_id']  #Get the unique request ID from the form
                action = request.form['action']

                if action == 'approve':
                    cursor.execute("""UPDATE borrowed_books 
                                    SET status = 'approved' 
                                    WHERE id = %s""",
                                (request_id,))
                    flash('Borrowing request approved!')
                    self.mysql.connection.commit()

            cursor.close()
            return render_template('admin_borrow_requests.html', requests=requests)

        #Approving user borrowing requests route
        @self.app.route("/approve_user/<int:user_id>", methods=['POST'])
        def approve_user(user_id):
            cursor = self.mysql.connection.cursor()
            cursor.execute("""UPDATE borrowed_books 
                            SET status = 'approved' 
                            WHERE user_id = %s""", (user_id,))
            self.mysql.connection.commit()
            cursor.close()

            flash('User borrowing request approved!')
            return redirect(url_for('admin_dashboard'))

        #View all borrowed books route
        @self.app.route("/borrowed_books")
        def borrowed_books():
            user_id = session.get('id')
            if not user_id:
                flash('Please log in first.')
                return redirect(url_for('login'))

            cursor = self.mysql.connection.cursor()
            cursor.execute("""SELECT u.Id AS user_id, u.Name AS user_name, b.Title AS book_name, 
                              bb.borrow_date, bb.return_date, bb.status
                              FROM borrowed_books bb
                              JOIN users u ON bb.user_id = u.Id
                              JOIN books b ON bb.book_id = b.id
                              ORDER BY bb.borrow_date DESC;""")
            borrowed_books = cursor.fetchall()
            cursor.close()

            return render_template('borrowed_books.html', borrowed_books=borrowed_books)

        #Admin logout route
        @self.app.route('/admin_logout')
        def admin_logout():
            session.pop('admin_login', None)
            flash('Successfully logged out as an admin.')
            return redirect(url_for('index'))

    def run(self):
        self.app.run(debug=True)

if __name__ == "__main__":
    library_app = LibraryApp()
    library_app.run()
