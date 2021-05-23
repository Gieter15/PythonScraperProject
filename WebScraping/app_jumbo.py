from selenium import webdriver
import sqlite3
from datetime import datetime

#pages_nr = 801
pages_nr = 9
base_url = 'https://www.jumbo.com/listers/producten/'
db_name = 'jumbo_products.db'
table_name = 'PRODUCTS'
clean_table = True

conn = sqlite3.connect(db_name)
c = conn.cursor()

if(clean_table):
    q1 = '''DROP TABLE IF EXISTS {}'''.format(table_name)
    c.execute(q1)
    conn.commit()
    print('***Table is cleaned***')

q1 = '''CREATE TABLE IF NOT EXISTS {}
             ([product_id] VARCHAR(10) PRIMARY KEY,
              [product_name] VARCHAR(30),
              [price_int] INTEGER,
              [price_frac] INTEGER,
              [sale] INTEGER,
              [record_date] date);'''.format(table_name)
c.execute(q1)
conn.commit()

driver = webdriver.Chrome()
driver.get(base_url)

while True:
    try:
        cookies_button = driver.find_element_by_id('onetrust-accept-btn-handler')
        cookies_button.click()
    except:
        continue
    break

for i in range(1, 5):
    print("page number {0}".format(i))
    while True:
        try:
            next_page_button = driver.find_element_by_xpath("//button[@class='jum-button pagination-buttons secondary']")
        except:
            print('cant find next_page_button')
            continue
        break

    while True:
        try:
            products = driver.find_elements_by_class_name("jum-product-card__content")
        except:
            print('cant find products')
            continue
        break


    for product in products:
        p = product.text.split('\n')

        try:
            url = product.find_element_by_tag_name('a').get_attribute('href')
        except:
            print('cannot find url, dummy url is used')
            url = 'cant_find_url_\n0000XX'
        title = p[0]
        price_int = int(p[2])
        price_frac = int(p[3])
        id = url.split('/')[-1]
        insert_date = datetime.now()
        try:
            q2 = '''INSERT OR IGNORE INTO {0} (product_id, product_name, price_int, price_frac, sale, record_date) 
            VALUES ('{1}',"{2}",{3},{4}, {5} ,'{6}')
            ;'''.format(table_name, id, title, price_int, price_frac, 0, insert_date)
            c.execute(q2)
            conn.commit()
        except:
            print('***Could not insert product: {0} with number {1}, skipping it***'.format(title, id))
    
    next_page_button.click()

driver.close()