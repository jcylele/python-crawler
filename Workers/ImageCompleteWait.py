from selenium import webdriver
from selenium.webdriver.common.by import By


class ImageCompleteWait(object):
    def __init__(self, selector: str):
        self.selector = selector

    def __call__(self, driver: webdriver.Chrome):
        img_ele = driver.find_element(By.CSS_SELECTOR, self.selector)
        complete = img_ele.get_attribute('complete')
        return complete == 'true'
