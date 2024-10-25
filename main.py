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

        self._setup_routes()

    def _setup_routes(self):
        @self.app.route("/")
        def index():
            return render_template("index.html")

        @self.app.route("/signin", methods=['GET', 'POST'])
        def signin():
            if request.method == "POST":
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
                    flash('⚠️ Email is already in use.', 'error')
                    return redirect(url_for('signin'))
                if password != repassword:
                    flash('⚠️ Passwords do not match.', 'error')
                    return redirect(url_for('signin'))

                hashed_password = generate_password_hash(password)
                cursor.execute('INSERT INTO users (Name, Course, Year, Email, Password) VALUES (%s, %s, %s, %s, %s)',
                               (name, course, year, email, hashed_password))
                self.mysql.connection.commit()
                cursor.close()

                flash('✅ Successfully registered! Please log in.', 'success')
                return redirect(url_for('login'))

            return render_template('signin.html')

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
                    flash('✅ Successfully logged in!', 'success')
                    return redirect(url_for('home'))
                else:
                    flash('⚠️ Login failed. Please check your credentials.', 'error')

            return render_template('login.html')
        @self.app.route("/home", methods=['GET', 'POST'])
        def home():
            user_id = session.get('id')
            if not user_id:
                flash('⚠️ Please log in first.', 'error')
                return redirect(url_for('login'))

            cursor = self.mysql.connection.cursor()
            cursor.execute("SELECT Name FROM users WHERE Id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                flash('⚠️ User not found.', 'error')
                return redirect(url_for('login'))

            # Fetch all books (no status filter)
            cursor.execute("SELECT Id, ISBN, Title FROM books")
            available_books = cursor.fetchall()
            cursor.close()

            if request.method == "POST":
                book_id = request.form.get("book_id")
                borrow_date = request.form.get("borrow_date")
                return_date = request.form.get("return_date")

                if not all([book_id, borrow_date, return_date]):
                    flash('⚠️ All fields are required.', 'error')
                    return redirect(url_for('home'))

                cursor = self.mysql.connection.cursor()
                cursor.execute("""INSERT INTO borrowed_books (user_id, book_id, borrow_date, return_date, status)
                                VALUES (%s, %s, %s, %s, 'approved')""",
                            (user_id, book_id, borrow_date, return_date))  # Directly set status to approved
                cursor.execute("UPDATE books SET status = 'borrowed' WHERE Id = %s", (book_id,))
                self.mysql.connection.commit()
                cursor.close()

                flash('✅ Book borrowed successfully!', 'success')
                return redirect(url_for('home'))

            return render_template('home.html', user=user, available_books=available_books)
        
        @self.app.route("/borrow")
        def borrow():
            user_id = session.get('id')
            if not user_id:
                flash('⚠️ Please log in first.', 'error')
                return redirect(url_for('login'))

            cursor = self.mysql.connection.cursor()
            cursor.execute("SELECT Name FROM users WHERE Id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                flash('⚠️ User not found.', 'error')
                return redirect(url_for('login'))

            # Fetch borrowed books for the user
            cursor.execute("""
                SELECT b.Title, b.ISBN, bb.return_date 
                FROM borrowed_books bb
                JOIN books b ON bb.book_id = b.id
                WHERE bb.user_id = %s AND bb.status = 'approved'
            """, (user_id,))
            borrowed_books = cursor.fetchall()
            cursor.close()

            return render_template("borrow.html", user=user, borrowed_books=borrowed_books)


        @self.app.route("/borrow_book", methods=['POST'])
        def borrow_book():
            user_id = session.get('id')
            if not user_id:
                flash('⚠️ Please log in first.', 'error')
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

            flash('✅ Book borrowed successfully! Approval required.', 'info')
            return redirect(url_for('home'))

        @self.app.route('/admin_dashboard')
        def admin_dashboard():
            user_id = session.get('id')
            if not user_id:
                flash('⚠️ Please log in first.', 'error')
                return redirect(url_for('login'))

            if not session.get('admin_login'):
                flash('⚠️ Access denied: Admins only.', 'error')
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

        @self.app.route("/borrowed_books")
        def borrowed_books():
            user_id = session.get('id')
            if not user_id:
                flash('⚠️ Please log in first.', 'error')
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

        @self.app.route("/admin/borrow-requests", methods=['GET', 'POST'])
        def borrow_requests():
            if not session.get('admin_login'):
                flash('⚠️ Access denied: Admins only.', 'error')
                return redirect(url_for('index'))

            cursor = self.mysql.connection.cursor()
            cursor.execute("""SELECT bb.id, bb.user_id, b.ISBN, u.Name, bb.borrow_date, bb.return_date, bb.status
                            FROM borrowed_books bb
                            JOIN users u ON bb.user_id = u.Id
                            JOIN books b ON bb.book_id = b.id
                            WHERE bb.status = 'pending'""")
            requests = cursor.fetchall()

            if request.method == 'POST':
                request_id = request.form['request_id']  # Get the unique request ID from the form
                action = request.form['action']

                if action == 'approve':
                    cursor.execute("""UPDATE borrowed_books 
                                    SET status = 'approved' 
                                    WHERE id = %s""",
                                (request_id,))
                    flash('✅ Borrowing request approved!', 'success')
                elif action == 'reject':
                    cursor.execute("""UPDATE borrowed_books 
                                    SET status = 'rejected' 
                                    WHERE id = %s""",
                                (request_id,))
                    flash('⚠️ Borrowing request rejected!', 'error')

                self.mysql.connection.commit()

            cursor.close()
            return render_template('admin_borrow_requests.html', requests=requests)

        @self.app.route("/profile")
        def profile():
            user_id = session.get('id')
            if not user_id:
                flash('⚠️ Please log in first.', 'error')
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
                flash('⚠️ User not found.', 'error')
                return redirect(url_for('login'))

        @self.app.route("/update_profile", methods=['GET', 'POST'])
        def update_profile():
            user_id = session.get('id')
            if not user_id:
                flash('⚠️ Please log in first.', 'error')
                return redirect(url_for('login'))

            cursor = self.mysql.connection.cursor()
            cursor.execute("SELECT Name, Course, Year, Email FROM users WHERE Id = %s", (user_id,))
            user = cursor.fetchone()

            if request.method == 'POST':
                name = request.form['name']
                course = request.form['course']
                year = request.form['year']
                email = request.form['email']

                if not all([name, course, year, email]):
                    flash('⚠️ All fields are required.', 'error')
                    return redirect(url_for('update_profile'))

                cursor.execute("""UPDATE users 
                                  SET Name = %s, Course = %s, Year = %s, Email = %s 
                                  WHERE Id = %s""",
                               (name, course, year, email, user_id))
                self.mysql.connection.commit()
                cursor.close()

                flash('✅ Profile updated successfully.', 'success')
                return redirect(url_for('profile'))

            cursor.close()
            return render_template('update_profile.html', user=user)

        @self.app.route("/logout")
        def logout():
            session.clear()
            flash('✅ Successfully logged out.', 'info')
            return redirect(url_for('index'))

        @self.app.route('/admin_login', methods=['GET', 'POST'])
        def admin_login():
            if request.method == 'POST':
                Email = request.form['Email']
                Password = request.form['Password']

                if Email == 'admin@gmail.com' and Password == 'admin':
                    session['admin_login'] = True
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('⚠️ Incorrect email or password.')

            return render_template('admin_login.html')

        @self.app.route('/admin_logout')
        def admin_logout():
            session.pop('admin_login', None)
            flash('✅ Successfully logged out of admin.', 'info')
            return redirect(url_for('index'))

        @self.app.route("/approve_user/<int:user_id>", methods=['POST'])
        def approve_user(user_id):
            cursor = self.mysql.connection.cursor()
            # Example logic to approve a user, assuming you want to update borrowed_books
            cursor.execute("""UPDATE borrowed_books 
                            SET status = 'approved' 
                            WHERE user_id = %s""", (user_id,))
            self.mysql.connection.commit()
            cursor.close()

            flash('✅ User borrowing request approved!', 'success')
            return redirect(url_for('admin_dashboard'))

    def run(self):
        self.app.run(debug=True)

if __name__ == "__main__":
    library_app = LibraryApp()
    library_app.run()
