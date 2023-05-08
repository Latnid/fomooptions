from selenium import webdriver

# 创建webdriver实例
driver = webdriver.Chrome()

# 打开百度首页
driver.get('https://www.baidu.com')

# 查找搜索框并输入关键字
search_box = driver.find_element_by_id('kw')
search_box.send_keys('Python')

# 点击搜索按钮
search_button = driver.find_element_by_id('su')
search_button.click()

# 退出webdriver
driver.quit()
