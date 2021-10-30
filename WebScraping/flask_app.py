#!/usr/bin/env python

import pandas as pd
from flask import Flask, render_template, request, url_for, request, url_for
import sqlite3
import os

app = Flask(__name__)
app.debug = True

@app.route("/all_data")
def all_data():
    cur_dir = os.getcwd()
    with sqlite3.connect(os.path.join(os.getcwd(),'WebScraping','databases','products.db')) as cnx:
        df = pd.read_sql_query("SELECT * FROM AH_PRODUCTS", cnx)
        return df.to_html()

@app.route("/product_names")
def product_names():

    with sqlite3.connect("C://Users//roy//Documents//PYTHON//PythonScraperProject//WebScraping//databases//products.db") as cnx:
        df = pd.read_sql_query("SELECT DISTINCT product_name, product_url FROM AH_PRODUCTS", cnx)
        return df.to_html()

@app.route('/', methods=['GET'])
def dropdown():

    with sqlite3.connect("C://Users//roy//Documents//PYTHON//PythonScraperProject//WebScraping//databases//products.db") as cnx:
        df = pd.read_sql_query("SELECT DISTINCT product_name FROM AH_PRODUCTS", cnx)
        # colours = ['Red', 'Blue', 'Black', 'Orange']
        products = df.values.tolist()
        return render_template('index.html', products=products)

@app.route('/input', methods=['GET', 'POST'])
def input_field():
    if request.method == 'POST':
        task_content = request.form['content']

    with sqlite3.connect("C://Users//roy//Documents//PYTHON//PythonScraperProject//WebScraping//databases//products.db") as cnx:
        df = pd.read_sql_query("SELECT DISTINCT product_name FROM AH_PRODUCTS", cnx)
        # colours = ['Red', 'Blue', 'Black', 'Orange']
        products = [x[0] for x in df.values.tolist()]
        return render_template('input_field.html', products=products)

@app.route("/test" , methods=['GET', 'POST'])
def test():
    select = request.form.get('comp_select')
    return(str(select)) # just to see what select is

if __name__=="__main__":
    app.run()