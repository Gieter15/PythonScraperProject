from logging import error
from os import path
from socket import timeout
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import sqlite3
from datetime import datetime
import time

from product import Product
from productsDB import ProductsDB
import re

#TODO: add product category. Add amount of product, now there will be unclear titles

#api_url = https://www.ah.nl/features/api/mega-menu/products
base_url = 'https://www.ah.nl/producten'
db_folder = 'databases'
db_name = 'products.db'
table_name = 'AH_PRODUCTS'
clean_table = False
max_tries = 2
start_time = datetime.now()

sale_1 = "[0-9] \+ [0-9] GRATIS"
sale_2 = "[0-9] VOOR [0-9].[0-9]{2}"
sale_3 = "[0-9][0-9]\% KORTING"
sale_4 = "2E HALVE PRIJS"

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
                print('Cant find cookies button, retrying...')
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

db_connection = ProductsDB(db_folder, db_name, table_name)

db_connection.clean_table() if clean_table else 0
    
all_products = db_connection.get_all_products()
product_ids = db_connection.get_all_product_ids()

db_connection.create_ah_table()

#driver = webdriver.Chrome()
opts = Options()
opts.set_headless()
assert opts.set_headless
driver = webdriver.Firefox(options = opts)
driver.get(base_url)

cookies_button = find_cookies_button(driver)
cookies_button.click()

urls = find_product_category_links(driver)

for url in urls:
    driver.get(url + '?page=30')
    time.sleep(1)

    try:
        popup_message = driver.find_element_by_xpath("//button[@class='popover_closeButton__2FHcJ']")
        popup_message.click()
    except:
        print("No popup message is found")

    html_products = find_products(driver)
    updates = 0
    inserts = 0
    untouched = 0
    for i, html_product in enumerate(html_products):
        p = Product()
        insert_date = datetime.now()

        product_text = html_product.text
        lines = product_text.split('\n')

        for line in lines:
            if not line.upper().isupper():
                try:
                    p.price_int = int(line.split('.')[0])
                    p.price_frac = int(line.split('.')[1])
                except:
                    print('***problem with obtaining price of product from string {0}. skipping***'.format(lines))

        if re.search(sale_1, product_text): # EXAMPLE:  "[0-9] + [0-9] GRATIS"
            sale_text = re.search(sale_1, product_text).group().split(' ')
            pay_amount = int(sale_text[0])
            get_amount =  pay_amount + int(sale_text[2])
            unit_price = round(p.get_price() * pay_amount / get_amount, 2)
            p.set_price(unit_price)
            p.sale = 1
        elif re.search(sale_2, product_text): #"[0-9] VOOR [0-9].[0-9]{2}"
            sale_text = re.search(sale_2, product_text).group().split(' ')
            pay_amount = float(sale_text[2])
            get_amount =  int(sale_text[0])
            unit_price = round(pay_amount / get_amount, 2)
            p.set_price(unit_price)
            p.sale = 1
        elif re.search(sale_3, product_text): #"[0-9][0-9]\% KORTING , correct price is already obtained in analyzing lines"
            p.sale = 1
        elif re.search(sale_4, product_text): # "2E HALVE PRIJS"           
            unit_price = round(p.get_price()*0.75, 2)
            p.set_price(unit_price)
            p.sale = 1

        p.title = find_product_title(html_product)
        p.url = find_url(html_product)
        try:
            p.product_id = int([u for u in p.url.split('/') if u.startswith('wi')][0][2::])
        except:
            print('Product is not a single product')
            continue

        try:
            p.id = int(str(p.product_id) + str(insert_date.isocalendar()[0]) + str(insert_date.isocalendar()[1]) + str(insert_date.isocalendar()[2]))
            if p.product_id != -1 and p.product_id not in product_ids:
                db_connection.insert_into_ah_db(p)
                print('Product: {0} inserted into table with price {1},{2}'.format(p.title, p.price_int, p.price_frac))
                inserts += 1
            elif p.product_id != -1 and (int(p.price_int) != all_products[product_ids.index(p.product_id)][1] or int(p.price_frac) != all_products[product_ids.index(p.product_id)][2]):
                old_price_int = all_products[product_ids.index(p.product_id)][1]
                old_price_frac = all_products[product_ids.index(p.product_id)][2]
                db_connection.update_ah_product(p)
                all_products[product_ids.index(p.product_id)][1] = p.price_int
                all_products[product_ids.index(p.product_id)][2] = p.price_frac
                print('Product: {0} already exists but price is updated from {1},{2} to {3},{4}'.format(p.title, old_price_int, old_price_frac, p.price_int, p.price_frac))
                updates += 1
            else:
                db_connection.update_date_ah_modified(p)
                print('Product: {0} already exists in table with same price, record date_modified updated'.format(p.title))
                untouched += 1
        except:
            print('***Could not insert product: {0} with number {1}, skipping it***'.format(p.title, p.id))
            raise
    print('{0} products analyzed, inserts: {1}, updates: {2}, untouched: {3}'.format(i, inserts, updates, untouched))

driver.close()
print("***Data scraping completed. ***")
end_time = datetime.now()
total_time = end_time - start_time
print('Total running time: {}'.format(total_time))