import numpy as np
from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import holoviews as hv
from Modules.DataBaseFlow import *
from Modules.DataBaseAuth import *
import hvplot.pandas

from bokeh.models import HoverTool

st.elements.utils._shown_default_value_warning = True  # Remove the duplicate widget value set warning

def FlowTrendPremium():

    # 使用 Streamlit 的 columns 函数创建两列布局给 selected_type 和 ticker_selected 并排使用
    col1, col2 = st.sidebar.columns(2)

    # 在同一个 columns 中放置两个组件
    with col1:
        # 定义回调函数，用于处理 st.session['selected_data_type']
        def type_select_display():
            st.session_state['selected_type'] = st.session_state.selected_data_type

        def type_init_display():
            st.session_state['selected_type'] = st.session_state.selected_type_init

        if 'selected_type' not in st.session_state:
            selected_data_type = st.selectbox("Data type", ['stocks', 'etfs'], key='selected_type_init', on_change=type_init_display)
            st.session_state['selected_type'] = selected_data_type
        else:
            selected_data_type = st.selectbox("Data type", ['stocks', 'etfs'], key='selected_data_type', on_change=type_select_display, index=['stocks', 'etfs'].index(st.session_state['selected_type']))

        # 定义两个回调函数，用于处理 st.session['ticker_selected']
        def ticker_select():
            st.session_state['ticker_selected'] = st.session_state.selected_ticker.upper()

        def ticker_init():
            st.session_state['ticker_selected'] = st.session_state.ticker_init

    with col2:
        if 'ticker_selected' not in st.session_state:
            ticker_selected = st.text_input('Ticker', key='ticker_init', on_change=ticker_init, value= 'AAPL')
            st.session_state['ticker_selected'] = ticker_selected
        else:
            ticker_selected = st.text_input('Ticker', key='selected_ticker', on_change=ticker_select, value=st.session_state['ticker_selected'])


    # 使用 Streamlit 的 columns 函数创建两列布局给 options_type 和 expired_date 并排使用
    col3, col4 = st.sidebar.columns(2)
    # 在第一列中放置第一个 selectbox
    # 定义回调函数，用于处理 st.session['options_type']
    def options_type():
        st.session_state['options_type'] = st.session_state.selected_options_type

    def options_type_init():
        st.session_state['options_type'] = st.session_state.options_type_init

    with col3:
        if 'options_type' not in st.session_state:
            selected_options_type = st.selectbox("Options type", ['Call', 'Put'], key='options_type_init', on_change=options_type_init)
            st.session_state['options_type'] = selected_options_type
        else:
            selected_options_type = st.selectbox("Options type", ['Call', 'Put'], key='selected_options_type', on_change=options_type, index=['Call', 'Put'].index(st.session_state['options_type']))

    # 在第二列中放置第二个 selectbox
    # 定义回调函数，用于处理 st.session['expired_date']
    def expired_date():
        st.session_state['expired_date'] = st.session_state.selected_expired_date

    def expired_date_init():
        st.session_state['expired_date'] = st.session_state.expired_date_init
    with col4:
        if 'expired_date' not in st.session_state:
            selected_expired_date = st.date_input('Expired date', value=pd.Timestamp.now(tz=pytz.timezone('US/Eastern')).date(), key="expired_date_init", on_change=expired_date_init)
            st.session_state['expired_date'] = selected_expired_date
        else:
            selected_expired_date = st.date_input('Expired date', value=st.session_state['expired_date'], key="selected_expired_date", on_change=expired_date)

    # 使用 Streamlit 的 columns 函数创建两列布局给 Strike price 和 Target value 并排使用
    col5, col6 = st.sidebar.columns(2)

    # 定义回调函数，用于处理 st.session['strike_price']
    with col5:
        def strike_price():
            st.session_state['strike_price'] = st.session_state.selected_strike_price

        def strike_price_init():
            st.session_state['strike_price'] = st.session_state.strike_price_init

        if 'strike_price' not in st.session_state:
            selected_strike_price = st.number_input('Strike price', key = 'strike_price_init', on_change=strike_price_init)
            st.session_state['strike_price'] = selected_strike_price
        else:
            selected_strike_price = st.number_input('Strike price', value= st.session_state['strike_price'], key = 'selected_strike_price', on_change=strike_price)

    #显示在Y轴的值
    # 定义回调函数，用于处理 st.session['target_value']
    with col6:
        def target_value():
            st.session_state['target_value'] = st.session_state.selected_target_value

        def target_value_init():
            st.session_state['target_value'] = st.session_state.target_value_init

        if 'target_value' not in st.session_state:
            selected_target_value = st.selectbox('Target Value(y)', ['Volume','Open Int','OI Chg', "Delta", 'IV', 'Last'], key = 'target_value_init', on_change=target_value_init)
            st.session_state['target_value'] = selected_target_value
        else:
            selected_target_value = st.selectbox("Target Value(y)", ['Volume','Open Int','OI Chg', "Delta", 'IV', 'Last'], key='selected_target_value', on_change= target_value, index=['Volume','Open Int','OI Chg', "Delta", 'IV', 'Last'].index(st.session_state['target_value']))

    # 使用 Streamlit 的 columns 函数创建两列布局给 data_date_begin 和 data_date_end 并排使用
    col7, col8 = st.sidebar.columns(2)
    # 在第一列中放置第一个 selectbox
    # 定义回调函数，用于处理 st.session['data_date_begin']
    def data_date_begin():
        st.session_state['data_date_begin'] = st.session_state.selected_data_date_begin

    def data_date_begin_init():
        st.session_state['data_date_begin'] = st.session_state.data_date_begin_init

    with col7:
        if 'data_date_begin' not in st.session_state:
            selected_data_date_begin = st.date_input('Data date begin', value=pd.Timestamp.now(tz=pytz.timezone('US/Eastern')).date()- pd.DateOffset(months=2), key="data_date_begin_init", on_change=data_date_begin_init)
            st.session_state['data_date_begin'] = selected_data_date_begin
        else:
            selected_data_date_begin = st.date_input('Data date begin', value=st.session_state['data_date_begin'], key="selected_data_date_begin", on_change=data_date_begin)

    # 在第二列中放置第二个 selectbox
    # 定义回调函数，用于处理 st.session['data_date_end']
    def data_date_end():
        st.session_state['data_date_end'] = st.session_state.selected_data_date_end

    def data_date_end_init():
        st.session_state['data_date_end'] = st.session_state.data_date_end_init
    with col8:
        if 'data_date_end' not in st.session_state:
            selected_data_date_end = st.date_input('Data date end', value=pd.Timestamp.now(tz=pytz.timezone('US/Eastern')).date(), key="data_date_end_init", on_change=data_date_end_init)
            st.session_state['data_date_end'] = selected_data_date_end
        else:
            selected_data_date_end = st.date_input('Data date end', value=st.session_state['data_date_end'], key="selected_data_date_end", on_change=data_date_end)


    # Call the database_rw function with values from st.session_state
    df = database_rw(
        operation='read_cross',
        Bdate=st.session_state['data_date_begin'],
        Edate=st.session_state['data_date_end'],
        tvalue=st.session_state['target_value'],
        strike=st.session_state['strike_price'],
        exp_date=st.session_state['expired_date'],
        otypes=st.session_state['options_type'],
        ticker=st.session_state['ticker_selected'],
        types=st.session_state['selected_type']
    ) 


    #Acquire current user broswer cookies and hash
    _, user_cookies = cookies_manager(method="Login_status",key = 'flowtrend')
    user_email = login_control(method = "user_data_read", user_cookies = user_cookies)

    #portfolio选择框    
    portfolio_df = login_control(method = "cross_list_read", user_cookies = user_cookies)
    if portfolio_df is None or portfolio_df.empty:
        if df is not None:
            df['index'] = 'QuickView_Mode'
            portfolio_df = df
    if portfolio_df is not None and not portfolio_df.empty:
        #Create a Streamlit selectbox to display DataFrame rows as options
        # 重命名列名
        portfolio_show_df = portfolio_df.rename(columns={
            'index': 'Options_summary',
            'types': 'Type',
            'ticker': 'Ticker',
            'otypes': 'Call/Put',
            'exp_date': 'Exp_date',
            'strike': 'Strike',
            'tvalue': 'Target',

        })
        # 重新设置索引从 1 开始
        portfolio_show_df.index = range(1, len(portfolio_df) + 1)

        #只有在非QuickViewMode的情况下才显示Portfolio
        if 'index' in portfolio_df and not portfolio_df['index'].eq('QuickView_Mode').any():
            st.write('<h5 style="color: #ff5733;">Your portfolio:</h5>', unsafe_allow_html=True)
            st.dataframe(portfolio_show_df)
        
        # 显示选择框和对应内容
        st.sidebar.write('-----------------')
        selected_row_index = st.sidebar.selectbox("Select from your portfolio:", portfolio_df['index'],help='You can add or remove items to manage your portfolio, or you will remain in QuickView mode')
        # 获取DataFrame中的选定行
        selected_row = portfolio_df[portfolio_df['index'] == selected_row_index].iloc[0]

        # 使用 Streamlit 的 columns 函数创建一行布局给 "ShowTrend," "Remove," 和 "Add to my portfolio"
        col9, col10, col11 = st.sidebar.columns(spec=[1,1,1.2])
        with col9:
            if st.button('Show'):
                if 'index' in portfolio_df and not portfolio_df['index'].eq('QuickView_Mode').any():
                    # 更新session_state值为选定行的值
                    st.session_state['selected_type'] = selected_row['types']
                    st.session_state['ticker_selected'] = selected_row['ticker']
                    st.session_state['options_type'] = selected_row['otypes']
                    st.session_state['expired_date'] = pd.to_datetime(selected_row['exp_date']).date()# 将日期字段从文本格式转换为日期时间格式
                    st.session_state['strike_price'] = selected_row['strike']
                    st.session_state['target_value'] = selected_row['tvalue']
                    #st.session_state['data_date_end'] = pd.to_datetime(selected_row['edate']).date() # 将日期字段从文本格式转换为日期时间格式,不更新这项因为希望能够保持在最新日期
                    #st.session_state['data_date_begin'] = pd.to_datetime(selected_row['bdate']).date()# 将日期字段从文本格式转换为日期时间格式
                    st.experimental_rerun()

        with col10:
            # Check if df is None
            if df is not None:
                #以下是把选项写入portfolio的按钮
                if st.button("Add"):

                    #把email生成user_id来写入数据库
                    login_control(method = "user_data_write_user_id", user_email = user_email)
                    #把数据构建成字典然后写入到对应的usid表
                    data_values = {
                        'index' : f"{st.session_state['ticker_selected']}_{st.session_state['strike_price']}{st.session_state['options_type'][0]}_{st.session_state['expired_date'].strftime('%y/%m/%d')}_{st.session_state['target_value']}",
                        'types': st.session_state['selected_type'],
                        'ticker': st.session_state['ticker_selected'],
                        'otypes': st.session_state['options_type'],
                        'exp_date': st.session_state['expired_date'],
                        'strike': st.session_state['strike_price'],
                        'tvalue': st.session_state['target_value'],
                        #'Edate': st.session_state['data_date_end'], #让用户自己选择，默认两个月内
                        #'Bdate': st.session_state['data_date_begin']
                    }

                    login_control(method = "cross_list_write", user_cookies = user_cookies, data_values = data_values)
                    st.write("Options added successfully")
                    st.experimental_rerun()                
        with col11:
            if st.button('Remove'):
                rr = login_control(method= "cross_list_delete", user_cookies= user_cookies, clindex= selected_row['index'])
                st.write('Options removed sucessfully')
                st.write(selected_row['index'])
                st.experimental_rerun()
        
        # Check if df is None
        if df is not None:
            # 设置图表标题
            chart_title = f"{st.session_state['ticker_selected']} {st.session_state['strike_price']} {st.session_state['options_type']} - Expired date: {st.session_state['expired_date']} - date range: {st.session_state['data_date_begin']} to {st.session_state['data_date_end']}                  From: options.fomostop.com"
            plot_trend1 = df.hvplot.scatter(
                        title = f"FlowTrend of {st.session_state['target_value']} - {chart_title}",
                        y=st.session_state['target_value'],
                        hover_cols=['Price', 'Initiator', 'Last', 'Volume', 'Open Int', 'OI Chg', 'IV', 'Delta', 'Time'],
                        xlabel= "Date",
                        ylabel= f"{st.session_state['target_value']}",
                        height=680,
                        width=980,
                        rot=90,
                        color='darkgreen',
                        yformatter="%.2f",
                    )
            plot_trend2 = df.hvplot.line(
                    y=st.session_state['target_value'],
                    hover_cols=['Price', 'Initiator', 'Last', 'Volume', 'Open Int', 'OI Chg', 'IV', 'Delta', 'Time'],
                    height=680,
                    width=980,
                    rot=90,
                )
            
            plot_trend = plot_trend1*plot_trend2

            # 在Streamlit应用程序中显示图表
            st.bokeh_chart(hv.render(plot_trend, backend="bokeh"))

            #展示df
            st.write('<h5 style="color: #ff5733;">Data detail:</h5>', unsafe_allow_html=True)
            st.dataframe(df)
    elif df is None:
        st.info("To see the trending activities of your stocks or ETF options, please input or select the appropriate parameters.😊" )
    else:
        # Handle the case where df is None, for example, display an error message
        st.write(df)
        st.info("To track your stocks or ETF options, just enter or choose the right settings.")




