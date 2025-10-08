from time import sleep

import faker
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

# from selenium import webdriver
from seleniumwire import webdriver


class USwitchPrices:
    def __init__(self, post_code: str):
        self.post_code = post_code

    def browser_session(self):
        options = Options()
        # options.headless = True
        driver = webdriver.Firefox(service=Service('/Users/nikhil/_Drive_E/python/selenium/geckodriver'), options=options)
        driver.maximize_window()

        try:
            driver.get('https://www.uswitch.com/gas-electricity/journey/postcode')
            WebDriverWait(driver, 200).until(
                EC.presence_of_element_located((By.NAME, 'postcode'))
            )

            accept_cookies = driver.find_element(By.CLASS_NAME, 'ucb-btn-accept--desktop')
            accept_cookies.click()
            sleep(2)

            pin_code_box = driver.find_element(By.NAME, 'postcode')
            pin_code_box.clear()
            pin_code_box.send_keys(self.post_code)
            pin_code_box.send_keys(Keys.ENTER)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, 'addresses'))
                )
            except Exception:
                return 'failed'

            address_box = Select(driver.find_element(By.NAME, 'addresses'))
            address_selected = address_box.select_by_index(1)

            confirm_ownership = driver.find_element(By.CLASS_NAME, '_checkboxText_18pt4_7')
            confirm_ownership.click()

            def continue_aka_submit(wait: bool = True):
                continue_1 = driver.find_element(By.XPATH, "//button[@type='submit']")
                continue_1.click()
                sleep(5)

                if 'Looks like you have a business meter' in driver.page_source:
                    return 'failed'

                if wait is True:
                    WebDriverWait(driver, 200).until(
                        EC.presence_of_element_located((By.XPATH, "//button[@type='submit']"))
                    )

            while True:
                status = continue_aka_submit(wait=True)
                if 'email-address-input' in driver.page_source:
                    break

                if status == 'failed':
                    return 'failed'

            f = faker.Faker()
            fake_email = f.email().split('@')[0] + '@gmail.com'

            email = driver.find_element(By.ID, 'email-address-input')
            email.send_keys(fake_email)
            sleep(5)

            continue_aka_submit(wait=False)
            sleep(5)

            if len(driver.find_elements(By.CLASS_NAME, '_smartMeterInterestContent_mkazr_1')) > 0:
                smart_meter_interest = driver.find_elements(By.NAME, 'smart-meter-interest')
                smart_meter_interest[1].click()
                continue_aka_submit(wait=False)

            WebDriverWait(driver, 200).until(
                EC.presence_of_element_located((By.CLASS_NAME, '_filterButton_1un9x_1'))
            )

            filter_ = driver.find_element(By.CLASS_NAME, '_filterButton_1un9x_1')
            filter_.click()
            sleep(2)

            show_all_plan_button = driver.find_elements(By.NAME, 'filters.onlyShowFulfillable')
            show_all_plan_button[1].click()
            sleep(1)

            show_results = driver.find_element(By.XPATH, "//button[@type='submit']")
            show_results.click()
            WebDriverWait(driver, 200).until(
                EC.presence_of_element_located((By.CLASS_NAME, '_filterButton_1un9x_1'))
            )

            self.cookies = driver.get_cookies()

            return 'success'
        
        except Exception:
            return 'failed'
        
        finally:
            driver.quit()

    def main(self):
        status = self.browser_session()
        if status == 'success':
            return self.cookies


if __name__ == '__main__':
    uswitch = USwitchPrices('WS13 8PE')
    print(uswitch.main())
