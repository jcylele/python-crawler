import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Ctrls import RequestCtrl
from Utils import LogUtil
from WorkQueue.FetchQueueItem import FetchActorQueueItem


def printTime():
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


if __name__ == '__main__':
    # chrome_options = Options()
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--disable-gpu')
    # driver = webdriver.Chrome(chrome_options)
    driver = webdriver.Chrome()

    item = FetchActorQueueItem("alexbreecooper")
    url = RequestCtrl.formatActorUrl(item.actor_name)
    driver.get(url)
    if not driver.current_url.startswith(url):
        LogUtil.error(f"actor {item.actor_name} not found")
        exit(1)
    post_count = 0
    for i in range(1, 1000000):
        # wait for page load
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, "li.pagination-button-current b"), f"{i}")
        )

        # analyze content
        article_list = driver.find_elements(By.CSS_SELECTOR, 'article.post-card')
        post_list = []
        for article in article_list:
            post_id = article.get_attribute("data-id")
            if post_id is None:
                continue
            post_id = int(post_id)
            post_list.append(post_id)

        # self.processPosts(item.actor_name, post_list)
        post_count += len(post_list)

        # next page
        next_btn = driver.find_element(By.CSS_SELECTOR, '.pagination-button-after-current')
        if next_btn is None:
            print("no more pages")
            break

        # download no more
        if post_count >= 200:
            print("download enough")
            break

        # js click
        driver.execute_script("arguments[0].click();", next_btn)
        # wait
        # driver.implicitly_wait(2)
        time.sleep(1)

