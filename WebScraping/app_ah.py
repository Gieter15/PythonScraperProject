from logging import error
from os import close, path, mkdir
from selenium.webdriver.firefox.options import Options
from datetime import datetime, date
import time
from objects.product import Product
from objects.productsDB import ProductsDB
from objects.browser import Browser
import re
import csv


class AhProductsScraper():
#TODO: add product category. Add amount of product, now there will be unclear titles

    def __init__(self, headless) -> None:
        #api_url = https://www.ah.nl/features/api/mega-menu/products
        self.base_url = 'https://www.ah.nl/producten'
        db_folder = 'databases'
        db_name = 'products.db'
        db_table_name = 'AH_PRODUCTS'
        csv_folder = 'csv_files'
        csv_file_prefix = 'ah_products'
        self.clean_table = False
        self.max_tries = 2
        self.headless = headless
        
        start_time = datetime.now()

        browser = Browser(headless=self.headless)
        browser.get_url(self.base_url)
        driver = browser.driver

        cookies_button = self.find_cookies_button(driver)
        cookies_button.click()

        urls = self.find_product_category_links(driver)

        for url in urls:
            browser.get_url(url + '?page=30')
            time.sleep(1)
            product_category = url.split('/')[-1]
            print('Product category: {}'.format(product_category))

            try:
                popup_message = driver.find_element_by_xpath("//button[@class='popover_closeButton__2FHcJ']")
                popup_message.click()
            except:
                print("No popup message is found")

            html_products = self.find_products(driver)
            self.updates = 0
            self.inserts = 0
            self.untouched = 0
            all_products = []
            print('Found {} products, analyzing...'.format(len(html_products)))
            for i, html_product in enumerate(html_products):
                product = self.analyze_html_product(html_product)
                if product:
                    all_products.append(product)
                    print('({}/{})\t€{},{}\t{}.'.format(i, len(html_products), product.price_int, product.price_frac,product.title))
                else:
                    print('Error finding {} product from {}'.format(i, html_product.text))

            self.store_products_in_database(all_products, db_folder, db_name, db_table_name)
            self.store_products_as_csv(all_products, csv_folder, csv_file_prefix)

            print('{0} products analyzed, inserts: {1}, updates: {2}, untouched: {3}'.format(i+1, self.inserts, self.updates, self.untouched))

        driver.close()
        print("***Data scraping completed. ***")
        end_time = datetime.now()
        total_time = end_time - start_time
        print('Total running time: {}'.format(total_time))


    def analyze_html_product(self, html_product):
        p = Product()
        sale_1 = "[0-9] \+ [0-9] GRATIS"
        sale_2 = "[0-9] VOOR [0-9].[0-9]{2}"
        sale_3 = "[0-9][0-9]\% KORTING"
        sale_4 = "2E HALVE PRIJS"

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

        p.title = self.find_product_title(html_product)
        p.url = self.find_url(html_product)
        try:
            p.product_id = int([u for u in p.url.split('/') if u.startswith('wi')][0][2::])
        except:
            print('Product is not a single product')
            return None

        return p

    def store_products_in_database(self, products: list[Product], db_folder, db_name, db_table_name):
        db_connection = ProductsDB(db_folder, db_name, db_table_name)

        db_connection.clean_table() if self.clean_table else 0
        db_connection.create_ah_table()

        all_products = db_connection.get_all_products()
        product_ids = db_connection.get_all_product_ids()

        print('Storing products in database {}, table {}.'.format(db_name, db_table_name))
        insert_date = datetime.now()
        for p in products:
            try:
                p.id = int(str(p.product_id) + str(insert_date.isocalendar()[0]) + str(insert_date.isocalendar()[1]) + str(insert_date.isocalendar()[2]))
                if p.product_id != -1 and p.product_id not in product_ids:
                    db_connection.insert_into_ah_db(p)
                    # print('Product: {0} inserted into table with price {1},{2}'.format(p.title, p.price_int, p.price_frac))
                    self.inserts += 1
                elif p.product_id != -1 and (int(p.price_int) != all_products[product_ids.index(p.product_id)][1] or int(p.price_frac) != all_products[product_ids.index(p.product_id)][2]):
                    old_price_int = all_products[product_ids.index(p.product_id)][1]
                    old_price_frac = all_products[product_ids.index(p.product_id)][2]
                    db_connection.update_ah_product(p)
                    all_products[product_ids.index(p.product_id)][1] = p.price_int
                    all_products[product_ids.index(p.product_id)][2] = p.price_frac
                    # print('Product: {0} already exists but price is updated from {1},{2} to {3},{4}'.format(p.title, old_price_int, old_price_frac, p.price_int, p.price_frac))
                    self.updates += 1
                else:
                    db_connection.update_date_ah_modified(p)
                    # print('Product: {0} already exists in table with same price, record date_modified updated'.format(p.title))
                    self.untouched += 1
            except:
                print('***Could not insert product: {0} with number {1}, skipping it***'.format(p.title, p.id))
                raise

    def store_products_as_csv(self, products: list[Product], file_prefix: str, folder: str):
        file_name = file_prefix + '_' + str(date.today().strftime("%Y%m%d")) + '.csv'

        mkdir(folder) if not path.exists(folder) else None

        with open(path.join(folder, file_name), 'a', newline='') as f:
            for p in products:
                csv_writer = csv.writer(f, delimiter=',')
                csv_writer.writerow([p.product_id, p.title, p.price_int, p.price_frac, p.url])
                # print('Product: {0} inserted into table with price {1},{2}'.format(p.title, p.price_int, p.price_frac))
            return
            
    def find_product_category_links(self, input_driver):
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
                if retry_nr < self.max_tries:
                    print('cannot find categories, retrying...')
                    continue
                else:
                    print('cannot find categories, empty list is returned')
                    break
            break
        urls = list(set(urls))
        return urls

    def find_cookies_button(self, input_driver):
        retry_nr = 0
        while True:
            try:
                cookies_button = input_driver.find_element_by_id('accept-cookies')
            except:
                if retry_nr < self.max_tries:
                    print('Cant find cookies button, retrying...')
                    continue
                else:
                    print('Maximum amount of tries reached for next_page_button, aborting...')
                    break
            break
        return cookies_button

    def find_products(self, input_driver):
        retry_nr = 0
        while True:
            try:
                container = input_driver.find_element_by_class_name("search-lane-wrapper")
                products = container.find_elements_by_tag_name("article")
            except:
                retry_nr += 1
                if retry_nr < self.max_tries:
                    print('Cant find products, retrying...')
                    continue
                else:
                    print('Maximum amount of tries reached for products, aborting...')
                    break
            break
        return products

    def find_url(self, input_product):
        retry_nr = 0
        while True:
            try:
                url = input_product.find_element_by_tag_name('a').get_attribute('href')
            except:
                retry_nr += 1
                if retry_nr < self.max_tries:
                    print('Cant find url, retrying...')
                    continue
                else:
                    print('cannot find url, dummy url is used')
                    url = 'cant_find_url_\n0000XX'
                    break
            break
        return url

    def find_product_title(self, input_product):
        retry_nr = 0
        prd_title = ''
        while True:
            try:
                prd_title = input_product.find_element_by_tag_name('a').get_attribute('title')
            except:
                retry_nr += 1
                if retry_nr < self.max_tries:
                    print('Cant find product title, retrying...')
                    continue
                else:
                    print('cannot find product title, dummy title is used')
                    break
            break
        return prd_title


if __name__ == '__main__':
    AhProductsScraper(headless=True)