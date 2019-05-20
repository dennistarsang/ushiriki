import hashlib

from app.db import clean_select_results, clean_select_row, connect


def get_subcounties():
    # returns a list of subcounties
    connection = connect()
    query = "SELECT * from subcounties order by subcounty_name ASC"
    subcounties = connection.execute(query)
    rows = subcounties.fetchall()
    keys = subcounties.keys()
    subcounties_data = clean_select_results(rows, keys)
    return subcounties_data

def get_wards():
    # This function returns a list of wards as a list of dicts
    connection = connect()
    query = "SELECT ward_id, ward_name, subcounty_id from wards order by ward_name asc"
    wards = connection.execute(query)
    rows = wards.fetchall()
    keys = wards.keys() # the field names in the table
    wards_data = clean_select_results(rows, keys)
    return wards_data

def dicts_to_tuples(dicts, keys):
    # this function takes a list of dictionaries and converts them to tuples
    # the keys contains the keys that we need to add to a tuple
    # example in a list of wards, the keys will be ward_id and ward_name
    tuples = []    
    for item in dicts:
        tuples.append(tuple([item[keys[0]], item[keys[1]]]))
    return tuples

def hash_password(password):
    hash_object = hashlib.sha256(password.encode('utf-8'))
    return hash_object.hexdigest()
