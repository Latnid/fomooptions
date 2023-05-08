from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time

# 创建webdriver实例
s = Service('../chromedriver/chromedriver')
driver = webdriver.Chrome(service=s)

# 登录网站
driver.get('https://www.barchart.com/login')
time.sleep(5)
username_input = driver.find_element_by_xpath('//input[@id="login_username"]')
password_input = driver.find_element_by_xpath('//input[@id="login_password"]')
username_input.send_keys('dintalsky@gmail.com')
password_input.send_keys('Y8Bs@LjmF4aqFHg')
submit_btn = driver.find_element_by_xpath('//button[@type="submit"]')
submit_btn.click()

# 打开目标网页并查找“download”按钮
driver.get('https://www.barchart.com/options/open-interest-change/increase')
time.sleep(5)
soup = BeautifulSoup(driver.page_source, 'html.parser')
download_btn = soup.find('a', {'class': ['toolbar-button', 'download', 'ng-isolate-scope']})
download_url = download_btn['href']

# 打开弹出页面并查找“Download Anyway”按钮
driver.get(download_url)
time.sleep(5)
soup = BeautifulSoup(driver.page_source, 'html.parser')
download_anyway_btn = soup.find('button', {'data-ng-click': 'redirectToDownload(true)'})
download_anyway_url = download_anyway_btn.parent['href']

# 下载CSV文件并保存到本地
driver.get(download_anyway_url)
time.sleep(5)
with open('a.csv', 'wb') as f:
    f.write(driver.page_source.encode())
print('CSV file saved successfully!')

# 退出webdriver
driver.quit()