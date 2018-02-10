from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import time


def main():
    game = Game()
    quit = False
    while not quit:
        command = input("Command: ")
        command = command.upper()
        if command == "QUIT":
            quit = True
        elif command == "HELP":
            print("Commands:")
            print("help: show list of commands")
            print("cookies: show how many cookies are in the bank")
            print("buy: purchase a product")
            print("autobuy: purchase the most efficient product")
            print("start: start clicking the cookie")
            print("stop: stop clicking the cookie")
            print("load: load saved game")
            print("save: save game to file")
            print("click: click the cookie")

        elif command == "COOKIES":
            print("There are " + str(game.get_cookies()) + " cookies in the bank.")

        elif command == "BUY":
            product = input("Product to buy: ")
            game.buy_product(product)

        elif command == "CLICK":
            clicks = input("Number of clicks: ")
            clicks = int(clicks)
            game.click_cookie(clicks)

        elif command == "LOAD":
            game.import_save()
            print("Game loaded.")

        elif command == "SAVE":
            game.export_save()
            print("Game saved.")

        else:
            print("Command not recognized. Type \"help\" for a list of commands.")
    game.close()

def main2():
    game = Game()
    game.import_save()
    quit = False
    next_product = None
    while not quit:
        time.sleep(0.02)
        game.click_cookie()
        if game.buy_upgrade():
            next_product = None
        # next_product = [name, replenish time, price]
        if not next_product:
            next_product = game.get_next_product()
            if next_product:
                print("Next product: " + next_product[0])
        elif next_product[2] < game.get_cookies():
            game.buy_product(next_product[0])
            next_product = None
            game.export_save()


class Game():

    # starts a fresh game of cookie clicker
    def __init__(self):
        self.browser = webdriver.Chrome()
        self.browser.get('http://orteil.dashnet.org/cookieclicker/')
        # wait for website to load
        while not ("Cookie Clicker" in self.browser.title):
            time.sleep(0.1)
        time.sleep(1)
        self.cookie = self.browser.find_element_by_id("bigCookie")
        self.cookies = 0
        self.prefsButton = self.browser.find_element_by_id("prefsButton")

        # Product entries are stored in a dictionary as so:
        # {productTitle:[WebElement, numberOfProducts, costToBuyProduct, cps]}
        self.products = {}

    # clicks the cookie
    # optional: tell it how many times to click
    def click_cookie(self, clicks=1):
        for i in range(0,clicks):
            self.cookie.click()
            self.cookies += 1

    # updates and returns the stored number of cookies in the bank
    def get_cookies(self):
        cookie_html = self.browser.find_element_by_id("cookies").get_attribute("innerHTML")
        try:
            cookies = cookie_html.split("<br>")[0]
            self.cookies = int_string(cookies)
        except ValueError:
            cookies = cookie_html.split(" cookie")[0]
            self.cookies = int_string(cookies)
        return self.cookies

    # TODO
    def get_formatted_cookies(self):
        pass

    # exports game to save.txt file
    def export_save(self):
        # open the options window
        self.prefsButton.click()
        time.sleep(0.5)  # delay because slow internet

        # locate and click the export save button
        section = self.browser.find_element_by_id("sectionMiddle")
        menu = section.find_element_by_id("menu")
        subsection = menu.find_element_by_class_name("subsection")
        listings = subsection.find_elements_by_class_name("listing")
        save_buttons = listings[1]
        buttons = save_buttons.find_elements_by_class_name("option")
        button = buttons[0]
        button.click()

        # save the save code
        text = self.browser.find_element_by_id("textareaPrompt").get_attribute("innerHTML")
        save_file = open("save.txt", "w")
        save_file.write(text)
        save_file.close()

        # close the dialog box
        prompt_div = self.browser.find_element_by_id("prompt")
        close_button = prompt_div.find_element_by_class_name("close")
        close_button.click()

        # close the options window
        self.prefsButton.click()
        time.sleep(0.5)  # delay because slow internet

    # imports game from save.txt file
    def import_save(self):
        # open the options window
        self.prefsButton.click()
        time.sleep(0.5)  # delay because slow internet

        # locate and click the import save button
        section = self.browser.find_element_by_id("sectionMiddle")
        menu = section.find_element_by_id("menu")
        subsection = menu.find_element_by_class_name("subsection")
        listings = subsection.find_elements_by_class_name("listing")
        save_buttons = listings[1]
        buttons = save_buttons.find_elements_by_class_name("option")
        button = buttons[1]
        button.click()

        # grab save text
        save_file = open("save.txt", "r")
        text = save_file.read()
        if text == "":
            print("No save file detected.")
        save_file.close()

        # insert text into dialog box
        prompt_div = self.browser.find_element_by_id("promptContent")
        blocks = prompt_div.find_elements_by_class_name("block")
        block = blocks[1]
        text_area = block.find_element_by_id("textareaPrompt")
        text_area.send_keys(text)

        # load code and close dialog box
        optionBox = prompt_div.find_element_by_class_name("optionBox")
        load_button = optionBox.find_element_by_id("promptOption0")
        load_button.click()

        # close the options window
        self.prefsButton.click()
        time.sleep(0.5)  # delay because slow internet

        # update products and cookies
        self.refresh_products()
        self.get_cookies()

    # returns the unlocked products with their price and number owned in dictionary format
    def get_products(self):
        return self.products

    # buys a product and updates its info
    def buy_product(self, product):
        if product in self.products:
            self.products[product][0].click()
            self.products[product][1] += 1
            content = self.products[product][0].find_element_by_class_name("content")
            html = content.get_attribute("innerHTML")
            html = html.split("</")
            price = html[3].split(">")[2]
            price = int_string(price)
            self.products[product][2] = price
            print("1 " + product + " purchased.")
        else:
            print("That product either doesn't exist or hasn't been unlocked yet.")

    # finds the product that will pay for itself in the least amount of time
    # returns [nextProduct, priceofproduct]
    def get_next_product(self):
        # {productTitle:[WebElement, numberOfProducts, costToBuyProduct, cps]}
        next_product = [None, None, None]  # [name, replenish time, price]
        mystery_product = [None, None, None]
        for product in self.products:
            if self.products[product][3] > 0:  # if the product is producing
                replenish_time = self.products[product][2] // self.products[product][3]
                if not next_product[0] or replenish_time < next_product[1]:
                    next_product = [product,replenish_time,self.products[product][2]]
            else:
                if mystery_product[0]:
                    if self.products[product][2] < mystery_product[2]:
                        mystery_product = [product, None, self.products[product][2]]
                else:
                    mystery_product = [product, None, self.products[product][2]]

        if next_product[0] and mystery_product[0]:
            if mystery_product[2] < next_product[2]:
                next_product = mystery_product
        elif mystery_product[0]:
            next_product = mystery_product
        else:
            next_product = None

        return next_product

    # updates product list
    # {productTitle:[WebElement, numberOfProducts, costToBuyProduct, cps]}
    def refresh_products(self):
        section = self.browser.find_element_by_id("sectionRight")
        subsection = section.find_element_by_id("products")
        # lists only products that are are either currently or were previously affordable
        products = subsection.find_elements_by_css_selector(".product.unlocked.enabled")
        products += subsection.find_elements_by_css_selector(".product.unlocked.disabled")
        products_list = {}
        for product in products:
            # parse the name, price and quantity of the product
            content = product.find_element_by_class_name("content")
            html = content.get_attribute("innerHTML")
            html = html.split("</")
            name = html[1].split(">")[2]
            price = html[3].split(">")[2]
            price = int_string(price)
            quantity = 0
            cookies_per_second = 0
            quantitylist = html[4].split(">")
            if quantitylist[2] != "":
                quantity = quantitylist[2]
                quantity = int_string(quantity)

            if quantity:
                # hover over the product
                hover = ActionChains(self.browser).move_to_element(product)
                hover.perform()
                time.sleep(0.4)

                data = self.browser.find_element_by_class_name("data")
                text = data.get_attribute("innerText")
                text_list = text.split(" cookie")
                text_list = text_list[0].split("produces ")
                cookies_per_second = text_list[len(text_list) - 1]
                cookies_per_second = int_string(cookies_per_second)
                cookies_per_second = int(cookies_per_second)

            # update products
            self.products[name] = [product, quantity, price, cookies_per_second]

    # closes browser
    def close(self):
        self.browser.close()

    # TODO buys the next upgrade and refreshes the products
    def buy_upgrade(self):
        success = False
        try:
            crate = self.browser.find_element_by_css_selector(".crate.upgrade.enabled")
            crate.click()
            print("Crate purchased.")
            self.refresh_products()
            success = True
        except:
            pass
        return success


# converts a string in format "100", "1,000" or "1 million" to int
def int_string(string):
    powers = {
        "million": 6,
        "billion": 9,
        "trillion": 12,
        "quadrillion": 15,
        "quintillion": 18
    }
    if "," in string and "." not in string:
        string = string.replace(",", "")
    elif string.isdigit():
        string = int(string)
    elif "lion" in string:
        string = string.split(" ")
        string = float(string[0])*10**powers[string[1]]
        string = int(string)
    else:
        string = string.replace(",", "")
        string = float(string)
        string = round(string,0)
        string = int(string)
    return int(string)

main2()
