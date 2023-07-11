import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime,timedelta
import pytz
import traceback
from Modules.AuthorControlAttach import cookies_manager
import traceback



# Load and assign variables.
load_dotenv()
SQL_DB = os.getenv('Auth_SQL_DB')
SQL_USER = os.getenv("Auth_SQL_USER")
SQL_PASSWORD = os.getenv("Auth_SQL_PASSWORD")
SQL_HOST = os.getenv("Auth_SQL_HOST")

def connect_data_base(database=SQL_DB, user=SQL_USER, password=SQL_PASSWORD, host=SQL_HOST):
    con = psycopg2.connect(database=SQL_DB, user=SQL_USER, password=SQL_PASSWORD, host=SQL_HOST)
    cur = con.cursor()
    cur.execute('SELECT version()')
    version = cur.fetchone()[0]
    print(f"DataBaseAuth Connected!\nVersion: {version}")
    return con, cur

#Login
def login_control(method, user_hash, user_cookies = None, user_email = None, user_group = None, premium_group = None, ):

    try:
        #connect db
        con,cur = connect_data_base()
        # prepare table_name
        verifier_table_name = "login_status"

        if method == 'login_success':   

            # Convert to NewYork Time
            ny_timezone = pytz.timezone("America/New_York")
            ny_time = datetime.now(ny_timezone)
            # Create table if not esists,
            cur.execute(
            "CREATE TABLE IF NOT EXISTS %s (create_time TIMESTAMPTZ, user_hash TEXT, user_cookies TEXT, user_email TEXT, user_group TEXT, premium_group TEXT);" %verifier_table_name)
            # excute SQL command
            con.commit()
            
            # Determine the number of records to keep based on the login device
            if premium_group == 'F/S Premium':
                login_device_count = 3
            elif premium_group == 'F/S Basic':
                login_device_count = 2
            else:
                login_device_count = 1
                
            query = """
                DELETE FROM login_status
                WHERE user_email = %s AND (create_time, user_cookies) NOT IN (
                    SELECT create_time, user_cookies
                    FROM (
                        SELECT create_time, user_cookies,
                            ROW_NUMBER() OVER (ORDER BY create_time DESC) AS row_num
                        FROM login_status
                        WHERE user_email = %s
                    ) AS subquery
                    WHERE row_num < %s
                )
            """
            cur.execute(query, (user_email, user_email, login_device_count))
            con.commit()

            # Insert all data to database and excute.  
            cur.execute("INSERT INTO {} (create_time, user_hash, user_cookies, user_email, user_group, premium_group) VALUES (%s,%s,%s,%s,%s,%s)".format(verifier_table_name),
            (ny_time, user_hash, user_cookies, user_email, user_group, premium_group))
            # excute query
            con.commit()


        elif method == 'login_status':
            #check user_hash, user_cookies, premium_group
            cur.execute("SELECT user_hash, user_cookies, premium_group FROM login_status WHERE user_cookies = %s", (user_cookies,))
            if cur.rowcount > 0: # Found the user_hash in the table
                row = cur.fetchone()
                user_hash_db, user_cookies_db, premium_group_db = row[:3]
                #check cookies match or not
                if user_cookies == user_cookies_db:
                    #check user hash match or not
                    if user_hash == user_hash_db:
                        return True, True,user_cookies_db, user_hash_db,premium_group_db
                    else:
                        return True, False,user_cookies_db, user_hash_db,"User_hash not match"
                else:
                    return False, False, None, None, "2"
            else:
                return False, False, None, None, "1"                        
            
        elif method == "logout":
            #Delete record ceated previously with the user_hash
            cur.execute("DELETE FROM {} WHERE user_hash = %s".format(verifier_table_name), (user_hash,))
            # excute query
            con.commit()
            #Delete cookies:
            cookies_manager(method= "Logout", key = 'db_logout')             
 
    except Exception as e:
        # 发生异常时记录错误信息
        error_message = traceback.format_exc()
        with open("DataBseAuth_error_log.txt", "a") as file:
            file.write(f"Error in database_auth function:\n{error_message}\n")

    finally:
        # 关闭数据库连接
        if cur is not None:
            cur.close()
        if con is not None:
            con.close()     
