import os
from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import holoviews as hv
import hvplot.pandas
from CleanData import get_data
from DataBase import *


# Set page configuration
st.set_page_config(
    page_title="FOMOSTOP FlowMaster: Unleashing Advanced Options Flow Analysis",
    page_icon="random",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 隐藏页脚，右上角菜单，减少页头空间。
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div.block-container{padding-top:2rem;}
    .css-1544g2n {
        padding: 1rem 1rem 1rem;
    }
    </style>
    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Add content to the sidebar
st.sidebar.markdown("<h1><a href='https://www.fomostop.com' style='text-decoration:none;'>FOMOSTOP</a></h1>", unsafe_allow_html=True)
st.sidebar.write("A daily analysis of options flow.")

# Sidebar components for user input
st.sidebar.title("Choose data parameters")
selected_date = st.sidebar.date_input("Select data date", key = 'selected_date_display', value=pd.Timestamp.now(tz=pytz.timezone('US/Eastern')).date())
selected_data_type = st.sidebar.selectbox("Select data type", ["stocks", "etfs"],key = 'selected_data_type_display')
selected_data_period = st.sidebar.selectbox('Days to expiration', ['min', 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 30, 60, 'max'], key = 'selected_data_period_display')
selected_top_tickers = st.sidebar.text_input("Top X tickers by OI flow", value="10", key = 'selected_top_tickers_display')

# 防止用户输入非法字符
try:
    selected_top_tickers = int(selected_top_tickers)
except ValueError:
    selected_top_tickers = 10


table_timestamps = None

try:
    # 连接数据库，获取所选日期所有表格的Timestamp列表
    _, _, table_timestamps = database_rw(operation='read', date=selected_date.strftime("%m-%d-%Y"), types=selected_data_type, DTE=selected_data_period)
except Exception:
    # Display a streamlit animation to notify the user that data is still being prepared
    st.warning("Data will be updated during market hours, see you later.")
    st.snow()

if table_timestamps is not None:
    # Convert timestamps to human-readable format
    eastern_tz = pytz.timezone('US/Eastern')
    formatted_table_timestamps = [datetime.fromtimestamp(int(timestamp), tz=eastern_tz).strftime("%Y-%m-%d %H:%M:%S %Z") for timestamp in table_timestamps]

    # 定义回调函数，用于处理st.session['time_selected']
    def time_select_display():
        st.session_state['time_selected'] = st.session_state.time_select_display

    def time_init_display():
        st.session_state['time_selected'] = st.session_state.time_init_display

    if 'time_selected' not in st.session_state or st.session_state['time_selected'] not in table_timestamps:
        time_selected_formatted = st.sidebar.selectbox('Data time', options=formatted_table_timestamps, key='time_init_display', on_change=time_init_display)
    else:
        time_selected_formatted = st.sidebar.selectbox('Data time', options=formatted_table_timestamps, key='time_select_display', on_change=time_select_display, index=formatted_table_timestamps.index(st.session_state['time_selected']))

    time_selected = table_timestamps[formatted_table_timestamps.index(time_selected_formatted)]

    # 定义回调函数，用于处理st.session['ticker_selected']
    def ticker_select():
        st.session_state['ticker_selected'] = st.session_state.ticker_sel

    def ticker_init():
        st.session_state['ticker_selected'] = st.session_state.ticker_init

    # 获取选定时间和数据类型的所有ticker

    option_change, last_update_time, _ = database_rw(operation='read', date=selected_date.strftime("%m-%d-%Y"), types=selected_data_type, DTE=selected_data_period, time=time_selected)

    # 获取所有的ticker选项，用于循环显示图表
    ticker_options = option_change['Symbol'].unique()

    # 按OI流量排序并选择前X个ticker
    sorted_tickers = option_change.groupby('Symbol')['Open Int'].sum().sort_values(ascending=False).index[:selected_top_tickers]
    sorted_option_change = option_change[option_change['Symbol'].isin(sorted_tickers)]

    # 设置图表标题
    chart_title = f"{selected_data_period} Days to Expiration"

    # 在同一个页面显示选定的ticker的图表
    for ticker in sorted_tickers:
        # Open Int call put in one ticker
        plot_one_tickerOI = sorted_option_change[sorted_option_change['Symbol'] == ticker].hvplot.bar(
            by='Type',
            hue=["Call", "Put"],
            color=['#0AA638', '#FF5635'],
            x='Strike',
            y='Open Int',
            yformatter='%0f',
            xlabel='Tickers by Call and Put',
            ylabel='Open Interest',
            title = f'Open Interest by strike price - {ticker} - Updated:{last_update_time} {chart_title}',
            hover_cols=['Strike', 'DTE', 'Last', 'Time'],
            height=280,
            width=980,
            rot=90,
        )

        # Open Int call put in one ticker
        plot_one_tickerOI_change = sorted_option_change[sorted_option_change['Symbol'] == ticker].hvplot.bar(
            x='Strike',
            y='OI Chg',
            by='Type',
            hue=["Call", "Put"],
            color=['#0AA638', '#FF5635'],
            stacked=False,
            height=280,
            width=980,
            yformatter='%0f',
            rot=90,
            hover_cols=['Strike', 'DTE', 'Last', 'Time'],
            xlabel='Tickers by Call and Put',
            ylabel='Open Interest Change',
            title = f"Call / Put OI changed - {ticker} - Updated:{last_update_time} {chart_title}",
            title_color='red'
        )

        # 在Streamlit应用程序中显示图表
        st.bokeh_chart(hv.render(plot_one_tickerOI, backend="bokeh", use_container_width=True))
        st.bokeh_chart(hv.render(plot_one_tickerOI_change, backend="bokeh", use_container_width=True))

else:
    st.markdown("[Fomostop.com](https://www.fomostop.com)")