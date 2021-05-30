from socket import timeout
from selenium import webdriver
import sqlite3
from datetime import datetime, timedelta
import time
import math

pages_nr = 801
#pages_nr = 100
base_url = 'https://www.jumbo.com/listers/producten/'
db_name = 'jumbo_products.db'
table_name = 'PRODUCTS'
clean_table = False
max_tries = 10
import re

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

def find_products(input_driver):
    retry_nr = 0
    while True:
        try:
            products = input_driver.find_elements_by_class_name("jum-product-card__content")
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

def find_next_page_button(input_driver):
    retry_nr = 0
    while True:
        try:
            next_page_button = input_driver.find_element_by_xpath("//button[@class='jum-button pagination-buttons secondary']")
        except:
            retry_nr += 1
            if retry_nr < max_tries:
                print('Cant find next_page_button, retrying...')
                continue
            else:
                print('Maximum amount of tries reached for next_page_button, aborting...')
                break
        break
    return next_page_button

def find_cookies_button(input_driver):
    retry_nr = 0
    while True:
        try:
            cookies_button = input_driver.find_element_by_id('onetrust-accept-btn-handler')
        except:
            if retry_nr < max_tries:
                print('Cant find next_page_button, retrying...')
                continue
            else:
                print('Maximum amount of tries reached for next_page_button, aborting...')
                break
        break
    return cookies_button


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
              [product_url] VARCHAR(30),
              [record_date] date);'''.format(table_name)
c.execute(q1)
conn.commit()

driver = webdriver.Chrome()
driver.get(base_url)

# TODO problem with lavazza Espresso, page: https://www.jumbo.com/producten/?offSet=4500&pageSize=25

cookies_button = find_cookies_button(driver)
cookies_button.click()

try:
    warning_message = driver.find_element_by_xpath("//button[@class='jum-button close tertiary icon']")
    warning_message.click()
except:
    print("No warning message is found")

next_page_button = find_next_page_button(driver)

regex = "[0-9] voor [0-9],[0-9]{2} euro"
max_price = 0
max_price_title = ''
start_time = datetime.now()

for i in range(1, pages_nr):
    print("***page number {0} ***".format(i))

    products = find_products(driver)

    for product in products:
        
        lines = product.text.split('\n')
        title = lines[0]
        insert_date = datetime.now()
        print(title)

        price_int = -1
        price_frac = -1
        sale = -1
        id = '-1' 
        url = ''
        if 'Binnenkort' in product.text:
            print('{} will soon be available again'.format(title))

        elif 'korting' in product.text:
            try:
                price_int = int(lines[5])
                price_frac = int(lines[6])
                sale = 1
                url = find_url(product)
                id = url.split('/')[-1]
            except:
                sale = 1
                print('Discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(i, title))

        elif re.search(regex, product.text):
            try:
                sale_text = lines[-2]
                sale_price = sale_text.split(' ')[-2]
                sale_price_int = int(sale_price.split(',')[0])
                sale_price_frac = int(sale_price.split(',')[1])
                sale_quantity = int(sale_text.split(' ')[0])
                sale_unit_price = ((sale_price_int*100 + sale_price_frac)/sale_quantity)/100

                price_int = math.floor(sale_unit_price)
                price_frac = round((sale_unit_price - price_int)*100)

                sale = 1
                url = find_url(product)
                id = url.split('/')[-1]
            except:
                sale = 1
                print('Discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(i, title))

        elif 'gratis' in product.text:
            try:
                price_int = int(lines[2])
                price_frac = int(lines[3])
                sale = 1
                url = find_url(product)
                id = url.split('/')[-1]
            except:
                sale = 1
                print('Discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(i, title))

        else:
            try:
                price_int = int(lines[2])
                price_frac = int(lines[3])
                sale = 0
                url = find_url(product)
                id = url.split('/')[-1]
            except:
                sale = 0
                print('No known discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(i, title))

        if max_price*100 < price_int*100+price_frac:
            max_price = price_int + price_frac/100
            max_price_title = title
            

        try:
            q2 = '''INSERT OR IGNORE INTO {0} (product_id, product_name, price_int, price_frac, sale, product_url, record_date) 
            VALUES ('{1}', "{2}", {3}, {4}, {5} , "{6}", '{7}' );'''.format(table_name, id, title, price_int, price_frac, sale, url, insert_date)
            c.execute(q2)
            conn.commit()
        except:
            print('***Could not insert product: {0} with number {1}, skipping it***'.format(title, id))
    
    next_page_button.click()
    time.sleep(3)
driver.close()
print("***Data scraping completed. {0} pages scanned with {1} products. Most expensive product: {2}, {3}".format(i, i*25, max_price_title, max_price))
end_time = datetime.now()
total_time = end_time - start_time
print('Total running time: {}'.format(total_time))


    