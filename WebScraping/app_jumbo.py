from logging import error
from os import path
from socket import timeout
from selenium import webdriver
import sqlite3
from datetime import datetime, timedelta
import time
import math
import re

#TODO: make this into a class for extra fancy points?

base_url = 'https://www.jumbo.com/listers/producten/'
base_url = 'https://www.jumbo.com/producten/?offSet=14475&pageSize=25'
db_name = 'jumbo_products.db'
table_name = 'PRODUCTS'
clean_table = False
max_tries = 10
all_products = []
product_ids = []
regex = "[0-9] voor [0-9],[0-9]{2} euro"
max_price = 0
max_price_title = ''
start_time = datetime.now()
develop_environment = True

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

def find_current_page_number(input_driver):
    retry_nr = 0
    page_number = 0
    while True:
        try:
            numbers_container = input_driver.find_element_by_xpath("//ul[@class='pagination unstyled d-block d-m-none']")
            numbers = numbers_container.find_elements_by_tag_name('li')
            for nr in numbers:
                if 'font-weight-bold' in nr.get_attribute('class'):
                    page_number = int(nr.get_attribute('innerHTML'))
        except:
            retry_nr += 1
            if retry_nr < max_tries:
                print('Cant find current_page_number, retrying...')
                continue
            else:
                print('Maximum amount of tries reached for next_page_button, aborting...')
                break
        break
    return page_number

def find_number_of_pages(input_driver):
    retry_nr = 0
    page_number = 0
    while True:
        try:
            numbers_container = driver.find_element_by_xpath("//ul[@class='pagination unstyled d-block d-m-none']")
            numbers = numbers_container.find_elements_by_tag_name('li')
            page_number = int(numbers[-1].get_attribute('innerHTML'))
        except:
            retry_nr += 1
            if retry_nr < max_tries:
                print('Cant find number_of_pages, retrying...')
                continue
            else:
                print('Maximum amount of tries reached for number_of_pages, aborting...')
                break
        break
    return page_number

def find_next_page_button(input_driver):
    retry_nr = 0
    while True:
        try:
            nav_buttons = input_driver.find_elements_by_xpath("//button[@class='jum-button pagination-buttons secondary']")
            next_page_button = nav_buttons[-1]
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
             ([id] VARCHAR(30) PRIMARY KEY,
              [product_id] VARCHAR(10),
              [product_name] VARCHAR(30),
              [price_int] INTEGER,
              [price_frac] INTEGER,
              [sale] INTEGER,
              [product_url] VARCHAR(30),
              [insert_date] date,
              [update_date] date);'''.format(table_name)
c.execute(qry)
conn.commit()

options = webdriver.ChromeOptions()
options.add_argument("user-data-dir=./profile")
driver = webdriver.Chrome()
driver.get(base_url)

cookies_button = find_cookies_button(driver)
cookies_button.click()

try:
    warning_message = driver.find_element_by_xpath("//button[@class='jum-button close tertiary icon']")
    warning_message.click()
    warning_message.click()
    warning_message.click()
    warning_message.click()
except:
    print("No warning message is found")

next_page_button = find_next_page_button(driver)
number_of_pages = find_number_of_pages(driver)
print('number_of_pages: {}'.format(number_of_pages))

page_number = 0
last_page = False
while not last_page:
    products = []
    page_number = find_current_page_number(driver)
    last_page = page_number == number_of_pages
    print("***page number {0} ***".format(page_number))

    products = find_products(driver)

    for product in products:

        try:
            product_text = product.text
        except:
            product_text = ''
            print('Problem loading product on page {0}'.format(page_number))
        
        lines = product_text.split('\n')

        title = lines[0]
        insert_date = datetime.now()
        price_int = -1
        price_frac = -1
        sale = -1
        product_id = '-1' 
        url = ''
        if 'Binnenkort' in product_text:
            print('{} will soon be available again'.format(title))

        elif 'korting' in product_text:
            try:
                for i, line in enumerate(lines):
                    if not line.upper().isupper(): #Check if no characters in string
                        price_int = int(line)
                        price_frac = int(lines[i+1])
                        break
                # price_int = int(lines[5])
                # price_frac = int(lines[6])
                sale = 1
                url = find_url(product)
                product_id = url.split('/')[-1]
            except:
                sale = 1
                print('Discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(i, title))

        elif re.search(regex, product_text):
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
                product_id = url.split('/')[-1]
            except:
                sale = 1
                print('Discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(i, title))

        elif 'gratis' in product_text:
            try:
                price_int = int(lines[2])
                price_frac = int(lines[3])
                sale = 1
                url = find_url(product)
                product_id = url.split('/')[-1]
            except:
                sale = 1
                print('Discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(i, title))

        else:
            try:
                price_int = int(lines[2])
                price_frac = int(lines[3])
                sale = 0
                url = find_url(product)
                product_id = url.split('/')[-1]
            except:
                sale = 0
                print('No known discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(i, title))

        if max_price*100 < price_int*100+price_frac:
            max_price = price_int + price_frac/100
            max_price_title = title
            

        try:
            id = product_id + str(insert_date.isocalendar()[0]) + str(insert_date.isocalendar()[1]) + str(insert_date.isocalendar()[2])
            if product_id not in product_ids:
                qry = '''INSERT OR IGNORE INTO {0} (id, product_id, product_name, price_int, price_frac, sale, product_url, insert_date, update_date) 
                VALUES ('{1}','{2}', "{3}", {4}, {5}, {6}, "{7}", '{8}','{9}');'''.format(table_name, id, product_id, title, price_int, price_frac, sale, url, insert_date, insert_date)
                c.execute(qry)
                conn.commit()
                print('Product: {0} inserted into table'.format(title))
            elif product_id != '-1' and (price_int != all_products[product_ids.index(product_id)][1] or price_frac != all_products[product_ids.index(product_id)][2]):
                old_price_int = all_products[product_ids.index(product_id)][1]
                old_price_frac = all_products[product_ids.index(product_id)][2]
                qry = '''INSERT OR IGNORE INTO {0} (id, product_id, product_name, price_int, price_frac, sale, product_url, insert_date, update_date) 
                VALUES ('{1}','{2}', "{3}", {4}, {5}, {6}, "{7}", '{8}', '{9}');'''.format(table_name, id, product_id, title, price_int, price_frac, sale, url, insert_date, insert_date)
                c.execute(qry)
                conn.commit()
                print('Product: {0} already exists but price is updated from {1},{2} to {3},{4}'.format(title, old_price_int, old_price_frac, price_int, price_frac))
            else:
                qry = '''INSERT OR IGNORE INTO {0} (update_date) 
                VALUES ('{1}');'''.format(table_name, insert_date)
                c.execute(qry)
                conn.commit()
                print('Product: {0} already exists in table, with same price record update_date updated'.format(title))
        except:
            print('***Could not insert product: {0} with number {1}, skipping it***'.format(title, id))
    
    next_page_button.click()
    time.sleep(3)

driver.close()
print("***Data scraping completed. {0} pages scanned with {1} products. Most expensive product: {2}, {3}".format(i, i*25, max_price_title, max_price))
end_time = datetime.now()
total_time = end_time - start_time
print('Total running time: {}'.format(total_time))


    