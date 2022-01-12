from objects.product import Product
from os import close, path, mkdir
from objects.productsDB import ProductsDB
from objects.browser import Browser
from selenium.webdriver.common.by import By
import time
from datetime import datetime, date
import csv

class DirkProductsScraper():
#TODO: add product category. Add amount of product, now there will be unclear titles

    def __init__(self, headless) -> None:
        self.base_url = 'https://www.dirk.nl/boodschappen'
        db_folder = 'databases'
        db_name = 'test.db'
        db_table_name = 'DIRK_PRODUCTS'
        csv_folder = 'csv_files'
        csv_file_prefix = 'dirk_products'
        self.clean_table = False
        self.max_tries = 3
        self.headless = headless
        

        start_time = datetime.now()

        browser = Browser(headless=self.headless)
        browser.get_url(self.base_url)
        driver = browser.driver

        browser.click_cookies_button_dirk()

        urls = self.find_product_category_links(driver)
        all_products = []   
        for i, url in enumerate(urls):
            browser.get_url(url)
            time.sleep(1)
            product_category = url.split('/')[-1]
            print('({}/{}) Product category: {}'.format(i+1, len(urls), product_category))

            sub_urls = self.find_product_category_links(driver)

            for j, sub_url in enumerate(sub_urls):
                browser.get_url(sub_url)
                time.sleep(1)
                product_sub_category = sub_url.split('/')[-1]
                print('({}/{}) Product sub category: {}'.format(j+1, len(sub_urls), product_sub_category))
                time.sleep(1)
                html_products = self.find_products(driver)
                self.updates = 0
                self.inserts = 0
                self.untouched = 0
                print('Found {} products, analyzing...'.format(len(html_products)))
                for i, html_product in enumerate(html_products):
                    product = self.analyze_html_product(html_product)
                    if product and product.product_id not in [p.product_id for p in all_products]:
                        all_products.append(product)
                        print('({}/{})  €{},{}\t{}.'.format(i+1, len(html_products), product.price_int, product.price_frac,product.title))
                    elif product and product.product_id in [p.product_id for p in all_products]:
                        print('({}/{})  product {} already in list'.format(i+1, len(html_products), product.title))
                    else:
                        print('Error finding {} product from {}'.format(i, html_product.text))
        
        self.store_products_as_csv(all_products, csv_folder, csv_file_prefix)
        
        print('{0} products analyzed, inserts: {1}, updates: {2}, untouched: {3}'.format(i+1, self.inserts, self.updates, self.untouched))

        driver.close()
        print("***Data scraping completed. ***")
        end_time = datetime.now()
        total_time = end_time - start_time
        print('Total running time: {}'.format(total_time))


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
                      

    def analyze_html_product(self, html_product):
        
        if not 'ACTIE' in html_product.text:
            p = Product()
            price = self.get_current_price(html_product)
            p.set_price(price)
            p.title = self.find_product_title(html_product)
            p.url = self.find_url(html_product)
            p.product_id = p.url.split('/')[-1]

            # has_old_price = html_product.find_elements(By.CLASS_NAME, 'product-card__price__old')

            return p

        return None

    def find_product_title(self, input_product):
        retry_nr = 0
        prd_title = ''
        while True:
            try:
                prd_title = input_product.find_element(By.CLASS_NAME, 'product-card__name').text
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

    def find_url(self, input_product):
        retry_nr = 0
        while True:
            try:
                url = input_product.find_element(By.CLASS_NAME, 'product-card__name').get_attribute('href')
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

    def get_current_price(self, html_product) -> str:
        retry_nr = 0
        price_int = -1
        price_frac = -1
        while True:
            try:
                price_int = html_product.find_element(By.CLASS_NAME, "product-card__price__euros").text
                price_frac = html_product.find_element(By.CLASS_NAME, "product-card__price__cents").text
            except:
                retry_nr += 1
                if retry_nr < self.max_tries:
                    print('Cant find price, retrying...')
                    continue
                else:
                    print('Maximum amount of tries reached for price, aborting...')
                    print(html_product.text)
                    break
            break
        return price_int + price_frac

    def find_products(self, input_driver) -> list:
        retry_nr = 0
        products = []
        while True:
            try:
                container = input_driver.find_element(By.CLASS_NAME, "products-wrapper")
                products = container.find_elements(By.CLASS_NAME, "product-card")
            except:
                retry_nr += 1
                time.sleep(1)
                if retry_nr < self.max_tries:
                    print('Cant find products, retrying...')
                    continue
                else:
                    print('Maximum amount of tries reached for products, aborting...')
                    break
            break
        return products

    def find_product_category_links(self, input_driver):
        retry_nr = 0
        urls = []
        while True:
            try:
                category_container = input_driver.find_element(By.CLASS_NAME, "product-category-header__nav")
                categories = category_container.find_elements(By.TAG_NAME, "li")
                for category in categories:
                    a = category.find_element(By.TAG_NAME, "a")
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


if __name__ == '__main__':
    DirkProductsScraper(headless=True)