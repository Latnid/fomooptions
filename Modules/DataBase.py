from CleanData import get_data
import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import pandas as pd
import pytz
from datetime import datetime
import traceback

# Load and assign variables.
load_dotenv()
SQL_DB = os.getenv('SQL_DB')
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
SQL_HOST = os.getenv("SQL_HOST")

def connect_data_base(database=SQL_DB, user=SQL_USER, password=SQL_PASSWORD, host=SQL_HOST):
    con = psycopg2.connect(database=SQL_DB, user=SQL_USER, password=SQL_PASSWORD, host=SQL_HOST)
    cur = con.cursor()
    cur.execute('SELECT version()')
    version = cur.fetchone()[0]
    print(f"DataBase Connected!\nVersion: {version}")
    return con, cur

# write/read to database.
def database_rw(operation, date, types, DTE='max', csv_time=datetime.now().timestamp(), time='latest'):
    now_timestamp = int(csv_time) #时间戳只保留秒（去掉更低的精度，保留整数部分）
    date_parts = date.split('-')  #分割日期字符串
    con, cur = connect_data_base() #连接数据库

    try:
        if operation == 'write':
            combine_data = get_data(date, types, DTE)
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
            read_table_name = cur.fetchone()[0]

            #获取表的内容。
            if DTE == 'min':
                select_query = f"SELECT * FROM {read_table_name} WHERE \"DTE\" <= (SELECT MIN(\"DTE\") FROM {read_table_name})"
            elif DTE == 'max':
                select_query = f"SELECT * FROM {read_table_name} WHERE \"DTE\" <= (SELECT MAX(\"DTE\") FROM {read_table_name})"
            else:
                select_query = f"SELECT * FROM {read_table_name} WHERE \"DTE\" <= {DTE}"

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
        with open("error_log.txt", "a") as file:
            file.write(f"Error in database_rw function:\n{error_message}\n")

    finally:
        # 关闭数据库连接
        if cur is not None:
            cur.close()
        if con is not None:
            con.close()   

if __name__ == '__main__':
    connect_data_base()
    print("Read/Write db Module")

