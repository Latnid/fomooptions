import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
import pytz
import traceback
from Modules.AuthorControlAttach import cookies_manager
import traceback
import hashlib
import pandas as pd



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
def login_control(method, user_hash = None, user_cookies = None, user_email = None, user_group = None, premium_group = None, data_values = None, clindex = None ):

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
                login_device_count = 4
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
            # Check user_hash, user_cookies, premium_group in the database
            cur.execute("SELECT user_hash, user_cookies, premium_group FROM login_status WHERE user_cookies = %s", (user_cookies,))
            row = cur.fetchone()

            if row is not None: # Found the user_cookies in the table
                user_hash_db, user_cookies_db, premium_group_db = row

                # Check user hash match or not
                if user_hash == user_hash_db:
                    return True, True, user_cookies_db, user_hash_db, premium_group_db
                else:
                    return True, False, user_cookies_db, user_hash_db, "User_hash not match"
            else:
                return False, False, None, None, "Not able to locate the cookie in DB"
               
        elif method == "logout":
            #Delete record ceated previously with the user_cookies
            cur.execute("DELETE FROM {} WHERE user_cookies = %s".format(verifier_table_name), (user_cookies,))
            # excute query
            con.commit()
            #Delete cookies from the user browser:
            cookies_manager(method= "Logout", key = 'db_logout')
        elif method == "user_data_read":
                # Check user_cookies in the database and fetch user_email
                cur.execute("SELECT user_email FROM login_status WHERE user_cookies = %s", (user_cookies,))
                row = cur.fetchone()

                if row is not None:  # Found the user_cookies in the table
                    user_email = row[0]
                    return user_email
                else:
                    return None  # No user found for the given user_cookies
        elif method == "user_data_write_user_id":
            # Generate user_id (hash of user_email)
            user_id = hashlib.sha256(user_email.encode()).hexdigest()

            # Add user_id column to the login_status table if it doesn't exist
            cur.execute("ALTER TABLE IF EXISTS login_status ADD COLUMN IF NOT EXISTS user_id TEXT;")
            con.commit()

            # Update the user_id for the corresponding user_email
            cur.execute("UPDATE login_status SET user_id = %s WHERE user_email = %s", (user_id, user_email))
            con.commit()
        elif method == "cross_list_write":
            # Find user_id using user_cookies
            cur.execute("SELECT user_id FROM login_status WHERE user_cookies = %s", (user_cookies,))
            row = cur.fetchone()

            if row is not None:
                user_id = row[0]

                # Create a new table with user_id as the table name
                table_name = 'usid'+ user_id

                # Specify column names and data types manually
                # Adjust data types as needed for your specific use case
                columns_definition = (
                    "index TEXT," 
                    "types TEXT, "
                    "ticker TEXT, "
                    "otypes TEXT, "
                    "exp_date TEXT, "
                    "strike FLOAT, "
                    "tvalue TEXT, "
                    "bdate TEXT, "
                    "edate TEXT "    
                )


                # Create the table with columns and specified data types
                create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_definition})"
                cur.execute(create_table_query)
                con.commit()

                # Initialize the new table with values from the data_values dictionary
                insert_data_query = f"INSERT INTO {table_name} ({', '.join(data_values.keys())}) VALUES ({', '.join(['%s'] * len(data_values))})"
                cur.execute(insert_data_query, list(data_values.values()))
                con.commit()
        elif method == "cross_list_read":
            # Find user_id using user_cookies
            cur.execute("SELECT user_id FROM login_status WHERE user_cookies = %s", (user_cookies,))
            row = cur.fetchone()

            if row is not None:
                user_id = row[0]

                # Construct the table name
                table_name = 'usid' + user_id

                # Check if the table exists before executing the query
                table_exists_query = f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s);"
                cur.execute(table_exists_query, (table_name,))
                table_exists = cur.fetchone()[0]

                if table_exists:
                    # Construct the SELECT query to retrieve all rows from the table
                    select_query = f"SELECT * FROM {table_name};"
                    cur.execute(select_query)

                    # Fetch all rows and column names
                    rows = cur.fetchall()
                    column_names = [desc[0] for desc in cur.description]

                    # Create a DataFrame with the results
                    df = pd.DataFrame(rows, columns=column_names)

                    return df
                else:
                    # Handle the case where the table does not exist
                    return None
            else:
                # Handle the case where no user_id was found for the given user_cookies
                return None
        elif method == "cross_list_delete":
            # Find user_id using user_cookies
            cur.execute("SELECT user_id FROM login_status WHERE user_cookies = %s", (user_cookies,))
            row = cur.fetchone()

            if row is not None:
                user_id = row[0]

                # Construct the table name
                table_name = 'usid' + user_id

                # 使用DELETE语句删除行，注意要使用字符串拼接构建SQL查询
                delete_query = f"DELETE FROM {table_name} WHERE index = %s"
                cur.execute(delete_query, (clindex,))
                con.commit()

 
 
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
