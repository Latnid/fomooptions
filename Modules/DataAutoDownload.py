from datetime import datetime, timedelta
import pytz
import time as t
import os
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import traceback
from dotenv import load_dotenv
from DataBase import database_rw

#加载环境变量
load_dotenv()


def download_csv():

    # 创建 Remote webdriver 实例，连接到 Selenium Server
    
    chrome_options = Options()
    #chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')

    driver = webdriver.Remote(
        command_executor='http://localhost:4444/wd/hub',
        options=chrome_options
    )


    # 登录网站
    driver.get('https://www.barchart.com/login')
    t.sleep(5)
    username_input = driver.find_element(By.NAME, 'email')
    password_input = driver.find_element(By.NAME, 'password')
    username_input.send_keys(os.getenv('username'))
    password_input.send_keys(os.getenv('password'))
    submit_btn = driver.find_element(By.XPATH, '//button[@type="submit"]')
    submit_btn.click()


    # 定义目标网页列表和对应的目标文件夹路径
    urls = {'https://www.barchart.com/options/open-interest-change/increase': os.path.join(os.path.dirname(__file__), '../Data/Increase'),
            'https://www.barchart.com/options/open-interest-change/decrease': os.path.join(os.path.dirname(__file__), '../Data/Decrease'),
            'https://www.barchart.com/options/open-interest-change/increase?sector=etf': os.path.join(os.path.dirname(__file__), '../Data/Increase'),
            'https://www.barchart.com/options/open-interest-change/decrease?sector=etf': os.path.join(os.path.dirname(__file__), '../Data/Decrease')}

    # 遍历目标网页列表并依次下载CSV文件
    for url, folder_path in urls.items():
        # 打开目标网页并查找“download”按钮
        driver.get(url)
        t.sleep(5)
        download_btn = driver.find_element(By.CSS_SELECTOR, 'a.toolbar-button.download.ng-isolate-scope')
        download_btn.click()


        # 判断是否需要点击第二个Download Anyway按钮
        try:
            t.sleep(5)
            download_anyway_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-ng-click="redirectToDownload(true)"]')
            download_anyway_btn.click()
        except:
            print('Download Anyway button not found,pass step')
            pass
        # 移动下载的CSV文件到目标位置
        t.sleep(5)
        downloads_path = os.path.expanduser('~/Downloads')  # 获取下载路径
        try:
            source_file = max([os.path.join(downloads_path, f) for f in os.listdir(downloads_path)], key=os.path.getctime)
            file_name = os.path.basename(source_file)
            destination_file = os.path.join(folder_path, file_name)  # 拼接目标路径
            shutil.move(source_file, destination_file)
            print(f'{file_name} downloaded and saved to {destination_file} successfully!')
        except Exception as e:
            print(f"Move Files Error: {e}")

    # 关闭浏览器
    driver.quit()

# 写入数据库过程
#定义一个函数获取csv的文件日期部分和csv的修改时间。
def write_data_to_database(directory):
    csv_files = [filename for filename in os.listdir(directory) if filename.endswith(".csv")]
    csv_files.sort(key=lambda filename: os.path.getmtime(os.path.join(directory, filename)), reverse=True)

    if csv_files:
        latest_csv = csv_files[0]
        date = (latest_csv.split("-")[-3] + '-' + latest_csv.split("-")[-2] + '-' + latest_csv.split("-")[-1]).replace(".csv", "")
        file_path = os.path.join(directory, latest_csv)
        modification_time = os.path.getmtime(file_path)
    else:
        # 没有最新的 CSV 文件，进行适当的处理
        print("No CSV files found in the directory.")
        return

    
    types_list = ['stocks', 'etfs']

    for types in types_list:
        database_rw(operation='write', date=date, csv_time=modification_time, types=types, DTE='max')



#删除默认下载目录的多余csv文件
def clean_csv():

    downloads_path = os.path.expanduser('~/Downloads')  # 获取下载路径

    for f in os.listdir(downloads_path):
        if f.endswith('.csv'):
            os.remove(os.path.join(downloads_path, f))
    print('.csv files cleaned')

def is_trading_hours(current_time):
    """判断当前时间是否在美国证券交易时间内"""
    trading_start_time = datetime.strptime('9:30', '%H:%M').time()
    trading_end_time = datetime.strptime('16:00', '%H:%M').time()
    if current_time.weekday() < 5 and trading_start_time <= current_time.time() <= trading_end_time:
        return True
    return False

if __name__ == '__main__':


    while True:
        try:
            #获取当前华尔街时间
            us_eastern_tz = pytz.timezone('America/New_York')
            current_time = datetime.now(us_eastern_tz)
            if is_trading_hours(current_time):
                print(f"{current_time} - The stock market is open, downloading CSV file...")
                clean_csv()
                download_csv()
                write_data_to_database(directory = os.path.join(os.path.dirname(__file__), "../Data/Increase/"))
                print("Repeat in one hour.")
                # 倒计时1小时
                for i in range(60*60, 0, -1):
                    mins, secs = divmod(i, 60)
                    time_format = f"{mins:02d}:{secs:02d}"
                    print(f"Next download in {time_format}...", end="\r")
                    t.sleep(1)
            else:
                # 倒计时到下一个整点小时
                next_hour = (current_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                time_diff = (next_hour - current_time).total_seconds()
                for i in range(int(time_diff), 0, -1):
                    mins, secs = divmod(i, 60)
                    time_format = f"{mins:02d}:{secs:02d}"
                    print(f"Market closed. Next trading time is {next_hour}. Waiting {time_format}...", end="\r")
                    t.sleep(1)
        except Exception as e:
            with open('Datadownload_error.log', 'a') as f:
                f.write(f'Error occurred at {datetime.now()}: {str(e)}\n')
                f.write(traceback.format_exc()+'\n')






