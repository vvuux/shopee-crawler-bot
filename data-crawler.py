from selenium import webdriver
import selenium
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common import keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_all_elements_located

from bs4 import BeautifulSoup

import csv
import json

from time import sleep

class ShopeeCrawler:
    """
    This tool works on Chrome Driver.
    Download Chrome Drive and create a new environment path for chromedriver.exe
    """
    def __init__(self,chromedriver_path,time_sleep=2):
        self.chromedriver_path = chromedriver_path
        self.time_sleep = time_sleep
        self.url = "https://shopee.vn/"

        # access to chrome
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging']) 
        self.driver = webdriver.Chrome(service=Service(self.chromedriver_path),options=options)
        self.driver.get(self.url)
        self.wait = WebDriverWait(self.driver,10)
        self.driver.implicitly_wait(self.time_sleep)

    def __get_product_links(self,num,keyword):
        # search for product data
        search_bar = self.driver.find_element(By.CSS_SELECTOR,"input[class='shopee-searchbar-input__input']")
        search_bar.send_keys(keyword)
        sleep(self.time_sleep)
        
        search_bar.send_keys(Keys.RETURN)
        sleep(self.time_sleep)


        ready_state = self.driver.execute_script("return document.readyState")
        
        search_origin_url = self.driver.current_url
        print("URL: ",search_origin_url)

        if ready_state == 'complete':
            print("Page has loaded")
            
            page = 0
            results = []
            page_data = []
            while len(results) + len(page_data) < num:    
                try:
                    # scroll down
                    sleep(self.time_sleep)
                    self.driver.execute_script("document.body.setAttribute('class','')") # shopee body class value is shopee-no-scroll
                    last_height = self.driver.execute_script("return document.body.scrollHeight")
                    html = self.driver.find_element(By.TAG_NAME,"html")
                    html.send_keys(Keys.PAGE_DOWN)
                    sleep(self.time_sleep)
                    self.driver.implicitly_wait(self.time_sleep) 
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    print("Page: ",page)

                    # find a tag having product detail link
                    page_data = self.driver.find_elements(By.CSS_SELECTOR,"a[data-sqe='link']")
                    print("Number of product links got: ",len(results) + len(page_data))
                    
                    """
                    if position of page is in ending part of page. Get to next page
                    else, keep scrolling.
                    """
                    if last_height == new_height:
                        results.extend(page_data)
                        page_data = []
                        page += 1
                        self.driver.get(f"{search_origin_url}&page={page}")
                        sleep(self.time_sleep)
                    else:
                        last_height = new_height
                except NoSuchElementException:
                    return results    

            # if position is not in ending part of page and get enough data. Add data to results  
            results.extend(page_data)
            return results[0:num]
        else:
            raise Exception("Page haven't loaded yet")

    def __write_to_csv(self,results_list,path):
        with open(path,"a",encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Product Name","Rate","Feedback Quantity","Sold Number","Price","Discount Price","Discount Percent","Shop Name","Shop's feedback Quantity","Product Quantity","Reply Rate","Reply Time","Register Time","Follower","Brand"])
            for data in results_list:
                writer.writerow([column for column in data.values()])
                

    def __write_to_txt(self,results_list,path):
        with open(path,"a",encoding="utf-8") as f:
            for data in results_list:
                for key, value in data.items():
                    f.write(f"{key}:{value}\n")
                    
                f.write("\n")

    def __write_to_json(self,results_list,path):
        with open(path,"a",encoding="utf-8") as f:
            for data in results_list:
                f.write(json.dumps(data,indent=4))
                f.write("\n")

    def __to_list(self,results):
        result_lst = []
        results = [link.get_attribute("href") for link in results]

        for link in results:
            data = self.__get_data(link)
            result_lst.append(data)
        return result_lst

    def scrape(self,keyword,num,save_path,file_extension,filename):

        """
        File extension includes csv,txt,json
        """
        
        # if num is smaller than 1, raise error
        if num <= 0:
            raise Exception("DataNumberError","Number of data should bigger than 0")
        

        results = self.__get_product_links(keyword=keyword,num=num) # get list of product detail links
        data_lst = self.__to_list(results) # scrape data then return a list of dictionary data

        if file_extension in ["csv","json","txt"]:

            file_location = save_path + "\\" + filename + f".{file_extension}"

            if file_extension == "csv":
                self.__write_to_csv(data_lst,file_location)
            elif file_extension == "txt":
                self.__write_to_txt(data_lst,file_location)
            elif file_extension == "json":
                self.__write_to_json(data_lst,file_location) 
        else:
            raise Exception("FileExtensionIsNotAvailableError","File extension should be one of 3 types (csv,txt,json)")
        print("Done")

    def __get_data(self,url):
        """
        get url that go to product details page and get data from it
        """
        self.driver.get(url)
        sleep(self.time_sleep)
        self.driver.implicitly_wait(self.time_sleep)
        
        page_source = self.driver.execute_script("return document.body.innerHTML")

        soup = BeautifulSoup(page_source,"html5lib")
        
        data = {}
        
        # product info
        data['product_name'] = soup.find("div",attrs={"class":"attM6y"}).span.text
        try:
            data["rate"] = soup.find("div",attrs={"class":"OitLRu _1mYa1t"}).text
        except:
            data["rate"] = "Chua co danh gia"
        data["feedback_quantity"] = soup.find("div",attrs={"class":"OitLRu"}).text
        data["sold_num"] = soup.find("div",attrs={"class":"aca9MM"}).text
        
        # price
        try:
            data["price"] = soup.find("div",attrs={"class":"_2MaBXe"}).text
            data["discount_price"] = soup.find("div",attrs={"class":"Ybrg9j"}).text
            data["discount_percent"] = soup.find("div",attrs={"class":"_3LRxdy"}).text
        except:
            data["price"] = soup.find("div",attrs={"class":"Ybrg9j"}).text
            data["discount_price"] = soup.find("div",attrs={"class":"Ybrg9j"}).text
            data["discount_percent"] = 0

        # shop_info
        data["shop_name"] = soup.find("div",attrs={"class":"_3uf2ae"}).text
        shop_info = soup.find_all("span",attrs={"class":"zw2E3N"})
        data["shop_feedback_quantity"] = shop_info[0].text
        data["product_quantity"] = shop_info[1].text
        data["reply_rate"] = shop_info[2].text
        data["reply_waiting_time"] = shop_info[3].text
        data["register_time"] = shop_info[4].text
        data["follower"] = shop_info[5].text
        try:
            data["brand"] = soup.find("a",attrs={"class":"_3Qy6bH"}).text
        except:
            data["brand"] = "No brand"

        return data

    def close(self):
        self.driver.close()

if __name__=="__main__":
    chromedriver = input("Chrome Driver Path: ")
    keyword = input("Keyword: ")
    num = int(input("Number of product data: "))
    while num <= 0:
        print("Number of product must be bigger than 0. Please try again!!")
        num = int(input("Number of product: "))
    save_path = input("Save path: ")
    file_extension = input("File extension: ")
    filename = input("File name: ")
    wait_time = int(input("Waiting time (above 2): "))
    while wait_time < 2:
        wait_time = int(input("Try again. Waiting time must be above 2 sec: "))

    crawler = ShopeeCrawler(time_sleep=wait_time)
    crawler.scrape(
        keyword=keyword,
        num = num,
        save_path=save_path,
        file_extension=file_extension,
        filename=filename,
    )
    crawler.close()







