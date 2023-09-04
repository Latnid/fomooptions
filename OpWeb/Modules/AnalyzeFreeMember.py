import os
from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import holoviews as hv
from Modules.DataBaseFlow import *
import hvplot.pandas
st.elements.utils._shown_default_value_warning=True # Remove the duplicate widget value set warning

def Analysis_free_member():

    # 定义回调函数，用于处理st.session['selected_date']
    def date_select():
        st.session_state['selected_date'] = st.session_state.selected_date
        
    def date_init():
        st.session_state['selected_date'] = st.session_state.selected_date_init

    if 'selected_date' not in st.session_state:
        selected_date = st.sidebar.date_input("Select data date", key = 'selected_date_init', value=pd.Timestamp.now(tz=pytz.timezone('US/Eastern')).date(),on_change=date_init)
        st.session_state['selected_date'] = selected_date
    else:
        selected_date = st.sidebar.date_input("Select data date",key = 'selected_date', on_change = date_select, value = st.session_state.selected_date)

    #定义回调函数,用于处理st.session['selected_data_type']
    def type_select():
        st.session_state['selected_type'] = st.session_state.selected_type
    def type_init():
        st.session_state['selected_type'] = st.session_state.selected_type_init

    if 'selected_type' not in st.session_state:
        selected_data_type = st.sidebar.selectbox("Select data type",['stocks','etfs'], key = 'selected_type_init',on_change= type_init)
    else:
        selected_data_type = st.sidebar.selectbox("Select data type", ['stocks','etfs'], key = 'selected_data_type',on_change= type_select, index=  ['stocks','etfs'].index(st.session_state['selected_type']) )

    #selected_data_type = st.sidebar.selectbox("Select data type", ["stocks", "etfs"])
    
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
                    selected_data_period_begin = st.number_input('Days to expiration range begin', min_value=min_DTE, max_value= max_DTE, value = min_DTE, key= "days_to_expiration_begin", on_change= days_expiration_begin,disabled=True )
                    st.session_state['expirations_day_begin'] = st.session_state.days_to_expiration_begin
                else:
                    #make sure min_DTE < st.session_state['expirations_day']/st.session_state['expirations_day_end'] < max_DTE
                    if st.session_state['expirations_day_begin'] < min_DTE:
                        st.session_state['expirations_day_begin'] = min_DTE
                    if st.session_state['expirations_day_end'] > max_DTE:
                        st.session_state['expirations_day_end'] = max_DTE

                    selected_data_period_begin = st.number_input('Days to expiration range begin', min_value=min_DTE, max_value= max_DTE, value = st.session_state['expirations_day_begin'], key= "days_to_expiration_begin", on_change= days_expiration_begin,disabled=True )
            # 在第二列中放置第二个 selectbox
            with col2:
                if 'expirations_day_end' not in st.session_state:
                    selected_data_period_end = st.number_input('Days to expiration range end', min_value=min_DTE, max_value= max_DTE, value = min_DTE, key="days_to_expiration_end", on_change= days_expiration_end,disabled=True)
                    st.session_state['expirations_day_end'] = st.session_state.days_to_expiration_end
                else:
                    #make sure min_DTE < st.session_state['expirations_day']/st.session_state['expirations_day_end'] < max_DTE
                    if st.session_state['expirations_day_end'] < min_DTE:
                        st.session_state['expirations_day_end'] = min_DTE
                    if st.session_state['expirations_day_end'] > max_DTE:
                        st.session_state['expirations_day_end'] = max_DTE
                    else:
                        selected_data_period_end = st.number_input('Days to expiration range end', min_value=min_DTE, max_value= max_DTE, value = st.session_state['expirations_day_end'], key="days_to_expiration_end", on_change= days_expiration_end,disabled=True) 

            selected_data_period = st.sidebar.slider('Days to expiration range', min_value=min_DTE, max_value= max_DTE, value=(st.session_state['expirations_day_begin'],st.session_state['expirations_day_end']), step=1, format= "%i",on_change= days_expiration_range, key= "days_to_expiration_range", help="Use the slider to select an expiration day range (e.g., 10-30,10-10) and view only the data within that range.",disabled=True)    
            
            selected_data_period_begin = selected_data_period[0]
            selected_data_period_end = selected_data_period[1]
            #连接数据库，获取所选日期所有表格的Timestamp列表
            _,_,table_timestamps = database_rw(operation = 'read', date = selected_date.strftime("%m-%d-%Y"), types = selected_data_type, BDTE = selected_data_period_begin, EDTE = selected_data_period_end)
        else:
            st.warning("Data will be refreshed throughout market hours. See you later!")
            st.snow()
        
    except Exception as e:
        # 发生异常时记录错误信息
        error_message = traceback.format_exc()
        with open("Analyze_error_log.txt", "a") as file:
            file.write(f"Error in database_rw function:\n{error_message}\n")
        # Display a streamlit animation to notify the user that data is still being prepared
        st.warning("Data will be updated during market hours, see you later.")


    if table_timestamps is not None:
        #Convert timestamps to human-readable format
        eastern_tz = pytz.timezone('US/Eastern')
        formatted_table_timestamps = [datetime.fromtimestamp(int(timestamp), tz=eastern_tz).strftime("%Y-%m-%d %H:%M:%S %Z") for timestamp in table_timestamps]

        #定义两个回调函数，用于处理st.session['time_selected']
        def time_select():
            st.session_state['time_selected'] = st.session_state.time_select

        def time_init():
            st.session_state['time_selected'] = st.session_state.time_init

        if 'time_selected' not in st.session_state or st.session_state['time_selected'] not in table_timestamps:
            time_selected_formatted = st.sidebar.selectbox('Data time snapshots', options=formatted_table_timestamps, key='time_init', on_change=time_init,disabled=True)
        else:
            time_selected_formatted = st.sidebar.selectbox('Data time snapshots', options=formatted_table_timestamps, key='time_select', on_change=time_select, index=formatted_table_timestamps.index(st.session_state['time_selected']),disabled=True)

        time_selected = table_timestamps[formatted_table_timestamps.index(time_selected_formatted)]

        #定义两个回调函数，用于处理st.session['ticker_selected']
        def ticker_select():
            if 'ticker_sel' not in st.session_state:
                st.session_state['ticker_sel'] = ticker_options[0]
            else:
                st.session_state['ticker_selected'] = st.session_state.ticker_sel

        def ticker_init():
            st.session_state['ticker_selected'] = st.session_state.ticker_init

        #读取数据库数据：
        option_change,last_update_time,_ = database_rw(operation = 'read', date = selected_date.strftime("%m-%d-%Y"), types = selected_data_type, BDTE = selected_data_period_begin, EDTE = selected_data_period_end , time = time_selected)

        # Ticker selected
        ticker_options = option_change['Symbol'].unique().tolist()
        if 'ticker_selected' not in st.session_state or st.session_state['ticker_selected'] not in ticker_options:
            ticker_selected = st.sidebar.selectbox('Ticker', options=ticker_options, key='ticker_init', on_change=ticker_init)
            
        elif 'ticker_selected' in st.session_state and st.session_state['ticker_selected'] in ticker_options:
            ticker_selected = st.sidebar.selectbox('Ticker', options=ticker_options, key='ticker_sel', on_change = ticker_select, index=ticker_options.index(st.session_state['ticker_selected']))

        st.sidebar.write(f"Last update: {last_update_time}")





        # Create DataFrame for all the required columns
        option_change_required = option_change[["Symbol", "Type", "Strike", "DTE", "Open Int", "OI Chg", "Volume", "Price", "IV", "Last", "Time"]]

        # Sorting step one
        # Groupby Symbol, then calculate the total Open Int, and make it as a new column
        option_change_required["Total Open Int"] = option_change_required.groupby("Symbol")["Open Int"].transform("sum")

        # Sorting step Two
        # Acquire the list of the top 20 Symbols
        top_20 = (
            option_change_required.groupby("Symbol")
            .agg({"Open Int": "sum"})
            .sort_values("Open Int", ascending=False)
            .iloc[:20]
        )

        # Sorting step three
        # Use groupby and transform to add a column called Total Open Int base on option_change_required
        option_change_required["Total Open Int"] = option_change_required.groupby("Symbol")["Open Int"].transform("sum")

        # Use .isin to filter the rows from top_20.index
        option_change_required_top_20 = (
            option_change_required[option_change_required.Symbol.isin(top_20.index)]
            .sort_values(by=["Total Open Int", "Symbol", "Type", "Strike", "Open Int"], ascending=False)
            .set_index(["Symbol", "Type", "Strike"])
        )
        
        #Title of the charts
        chart_title = f"options expiration range: {selected_data_period_begin} to {selected_data_period_end}            options.fomostop.com"
        # Top 20 symbols ranked by total open interest，Call / Put Open Interest comparation
        
        plot_top20OI = option_change_required_top_20.hvplot.bar(
            height=280,
            width=980,
            x="Symbol",
            xlabel="Symbol by Type",
            y="Open Int",
            yformatter='%0f',
            ylabel="Open Interest",
            by="Type",
            #hue=["Call","Put"],
            color=['#FF5635', '#0AA638'], 
            hover_cols=["Strike", "DTE", 'Last', "Time"],
            rot=90,
            title=f"Total Open Interest(Top 20) - Updated:{last_update_time} - {chart_title}",
            
            

        )
        # Top 20 Open Interest change
        plot_top20OI_chg = option_change_required_top_20.hvplot.bar(
            y="OI Chg",
            by="Type",
            #hue=["Call","Put"], 
            color=['#FF5635', '#0AA638'],
            stacked=False,
            height=280,
            width=980,
            yformatter="%0f",
            rot=90,
            hover_cols=["Strike", "DTE", 'Last', "Time"],
            xlabel="Tickers by Call and Put",
            ylabel="Open Interest Change",
            title= f"Open Interests Change - Updated:{last_update_time} - {chart_title}",
        )


        #Open Int call put in one ticker
        plot_one_tickerOI = option_change[option_change['Symbol'] == ticker_selected].hvplot.bar(
            by='Type',
            #hue=["Call","Put"], 
            color=['#0AA638','#FF5635'],
            x = 'Strike',
            y = 'Open Int',
            yformatter='%0f',
            xlabel='Tickers by Call and Put',
            ylabel='Open Interest',
            title = f'Open Interest Spread - Ticker: {ticker_selected} - Updated:{last_update_time} - {chart_title}',
            hover_cols = ['Strike','DTE', 'Last','Time'],
            height=280,
            width=980, 
            rot = 90,
        )
        
        #Open Int call put in one ticker
        plot_one_tickerOI_change = option_change[option_change['Symbol'] == ticker_selected].hvplot.bar(
            x = 'Strike',
            y='OI Chg',
            by='Type',
            #hue=["Call","Put"], 
            color=['#0AA638','#FF5635'],
            stacked=False,
            height=280,
            width=980, 
            yformatter='%0f',
            rot=90,
            hover_cols = ['Strike', 'DTE', 'Last','Time'],
            xlabel='Tickers by Call and Put',
            ylabel = 'Open Interest Change',
            title = f"Open Interest Change - Ticker: {ticker_selected} - Updated:{last_update_time} - {chart_title}"
        )


        # Show the Bokeh figure using st.bokeh_chart
        st.bokeh_chart(hv.render(plot_top20OI, backend="bokeh", ))
        st.bokeh_chart(hv.render(plot_top20OI_chg, backend="bokeh",))
        st.bokeh_chart(hv.render(plot_one_tickerOI, backend="bokeh",))
        st.bokeh_chart(hv.render(plot_one_tickerOI_change, backend="bokeh"))
            
        
    #Shows weblink if error happen.
    else:
        st.markdown("[Join our group at pro.Fomostop.com](https://links.fomostop.com/join)")
