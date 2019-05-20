"""" The first three functions in this file
: connect - connecting to the database
: clean_select_row : returns the result of a single table row as a dictionary
: clean_select_results : does the same as above but for more than one result

You can put them in one file and import them wherever you want to run queries
---
The sections below the three functions are demonstrations on how to run queries
"""

from sqlalchemy import create_engine
from datetime import datetime

def connect():
    """Replace username, password and database_name with the real values """
    db_engine = create_engine("mysql+pymysql://sang:nyiganet@localhost/ushiriki_db")
    connection = db_engine.connect()
    return connection

def clean_select_row(row, keys):
    clean_row = [str(field) if isinstance(field, datetime)
                 else field for field in list(row)]
    current_row = {}
    for i in range(len(keys)):
        current_row[keys[i]] = clean_row[i]
    return current_row


def clean_select_results(data, keys):
    if len(data) == 0:
        return {}

    result_data = []
    for row in data:
        result_data.append(clean_select_row(row, keys))
    return result_data

def select_one(query, values=[]):
    connection = connect()
    result = connection.execute(query, values)
    row = result.fetchone()
    keys = result.keys()
    return clean_select_row(row, keys)

def select_many(query, values=[]):
    connection = connect()
    result = connection.execute(query, values)
    rows = result.fetchall()
    keys = result.keys()
    return clean_select_results(rows, keys)

if __name__ == "__main__":
    # So you can run insert queries like this
    query = "INSERT INTO users (firstname, lastname, gender) VALUES (%s, %s, %s)"
    connection = connect()
    try:
        connection.execute(query, ('Sam', 'Rapando', 'Male')) # the values to insert into table
    except Exception as e:
        print ("Query failed because %r" % e)


    # Then update queries like
    query = "UPDATE users SET firstname=%s, lastname=%s where id=%s"
    connection = connect()
    try:
        connection.execute(query, ('Samson', 'Raps', 1))
        connection.commit()
    except Exception as e:
        print ("Query failed because %r" % e)

    # Select queries
    connection = connect()
    query = "SELECT * FROM users"
    users = connection.execute(query)
    rows = users.fetchall()
    keys = users.keys()
    user_list = clean_select_results(rows, keys)
    print (user_list)

    # select one user
    connection = connect()
    query = "SELECT * FROM users WHERE id=%s"
    user = connection.execute(query, ('1', ))
    row = user.fetchone()
    keys = user.keys()
    user_details = clean_select_row(row, keys)
    print (user_details)

