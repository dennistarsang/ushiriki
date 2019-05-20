from datetime import datetime
from functools import wraps

from flask import (Flask, flash, jsonify, logging, redirect, render_template,
                   request, session, url_for)
from passlib.hash import sha256_crypt
from sqlalchemy import create_engine
from wtforms import (Form, PasswordField, SelectField, StringField,
                     TextAreaField, validators)

from app.db import connect, clean_select_results, clean_select_row, select_one, select_many
from app.functions import (dicts_to_tuples, get_subcounties, get_wards,
                           hash_password)

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
    connection = connect()  # make the connection to db
    # make sample query say to fetch a list of wards and subcounties
    query = "SELECT ward_name, subcounty_name from wards inner join subcounties on wards.subcounty_id = subcounties.subcounty_id"
    # run the query
    wards = connection.execute(query)
    rows = wards.fetchall()
    keys = wards.keys()  # the field names in the table
    wards_data = clean_select_results(rows, keys)
    print(wards_data)
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
    posts_content = select_many("SELECT * FROM posts order by post_id desc")

    if posts_content:
        return render_template('articles.html', posts=posts_content)
    else:
        msg = 'No Articles Found'
    return render_template('articles.html', msg=msg)


# Single Article
@app.route('/article/<string:id>/')
def article(post_id):

    post_content = select_one("SELECT * FROM posts WHERE id = %s", [post_id])

    return render_template('article.html', post=post_content)


@app.route('/fetch-areas')
def fetch_areas():
    wards = get_wards()
    subcounties = get_subcounties()

    areas = {
        'subcounties': subcounties,
        'wards': wards
    }
    return jsonify(areas)


# Register Form Class
class RegisterForm(Form):
    # username = StringField('Username', [validators.Length(min=4, max=25)])
    first_name = StringField('First Name', [validators.Length(min=1, max=50)])
    last_name = StringField('Surname', [validators.Length(min=1, max=50)])

    # Should I assign this to subcounty name or subcounty id..considering they are subcounties with ids from auto incr?
    subcounty_id = SelectField(u'Subcounties', choices=[
                               (None, 'Choose your Subcounty')])
    ward_id = SelectField(u'Wards', choices=[(None, 'Choose your ward')])

    email_address = StringField('Email', [validators.Length(min=6, max=50)])
    phone_number = StringField(
        'Phone Number', [validators.Length(min=10, max=12)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST':
        hashed_password = hash_password(form.password.data)

        username = form.email_address.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        ward_id = form.ward_id.data
        email_address = form.email_address.data
        phone_number = form.phone_number.data
        password = hashed_password

        connection = connect()
        query = "INSERT INTO users (username, first_name, last_name, ward_id, email_address, phone_number, password) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        try:
            connection.execute(query, (username, first_name, last_name,
                                       ward_id, email_address, phone_number, password))
            flash('Your account has been created! You are now able to log in', 'success')
        except Exception as e:
            print("Unable to insert because %r" % e)
            flash('Unable to register you', 'danger')

    return render_template('register.html', form=form)
    # else:
    #     import pdb; pdb.set_trace()
    #     flash("There are errors", "danger")
    #     return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['email_address']
        password_candidate = request.form['password']

        connection = connect()

        # Get user by username
        user = connection.execute(
            "SELECT * FROM users WHERE username = %s", [username])
        row = user.fetchone()
        keys = user.keys()
        result = clean_select_row(row, keys)

        if result:
            # Get stored hash

            password = result['password']

            # Compare Passwords
            if hash_password(password_candidate) == password:
                # Passed
                session['logged_in'] = True
                session['username'] = username
                session['user_id'] = result['user_id']

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
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
    articles = select_many(
        "SELECT posts.*, first_name, last_name FROM posts INNER JOIN users ON users.user_id = posts.user_id WHERE posts.user_id = %s ", [session['user_id']])
    return render_template('dashboard.html', articles=articles)

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

        connection = connect()

        # Execute
        connection.execute("INSERT INTO posts(title, post_content, user_id) VALUES(%s, %s, %s)",
                           (title, body, session['user_id']))

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    form = ArticleForm(request.form)
    if request.method == 'GET':
        article = select_one("SELECT * FROM posts where post_id = %s", [id])
        # get form
        
        form.body.data = article['post_content']
        # Populate article form fields
        form.title.data = article['title']

    if request.method == 'POST':
        title = form.title.data
        body = form.body.data

        connection = connect()

        # Execute
        connection.execute(
            "UPDATE posts SET title=%s, post_content=%s WHERE post_id=%s", (title, body, id))

        flash('Article Edited', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


# Delete Article
@app.route('/delete_article/<string:id>', methods=['GET'])
@is_logged_in
def delete_article(id):
    connection = connect()

    connection.execute("DELETE FROM posts WHERE post_id = %s", [id])

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))

@app.route('/poll')
def poll():
    return render_template('poll.html')


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
