from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, date
from os import close, path, mkdir
import time
import csv
import re
from objects.product import Product
from objects.productsDB import ProductsDB
from objects.browser import Browser
from selenium.webdriver.common.action_chains import ActionChains


class JumboProductsScraper():

    def __init__(self, headless=False) -> None:

        start_time = datetime.now()

        base_url = 'https://www.jumbo.com/producten/'
        # base_url = 'https://www.jumbo.com/producten/?offSet=2400&pageSize=25'
        db_folder = 'databases'
        db_name = 'products.db'
        db_table_name = 'JUMBO_PRODUCTS'

        self.clean_table = False

        start_time = datetime.now()

        self.browser = Browser(headless=headless)
        self.browser.get_url(base_url)

        cookies_button = self.browser.find_cookies_button()
        cookies_button.click()

        self.browser.click_warning_message()

        next_page_button = self.browser.find_next_page_button()
        number_of_pages = self.browser.find_number_of_pages()
        print('number_of_pages: {}'.format(number_of_pages))

        page_products = []

        page_number = 0
        last_page = False
        while not last_page:
            page_number = self.browser.find_current_page_number()
            last_page = page_number == number_of_pages
            print(
                "***page number {0}/{1} ***".format(page_number, number_of_pages))

            last_product = page_products[-1] if page_products else None
            page_products = self.browser.find_products()
            all_products = []

            while last_product and len(page_products) > 0 and last_product == page_products[-1]:
                page_products = self.browser.find_products()
                print("products not properly refresed, retrying...")
                time.sleep(3)

            for i, html_product in enumerate(page_products):

                product = self.analyze_html_product(html_product, page_number)

                if product:
                    all_products.append(product)
                    print('({}/{})\t€{},{}\t{}.'.format(i+1, len(page_products),
                          product.price_int, product.price_frac, product.title))
                elif product == None:
                    print('Product will soon become available again.')
                else:
                    print('Error finding {} product from {}'.format(
                        i, html_product.text))

            while page_number == self.browser.find_current_page_number() and page_number != last_page:
                actions = ActionChains(self.browser.driver)
                # actions.click(next_page_button).perform()
                next_page_button.click()
                time.sleep(2)

            if page_number % 100 == 0:  # delete all cookies every 100 pages
                current_url = self.browser.get_current_url()
                print(current_url)
                self.browser.delete_all_cookies()
                print('*** deleting all cookies***')
                self.browser.get_url(current_url)
                time.sleep(3)
                cookies_button = self.browser.find_cookies_button()
                cookies_button.click()
                next_page_button = self.browser.find_next_page_button()
                self.browser.click_warning_message()

            self.store_products_in_database(
                all_products, db_folder, db_name, db_table_name)

        self.browser.close()
        print(
            "***Data scraping completed. {0} pages scanned with {1} products.".format(i, i*25))
        end_time = datetime.now()
        total_time = end_time - start_time
        print('Total running time: {}'.format(total_time))

    def analyze_html_product(self, html_product, page_number) -> Product:

        sale_1 = "[0-9] voor [0-9],[0-9]{2} euro"
        p = Product()
        try:
            product_text = html_product.text
        except:
            product_text = ''
            print('Problem loading product on page {0}'.format(page_number))

        lines = product_text.split('\n')
        p.set_title(lines[0])
        if 'Binnenkort' in product_text:
            # print('{} will soon be available again'.format(p.title))
            return None
        elif 'korting' in product_text:
            try:
                for i, line in enumerate(lines):
                    # Check if no characters in string, check for the comma in case of 15,30
                    if not line.upper().isupper() and ',' not in line:
                        p.price_int = int(line)
                        p.price_frac = int(lines[i+1])
                        break
                p.sale = 1
                p.url = self.browser.find_product_url(html_product)
                p.product_id = p.url.split('/')[-1].split('-')[-1]
            except:
                p.sale = 1
                print('Discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(
                    page_number, p.title))

        # "[0-9] voor [0-9],[0-9]{2} euro"
        elif re.search(sale_1, product_text):
            sale_text = re.search(sale_1, product_text).group().split(' ')
            sale_price = sale_text[-2]
            p.set_price(sale_price.replace(',', '.'))
            sale_quantity = int(sale_text[0])
            sale_unit_price = p.get_price()/sale_quantity

            p.set_price(sale_unit_price)
            p.sale = 1
            p.url = self.browser.find_product_url(html_product)
            p.product_id = p.url.split('/')[-1].split('-')[-1]

        elif 'gratis' in product_text:
            try:
                for i, line in enumerate(lines):
                    # Check if no characters in string, check for the comma in case of 15,30
                    if not line.upper().isupper() and ',' not in line:
                        p.price_int = int(line)
                        p.price_frac = int(lines[i+1])
                        break
                p.sale = 1
                p.url = self.browser.find_product_url(html_product)
                p.product_id = p.url.split('/')[-1].split('-')[-1]
            except:
                p.sale = 1
                print('Discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(
                    page_number, p.title))

        else:
            try:
                for i, line in enumerate(lines):
                    # Check if no characters in string, check for the comma in case of 15,30
                    if not line.upper().isupper() and ',' not in line:
                        p.price_int = int(line)
                        p.price_frac = int(lines[i+1])
                        break
                p.url = self.browser.find_product_url(html_product)
                p.product_id = p.url.split('/')[-1].split('-')[-1]
            except:
                print('No known discount found, but int parsing unsuccesfull on page {0} for product: {1}'.format(
                    page_number, p.title))

        if p.product_id:
            p.id = p.product_id + str(datetime.now().isocalendar()[0]) + str(
                datetime.now().isocalendar()[1]) + str(datetime.now().isocalendar()[2])
        return p

    def store_products_in_database(self, products: list[Product], db_folder: str, db_name: str, db_table_name: str) -> None:

        db_connection = ProductsDB(db_folder, db_name, db_table_name)
        db_connection.clean_table() if self.clean_table else 0

        all_products = db_connection.get_all_products()
        product_ids = db_connection.get_all_product_ids()

        db_connection.create_jumbo_table()

        db_connection.clean_table if self.clean_table else 0
        all_products = db_connection.get_all_products()
        product_ids = db_connection.get_all_product_ids()

        db_connection.create_jumbo_table()

        inserts = 0
        updates = 0
        untouched = 0

        print('Storing products in database {}, table {}.'.format(
            db_name, db_table_name))

        for p in products:
            try:
                if p.price_int == -1 or p.price_frac == -1:
                    continue
                elif p.product_id not in product_ids and p.url != '':
                    db_connection.insert_into_jumbo_db(p)
                    inserts += 1
                elif p.product_id != '-1' and p.url != '' and (p.price_int != all_products[product_ids.index(p.product_id)][1] or p.price_frac != all_products[product_ids.index(p.product_id)][2]):
                    old_price_int = all_products[product_ids.index(
                        p.product_id)][1]
                    old_price_frac = all_products[product_ids.index(
                        p.product_id)][2]
                    db_connection.update_jumbo_product(p)
                    all_products[product_ids.index(
                        p.product_id)][1] = p.price_int
                    all_products[product_ids.index(
                        p.product_id)][2] = p.price_frac
                    updates += 1
                elif p.url != '' and p.product_id != '-1':
                    db_connection.update_date_jumbo_modified(p)
                    untouched += 1
                else:
                    # print("***********Problem with product {0} on page {1}, product text = {2} price = {3},{4}".format( p.title, page_number, product_text, p.price_int, p.price_frac))
                    # print(html_product.get_attribute('outerHTML'))
                    # print('page number = {0}'.format(page_number))
                    # print('found page number = {0}'.format(browser.find_current_page_number()))
                    pass

            except:
                print(
                    '***Could not insert product: {0} with number {1}, skipping it***'.format(p.title, p.id))
                raise

        print('{0} products analyzed, inserts: {1}, updates: {2}, untouched: {3}'.format(
            len(products), inserts, updates, untouched))
        db_connection.end_db_connection()
        return

    def store_products_as_csv(self, products: list[Product], file_prefix: str, folder: str):
        file_name = file_prefix + '_' + \
            str(date.today().strftime("%Y%m%d")) + '.csv'

        mkdir(folder) if not path.exists(folder) else None

        with open(path.join(folder, file_name), 'a', newline='') as f:
            for p in products:
                csv_writer = csv.writer(f, delimiter=',')
                csv_writer.writerow(
                    [p.product_id, p.title, p.price_int, p.price_frac, p.url])
                # print('Product: {0} inserted into table with price {1},{2}'.format(p.title, p.price_int, p.price_frac))
            return


if __name__ == '__main__':
    JumboProductsScraper(headless=False)
