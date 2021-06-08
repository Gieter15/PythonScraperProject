from logging import error
from os import path
from socket import timeout
from selenium import webdriver
import sqlite3
from datetime import datetime
import time

#TODO: add product category. Add amount of product, now there will be unclear titles

#api_url = https://www.ah.nl/features/api/mega-menu/products
base_url = 'https://www.ah.nl/producten'
db_name = 'ah_products2.db'
table_name = 'PRODUCTS'
clean_table = True
max_tries = 10
all_products = []
product_ids = []
regex = "[0-9] voor [0-9],[0-9]{2} euro"
max_price = 0
max_price_title = ''
start_time = datetime.now()
develop_environment = True

def find_product_category_links(input_driver):
    retry_nr = 0
    urls = []
    while True:
        try:
            category_container = input_driver.find_element_by_class_name("product-category-overview_root__2Lyn0")
            categories = category_container.find_elements_by_tag_name("div")
            for category in categories:
                a = category.find_element_by_tag_name("a")
                url = a.get_attribute('href')
                urls.append(url)
        except:
            retry_nr += 1
            if retry_nr < max_tries:
                print('cannot find categories, retrying...')
                continue
            else:
                print('cannot find categories, empty list is returned')
                break
        break
    urls = list(set(urls))
    return urls

def find_cookies_button(input_driver):
    retry_nr = 0
    while True:
        try:
            cookies_button = input_driver.find_element_by_id('accept-cookies')
        except:
            if retry_nr < max_tries:
                print('Cant find next_page_button, retrying...')
                continue
            else:
                print('Maximum amount of tries reached for next_page_button, aborting...')
                break
        break
    return cookies_button

def find_products(input_driver):
    retry_nr = 0
    while True:
        try:
            container = input_driver.find_element_by_class_name("search-lane-wrapper")
            products = container.find_elements_by_tag_name("article")
        except:
            retry_nr += 1
            if retry_nr < max_tries:
                print('Cant find products, retrying...')
                continue
            else:
                print('Maximum amount of tries reached for products, aborting...')
                break
        break
    return products

def find_url(input_product):
    retry_nr = 0
    while True:
        try:
            url = input_product.find_element_by_tag_name('a').get_attribute('href')
        except:
            retry_nr += 1
            if retry_nr < max_tries:
                print('Cant find url, retrying...')
                continue
            else:
                print('cannot find url, dummy url is used')
                url = 'cant_find_url_\n0000XX'
                break
        break
    return url

def find_product_title(input_product):
    retry_nr = 0
    prd_title = ''
    while True:
        try:
            prd_title = input_product.find_element_by_tag_name('a').get_attribute('title')
        except:
            retry_nr += 1
            if retry_nr < max_tries:
                print('Cant find product title, retrying...')
                continue
            else:
                print('cannot find product title, dummy title is used')
                break
        break
    return prd_title


def chrome_clear_cache(input_driver):
    input_driver.get('chrome://settings/clearBrowserData')
    input_driver.find_element_by_id('clearBrowsingDataConfirm')

conn = sqlite3.connect(db_name)
c = conn.cursor()

if(clean_table):
    qry = '''DROP TABLE IF EXISTS {}'''.format(table_name)
    c.execute(qry)
    conn.commit()
    print('***Table is cleaned***')
else:
    qry = '''SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{0}';'''.format(table_name)
    run_query = c.execute(qry).fetchall()
    
    if (run_query[0][0]):
        qry = '''SELECT product_id, price_int, price_frac FROM {} '''.format(table_name)
        all_products = c.execute(qry).fetchall()  #TODO: these need to be ordered by input date so that when the last version of the product is compared with new entries
        product_ids = [pid[0] for pid in all_products]

qry = '''CREATE TABLE IF NOT EXISTS {}
             ([id] BIGINT PRIMARY KEY,
              [product_id] INTEGER,
              [product_name] VARCHAR(30),
              [price_int] INTEGER,
              [price_frac] INTEGER,
              [sale] INTEGER,
              [product_url] VARCHAR(30),
              [date_created] date,
              [date_modified] date);'''.format(table_name)
c.execute(qry)
conn.commit()

driver = webdriver.Chrome()
driver.get(base_url)

cookies_button = find_cookies_button(driver)
cookies_button.click()

urls = find_product_category_links(driver)

for url in urls:
    driver.get(url + '?page=30')
    time.sleep(2)

    try:
        popup_message = driver.find_element_by_xpath("//button[@class='popover_closeButton__2FHcJ']")
        popup_message.click()
    except:
        print("No popup message is found")

    products = find_products(driver)
    updates = 0
    inserts = 0
    untouched = 0
    for i, product in enumerate(products):
        product_id = -1
        insert_date = datetime.now()
        price_int = -1
        price_frac = -1
        title = ''
        product_text = ''
        sale = 0

        product_text = product.text
        lines = product_text.split('\n')

        for line in lines:
            if not line.upper().isupper():
                try:
                    price_int = line.split('.')[0]
                    price_frac = line.split('.')[1]
                except:
                    print('***problem with obtaining price of product from string {0}. skipping***'.format(lines))
                    price_int = -1

        if '2E HALVE PRIJS' in product_text:
            sale = 1

        title = find_product_title(product)
        url = find_url(product)
        try:
            product_id = int([u for u in url.split('/') if u.startswith('wi')][0][2::])
        except:
            print('Product is not a single product')
            continue

        try:
            id = int(str(product_id) + str(insert_date.isocalendar()[0]) + str(insert_date.isocalendar()[1]) + str(insert_date.isocalendar()[2]))
            if product_id != -1 and product_id not in product_ids:
                qry = '''INSERT OR IGNORE INTO {0} (id, product_id, product_name, price_int, price_frac, sale, product_url, date_created, date_modified) 
                VALUES ({1}, {2}, "{3}", {4}, {5}, {6}, "{7}", '{8}','{9}');'''.format(table_name, id, product_id, title, price_int, price_frac, sale, url, insert_date, insert_date)
                c.execute(qry)
                conn.commit()
                print('Product: {0} inserted into table with price {1},{2}'.format(title, price_int, price_frac))
                inserts += 1
            elif product_id != -1 and (int(price_int) != all_products[product_ids.index(product_id)][1] or int(price_frac) != all_products[product_ids.index(product_id)][2]):
                old_price_int = all_products[product_ids.index(product_id)][1]
                old_price_frac = all_products[product_ids.index(product_id)][2]
                qry = '''INSERT OR IGNORE INTO {0} (id, product_id, product_name, price_int, price_frac, sale, product_url, date_created, date_modified) 
                VALUES ({1}, {2}, "{3}", {4}, {5}, {6}, "{7}", '{8}', '{9}');'''.format(table_name, id, product_id, title, price_int, price_frac, sale, url, insert_date, insert_date)
                c.execute(qry)
                conn.commit()
                print('Product: {0} already exists but price is updated from {1},{2} to {3},{4}'.format(title, old_price_int, old_price_frac, price_int, price_frac))
                updates += 1
            else:
                qry = '''INSERT OR IGNORE INTO {0} (update_date) 
                VALUES ('{1}');'''.format(table_name, insert_date)
                c.execute(qry)
                conn.commit()
                print('Product: {0} already exists in table, with same price record update_date updated'.format(title))
                untouched += 1
        except:
            print('***Could not insert product: {0} with number {1}, skipping it***'.format(title, id))
    print('{0} products analyzed, inserts: {1}, updates: {2}, untouched: {3}'.format(i, inserts, updates, untouched))


    

driver.close()
print("***Data scraping completed. ***")
end_time = datetime.now()
total_time = end_time - start_time
print('Total running time: {}'.format(total_time))