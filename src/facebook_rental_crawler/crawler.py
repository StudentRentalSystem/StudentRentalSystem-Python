import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from src.facebook_rental_crawler.crawler_config import CrawlerConfig as Config
from src.facebook_rental_crawler.utils import hash_content
from src.facebook_rental_crawler.database import database

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Crawler:
    POISON_PILL = None

    def __init__(self, scroll_count, post_queue):
        logger.info("Starting Crawler")
        logger.info(f"Group URL: {Config.GROUP_URL}")
        logger.info(f"Chrome User Data: {Config.get_chrome_user_data()}")

        self.options = Options()
        self.options.add_argument(f"user-data-dir={Config.get_chrome_user_data()}")
        self.options.add_argument("profile-directory=Default")
        # Keep browser open (optional, but useful for debugging)
        self.options.add_experimental_option("detach", True)

        self.driver = webdriver.Chrome(options=self.options)

        logger.info("Facebook Crawler initialized.")
        self.scroll_count = scroll_count
        
        # Corresponds to Java's FluentWait (Timeout 3s, Polling 100ms)
        self.wait = WebDriverWait(self.driver, 3, poll_frequency=0.1)
        
        self.post_set = set()
        # Load existing IDs from database
        self.post_set.update(database.collection.get()['ids'])
        
        self.queue = post_queue

    def crawl(self):
        try:
            logger.info("Starting Facebook Crawler...")
            self.driver.get(Config.FACEBOOK_URL)
            self.wait.until(EC.url_contains(Config.FACEBOOK_URL))
            self.driver.get(Config.GROUP_URL)
            self.wait.until(EC.url_contains(Config.GROUP_URL))

            same_post_count = 0
            last_post_set_size = 0
            re_scroll_times = 0

            for i in range(self.scroll_count):
                self.crawl_one_page()
                self.scroll_down_one_post_each_time(1)
                time.sleep(1)

                current_post_set_size = len(self.post_set)
                print(f"{current_post_set_size}, {last_post_set_size}")
                
                if current_post_set_size == last_post_set_size:
                    same_post_count += 1
                    print(f"No new posts found. samePostCount = {same_post_count}")
                    if same_post_count >= 2:
                        print("Detected stagnant post set. Scrolling extra times to force refresh...")
                        self.force_scroll_down(re_scroll_times + 1, 2000)
                        re_scroll_times += 1
                        same_post_count = 0
                else:
                    same_post_count = 0
                    re_scroll_times = 0
                
                last_post_set_size = current_post_set_size

            self.queue.put(Crawler.POISON_PILL)
            logger.info("Facebook Crawler finished.")

        except Exception as e:
            print(e)
        finally:
            self.driver.quit()

    def crawl_one_page(self):
        # 1. Find all "See more" buttons
        see_more_buttons = self.driver.find_elements(By.XPATH, "//div[text()='查看更多']")
        
        # If Chinese not found, try finding English "See more"
        if not see_more_buttons:
            see_more_buttons = self.driver.find_elements(By.XPATH, "//div[text()='See more']")
        
        # 2. Expand all buttons
        for button in see_more_buttons:
            try:
                if button.is_displayed():
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    self.wait.until(EC.element_to_be_clickable(button))
                    self.driver.execute_script("arguments[0].click();", button)
                    time.sleep(1)
            except Exception:
                logger.warning("Skip a `查看更多`")
        
        time.sleep(1)
        
        # 3. Scrape all post elements
        post_elements = self.driver.find_elements(By.XPATH, "//div[@data-ad-preview='message']")
        
        for post in post_elements:
            success = False
            # Retry mechanism (max 3 times)
            for retry in range(3):
                if success: break
                try:
                    if post is None: continue 
                    
                    text = post.text.strip()
                    # Ensure text is not empty and does not contain unexpanded "See more"
                    if text and "查看更多" not in text and "See more" not in text:
                        hash_val = hash_content(text)
                        
                        if hash_val in self.post_set:
                            print("跳過重複貼文")
                            continue # In Java logic, this continues the inner loop (retry loop), effectively skipping this processing
                        
                        print("------------------------")
                        print(text)
                        print("------------------------")
                        
                        result = self.add_post(text, hash_val)
                        if not result:
                            logger.info("The post has existed")
                    
                    success = True
                except StaleElementReferenceException:
                    logger.warning("Retry post text extraction due to stale element")
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Unexpected error when processing post: {e}")
                    break

    def force_scroll_down(self, times, size):
        for _ in range(times):
            try:
                self.driver.execute_script(f"window.scrollBy(0, {size});")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Force scroll error: {e}")

    def scroll_down_one_post_each_time(self, times):
        for _ in range(times):
            try:
                posts = self.driver.find_elements(By.XPATH, "//div[@data-ad-preview='message']")
                
                if not posts:
                    logger.warning("Unable to find the posts")
                    break
                
                last_post = posts[-1]
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'end'});", last_post)
                
                time.sleep(0.6)
            except Exception:
                logger.error("Scrolling Error")

    def add_post(self, content, hash_val):
        if hash_val not in self.post_set:
            self.post_set.add(hash_val)
            print(f"Hashed content:{hash_val}")
            # Create post object and put into Queue (Here using Dict to simulate Post object)
            p = {"id": hash_val, "content": content}
            try:
                self.queue.put(p)
            except Exception:
                pass
            return True
        return False