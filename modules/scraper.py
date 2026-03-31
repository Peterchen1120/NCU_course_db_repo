from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import re


class NCUScraper():
    def __init__(self,account = None, password = None):
        opts = Options()
        opts.add_argument(r"user-data-dir=C:\Users\ZHENG\AppData\Local\Google\Chrome")
        opts.add_argument("--start-maximized")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option('useAutomationExtension', False)
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
        self.wait = WebDriverWait(self.driver,15)
        #self.login()
        self.account = account
        self.password = password

    # 可讓外部呼叫的func
    '''def get_dept_courses(self,dept_code):
        self.get_web(dept_code)
        a_element = self.get_links(dept_code)
        raw_html = self.read_table(a_element,dept_code)
        return raw_html'''
    def get_dept_courses(self, dept_code):
        dept_link = self.get_web(dept_code)
        if not dept_link:
            return []

        a_element = self.get_links(dept_link)
        raw_html = self.read_table(a_element, dept_code)
        return raw_html

    def login(self):
        self.driver.get("https://cis.ncu.edu.tw/Course/main/login")
        time.sleep(1.5)
        try:
            self.driver.find_element("name", "account").send_keys(self.account)
            self.driver.find_element("name", "passwd").send_keys(self.password)
            self.driver.find_element(By.NAME, "submit").click()
        except:
            print("登入失敗!請檢查帳密是否錯誤") 

        time.sleep(3)


    def back_to_mainPage(self):
        self.driver.get(r"https://cis.ncu.edu.tw/Course/main/query/byClass")
        time.sleep(2)

    '''

    def get_links(self,dept_code):
        wait = WebDriverWait(self.driver, 15)
        #links_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#deptdeptI1I4003I0 li a")))
        links_elements = self.driver.find_elements(By.TAG_NAME, "li")
        
        # 預存連結資訊，避免跳轉頁面後 element 失效
        a_element = []
        for link in links_elements:
            url = link.get_attribute("href")
            match = re.match(r"(.+)\s\((\d+)\)", link.text)
            if match:
                a_element.append({"url": url, "linkText": match.group(1), "numOfCourses": match.group(2)})
        return a_element        
    '''
    
    def get_links(self, dept_link):
        parent_li = dept_link.find_element(By.XPATH, "./ancestor::li[1]")
        child_ul = parent_li.find_element(By.XPATH, ".//ul")

        li_elements = child_ul.find_elements(By.TAG_NAME, "li")

        a_element = []
        for li in li_elements:
            text = li.text.strip()
            match = re.match(r"(.+?)\s*\((\d+)\)", text)
            if not match:
                continue

            try:
                a = li.find_element(By.TAG_NAME, "a")
                url = a.get_attribute("href")
            except:
                url = None

            a_element.append({
                "url": url,
                "linkText": match.group(1),
                "numOfCourses": int(match.group(2))
            })

        return a_element
    
    '''def get_web(self,dept_code):
        self.back_to_mainPage()
        wait = WebDriverWait(self.driver, 15)
        time.sleep(3)
        try:
            #course_btn = self.driver.find_element(By.CSS_SELECTOR, "td[menu='menu_query']")
            #self.driver.execute_script("arguments[0].click();", course_btn)
            #time.sleep(1)
            #general_btn = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "依照授課對象查詢")))
            #self.driver.execute_script("arguments[0].click();", general_btn)
            time.sleep(1)
            dept_link = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT,dept_code)))
            self.driver.execute_script("arguments[0].click();", dept_link)
            
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")
    '''

    def get_web(self, dept_code):
        self.back_to_mainPage()
        wait = WebDriverWait(self.driver, 15)
        time.sleep(1)

        try:
            dept_link = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//a[contains(normalize-space(.), '{dept_code}')]")
                )
            )
            self.driver.execute_script("arguments[0].click();", dept_link)
            return dept_link

        except Exception as e:
            print(f"❌ 發生錯誤: {e}")
            return None

    def read_table(self,a_element,dept_code):
        result = []
        for item in a_element:
            self.driver.get(item["url"])
            time.sleep(0.5)
            print(f"🔗 抓取 『{item['linkText']}』...")
            self.wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#item tbody tr td")) > 0)
            for tr in self.driver.find_elements(By.CSS_SELECTOR, "#item tbody tr"):
                raw_html = tr.get_attribute("innerHTML")
                result.append({
                    "raw_html":raw_html,
                    "dept_code":dept_code,
                    "grade":item["linkText"]
                })
        return result
            

    def close(self):
        self.driver.quit()





