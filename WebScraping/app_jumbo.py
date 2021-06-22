from logging import error
from os import path
from socket import timeout
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import sqlite3
from datetime import datetime, timedelta
import time
import math
import re
from product import Product
from productsDB import ProductsDB

#TODO: make this into a class for extra fancy points?

base_url = 'https://www.jumbo.com/producten/'
#base_url = 'https://www.jumbo.com/producten/?offSet=12075&pageSize=25'
db_folder = 'databases'
db_name = 'products.db'
table_name = 'JUMBO_PRODUCTS'
clean_table = False
max_tries = 3
sale_1 = "[0-9] voor [0-9],[0-9]{2} euro"
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
                print('cannot find url, url is set empty')
                url = ''
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

db_connection = ProductsDB(db_folder, db_name, table_name)
db_connection.clean_table() if clean_table else 0

all_products = db_connection.get_all_products()
product_ids = db_connection.get_all_product_ids()

db_connection.create_jumbo_table()

opts = Options()
opts.set_headless()
assert opts.set_headless
driver = webdriver.Firefox(options = opts)
driver.get(base_url)
time.sleep(3)

db_connection.clean_table if clean_table else 0
all_products = db_connection.get_all_products()
product_ids = db_connection.get_all_product_ids()

db_connection.create_jumbo_table()

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
    page_number = find_current_page_number(driver)
    last_page = page_number == number_of_pages
    print("***page number {0} ***".format(page_number))

    products = find_products(driver)

    for html_product in products:

        p = Product()

        try:
            product_text = html_product.text
        except:
            product_text = ''
            print('Problem loading product on page {0}'.format(page_number))
        
        lines = product_text.split('\n')

        p.title = lines[0]
        insert_date = datetime.now()
        if 'Binnenkort' in product_text:
            print('{} will soon be available again'.format(p.title))
            continue
        elif 'korting' in product_text:
            try:
                for i, line in enumerate(lines):
                    if not line.upper().isupper(): #Check if no characters in string
                        p.price_int = int(line)
                        p.price_frac = int(lines[i+1])
                        break
                p.sale = 1
                p.url = find_url(html_product)
                p.product_id = p.url.split('/')[-1]
            except:
                p.sale = 1
                print('Discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(page_number, p.title))

        elif re.search(sale_1, product_text): #"[0-9] voor [0-9],[0-9]{2} euro"
            sale_text = re.search(sale_1, product_text).group().split(' ')
            sale_price = sale_text[-2]
            p.set_price(sale_price.replace(',','.'))
            sale_quantity = int(sale_text[0])
            sale_unit_price = p.get_price()/sale_quantity

            p.set_price(sale_unit_price)
            p.sale = 1
            p.url = find_url(html_product)
            p.product_id = p.url.split('/')[-1]

        elif 'gratis' in product_text:
            try:
                p.price_int = int(lines[2])
                p.price_frac = int(lines[3])
                p.sale = 1
                p.url = find_url(html_product)
                p.product_id = p.url.split('/')[-1]
            except:
                p.sale = 1
                print('Discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(page_number, p.title))

        else:
            try:
                p.price_int = int(lines[2])
                p.price_frac = int(lines[3])
                p.url = find_url(html_product)
                p.product_id = p.url.split('/')[-1]
            except:
                print('No known discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(page_number, p.title))

        try:
            id = p.product_id + str(insert_date.isocalendar()[0]) + str(insert_date.isocalendar()[1]) + str(insert_date.isocalendar()[2])
            if p.product_id not in product_ids and p.url != '':
                db_connection.insert_into_jumbo_db(p)
                print('Product: {0} inserted into table'.format(p.title))
            elif p.product_id != '-1' and p.url != '' and (p.price_int != all_products[product_ids.index(p.product_id)][1] or p.price_frac != all_products[product_ids.index(p.product_id)][2]):
                old_price_int = all_products[product_ids.index(p.product_id)][1]
                old_price_frac = all_products[product_ids.index(p.product_id)][2]
                db_connection.update_jumbo_product(p)
                print('Product: {0} already exists but price is updated from {1},{2} to {3},{4}'.format(p.title, old_price_int, old_price_frac, p.price_int, p.price_frac))
            elif p.url != '' and p.product_id != '-1':
                db_connection.update_date_jumbo_modified(p)
                print('Product: {0} already exists in table, with same price record update_date updated'.format(p.title))
            else: 
                print("***********Problem with product {0} on page {1}, product text = {2} price = {3},{4}".format( p.title, page_number, product_text, p.price_int, p.price_frac))
                print(html_product.get_attribute('outerHTML'))
        except:            
            print('***Could not insert product: {0} with number {1}, skipping it***'.format(p.title, p.id))
            raise    

    next_page_button.click()
    time.sleep(3)
    if page_number % 100 == 0: # delete all cookies every 100 pages
        current_url = driver.current_url
        print(current_url)
        driver.delete_all_cookies()
        print('*** deleting all cookies***')
        driver.get(current_url)
        time.sleep(3)
        cookies_button = find_cookies_button(driver)
        cookies_button.click()
        next_page_button = find_next_page_button(driver)
        try:
            warning_message = driver.find_element_by_xpath("//button[@class='jum-button close tertiary icon']")
            warning_message.click()
            warning_message.click()
            warning_message.click()
            warning_message.click()
        except:
            print("No warning message is found")


driver.close()
print("***Data scraping completed. {0} pages scanned with {1} products.".format(i, i*25))
end_time = datetime.now()
total_time = end_time - start_time
print('Total running time: {}'.format(total_time))


    