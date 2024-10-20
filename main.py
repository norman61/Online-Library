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

        # Define routes
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route("/")
        def index():
            return render_template("index.html")
        
        @self.app.route("/about")
        def about():
            return render_template('about.html')

        @self.app.route("/contact")
        def contact():
            return render_template('contact.html')

        @self.app.route("/signin", methods=['GET', 'POST'])
        def signin():
            if request.method == "POST":
                id = request.form['id']
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
                cursor.execute('INSERT INTO users (Id, Name, Course, Year, Email, Password) VALUES (%s, %s, %s, %s, %s, %s)',
                               (id, name, course, year, email, password))
                self.mysql.connection.commit()
                cursor.close()

                session['id'] = id
                return redirect(url_for('login'))

            return render_template('signin.html')

        @self.app.route("/login", methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                email = request.form['email']
                password = request.form['password']

                if email == "admin@phinmaed.com" and password == "admin":
                    return redirect(url_for('admin_index1'))

                cursor = self.mysql.connection.cursor()
                cursor.execute("SELECT Id FROM users WHERE Email = %s AND Password = %s", (email, password))
                user = cursor.fetchone()
                cursor.close()

                if user:
                    session['id'] = user[0]
                    return redirect(url_for('home'))
                else:
                    flash('Wrong account number or password')
                    return redirect(url_for('login'))

            return render_template('login.html')

        @self.app.route("/admin_index/<string:id>", methods=['GET', 'POST'])
        def admin_index(id):
            cursor = self.mysql.connection.cursor()
            cursor.execute("DELETE FROM books WHERE no_id = %s", (id,))
            self.mysql.connection.commit()
            cursor.close()
            return redirect(url_for('admin_index1'))

        @self.app.route("/admin_index1", methods=["POST", "GET"])
        def admin_index1():
            cursor = self.mysql.connection.cursor()
            cursor.execute("SELECT * FROM books")
            result = cursor.fetchall()
            cursor.close()
            return render_template('admin_index.html', result=result)

        @self.app.route('/admin/<string:id>', methods=["GET", "POST"])
        def admin(id):
            cursor = self.mysql.connection.cursor()
            cursor.execute("UPDATE books SET status = 'Accepted' WHERE no_id = %s", (id,))
            self.mysql.connection.commit()
            cursor.close()
            return redirect(url_for('admin_index1'))

        @self.app.route("/home", methods=['GET', 'POST'])
        def home():
            user_id = session.get('id')
            cursor = self.mysql.connection.cursor()
            cursor.execute("SELECT Name FROM users WHERE Id = %s", (user_id,))
            user = cursor.fetchone()
            cursor.close()

            if request.method == "POST":
                name = request.form["name"]
                title = request.form["title"]
                author = request.form["author"]
                bdate = request.form["bdate"]
                rdate = request.form["rdate"]

                cursor = self.mysql.connection.cursor()
                cursor.execute('INSERT INTO books (Name, Title, Author, Borrow_Date, Return_Date, Id) VALUES (%s, %s, %s, %s, %s, %s)',
                               (name, title, author, bdate, rdate, user_id))
                self.mysql.connection.commit()
                cursor.close()

                return redirect(url_for('borrow'))

            return render_template('home.html', user=user)

        @self.app.route("/borrow")
        def borrow():
            user_id = session.get('id')
            cursor = self.mysql.connection.cursor()
            cursor.execute("""
                SELECT Title, Author, Borrow_Date, Return_Date 
                FROM books 
                WHERE Id = %s 
                ORDER BY Borrow_Date DESC 
                LIMIT 1
            """, (user_id,))
            books = cursor.fetchone()
            cursor.close()

            return render_template("borrow.html", books=books)

        @self.app.route("/notifications")
        def notifications():
            return render_template('notifications.html')

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
            cursor.execute("SELECT Id, Name, Course, Year, Email FROM users WHERE Id = %s", (user_id,))
            user = cursor.fetchone()

            if request.method == 'POST':
                new_id = request.form['id']
                name = request.form['name']
                course = request.form['course']
                year = request.form['year']
                email = request.form['email']

                cursor.execute("""
                    UPDATE users 
                    SET Id = %s, Name = %s, Course = %s, Year = %s, Email = %s 
                    WHERE Id = %s
                """, (new_id, name, course, year, email, user_id))

                self.mysql.connection.commit()
                cursor.close()

                session['id'] = new_id
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