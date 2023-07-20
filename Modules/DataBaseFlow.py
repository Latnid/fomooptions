import sys
import os

# 将根目录添加到模块搜索路径中
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_path)

from Modules.CleanData import get_data
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import pandas as pd
import pytz
from datetime import datetime
import traceback

# Load and assign variables.
load_dotenv()
SQL_DB = os.getenv('Flow_SQL_DB')
SQL_USER = os.getenv("Flow_SQL_USER")
SQL_PASSWORD = os.getenv("Flow_SQL_PASSWORD")
SQL_HOST = os.getenv("Flow_SQL_HOST")

def connect_data_base(database=SQL_DB, user=SQL_USER, password=SQL_PASSWORD, host=SQL_HOST):
    con = psycopg2.connect(database=SQL_DB, user=SQL_USER, password=SQL_PASSWORD, host=SQL_HOST)
    cur = con.cursor()
    cur.execute('SELECT version()')
    version = cur.fetchone()[0]
    print(f"DataBaseFlow Connected!\nVersion: {version}")
    return con, cur

# write/read to database.
def database_rw(operation, date, types, BDTE=None, EDTE=None, csv_time=datetime.now().timestamp(), time='latest'):
    now_timestamp = int(csv_time) #时间戳只保留秒（去掉更低的精度，保留整数部分）
    date_parts = date.split('-')  #分割日期字符串
    con, cur = connect_data_base() #连接数据库

    try:
        #write data to database, DTE = 'max' means all the data collected.
        if operation == 'write':
            combine_data = get_data(date, types, DTE = 'max')

            # 自定义函数，根据"Last"和"Midpoint"的关系判断"sentiment"
            def get_initiator(row):
                if row['Last'] < row['Bid']:
                    return 'Aggressive Seller'
                elif row['Last'] > row['Ask']:
                    return 'Aggressive Buyer'
                elif row['Last'] < row['Midpoint']:
                    return 'Seller'
                elif row['Last'] > row['Midpoint']:
                    return 'Buyer'
                else:
                    return 'Neutral'
            # Add "Initiator" column
            combine_data['Initiator'] = combine_data.apply(get_initiator, axis=1)

            #重新排列，把'Initiator'放在'Last'后：
            new_order = ['Symbol', 'Price', 'Type', 'Strike', 'Exp Date', 'DTE', 'Bid', 'Midpoint', 'Ask', 'Last', 'Initiator', 'Volume', 'Open Int', 'OI Chg', 'IV', 'Time']

            # 使用reindex()方法重新排列列的顺序
            combine_data = combine_data.reindex(columns=new_order)

            #构建写操作的表名
            write_table_name = f"_{date_parts[2]}_{date_parts[0]}_{date_parts[1]}_{types}_{now_timestamp}"  # 按照'YYYY_MM_DD'格式重新排列日期部分

            # Delete old data from the table if it exists
            delete_query = f"DROP TABLE IF EXISTS {write_table_name}"
            cur.execute(delete_query)
            con.commit()
            
            # Create table if not exists
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {write_table_name} (
                "Symbol" TEXT,
                "Price" NUMERIC,
                "Type" TEXT,
                "Strike" NUMERIC,
                "Exp Date" TEXT,
                "DTE" NUMERIC,
                "Bid" NUMERIC,
                "Midpoint" NUMERIC,
                "Ask" NUMERIC,
                "Last" NUMERIC,
                "Initiator" TEXT,
                "Volume" NUMERIC,
                "Open Int" NUMERIC,
                "OI Chg" NUMERIC,
                "IV" NUMERIC,
                "Time" TEXT
            )
            """
            cur.execute(create_table_query)
            con.commit()

            # 批量插入数据
            insert_query = f"INSERT INTO {write_table_name} VALUES %s"
            rows = [tuple(row) for _, row in combine_data.iterrows()]
            psycopg2.extras.execute_values(cur, insert_query, rows)
            con.commit()
            print("Data inserted successfully!")

        elif operation == 'read':
            #搜索用户输入的数据日期，以时间形式列出当天所有数据列表。
            query = f"SELECT table_name FROM information_schema.tables WHERE table_name LIKE '_{date_parts[2]}_{date_parts[0]}_{date_parts[1]}_{types}_%' ORDER BY table_name DESC"
            cur.execute(query)
            table_timestamps = []
            for table_name in cur.fetchall():
                timestamp = table_name[0].split('_')[-1]
                table_timestamps.append(timestamp)

            # Return the time required if the time is valid.
            if time in table_timestamps:
                read_table_query = f"SELECT table_name FROM information_schema.tables WHERE table_name LIKE '_{date_parts[2]}_{date_parts[0]}_{date_parts[1]}_{types}_{time}' ORDER BY table_name DESC LIMIT 1"
            else:
                read_table_query = f"SELECT table_name FROM information_schema.tables WHERE table_name LIKE '_{date_parts[2]}_{date_parts[0]}_{date_parts[1]}_{types}_%' ORDER BY table_name DESC LIMIT 1"

            cur.execute(read_table_query)
            result = cur.fetchone()

            # 没有找到当前日期任何table数据
            if result is None:
                return None
            else:
                read_table_name = result[0]

            # 获取表的内容，如果数据为空，则先返回max和min的值，如果不是空则返回请求数值。
            if BDTE == None or EDTE == None:
                select_query = f"SELECT MAX(\"DTE\"), MIN(\"DTE\") FROM {read_table_name}"
                cur.execute(select_query)
                result = cur.fetchone()
                # 没有找到当前日期任何table数据
                if result is None:
                    return None
                elif result is not None:
                    max_DTE = int(result[0])
                    min_DTE = int(result[1])
                    return max_DTE, min_DTE
            
            elif EDTE != None and BDTE != None:

                select_query = f"SELECT * FROM {read_table_name} WHERE \"DTE\" BETWEEN {BDTE} AND {EDTE}"
                cur.execute(select_query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]  # 获取列名

                # 将获取到的数据转换为DataFrame
                df = pd.DataFrame(rows, columns=columns)
                # 显式指定列的数据类型
                df = df.astype({
                    "Symbol": str,
                    "Price": float,
                    "Type": str,
                    "Strike": float,
                    "Exp Date": str,
                    "DTE": float,
                    "Bid": float,
                    "Midpoint": float,
                    "Ask": float,
                    "Last": float,
                    "Initiator": str,
                    "Volume": float,
                    "Open Int": float,
                    "OI Chg": float,
                    "IV": float,
                    "Time": str
                })

                # 获取该表最后修改的时间
                last_modified_timestamp = int(read_table_name.split("_")[-1])

                # 将时间戳转换为 datetime 对象，并指定时区为华尔街时间（美国东部标准时间）
                eastern_tz = pytz.timezone('US/Eastern')
                eastern_datetime = (datetime.fromtimestamp(last_modified_timestamp, tz=eastern_tz)).strftime("%Y-%m-%d %H:%M:%S %Z")

                return df, eastern_datetime, table_timestamps
            

    except Exception as e:
        # 发生异常时记录错误信息
        error_message = traceback.format_exc()
        with open("DataBaseFlow_error_log.txt", "a") as file:
            file.write(f"Error in DataBaseFlow_database_rw function:\n{error_message}\n")

    finally:
        # 关闭数据库连接
        if cur is not None:
            cur.close()
        if con is not None:
            con.close()   

if __name__ == '__main__':
    connect_data_base()
    print("Read/Write db Module")

