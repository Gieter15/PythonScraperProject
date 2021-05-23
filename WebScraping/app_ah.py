from sqlite3.dbapi2 import Connection
import requests
from bs4 import BeautifulSoup
import sqlite3
from pandas import DataFrame
from datetime import datetime

base_url = 'https://www.ah.nl/producten/product/'
db_name = 'ah_products.db'
table_name = 'PRODUCTS'
clean_table = False

conn = sqlite3.connect(db_name)
c = conn.cursor()

if(clean_table):
    q1 = '''DROP TABLE IF EXISTS {}'''.format(table_name)
    c.execute(q1)
    conn.commit()
    print('***Table is cleaned***')

q1 = '''CREATE TABLE IF NOT EXISTS {}
             ([product_id] INTEGER PRIMARY KEY,
              [product_name] VARCHAR(30),
              [price_int] INTEGER,
              [price_frac] INTEGER,
              [sale] INTEGER,
              [record_date] date);'''.format(table_name)
c.execute(q1)
conn.commit()

for nr in range(123000, 495905):
    URL = base_url + 'wi{}'.format(nr)
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, 'html.parser')
    not_found = soup.find_all('img', class_='not-found_image__2hTsV')
    if len(not_found) == 0:
        title = soup.find('title').text.strip().split("  ")[0]
        bonus = soup.find_all('div', class_='promo-sticker_root__c_crh promo-sticker_bonus__3f8ua product-card-hero_promoSticker__KZmyN')

        if len(bonus) == 0:
            sale = 0
        else:
            sale = 1
            print('***SALE***')

        try:
            price_int = soup.find('span', class_ = 'price-amount_integer__1cJgL').text.strip()
            price_frac = soup.find('span', class_ = 'price-amount_fractional__2wVIK').text.strip()
            
        except:
            print('***Price of product: "{0}" is unknown***'.format(title))
            price_int = -1
            price_frac = -1

        insert_date = datetime.now()
        print(nr, title, price_int, price_frac, insert_date)
        try:
            q2 = '''INSERT OR IGNORE INTO {0} (product_id, product_name, price_int, price_frac, sale, record_date) 
            VALUES ({1},"{2}",{3},{4}, {5} ,'{6}')
            ;'''.format(table_name, nr, title, price_int, price_frac, sale, insert_date)
            c.execute(q2)
            conn.commit()
        except:
            print('***Could not insert product: {0} with number {1}, skipping it***'.format(title, nr))

q3 = '''SELECT COUNT(*) from {};'''.format(table_name)
c.execute(q3)
result = c.fetchall()[0]
print(result)