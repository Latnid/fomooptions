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
from DataBase import connect_data_base,database_rw

# 写入数据库过程
#定义一个函数获取csv的文件日期部分和csv的修改时间。
def get_latest_csv_info(directory):
    # Get a list of CSV filenames in the directory
    csv_files = [filename for filename in os.listdir(directory) if filename.endswith(".csv")]

    # Sort the list of files by modification time (newest first)
    csv_files.sort(key=lambda filename: os.path.getmtime(os.path.join(directory, filename)), reverse=True)

    # Retrieve the latest CSV filename and extract the date
    if csv_files:
        latest_csv = csv_files[0]
        date = (latest_csv.split("-")[-3]+ '-' + latest_csv.split("-")[-2]+ '-' + latest_csv.split("-")[-1]).replace(".csv", "")

        # Get the file modification time
        file_path = os.path.join(directory, latest_csv)
        modification_time = os.path.getmtime(file_path)

        return date, modification_time
    else:
        return None, None

# Specify the directory path
directory = os.path.join(os.path.dirname(__file__), "../Data/Increase/")

# Call the function and retrieve the date and modification time
date, modification_time = get_latest_csv_info(directory)
print(date)

#连接数据库进行数据写入
con, cur = connect_data_base()
types_list = ['stocks', 'etfs']
for types in types_list:
    database_rw(operation='write', con=con, cur=cur, date=date, types=types, DTE='max')