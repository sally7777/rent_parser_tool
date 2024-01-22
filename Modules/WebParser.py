import os
import re
import time
import logging
import sqlite3
import random
import hashlib
import requests
import warnings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException, NoSuchElementException
from bs4 import BeautifulSoup

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.WARNING)

class web_parser:
    def __init__(self):
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        self.options = Options()
        self.options.add_argument("ignore-certificate-errors")
        self.options.add_argument("--disable-blink-features=AutomationControlled")  # 是否driver控制瀏覽器
        self.options.add_experimental_option("excludeSwitches", ["enable-logging"])  # 關閉除錯LOG(selenium自帶的,並非程式碼錯誤)
        self.options.add_argument('headless') ###不顯示瀏覽器
        self.options.add_argument("--disable-notifications")  # 取消所有的alert彈出視窗
        self.options.add_argument("--blink-settings=imagesEnabled=false") #不顯示圖片 增加效能
        self.options.add_argument('--disable-web-security')
        self.options.add_argument('--allow-running-insecure-content')
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        self.driver.implicitly_wait('10')  ###隱性等待時間 

    def __del__(self):
        if self.driver.service.process is not None:
            self.driver.quit()

    def check_browser_state(self):
        try:
            x = self.driver.current_url
        except InvalidSessionIdException and WebDriverException:
            self.driver.quit()
            print('Restarting browser..')

    def parser_service(self):
        url = 'https://www.firsthome.tw/Findhouse'  #台中租屋網
        self.driver.get(url)
        all_result =[]
        try:
            for page in range(1, 6):  
                soup = BeautifulSoup(self.driver.page_source.replace('http://','https://'), "html.parser")
                houses_list = soup.find_all('div', class_='house_detail')
                for house in houses_list:
                    title = house.a.text ###物件標題
                    img_url =house.img['src'].replace('http://','https://') ###圖片網址
                    if 'http' in img_url:self.save_img_url(img_url)   #下載圖片到指定資料夾
                    rent=house.span.text
                    addr =house.find('dt', class_='add2').text
                    detail=house.find_all('dd', class_='item2')
                    detail =[data.text for data in detail if data]
                    coummary,kind_h,type_h,area,rooms,floors=detail[:-2]
                    house_id =self.generate_hash(title+addr)  ####hasu值創建id
                    add_time = int(time.time())
                    detail_code = re.findall('\d+',str(house.a['onclick']))
                    if detail_code:detail_code= detail_code[0]
                    ####id,addtime,title,add,img_url,rent,coummary,kind_h,type_h,area,rooms,floors,detail_code
                    all_result.append((house_id,add_time,title,addr,img_url.split('/')[-1],rent,coummary,kind_h,type_h,area,rooms,floors,detail_code))
                time.sleep(round(random.uniform(3,6),2))
                page_next = self.driver.find_element(By.CSS_SELECTOR,f"body > div.findhouse > div > div:nth-child(7) > div > a:nth-child({page+1})")
                page_next.click()  # 點擊下一頁按鈕
                time.sleep(round(random.uniform(3,6),2))  
            if all_result:self.write_db(all_result)
            self.driver.close()
            self.delete_old_records()
        except Exception as e:
            print(e)

    def save_img_url(self,img_url):
        # 指定存檔的資料夾
        download_folder = "rent_pic"
        # 檢查資料夾是否存在，否則創一個新的
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        # Extract the filename from the URL
        filename = os.path.join(download_folder, os.path.basename(img_url))
        # Download the image
        response = requests.get(img_url)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
        else:
            logging.warning(f"Failed to download image. Status code:{response.status_code}\n img_url:{img_url}")

    def generate_hash(self,chinese_string):
        """利用標題和地址 製作hasu碼當作ID"""
        encoded_string = chinese_string.encode('utf-8')
        hash_object = hashlib.md5()
        hash_object.update(encoded_string)
        hash_value = hash_object.hexdigest()
        return hash_value
    
    def write_db(self,all_result):
        connection = sqlite3.connect('rent_house.sqlite')
        try:
            cursor = connection.cursor()
            cursor.execute('create table if not exists rent(id text primary key,addtime integer ,title text,addrs text,img_name text,rent text,coummary text,kind_h text,type_h text,area text,rooms text,floors text,detail_code text);')
            sql_insert = "INSERT OR REPLACE INTO rent (id,addtime,title,addrs,img_name,rent,coummary,kind_h,type_h,area,rooms,floors,detail_code) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
            cursor.executemany(sql_insert, all_result)
            connection.commit()
        except Exception as e:
            logging.error(e)
            print('error',all_result)
        finally:
            connection.close()
    
    def delete_old_records(self):
        connection = sqlite3.connect('rent_house.sqlite')
        try:
            cursor = connection.cursor()
            current_time = time.time()
            cursor.execute("SELECT * FROM rent")
            data = cursor.fetchall()
            for row in data:
                addtime = row[1]  # 這裡請根據你的實際欄位名稱調整
                if current_time - addtime > 60*60*24*7:  #超過7天的資料要刪除
                    cursor.execute("DELETE FROM rent WHERE id=?", (row['id'],))  # 這裡假設你有一個名為 id 的主鍵欄位
            connection.commit()
        except Exception as e:
            logging.error(e)
        finally:
            connection.close()

    def get_all_data(self):
        ####連線所有資料###
        datas=[]
        connection = sqlite3.connect('rent_house.sqlite')
        try:
            cursor = connection.cursor()
            # 查詢資料庫中的所有資料
            cursor.execute("SELECT * FROM rent")
            datas = cursor.fetchall()
        except Exception as e:
            print(e)
        finally:
            connection.close()
        return datas


