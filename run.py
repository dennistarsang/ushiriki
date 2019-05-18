from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from sqlalchemy import create_engine
from datetime import datetime
from wtforms import Form, StringField, SelectField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

from app.functions import get_wards, get_subcounties, dicts_to_tuples

from app.db import connect, clean_select_results


app = Flask(__name__)

app.config.from_pyfile("config.py")
# Config MySQL I can do away with this
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://sang:nyiganet@localhost/ushiriki_db'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'nyiganet'
app.config['MYSQL_DB'] = 'ushiriki_db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor' 

# Found this to be a way of changing a tuple to a dict
# I can remove it since I won't need it
# init MYSQL

# def connect():
#     """Replace username, password and database_name with the real values """
#     db_engine = create_engine("mysql+pymysql://sang:nyiganet@localhost/ushiriki_db")
#     connection = db_engine.connect()
#     return connection

# Index
@app.route('/')
def index():
    connection = connect() # make the connection to db
    # make sample query say to fetch a list of wards and subcounties
    query = "SELECT ward_name, subcounty_name from wards inner join subcounties on wards.subcounty_id = subcounties.subcounty_id"
    # run the query
    wards = connection.execute(query)
    rows = wards.fetchall()
    keys = wards.keys() # the field names in the table
    wards_data = clean_select_results(rows, keys)
    print (wards_data)
    # Let me just show the list on screen
    # from flask import jsonify
    # return jsonify(wards_data)

    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')


# Articles
@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)


# Register Form Class
class RegisterForm(Form):
    wards = get_wards()
    subcounties = get_subcounties()

    # At this moment, the wards are a list of dictionaries, we have to convert them to tuples
    # # we now set this tuple to Select Option
    wards_tuple = dicts_to_tuples(wards, ['ward_id', 'ward_name'])
    # the subcounties tuple
    subcounties_tuple = dicts_to_tuples(subcounties, ['subcounty_id', 'subcounty_name'])
    
    username = StringField('Username', [validators.Length(min=4, max=25)])
    first_name = StringField('First Name', [validators.Length(min=1, max=50)])
    last_name = StringField('Surname', [validators.Length(min=1, max=50)])
    
    #Should I assign this to subcounty name or subcounty id..considering they are subcounties with ids from auto incr?
    subcounty_id = SelectField(u'Subcounties', choices=subcounties_tuple)
    ward_id = SelectField(u'Wards', choices=wards_tuple) 
    
    ward_name= StringField('Ward')
    email_address = StringField('Email', [validators.Length(min=6, max=50)])
    phone_number = StringField('Phone Number', [validators.Length(min=10, max=12)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, first_name=form.first_name.data, ward_name= form.ward_name.data, 
        email_address=form.email_address.data, phone_number=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    #result = cur.execute("SELECT * FROM articles")
    # Show articles only from the user logged in 
    result = cur.execute("SELECT * FROM articles WHERE author = %s", [session['username']])

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)