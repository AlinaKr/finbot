from copy import deepcopy
from price_parser import Price
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from finbot import providers
from finbot.providers.support.selenium import any_of, SeleniumHelper
from finbot.providers.errors import AuthFailure
import logging


BARCLAYCARD_URL = "https://www.barclaycard.co.uk/personal/customer"


class Credentials(object):
    def __init__(self, user_name, passcode, memorable_word):
        self.user_name = user_name
        self.passcode = passcode
        self.memorable_word = memorable_word

    @property
    def user_id(self):
        return str(self.user_name)

    @staticmethod
    def init(data):
        return Credentials(
            data["username"],
            data["passcode"],
            data["memorable_word"])


class Api(providers.SeleniumBased):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account = None

    def authenticate(self, credentials):
        self._do.get(BARCLAYCARD_URL)

        logging.info("getting logging form")
        login_button = self._do.wait_element(By.XPATH, "//a[@data-aem-js='loginButton']")
        self._do.click(login_button)

        # step 2: provide username

        logging.info(f"providing username {credentials.user_name}")
        username_input = self._do.wait_element(By.XPATH, "//input[@name='usernameAndID']")
        username_input.send_keys(credentials.user_name)
        self._do.find(By.XPATH, "//button[@type='submit']").click()

        # step 3: provide passcode

        logging.info(f"providing passcode")
        passcode_input = self._do.wait_element(By.XPATH, "//input[@type='password']")
        passcode_input.send_keys(credentials.passcode)
        self._do.find(By.XPATH, "//button[@type='submit']").click()

        # step 4: provide partial memorable word

        logging.info(f"providing memorable word")

        input1 = self._do.wait_element(By.XPATH, "//input[@data-id='memorableWord-letter1']")
        input1_id = input1.get_attribute("id")

        input2 = self._do.wait_element(By.XPATH, "//input[@data-id='memorableWord-letter2']")
        input2_id = input2.get_attribute("id")

        letter1_label_id = f"{input1_id}-label"
        letter1_idx = int(self._do.wait_element(By.ID, letter1_label_id).text.strip()[0]) - 1

        letter2_label_id = f"{input2_id}-label"
        letter2_idx = int(self._do.wait_element(By.ID, letter2_label_id).text.strip()[0]) - 1

        input1.send_keys(credentials.memorable_word[letter1_idx])
        input2.send_keys(credentials.memorable_word[letter2_idx])
        self._do.find(By.XPATH, "//button[@type='submit']").click()

        self._do.wait_cond(any_of(
            presence_of_element_located((By.CSS_SELECTOR, "div.sitenav-select-account-link")),
            lambda _: _get_login_error(self._do)
        ))

        error_message = _get_login_error(self._do)
        if error_message:
            raise AuthFailure(error_message)

        # step 5: collect account info
        account_area = self._do.wait_element(By.CSS_SELECTOR, "div.sitenav-select-account-link")
        account_name, account_id = account_area.text.strip().split("...")
        self.account = {
            "id": account_id,
            "name": account_name.strip(),
            "iso_currency": "GBP"
        }

    def get_balances(self):
        balance_area = self._do.wait_element(By.CSS_SELECTOR, "div.current-balance")
        balance_amount_str = balance_area.find_element_by_css_selector("span.value").text.strip()
        balance_amount = Price.fromstring(balance_amount_str)
        return {
            "accounts": [
                {
                    "account": deepcopy(self.account),
                    "balance": balance_amount.amount_float * -1.0
                }
            ]
        }

    def get_liabilities(self):
        return {
            "accounts": [
                {
                    "account": entry["account"],
                    "liabilities": [{
                        "name": "credit",
                        "type": "credit",
                        "value": entry["balance"]
                    }]
                }
                for entry in self.get_balances()["accounts"]
            ]
        }


def _get_login_error(browser_helper: SeleniumHelper):
    form_error_area = browser_helper.find_many(By.XPATH, "//div[contains(@class, 'FormErrorWell')]")
    if form_error_area:
        return form_error_area.find_element_by_tag_name("strong").text.strip()
