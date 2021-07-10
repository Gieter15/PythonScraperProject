from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import re
from product import Product
from productsDB import ProductsDB
from browser import Browser

#TODO: make this into a class for extra fancy points?
base_url = 'https://www.jumbo.com/producten/'
#base_url = 'https://www.jumbo.com/producten/?offSet=2400&pageSize=25'
db_folder = 'databases'
db_name = 'products.db'
table_name = 'JUMBO_PRODUCTS'
headless = True
clean_table = False

sale_1 = "[0-9] voor [0-9],[0-9]{2} euro"
start_time = datetime.now()
develop_environment = True

db_connection = ProductsDB(db_folder, db_name, table_name)
db_connection.clean_table() if clean_table else 0

all_products = db_connection.get_all_products()
product_ids = db_connection.get_all_product_ids()

db_connection.create_jumbo_table()

browser = Browser(headless=headless)
browser.get_url(base_url)

db_connection.clean_table if clean_table else 0
all_products = db_connection.get_all_products()
product_ids = db_connection.get_all_product_ids()

db_connection.create_jumbo_table()

cookies_button = browser.find_cookies_button()
cookies_button.click()

browser.click_warning_message()

next_page_button = browser.find_next_page_button()
number_of_pages = browser.find_number_of_pages()
print('number_of_pages: {}'.format(number_of_pages))

page_number = 0
last_page = False
while not last_page:
    page_number = browser.find_current_page_number()
    last_page = page_number == number_of_pages
    print("***page number {0} ***".format(page_number))

    products = browser.find_products()

    for html_product in products:

        p = Product()

        try:
            product_text = html_product.text
        except:
            product_text = ''
            print('Problem loading product on page {0}'.format(page_number))
        
        lines = product_text.split('\n')
        p.set_title(lines[0])
        insert_date = datetime.now()
        if 'Binnenkort' in product_text:
            print('{} will soon be available again'.format(p.title))
            continue
        elif 'korting' in product_text:
            try:
                for i, line in enumerate(lines):
                    if not line.upper().isupper() and ',' not in line: #Check if no characters in string, check for the comma in case of 15,30
                        p.price_int = int(line)
                        p.price_frac = int(lines[i+1])
                        break
                p.sale = 1
                p.url = browser.find_product_url(html_product)
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
            p.url = browser.find_product_url(html_product)
            p.product_id = p.url.split('/')[-1]

        elif 'gratis' in product_text:
            try:
                p.price_int = int(lines[2])
                p.price_frac = int(lines[3])
                p.sale = 1
                p.url = browser.find_product_url(html_product)
                p.product_id = p.url.split('/')[-1]
            except:
                p.sale = 1
                print('Discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(page_number, p.title))

        else:
            try:
                p.price_int = int(lines[2])
                p.price_frac = int(lines[3])
                p.url = browser.find_product_url(html_product)
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
    while page_number == browser.find_current_page_number() and page_number != last_page:
        next_page_button.click()
        time.sleep(3)
    
    if page_number % 100 == 0: # delete all cookies every 100 pages
        current_url = browser.get_current_url()
        print(current_url)
        browser.delete_all_cookies()
        print('*** deleting all cookies***')
        browser.get_url(current_url)
        time.sleep(3)
        cookies_button = browser.find_cookies_button()
        cookies_button.click()
        next_page_button = browser.find_next_page_button()
        warning_message = browser.click_warning_message()

browser.close()
print("***Data scraping completed. {0} pages scanned with {1} products.".format(i, i*25))
end_time = datetime.now()
total_time = end_time - start_time
print('Total running time: {}'.format(total_time))


    