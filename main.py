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
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/signin', 'signin', self.signin, methods=['GET', 'POST'])
        self.app.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        self.app.add_url_rule('/admin_index', 'admin_index', self.admin_index, methods=['GET', 'POST'])
        self.app.add_url_rule('/home', 'home', self.home, methods=['GET', 'POST'])
        self.app.add_url_rule('/borrow', 'borrow', self.borrow)
        self.app.add_url_rule('/notifications', 'notifications', self.notifications)
        self.app.add_url_rule('/profile', 'profile', self.profile)
        self.app.add_url_rule('/update_profile', 'update_profile', self.update_profile, methods=['GET', 'POST'])
        self.app.add_url_rule('/logout', 'logout', self.logout)

    def index(self):
        return render_template("index.html")

    def signin(self):
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

            if id_count > 0:
                flash('⚠️ This ID is already in use.')
                return redirect(url_for('signin'))

            cursor.execute('SELECT COUNT(*) FROM users WHERE Email = %s', (email,))
            email_count = cursor.fetchone()[0]
            cursor.close()

            if email_count > 0 and password != repassword:
                flash('⚠️ Email is already in use and Passwords do not match')
                return redirect(url_for('signin'))
            elif email_count > 0:
                flash('⚠️ Email is already in use.')
                return redirect(url_for('signin'))
            elif password != repassword:
                flash('⚠️ Passwords do not match.')
                return redirect(url_for('signin'))

            # Insert data into user table
            cursor = self.mysql.connection.cursor()
            cursor.execute('INSERT INTO users (Id, Name, Course, Year, Email, Password) VALUES (%s, %s, %s, %s, %s, %s)',
                           (id, name, course, year, email, password))

            self.mysql.connection.commit()
            cursor.close()

            session['id'] = id
            return redirect(url_for('login'))

        return render_template('signin.html')

    def login(self):
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']

            cursor = self.mysql.connection.cursor()
            cursor.execute("SELECT Id FROM users WHERE Email = %s AND Password = %s", (email, password))
            user = cursor.fetchone()
            cursor.close()

            if user:
                session['id'] = user[0]
                return redirect(url_for('home'))

            elif email == "admin@phinmaed.com" and password == "admin":
                return redirect(url_for('admin_index'))
            else:
                flash('Wrong account number or password')
                return redirect(url_for('login'))

        return render_template('login.html')

    def admin_index(self):
        cursor = self.mysql.connection.cursor()
        cursor.execute("SELECT * FROM books")
        result = cursor.fetchall()
        return render_template('admin_index.html', result=result)

    def home(self):
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

    def borrow(self):
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

    def notifications(self):
        return render_template('notifications.html')

    def profile(self):
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

    def update_profile(self):
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

    def logout(self):
        session.clear()  
        return redirect(url_for('index'))

    def run(self):
        self.app.run(debug=True)


if __name__ == "__main__":
    library_app = LibraryApp()
    library_app.run()