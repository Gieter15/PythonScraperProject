from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

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
        self.driver.get(url)

    def get_current_url(self):
        return self.driver.current_url

    def close(self):
        return self.driver.close()

    def delete_all_cookies(self):
        self.driver.delete_all_cookies()

    def find_product_url(self, input_product):
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
                    print('cannot find url, url is set empty')
                    url = ''
                    break
            break
        return url

    def find_products(self):
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
                numbers_container = self.driver.find_element(By.XPATH, "//ul[@class='pagination unstyled d-block d-m-none']")
                numbers = numbers_container.find_elements_by_tag_name('li')
                for nr in numbers:
                    if 'font-weight-bold' in nr.get_attribute('class'):
                        page_number = int(nr.get_attribute('innerHTML'))
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
                numbers_container = self.driver.find_element(By.XPATH, "//ul[@class='pagination unstyled d-block d-m-none']")
                numbers = numbers_container.find_elements_by_tag_name('li')
                page_number = int(numbers[-1].get_attribute('innerHTML'))
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
                nav_buttons = self.driver.find_elements(By.XPATH, "//button[@class='jum-button pagination-buttons secondary']")
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
            warning_message = self.driver.find_element(By.XPATH,"//button[@class='jum-button close tertiary icon']")
            warning_message.click()
        except:

            print("No warning message is found")