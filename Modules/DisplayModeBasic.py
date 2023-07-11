import os
from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import holoviews as hv
#import hvplot.pandas
from Modules.CleanData import get_data
from Modules.DataBaseFlow import *
st.elements.utils._shown_default_value_warning=True # Remove the duplicate widget value set warning

def Display_basic():
    # Sidebar components for user input
    st.sidebar.title("Choose data parameters")

    
    # 定义回调函数，用于处理st.session['selected_date']
    def date_select_display():
        st.session_state['selected_date'] = st.session_state.selected_date

    def date_init_display():
        st.session_state['selected_date'] = st.session_state.selected_date_init

    if 'selected_date' not in st.session_state:
        selected_date = st.sidebar.date_input("Select data date", key = 'selected_date_init', value=pd.Timestamp.now(tz=pytz.timezone('US/Eastern')).date(), on_change= date_init_display)
        st.session_state['selected_date'] = selected_date
    else:
        selected_date = st.sidebar.date_input("Select data date",key = 'selected_date', on_change = date_select_display, value = st.session_state.selected_date)

    #定义回调函数,用于处理st.session['selected_data_type']
    def type_select_display():
        st.session_state['selected_type'] = st.session_state.selected_type
    def type_init_display():
        st.session_state['selected_type'] = st.session_state.selected_type_init

    if 'selected_type' not in st.session_state:
        selected_data_type = st.sidebar.selectbox("Select data type",['stocks','etfs'], key = 'selected_type_init',on_change= type_init_display)
    else:
        selected_data_type = st.sidebar.selectbox("Select data type", ['stocks','etfs'], key = 'selected_data_type',on_change= type_select_display, index=  ['stocks','etfs'].index(st.session_state['selected_type']) )
    #selected_data_type = st.sidebar.selectbox("Select data type", ["stocks", "etfs"],key = 'selected_data_type_display')
    selected_top_tickers = st.sidebar.text_input("Top X tickers by OI flow", value="10", key = 'selected_top_tickers_display', disabled= True)

    # 防止用户输入非法字符
    try:
        selected_top_tickers = int(selected_top_tickers)
    except ValueError:
        selected_top_tickers = 10


    table_timestamps = None

    try:
        #连接数据库，获取所选日期中DTE的最大和最小值
        result = database_rw(operation = 'read', date = selected_date.strftime("%m-%d-%Y"), types = selected_data_type)
        if result:
            max_DTE, min_DTE = result
            def days_expiration_begin():
                if 'expirations_day_begin' not in st.session_state:
                    st.session_state['expirations_day_begin'] = min_DTE
                else:
                    st.session_state['expirations_day_begin'] = st.session_state.days_to_expiration_begin
            def days_expiration_end():
                if 'expirations_day_end' not in st.session_state:
                    st.session_state['expirations_day_end'] = min_DTE
                else:
                    st.session_state['expirations_day_end'] = st.session_state.days_to_expiration_end
            def days_expiration_range():
                st.session_state['expirations_day_range'] = st.session_state.days_to_expiration_range
                st.session_state['expirations_day_begin'] = st.session_state['expirations_day_range'][0]
                st.session_state['expirations_day_end'] = st.session_state['expirations_day_range'][1]
            
            # 使用 Streamlit 的 columns 函数创建两列布局给expirations_day_begin和expirations_day_end并排使用
            col1, col2 = st.sidebar.columns(2)
            # 在第一列中放置第一个 selectbox
            with col1:
                if 'expirations_day_begin' not in st.session_state:
                    selected_data_period_begin = st.number_input('Days to expiration range begin', min_value=0, max_value= max_DTE, value = min_DTE, key= "days_to_expiration_begin", on_change= days_expiration_begin, disabled=True )
                    st.session_state['expirations_day_begin'] = st.session_state.days_to_expiration_begin
                else:
                    #make sure min_DTE < st.session_state['expirations_day']/st.session_state['expirations_day_end'] < max_DTE
                    if st.session_state['expirations_day_begin'] < min_DTE:
                        st.session_state['expirations_day_begin'] = min_DTE
                    if st.session_state['expirations_day_end'] > max_DTE:
                        st.session_state['expirations_day_end'] = max_DTE
                        
                    selected_data_period_begin = st.number_input('Days to expiration range begin', min_value=0, max_value= max_DTE, value = st.session_state['expirations_day_begin'], key= "days_to_expiration_begin", on_change= days_expiration_begin, disabled=True )
            # 在第二列中放置第二个 selectbox
            with col2:
                if 'expirations_day_end' not in st.session_state:
                    selected_data_period_end = st.number_input('Days to expiration range end', min_value=min_DTE, max_value= max_DTE, value = min_DTE, key="days_to_expiration_end", on_change= days_expiration_end)
                    st.session_state['expirations_day_end'] = st.session_state.days_to_expiration_end
                else:
                    #make sure min_DTE < st.session_state['expirations_day']/st.session_state['expirations_day_end'] < max_DTE
                    if st.session_state['expirations_day_end'] < min_DTE:
                        st.session_state['expirations_day_end'] = min_DTE
                    if st.session_state['expirations_day_end'] > max_DTE:
                        st.session_state['expirations_day_end'] = max_DTE
                        
                    selected_data_period_end = st.number_input('Days to expiration range end', min_value=min_DTE, max_value= max_DTE, value = st.session_state['expirations_day_end'], key="days_to_expiration_end", on_change= days_expiration_end) 

            selected_data_period = st.sidebar.slider('Days to expiration range', min_value=min_DTE, max_value= max_DTE, value=(st.session_state['expirations_day_begin'],st.session_state['expirations_day_end']), step=1, format= "%i",on_change= days_expiration_range, key= "days_to_expiration_range", help="Use the slider to select an expiration day range (e.g., 10-30,10-10) and view only the data within that range.", disabled=True)    
            
            selected_data_period_begin = selected_data_period[0]
            selected_data_period_end = selected_data_period[1]

            # 连接数据库，获取所选日期所有表格的Timestamp列表
            _, _, table_timestamps = database_rw(operation='read', date=selected_date.strftime("%m-%d-%Y"), types=selected_data_type, BDTE = selected_data_period_begin, EDTE=selected_data_period_end)

        else:
            st.warning("Data will be refreshed throughout market hours. See you later!")
            st.snow()

    except Exception:
        # Display a streamlit animation to notify the user that data is still being prepared
        st.warning("Data will be updated during market hours, see you later.")


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
            time_selected_formatted = st.sidebar.selectbox('Data time', options=formatted_table_timestamps, key='time_init_display', on_change=time_init_display, disabled=True)
        else:
            time_selected_formatted = st.sidebar.selectbox('Data time', options=formatted_table_timestamps, key='time_select_display', on_change=time_select_display, index=formatted_table_timestamps.index(st.session_state['time_selected']), disabled=True)

        time_selected = table_timestamps[formatted_table_timestamps.index(time_selected_formatted)]

        # 获取选定时间和数据类型的所有ticker

        option_change, last_update_time, _ = database_rw(operation='read', date=selected_date.strftime("%m-%d-%Y"), types=selected_data_type, BDTE = selected_data_period_begin, EDTE=selected_data_period_end, time=time_selected)

        # 按OI流量排序并选择前X个ticker
        sorted_tickers = option_change.groupby('Symbol')['Open Int'].sum().sort_values(ascending=False).index[:selected_top_tickers]
        sorted_option_change = option_change[option_change['Symbol'].isin(sorted_tickers)]

        # 设置图表标题
        chart_title = f"options expiration range: {selected_data_period_begin} to {selected_data_period_end}            options.fomostop.com"

        # 在同一个页面显示选定的ticker的图表
        for ticker in sorted_tickers:
            # Open Int call put in one ticker
            plot_one_tickerOI = sorted_option_change[sorted_option_change['Symbol'] == ticker].hvplot.bar(
                by='Type',
                #hue=["Call", "Put"],
                color=['#0AA638', '#FF5635'],
                x='Strike',
                y='Open Int',
                yformatter='%0f',
                xlabel='Tickers by Call and Put',
                ylabel='Open Interest',
                title = f'Open Interest Spread - Ticker: {ticker} - Updated:{last_update_time} - {chart_title}',
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
                #hue=["Call", "Put"],
                color=['#0AA638', '#FF5635'],
                stacked=False,
                height=280,
                width=980,
                yformatter='%0f',
                rot=90,
                hover_cols=['Strike', 'DTE', 'Last', 'Time'],
                xlabel='Tickers by Call and Put',
                ylabel='Open Interest Change',
                title = f"Open Interest Change - Ticker: {ticker} - Updated:{last_update_time} - {chart_title}",
                
            )

            # 在Streamlit应用程序中显示图表
            st.bokeh_chart(hv.render(plot_one_tickerOI, backend="bokeh",))
            st.bokeh_chart(hv.render(plot_one_tickerOI_change, backend="bokeh"))

    else:
        st.markdown("[Join our group at pro.Fomostop.com](https://links.fomostop.com/join)")