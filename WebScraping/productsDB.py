import sqlite3
from datetime import datetime
from product import Product

class ProductsDB:
    #constructor
    def __init__(self, db_name, table_name) -> None:
        self.db_name = db_name
        self.table_name = table_name
        self.products = []
        self.connection = None
        self.cursor = None

    def start_db_connection(self):
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()

    def create_table(self):
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

    def clean_table(self):
        self.start_db_connection() if not self.connection else 0
        qry = '''DROP TABLE IF EXISTS {}'''.format(self.table_name)
        self.cursor.execute(qry)
        self.connection.commit()
        print('***Table is cleaned***')

    def insert_into_db(self, product):
        self.start_db_connection() if not self.connection else 0
        insert_date = datetime.now()
        id = int(str(product.product_id) + str(insert_date.isocalendar()[0]) + str(insert_date.isocalendar()[1]) + str(insert_date.isocalendar()[2]))
        try:
            qry = '''INSERT OR IGNORE INTO {0} (id, product_id, product_name, price_int, price_frac, sale, product_url, date_created, date_modified) 
            VALUES ({1}, {2}, "{3}", {4}, {5}, {6}, "{7}", '{8}','{9}');'''.format(self.table_name, product.id, product.product_id, product.title, product.price_int, product.price_frac, product.sale, product.url, insert_date, insert_date)
            self.cursor.execute(qry)
            self.connection.commit()
            print('Product: {0} inserted into table with price {1},{2}'.format(product.title, product.price_int, product.price_frac))
        except:
            pass

    def update_product(self, product):
        insert_date = datetime.now()
        qry = '''INSERT OR IGNORE INTO {0} (id, product_id, product_name, price_int, price_frac, sale, product_url, date_created, date_modified) 
        VALUES ({1}, {2}, "{3}", {4}, {5}, {6}, "{7}", '{8}', '{9}');'''.format(self.table_name, product.id, product.product_id, product.title, product.price_int, product.price_frac, product.sale, product.url, insert_date, insert_date)
        self.cursor.execute(qry)
        self.connection.commit()

    def get_all_products(self):
        self.start_db_connection() if not self.connection else 0
        qry = '''SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{0}';'''.format(self.table_name)
        run_query = self.cursor.execute(qry).fetchall()

        if (run_query[0][0]):
            qry = '''SELECT product_id, price_int, price_frac FROM {} ORDER BY date_modified DESC'''.format(self.table_name)
            self.products = self.cursor.execute(qry).fetchall() 
        return self.products

    def update_date_modified(self, product):
        insert_date = datetime.now()
        qry = '''UPDATE {0} SET date_modified =  '{1}' 
        WHERE product_id = {2} AND price_int = {3} AND price_frac = {4};'''.format(self.table_name, insert_date, product.product_id, product.price_int, product.price_frac)
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