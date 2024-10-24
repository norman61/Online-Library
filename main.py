from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL

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
                cursor.execute('SELECT COUNT(*) FROM users WHERE Id = %s', (id,))
                id_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM users WHERE Email = %s', (email,))
                email_count = cursor.fetchone()[0]
                cursor.close()

                if id_count > 0:
                    flash('⚠️ There is already an account.')
                    return redirect(url_for('signin'))
                if email_count > 0:
                    flash('⚠️ Email is already in use.')
                    return redirect(url_for('signin'))
                if password != repassword:
                    flash('⚠️ Passwords do not match.')
                    return redirect(url_for('signin'))

                cursor = self.mysql.connection.cursor()
                cursor.execute('INSERT INTO users (Id, Name, Course, Year, Email, Password) VALUES (%s, %s, %s, %s, %s)',
                               (name, course, year, email, password))
                self.mysql.connection.commit()
                cursor.close()

                session['id'] = id
                flash('✅ Successfully registered! Please log in.', 'success')
                return redirect(url_for('login'))

            return render_template('signin.html')

        @self.app.route("/login", methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                email = request.form['email']
                password = request.form['password']

                cursor = self.mysql.connection.cursor()
                cursor.execute("SELECT Id is_admin FROM users WHERE Email = %s AND Password = %s", (email, password))
                user = cursor.fetchone()
                cursor.close()

                if user:
                    session['id'] = user[0]
                    is_admin = user[0]
                    flash('✅ Successfully logged in!', 'success')

                    if is_admin:
                        return redirect(url_for('admin_dashboard'))
                
                    else:
                        return redirect(url_for('home'))
                
                flash('⚠️Login failed. Please check your credentials.')
                return redirect(url_for('login'))
            
            return render_template('login.html')

        @self.app.route("/home", methods=['GET', 'POST'])
        def home():
            user_id = session.get('id')

            if not user_id:
                flash('⚠️ Please log in first.')
                return render_template(url_for('login'))
            
            cursor = self.mysql.connection.cursor()
            cursor.execute("SELECT Name FROM users WHERE Id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                flash('⚠️ User not found.')
                return render_template(url_for('login'))
            
            cursor.close()
            
            if request.method == "POST":
                name = request.form["name"]
                isbn = request.form["isbn"]
                bdate = request.form["bdate"]
                rdate = request.form["rdate"]

                cursor = self.mysql.connection.cursor()
                cursor.execute('INSERT INTO books (Name, ISBN, Borrow_Date, Return_Date) VALUES (%s, %s, %s, %s, %s, %s)',
                               (name, isbn, bdate, rdate,))
                self.mysql.connection.commit()
                cursor.close()

                return redirect(url_for('borrow'))
            
            return render_template('home.html', user=user)
        
        @self.app.route("/borrow")
        def borrow():
            user_id = session.get('id')

            if not user_id:
                flash('⚠️ Please log in first.')
                return render_template(url_for('login'))
            
            cursor = self.mysql.connection.cursor()
            cursor.execute
            ("SELECT Name FROM users WHERE Id = %s", user_id,)
            user = cursor.fetchone()

            if not user:
                flash('⚠️ User not found.')
                return render_template(url_for('login'))
            cursor.execute("""SELECT ISBN, Borrow_Date, Return_Date 
                FROM books 
                WHERE Id = %s 
                ORDER BY Borrow_Date DESC 
                LIMIT 1""", (user_id,))
            books = cursor.fetchone()

            cursor.close()

            return render_template("borrow.html", books=books, user=user)
        
        @self.app.route("/borrow_book/<int:book_id>", methods=['GET', 'POST'])
        def borrow_book(book_id):
            user_id = session.get('id')

            if not user_id:
                return redirect(url_for('login'))
            
            cursor = self.mysql.connection.cursor()
            cursor.execute("""
        INSERT INTO borrowed_books (user_id, book_id, borrow_date, return_date)
        VALUES (%s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY))
    """, (user_id, book_id))
            
            cursor.execute("UPDATE books SET status = 'borrowed' WHERE id = %s", (book_id,))
            self.mysql.connection.commit()
            cursor.close()
            
            flash('Book borrowed successfully!')
            return redirect(url_for('home'))

        @self.app.route('/admin_dashboard')
        def admin_dashboard():
            user_id = session.get('id')  # Get the user ID from session

            if not user_id:  # If no user ID, redirect to login
                flash('⚠️ Please log in first.')
                return redirect(url_for('login'))
            cursor = self.mysql.connection.cursor()
            cursor.execute("SELECT is_admin FROM users WHERE Id = %s", (user_id,))
            is_admin = cursor.fetchone()
            
            if not is_admin or not is_admin[0]:  # If not admin, redirect to home
                flash('⚠️ Access denied: Admins only.')
                return redirect(url_for('home'))
            cursor.execute("SELECT Id, Name, Email, Course, Year FROM users")
            users = cursor.fetchall()

    # Fetch all books along with the count of unique borrowers for each book
            cursor.execute("""SELECT books.id, isbn, COUNT(DISTINCT borrowed_books.user_id) AS borrower_count
                           FROM books
                           LEFT JOIN borrowed_books ON books.id = borrowed_books.book_id
                           GROUP BY books.id""")
            books_with_borrowers = cursor.fetchall()  # [(book_id, isbn, borrower_count), ...]

    # Fetch the list of users who borrowed books and join with user data
            cursor.execute("""SELECT users.Id, users.Name, isbn, borrowed_books.borrow_date, borrowed_books.return_date
                           FROM borrowed_books
                           JOIN users ON borrowed_books.user_id = users.Id
                           JOIN books ON borrowed_books.book_id = books.id
                           ORDER BY borrowed_books.borrow_date DESC""")
            borrowed_books = cursor.fetchall()  # [(user_id, user_name, isbn, borrow_date, return_date), ...]
            cursor.close()
            
            return render_template(
                'admin_dashboard.html', 
                users=users, 
                books=books_with_borrowers, 
                borrowed_books=borrowed_books)
        
        @self.app.route("/borrowing_transactions")
        def borrowing_transactions():
            return render_template('borrowing_transactions.html')

        @self.app.route("/profile")
        def profile():
            user_id = session.get('id')
            if not user_id:
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

        @self.app.route("/update_profile", methods=['GET', 'POST'])
        def update_profile():
            user_id = session.get('id')

            if not user_id:
                flash('Please log in first.')
                return redirect(url_for('login'))

            cursor = self.mysql.connection.cursor()
            cursor.execute("Name, Course, Year, Email FROM users WHERE Id = %s", (user_id,))
            user = cursor.fetchone()

            if request.method == 'POST':
                name = request.form['name']
                course = request.form['course']
                year = request.form['year']
                email = request.form['email']

                cursor.execute("""
                    UPDATE users 
                    SET Id = Name = %s, Course = %s, Year = %s, Email = %s 
                    WHERE Id = %s
                """, (name, course, year, email, user_id))

                self.mysql.connection.commit()
                cursor.close()

                session['id'] = id
                flash('Profile updated successfully.')
                return redirect(url_for('profile'))

            cursor.close()
            return render_template('update_profile.html', user=user)

        @self.app.route("/logout")
        def logout():
            session.clear()
            return redirect(url_for('index'))

    def run(self):
        self.app.run(debug=True)

if __name__ == "__main__":
    library_app = LibraryApp()
    library_app.run()