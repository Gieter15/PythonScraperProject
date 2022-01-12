from selenium import webdriver
import selenium
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time

class Browser:
    #constructor
    def __init__(self, max_tries= 3, headless=False, wait_time = 10) -> None:
        self.max_tries = max_tries
        self.headless=headless
        self.wait_time = wait_time
        self.driver = None
        self.get_driver()


    def get_driver(self):

        
        opts = Options()
        opts.add_argument("--headless") if self.headless else 0
        opts.add_argument("--kiosk-printing")
        opts.add_argument("window-size=1920,1080") 
        driver = webdriver.Firefox(options = opts)
        driver.implicitly_wait(self.wait_time)
        self.driver = driver 

    def get_url(self, url):
        print('Navigating to url: {}'.format(url))
        self.driver.get(url)

    def get_current_url(self):
        return self.driver.current_url

    def close(self):
        return self.driver.close()

    def delete_all_cookies(self):
        self.driver.delete_all_cookies()

    def find_product_url(self, input_product) -> str:
        retry_nr = 0
        while True:
            try:
                url = input_product.find_element(By.TAG_NAME, 'a').get_attribute('href')
            except:
                retry_nr += 1
                if retry_nr < self.max_tries:
                    print('Cant find url, retrying...')
                    continue
                else:
                    print('cannot find url, url is set empty')
                    url = ''
                    break
            break
        return url

    def find_products(self) -> list:
        retry_nr = 0
        while True:
            try:
                products = self.driver.find_elements(By.CLASS_NAME, "product-container")
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

    def find_current_page_number(self):
        retry_nr = 0
        page_number = 0
        while True:
            try:
                current_page_html = self.driver.find_element(By.XPATH, "//button[@class='page selected']")
                page_number = int(current_page_html.text)
            except:
                retry_nr += 1
                if retry_nr < self.max_tries:
                    print('Cant find current_page_number, retrying...')
                    continue
                else:
                    print('Maximum amount of tries reached for next_page_button, aborting...')
                    break
            break
        return page_number

    def find_number_of_pages(self):
        retry_nr = 0
        page_number = 0
        while True:
            try:
                html_pages = self.driver.find_elements(By.XPATH, "//button[@class='page']")
                last_html = html_pages[-1]
                page_number = int(last_html.text)
            except:
                retry_nr += 1
                if retry_nr < self.max_tries:
                    print('Cant find number_of_pages, retrying...')
                    continue
                else:
                    print('Maximum amount of tries reached for number_of_pages, aborting...')
                    break
            break
        return page_number

    def find_next_page_button(self):
        retry_nr = 0
        while True:
            try:
                nav_buttons = self.driver.find_elements(By.XPATH, "//button[@class='jum-button pagination-button secondary']")
                next_page_button = nav_buttons[-1]
            except:
                retry_nr += 1
                if retry_nr < self.max_tries:
                    print('Cant find next_page_button, retrying...')
                    continue
                else:
                    print('Maximum amount of tries reached for next_page_button, aborting...')
                    break
            break
        return next_page_button

    def find_cookies_button(self):
        retry_nr = 0
        while True:
            try:
                cookies_button = self.driver.find_element(By.ID, 'onetrust-accept-btn-handler')
            except:
                if retry_nr < self.max_tries:
                    print('Cant find next_page_button, retrying...')
                    continue
                else:
                    print('Maximum amount of tries reached for next_page_button, aborting...')
                    break
            break
        return cookies_button

    def click_cookies_button_dirk(self):
        retry_nr = 0
        while True:
            try:
                cookies_button = self.driver.find_element(By.CLASS_NAME, 'large-banner__button')
                cookies_button.click()
            except:
                if retry_nr < self.max_tries:
                    print('Cant find next_page_button, retrying...')
                    continue
                else:
                    print('Maximum amount of tries reached for next_page_button, aborting...')
                    break
            break
        return cookies_button

    def click_warning_message(self):
        actions = ActionChains(self.driver)
        try:
            warning_message = self.driver.find_element(By.XPATH, "//button[@class='jum-button close tertiary icon']")
            actions.move_to_element(warning_message).click().perform()
        except:
            print("No warning message is found")
        # try:
        #     warning_box = self.driver.find_element(By.XPATH, "//div[@class='notification compact']")
        #     actions.move_to_element(warning_box).click().perform()
        #     warning_message = self.driver.find_element(By.XPATH,"//button[@class='jum-button close tertiary icon']")
        #     actions.move_to_element(warning_message).click().perform()
        # except:
        #     print("No warning message is found")
        try:
            notification = self.driver.find_element(By.CLASS_NAME, 'notification')
            notification.click()
            time.sleep(0.5)
            warning_message = self.driver.find_element(By.XPATH,"//button[@class='jum-button close tertiary icon']")
            warning_message.click()
            time.sleep(0.5)
        except:

            print("No warning message is found")
        return