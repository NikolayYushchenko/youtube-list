import time
from datetime import timedelta
from datetime import datetime
import json
import os
import sys
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import asyncio
import Exel_Test as open_exel


class SVSettings:
    DEFAULT_SETTINGS = {
        'username': 'sale@dyvomart.com',
        'password': 'Manager@23',
        'login_url': 'https://umma.io/signin',
        'username_field_css': 'input[formcontrolname="email"]',
        'password_field_css': 'input[formcontrolname="password"]',
        'login_button_css': 'input[type="submit"]',
        'category_url': 'https://umma.io/u-quick, https://umma.io/u-outlet',
        'category_parse_step': 0,
        'start_page': 0,
        'index_cart': 0
    }

    @classmethod
    def save_default_settings_to_file(cls, filename='umasettings.json'):
        with open(filename, 'w', encoding="utf-8") as file:
            json.dump(cls.DEFAULT_SETTINGS, file, ensure_ascii=False, indent=4)

    @classmethod
    def load_settings_from_file(cls, filename='umasettings.json'):
        settings = {}
        if not os.path.exists(filename):
            cls.save_default_settings_to_file(filename)

        if os.path.exists(filename):
            with open(filename, 'r', encoding="utf-8") as file:
                settings = json.load(file)

            for key, value in cls.DEFAULT_SETTINGS.items():
                if key not in settings:
                    settings[key] = value

            with open(filename, 'w') as file:
                json.dump(settings, file, indent=4)

        return settings

class Settings:
    loaded_settings = SVSettings.load_settings_from_file()
    #print(loaded_settings)
    try:
        if(not loaded_settings["category_url"]):
            raise KeyError
    except KeyError:
        print("Invalid value: category_url = \"\" ")
        time.sleep(2)
        sys.exit()

    username = loaded_settings['username']
    password = loaded_settings['password']
    login_url = loaded_settings['login_url']
    username_field_css = loaded_settings['username_field_css']
    password_field_css = loaded_settings['password_field_css']
    login_button_css = loaded_settings['login_button_css']
    category_url = loaded_settings['category_url'].split(', ')
    category_parse_step = loaded_settings['category_parse_step']
    start_page = loaded_settings['start_page']
    index_cart = loaded_settings['index_cart']

    @staticmethod
    def set_options():
        options = Options()
        options.add_argument(
            fr"--user-data-dir={os.path.expandvars('%USERPROFILE%')}\AppData\Local\Google\Chrome\User Data\Default")
        return options

    @staticmethod
    def start_driver():
        driver = webdriver.Chrome(options=Settings.set_options())
        return driver

class ParseURL:
    def __init__(self, target_url):
        self.target_url = target_url
        self.driver = Settings.start_driver()
        self.category_parse_step = Settings.category_parse_step
        self.login()

    def login(self):
        print(f"Список категорій на парсинг: {Settings.category_url}")
        for category_url in Settings.category_url:
            if self.check_authorization():
                print(f"Start page for parsing: {self.check_start_page(category_url)}")
                carts_url = self.parse_container_category(self.check_start_page(category_url), self.category_parse_step)
                print(f"Всього карток: {len(carts_url)-1}. Category: {carts_url[0]}")
                start_time = time.time()
                asyncio.run(self.parse_cart(carts_url))
                end_time = time.time()
                print(f"Parsing time for a card: {str(timedelta(seconds=end_time - start_time)).split('.')[0]} (Hours:Minutes:Seconds)")
            else:
                self.get_target_url(Settings.login_url)

                username_field = self.driver.find_element(By.CSS_SELECTOR, Settings.username_field_css)
                password_field = self.driver.find_element(By.CSS_SELECTOR, Settings.password_field_css)
                login_button = self.driver.find_element(By.CSS_SELECTOR, Settings.login_button_css)

                username_field.send_keys(Settings.username)
                password_field.send_keys(Settings.password)
                login_button.click()
                time.sleep(1)
                print(f"Start page for parsing: {self.check_start_page(category_url)}")
                carts_url = self.parse_container_category(self.check_start_page(category_url), self.category_parse_step)
                print(f"Number of cards: {len(carts_url)-1}. Category: {carts_url[0]}")
                start_time = time.time()
                asyncio.run(self.parse_cart(carts_url))
                end_time = time.time()
                print(f"Parsing time for a card: {str(timedelta(seconds=end_time - start_time)).split('.')[0]} (Hours:Minutes:Seconds)")

    def get_target_url(self, target_url):
        self.driver.get(target_url)
        time.sleep(4)

    def check_authorization(self, home_page=Settings.login_url):
        self.get_target_url(home_page)
        return True if "/home" in self.driver.current_url else False

    def check_start_page(self, category_url):

        if Settings.start_page > 0:
            regex_pattern = r'https://umma\.io/category/\d+\?categoryId=\d+'
            match_result = re.match(regex_pattern, category_url).group(0)
            match category_url:
                case 'https://umma.io/u-quick':
                    start_url = f"https://umma.io/u-quick?page={Settings.start_page}"
                    return start_url
                case 'https://umma.io/u-outlet':
                    start_url = f"https://umma.io/u-outlet?page={Settings.start_page}"
                    return start_url
                case str(match_result):
                    print(match_result)
                    cleaned_url = re.match(r"(https://umma\.io/category/[^?&]+)[?&].*", category_url)
                    start_url = f"{cleaned_url.group(1)}?page={1}"
                    return start_url
                case None:
                    return "Invalid category_url"
        else:
            start_url = category_url
            return start_url

    def parse_container_category(self, category_url, category_parse_step, category_items_link=[]):
        def check_paginator(pagin_code, category_parse_step, category_items_link, current_step=0):
            soup = BeautifulSoup(paginator, 'html.parser')
            current_li = soup.find("li", class_="current")

            if category_parse_step > current_step and category_parse_step != 0:
                current_step = current_step + 1

            if category_parse_step == current_step and category_parse_step != 0:
                print(f"Total steps: {category_parse_step} Current step: {current_step}")
                return

            next_sibling = current_li.find_next_sibling()
            print(f"Pagination Page: {current_li.text}")

            if next_sibling and "next" not in next_sibling.get("class", []):
                if category_parse_step > current_step or category_parse_step == 0:
                    pagination_next = self.driver.find_element(By.CSS_SELECTOR, "div.paging li.current + li")
                    pagination_next.click()
                    time.sleep(2)
                    print(f"Total steps: {category_parse_step} Current step: {current_step}")
                    print(self.driver.current_url)
                    self.parse_container_category(self.driver.current_url, category_parse_step, category_items_link)
            else:
                priv = self.driver.current_url
                pagination_next = self.driver.find_element(By.CSS_SELECTOR, "div.paging li.next")
                pagination_next.click()
                time.sleep(2)
                if(priv == self.driver.current_url):
                    print("Last URL: null")
                else:
                    print(f"Next URL: {self.driver.current_url}")
                    self.parse_container_category(self.driver.current_url, category_parse_step, category_items_link)



        self.get_target_url(category_url)

        app_paging = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "app-paging")))
        paginator = self.driver.execute_script('return arguments[0].innerHTML;', app_paging)
        product_elements = self.driver.find_elements(By.TAG_NAME, 'app-product-single')

        if product_elements[0].get_attribute('data-list') not in category_items_link:
            category_items_link.append(product_elements[0].get_attribute('data-list'))
            if not os.path.exists("category"):
                os.mkdir("category")
            if not os.path.exists("category/" + category_items_link[0]):
                os.mkdir(f"category/{product_elements[0].get_attribute('data-list')}")

        for item in product_elements:
            category_items_link.append(f"https://umma.io/product/{item.get_attribute('data-id')}")

        check_paginator(paginator, category_parse_step, category_items_link)

        return category_items_link

    async def parse_cart(self, cart_link):
        lock = asyncio.Lock()

        async def write_file(file_name, product, lock):
            async with lock:
                await asyncio.sleep(1)
                open_exel.append_dict_to_excel(product, file_name)

        folder_category = cart_link[0]
        cart_list_url = cart_link

        def exist_element(element, css_selector):
            try:
                element = element.find_element(By.CSS_SELECTOR, css_selector)
                #print("Елемент знайдено на сторінці")
                return element.get_attribute("textContent")

            except:
                print(f"Елемент {css_selector} не знайдено на веб-сторінці, тому записано значення: 'empty'")
                return "empty"

        if("category" in cart_list_url[1]):
            tag_name = 'app-product-single'
        else:
            tag_name = 'app-product-detail'

        if(Settings.index_cart !=0 and Settings.index_cart < len(cart_list_url[1:])):
            index_cart = Settings.index_cart
            print(f"Парсинг почато з карточки: {index_cart}. Обсяг карточок cтав: {len(cart_list_url[index_cart+1:])}")
        else:
            index_cart = 0

        for index, url in enumerate(cart_list_url[index_cart+1:]):
            self.get_target_url(url)

            id = re.search(r'/(\d+)$', self.driver.current_url)

            if id:
                id = id.group(1)
                print("Product ID:", id)
                print(f"Оброблюється: {index} картка з {len(cart_list_url[index_cart+1:])}")
            else:
                raise f"Product ID not found in the URL:{self.driver.current_url}"

            try:

                element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, tag_name))
                )
            except:
                raise f"TAG: 'app-product-detail' not found in the URL:{self.driver.current_url}"
                self.driver.quit()

            category = exist_element(element,'.breadcrumb > div')
            image = exist_element(element, 'img[src*="product-image"]')
            brand = exist_element(element, '.wrap-title > div:nth-child(1) > h3:nth-child(1)')
            name = exist_element(element, '.wrap-title > h4:nth-child(2)')

            price = exist_element(element, '.wrap-price_info > span:nth-child(2)')
            discount = exist_element(element, '.wrap-price_info > span:nth-child(3)')
            normal_price = exist_element(element, 'span.ng-star-inserted:nth-child(4)')
            volume = exist_element(element, 'ul.ng-star-inserted > li:nth-child(1) > strong')
            barcode = exist_element(element, 'ul.ng-star-inserted > li:nth-child(2) > strong:nth-child(2)')
            mqq_min = exist_element(element, '.wrap-basic_info > ul:nth-child(2) > li:nth-child(1) > strong:nth-child(2)')
            mqq_max = exist_element(element, '.wrap-basic_info > ul:nth-child(2) > li:nth-child(2) > strong:nth-child(2)')
            country_origin = exist_element(element, '.information > div:nth-child(2) > ul:nth-child(1) > li:nth-child(1) > strong:nth-child(2)')
            u_quick_available = exist_element(element, '.wrap-basic > span:nth-child(1)')

            current_datetime = datetime.now()
            formatted_date = current_datetime.strftime("%d-%m-%Y")
            status = formatted_date

            print(
                    id,
                    category,
                    image,
                    brand,
                    name,
                    price,

                    discount,
                    normal_price,
                    volume,
                    barcode,
                    mqq_min,
                    mqq_max,
                    country_origin,
                    u_quick_available,

                    status
                )

            product = {
                'ID': id,
                'Category': category,
                'Image': image,
                'Brand': brand,
                'Name': name,
                'Price': price,
                'Discount%':  discount if "empty" in discount else str(re.search(r'\d+', discount).group(0)),
                'Normal price(USD)': normal_price if "empty" in normal_price else str(re.search(r'\d+\.\d+', normal_price).group(0)),
                'Volume': volume,
                'Barcode': barcode,
                'MQQ(min)': mqq_min,
                'MQQ(max)': mqq_max,
                'Country of Origin': country_origin,
                'U-Quick available(pcs)': u_quick_available if "empty" in u_quick_available else str(re.search(r'\d+', u_quick_available).group(0)),
                'Status': status
            }

            await write_file('uma_data.xlsx', product, lock)

    def __del__(self):
        self.driver.quit()

if __name__ == "__main__":
    parse = ParseURL(Settings.category_url)
    parse.__del__()
