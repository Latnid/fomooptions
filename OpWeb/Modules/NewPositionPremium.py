import numpy as np
from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import holoviews as hv
from Modules.DataBaseFlow import *
import hvplot.pandas

from bokeh.models import HoverTool
st.elements.utils._shown_default_value_warning=True # Remove the duplicate widget value set warning

def New_position_premium():

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
        st.session_state['selected_type'] = st.session_state.selected_data_type
    def type_init_display():
        st.session_state['selected_type'] = st.session_state.selected_type_init

    if 'selected_type' not in st.session_state:
        selected_data_type = st.sidebar.selectbox("Select data type",['stocks','etfs'], key = 'selected_type_init',on_change= type_init_display)
    else:
        selected_data_type = st.sidebar.selectbox("Select data type", ['stocks','etfs'], key = 'selected_data_type',on_change= type_select_display, index=  ['stocks','etfs'].index(st.session_state['selected_type']) )

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
                    selected_data_period_begin = st.number_input('Days to expiration range begin', min_value=0, max_value= max_DTE, value = min_DTE, key= "days_to_expiration_begin", on_change= days_expiration_begin )
                    st.session_state['expirations_day_begin'] = st.session_state.days_to_expiration_begin
                else:
                    #make sure min_DTE < st.session_state['expirations_day']/st.session_state['expirations_day_end'] < max_DTE
                    if st.session_state['expirations_day_begin'] < min_DTE:
                        st.session_state['expirations_day_begin'] = min_DTE
                    if st.session_state['expirations_day_end'] > max_DTE:
                        st.session_state['expirations_day_end'] = max_DTE
                        
                    selected_data_period_begin = st.number_input('Days to expiration range begin', min_value=0, max_value= max_DTE, value = st.session_state['expirations_day_begin'], key= "days_to_expiration_begin", on_change= days_expiration_begin )
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

            selected_data_period = st.sidebar.slider('Days to expiration range', min_value=min_DTE, max_value= max_DTE, value=(st.session_state['expirations_day_begin'],st.session_state['expirations_day_end']), step=1, format= "%i",on_change= days_expiration_range, key= "days_to_expiration_range", help="Use the slider to select an expiration day range (e.g., 10-30,10-10) and view only the data within that range.")    
            
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
            time_selected_formatted = st.sidebar.selectbox('Data time snapshots', options=formatted_table_timestamps, key='time_init_display', on_change=time_init_display)
        else:
            time_selected_formatted = st.sidebar.selectbox('Data time snapshots', options=formatted_table_timestamps, key='time_select_display', on_change=time_select_display, index=formatted_table_timestamps.index(st.session_state['time_selected']))

        time_selected = table_timestamps[formatted_table_timestamps.index(time_selected_formatted)]

        # 获取选定时间和数据类型的所有ticker
        option_change, last_update_time, _ = database_rw(operation='read', date=selected_date.strftime("%m-%d-%Y"), types=selected_data_type, BDTE = selected_data_period_begin, EDTE=selected_data_period_end, time=time_selected)

        # 按OI流量排序并选择前X个ticker
        option_change['strike OI'] = option_change.groupby(['Symbol', 'Strike'])['Open Int'].transform('sum')
        option_change['strike OI Chg'] = option_change.groupby(['Symbol', 'Strike'])['OI Chg'].transform('sum')
        # 计算相对差异
        option_change['OI Diff'] = np.abs(option_change['strike OI'] - option_change['strike OI Chg'])

        # 计算OI相似度百分比
        max_oi = option_change[['strike OI', 'strike OI Chg']].max(axis=1)
        oi_similarity = 1 - (option_change['OI Diff'] / max_oi)

        #定义回调函数，用于处理st.session['similarity_threshold']
        def similarity_threshold_select():
            st.session_state['similarity_threshold'] = st.session_state.similarity_threshold_select

        def similarity_threshold_init():
            st.session_state['similarity_threshold'] = st.session_state.similarity_threshold_init
        # 设置阈值，用于确定数量接近的行
        if 'similarity_threshold' not in st.session_state:
            similarity_threshold = st.sidebar.slider('New position accuracy threshold',min_value=0.1, max_value= 1.0, value=0.8, step=0.1, format = '%f',on_change = similarity_threshold_init, key= "similarity_threshold_init", help="Determines the accuracy rate of identifying initial opening positions based on the similarity between OI and OI Chg (range 0-1). A higher threshold indicates a higher accuracy rate in identifying initial opening positions.")  # 根据需求调整阈值
        else:
            similarity_threshold = st.sidebar.slider('New position accuracy threshold',min_value=0.1, max_value= 1.0, value=st.session_state['similarity_threshold'], step=0.1, format = '%f',on_change = similarity_threshold_select, key= "similarity_threshold_select", help="Determines the accuracy rate of identifying initial opening positions based on the similarity between OI and OI Chg (range 0-1). A higher threshold indicates a higher accuracy rate in identifying initial opening positions.")

        # 使用np.where将百分比相似度大于阈值的行标记为1，否则标记为0
        option_change['Similar Rows'] = np.where(oi_similarity > similarity_threshold, 1, 0)

        #去除Similar Rows下被标记为0的项目
        new_position_df = option_change[option_change['Similar Rows']== 1]
        #设置Symbol为index
        new_position_show_df = new_position_df.set_index('Symbol')

        # 选择所需显示的列
        selected_columns = ['Price', 'Type', 'Strike', 'DTE', 'Exp Date', 'Initiator', 'Last', 'Volume', 'Open Int', 'OI Chg', 'Delta', 'IV', 'Time',]
        new_position_show_df = new_position_show_df.loc[:, selected_columns]
        new_position_show_df.reset_index(inplace = True)
        
        #Show DataFrame
        st.dataframe(new_position_show_df)

        #获取new_position_df含有的所有ticker，用于循环显示图表
        new_position_tickers = new_position_df['Symbol'].unique()
        #排序option_change,用于图表
        option_change = option_change.sort_values(['Symbol','Strike','Open Int','Volume','OI Chg','IV'])
        # 设置图表标题
        chart_title = f"options expiration range: {selected_data_period_begin} to {selected_data_period_end}            options.fomostop.com"

        # 在同一个页面显示选定的ticker的图表
        for ticker in new_position_tickers:

            # Open Int call put in one ticker
            plot_one_tickerOI_change = option_change[option_change['Symbol'] == ticker].hvplot.bar(
                x='Strike',
                y='Open Int',
                color=['#329C97'],
                yformatter='%0.0f',
                xlabel='Tickers by Call and Put',
                ylabel='Open Interest',
                title = f'NewPosition - Ticker: {ticker} - Updated:{last_update_time} - {chart_title}',
                hover=False,
                height=280,
                width=980,
                rot=90
            )
            # Define the formatter for hover tooltip
            hover=HoverTool(tooltips=[
                  ('Price','@Price{ .2f}'),
                  ('Type','@Type'),
                  ('Strike','@Strike'),
                  ('DTE','@DTE'),
                  ('Exp Date','@Exp_Date'),
                  ('Initiator','@Initiator'),
                  ('Last','@Last{ .2f}'),
                  ('Volume','@Volume'),
                  ('Open Int', '@Open_Int'),
                  ('OI Chg', '@OI_Chg'), #if original column has space, use '_' instead!
                  ('Delta', '@Delta{ .3ff}'),
                  ('IV', '@IV'),
                  ('Time','@Time')
                ]
            )

            # Open Int call put in one ticker
            plot_two_tickerOI_change = new_position_show_df[new_position_show_df['Symbol'] == ticker].hvplot.scatter(
                x='Strike',
                y='OI Chg',
                size=350,  # Further increase the marker size for better visibility
                marker='diamond',  # Use a different marker shape (diamond) to differentiate from bars
                color='#FF5733',  # Choose a more contrasting color (e.g., orange) for the markers
                hover_cols=['Price', 'Type', 'Strike', 'DTE', 'Exp Date', 'Initiator', 'Last', 'Volume', 'Open Int', 'OI Chg', 'Delta', 'IV', 'Time'],
                xlabel='Tickers by Call and Put',
                ylabel='Open Interest',
                height=280,
                width=980,
                rot=90,
                tools=[hover]
            )

            plot_three_combine = plot_one_tickerOI_change * plot_two_tickerOI_change
            
            # 在Streamlit应用程序中显示图表
            st.bokeh_chart(hv.render(plot_three_combine, backend="bokeh"))

    else:
        st.markdown("[Join our group at pro.Fomostop.com](https://links.fomostop.com/join)")
