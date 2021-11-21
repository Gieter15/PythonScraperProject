import sqlite3
from datetime import datetime
import os
from objects.product import Product
import logging

class ProductsDB:
    #constructor
    def __init__(self, db_folder, db_name, table_name) -> None:
        self.db_folder = db_folder
        self.db_name = db_name
        self.table_name = table_name
        self.products = []
        self.connection = None
        self.cursor = None

        self.start_db_connection()

    def start_db_connection(self):
        if os.path.exists(os.path.join(self.db_folder,self.db_name)):
            self.connection = sqlite3.connect(os.path.join(self.db_folder,self.db_name))
            self.cursor = self.connection.cursor()
        else:
            logging.warning("Cannot find path")

    def create_ah_table(self):
        qry = '''CREATE TABLE IF NOT EXISTS {}
             ([id] BIGINT PRIMARY KEY,
              [product_id] INTEGER,
              [product_name] VARCHAR(30),
              [price_int] INTEGER,
              [price_frac] INTEGER,
              [sale] INTEGER,
              [product_url] VARCHAR(30),
              [date_created] date,
              [date_modified] date);'''.format(self.table_name)
        self.cursor.execute(qry)
        self.connection.commit()

    def create_jumbo_table(self):
        qry = '''CREATE TABLE IF NOT EXISTS {}
             ([id] VARCHAR(30) PRIMARY KEY,
              [product_id] VARCHAR(10),
              [product_name] VARCHAR(30),
              [price_int] INTEGER,
              [price_frac] INTEGER,
              [sale] INTEGER,
              [product_url] VARCHAR(30),
              [date_created] date,
              [date_modified] date);'''.format(self.table_name)
        self.cursor.execute(qry)
        self.connection.commit()

    def clean_table(self):
        self.start_db_connection() if not self.connection else 0
        qry = '''DROP TABLE IF EXISTS {}'''.format(self.table_name)
        self.cursor.execute(qry)
        self.connection.commit()
        print('***Table is cleaned***')

    def insert_into_ah_db(self, product):
        self.start_db_connection() if not self.connection else 0
        insert_date = datetime.now()
        product.id = int(str(product.product_id) + str(insert_date.isocalendar()[0]) + str(insert_date.isocalendar()[1]) + str(insert_date.isocalendar()[2]))
        try:
            qry = '''INSERT OR IGNORE INTO {0} (id, product_id, product_name, price_int, price_frac, sale, product_url, date_created, date_modified) 
            VALUES ({1}, {2}, "{3}", {4}, {5}, {6}, "{7}", '{8}','{9}');'''.format(self.table_name, product.id, product.product_id, product.title, product.price_int, product.price_frac, product.sale, product.url, insert_date, insert_date)
            self.cursor.execute(qry)
            self.connection.commit()
        except:
            pass

    def update_ah_product(self, product):
        insert_date = datetime.now()
        product.id = int(str(product.product_id) + str(insert_date.isocalendar()[0]) + str(insert_date.isocalendar()[1]) + str(insert_date.isocalendar()[2]))
        qry = '''INSERT OR IGNORE INTO {0} (id, product_id, product_name, price_int, price_frac, sale, product_url, date_created, date_modified) 
        VALUES ({1}, {2}, "{3}", {4}, {5}, {6}, "{7}", '{8}', '{9}');'''.format(self.table_name, product.id, product.product_id, product.title, product.price_int, product.price_frac, product.sale, product.url, insert_date, insert_date)
        self.cursor.execute(qry)
        self.connection.commit()

    def insert_into_jumbo_db(self, product):
        self.start_db_connection() if not self.connection else 0
        insert_date = datetime.now()
        product.id = str(product.product_id) + str(insert_date.isocalendar()[0]) + str(insert_date.isocalendar()[1]) + str(insert_date.isocalendar()[2])
        try:
            qry = '''INSERT OR IGNORE INTO {0} (id, product_id, product_name, price_int, price_frac, sale, product_url, date_created, date_modified) 
            VALUES ('{1}','{2}', "{3}", {4}, {5}, {6}, "{7}", '{8}','{9}');'''.format(self.table_name, product.id, product.product_id, product.title, product.price_int, product.price_frac, product.sale, product.url, insert_date, insert_date)
            self.cursor.execute(qry)
            self.connection.commit()
        except:
            raise

    def update_jumbo_product(self, product):
        self.start_db_connection() if not self.connection else 0
        insert_date = datetime.now()
        product.id = str(product.product_id) + str(insert_date.isocalendar()[0]) + str(insert_date.isocalendar()[1]) + str(insert_date.isocalendar()[2])
        qry = '''INSERT OR IGNORE INTO {0} (id, product_id, product_name, price_int, price_frac, sale, product_url, date_created, date_modified) 
        VALUES ('{1}','{2}', "{3}", {4}, {5}, {6}, "{7}", '{8}', '{9}');'''.format(self.table_name, product.id, product.product_id, product.title, product.price_int, product.price_frac, product.sale, product.url, insert_date, insert_date)  
        self.cursor.execute(qry)
        self.connection.commit()


    def get_all_products(self):
        self.start_db_connection() if not self.connection else 0
        qry = '''SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{0}';'''.format(self.table_name)
        run_query = self.cursor.execute(qry).fetchall()

        if (run_query[0][0]):
            qry = '''SELECT product_id, price_int, price_frac FROM {} ORDER BY date_modified DESC'''.format(self.table_name)
            temp_products = self.cursor.execute(qry).fetchall() 
            self.products = list([list(prd) for prd in temp_products])
        return self.products

    def update_date_ah_modified(self, product):
        insert_date = datetime.now()
        qry = '''UPDATE {0} SET date_modified =  '{1}' 
        WHERE product_id = {2} AND 
        date_created = (SELECT date_created FROM {0} WHERE product_id = {2} AND price_int = {3} AND price_frac = {4}
        ORDER BY date_created desc LIMIT 1);'''.format(self.table_name, insert_date, product.product_id, product.price_int, product.price_frac)
        self.cursor.execute(qry)
        self.connection.commit()

    def update_date_jumbo_modified(self, product):
        insert_date = datetime.now()
        qry = '''UPDATE {0} SET date_modified =  '{1}' 
        WHERE product_id = '{2}' AND date_created = (
            SELECT date_created FROM {0} WHERE product_id = '{2}' AND price_int = {3} AND price_frac = {4} 
            Order By date_created desc LIMIT 1);'''.format(self.table_name, insert_date, product.product_id, product.price_int, product.price_frac)
        self.cursor.execute(qry)
        self.connection.commit()

    def get_all_product_ids(self):
        self.start_db_connection() if not self.connection else 0
        self.get_all_products()
        product_ids = [pid[0] for pid in self.products]
        return product_ids

    def update_db_record(self):
        pass


if __name__== "__main__":
    db = ProductsDB('test.db', 'test_table')