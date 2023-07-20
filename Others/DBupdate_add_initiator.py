import pandas as pd
import psycopg2
from sqlalchemy import create_engine

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

# 连接到PostgreSQL数据库
conn = psycopg2.connect(
    host="192.168.123.88",
    database="fomostop",
    user="postgres",
    password='l5F|XSfOdY]rYdZ?'
)

# 使用SQLAlchemy创建PostgreSQL engine
engine = create_engine('postgresql+psycopg2://postgres:l5F|XSfOdY]rYdZ?@192.168.123.88/fomostop')

# 获取数据库中所有表的表名
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
table_names = [row[0] for row in cur.fetchall()]

# 遍历每个表并进行相同操作
for table_name in table_names:
    print(f"Processing table: {table_name}")
    # 读取数据到DataFrame
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", engine)
    print(f"df readed")

    # 删除"Initiator"列（如果存在）
    if 'Initiator' in df.columns:
        df.drop(columns=['Initiator'], inplace=True)
        print(f"drop check finish")

    # 添加"Initiator"列
    df['Initiator'] = df.apply(get_initiator, axis=1)
    print(f"Initiator added")

    # 排序
    new_order = ['Symbol', 'Price', 'Type', 'Strike', 'Exp Date', 'DTE', 'Bid', 'Midpoint', 'Ask', 'Last', 'Initiator', 'Volume', 'Open Int', 'OI Chg', 'IV', 'Time']
    df = df[new_order]
    # 重命名列
    df.columns = ["Symbol", "Price", "Type", "Strike", "Exp Date", "DTE", "Bid", "Midpoint", "Ask", "Last", "Initiator", "Volume", "Open Int", "OI Chg", "IV", "Time"]
    print(f"recorder")

    # 删除数据库中同名的表（如果存在）
    cur.execute(f"DROP TABLE IF EXISTS {table_name}")
    print(f"DROP TABLE IF EXISTS {table_name}")

    # Commit the transaction to apply the changes permanently
    conn.commit()

    # 将DataFrame写回数据库
    df.to_sql(table_name, engine, index=False, if_exists='replace')
    print(f"Created TABLE {table_name}")

    print(f"Table {table_name} updated.")

# 关闭连接
cur.close()
conn.close()