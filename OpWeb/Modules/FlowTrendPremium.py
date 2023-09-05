import numpy as np
from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import holoviews as hv
from Modules.DataBaseFlow import *
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
            st.session_state['ticker_selected'] = st.session_state.ticker_selected.upper()

        def ticker_init():
            st.session_state['ticker_selected'] = st.session_state.ticker_init

    with col2:
        if 'ticker_selected' not in st.session_state:
            ticker_selected = st.text_input('Ticker', key='ticker_init', on_change=ticker_init, value= 'AAPL')
            st.session_state['ticker_selected'] = ticker_selected
        else:
            ticker_selected = st.text_input('Ticker', key='ticker_selected', on_change=ticker_select, value=st.session_state['ticker_selected'])


    # 使用 Streamlit 的 columns 函数创建两列布局给 options_type 和 expired_date 并排使用
    col3, col4 = st.sidebar.columns(2)
    # 在第一列中放置第一个 selectbox
    # 定义回调函数，用于处理 st.session['options_type']
    def options_type():
        st.session_state['options_type'] = st.session_state.options_type

    def options_type_init():
        st.session_state['options_type'] = st.session_state.options_type_init

    with col3:
        if 'options_type' not in st.session_state:
            selected_options_type = st.selectbox("Options type", ['Call', 'Put'], key='options_type_init', on_change=options_type_init)
            st.session_state['options_type'] = selected_options_type
        else:
            selected_options_type = st.selectbox("Options type", ['Call', 'Put'], key='options_type', on_change=options_type, index=['Call', 'Put'].index(st.session_state['options_type']))

    # 在第二列中放置第二个 selectbox
    # 定义回调函数，用于处理 st.session['expired_date']
    def expired_date():
        st.session_state['expired_date'] = st.session_state.expired_date

    def expired_date_init():
        st.session_state['expired_date'] = st.session_state.expired_date_init
    with col4:
        if 'expired_date' not in st.session_state:
            selected_expired_date = st.date_input('Expired date', value=pd.Timestamp.now(tz=pytz.timezone('US/Eastern')).date(), key="expired_date_init", on_change=expired_date_init)
            st.session_state['expired_date'] = selected_expired_date
        else:
            selected_expired_date = st.date_input('Expired date', value=st.session_state['expired_date'], key="expired_date", on_change=expired_date)

    # 使用 Streamlit 的 columns 函数创建两列布局给 Strike price 和 Target value 并排使用
    col5, col6 = st.sidebar.columns(2)

    # 定义回调函数，用于处理 st.session['strike_price']
    with col5:
        def strike_price():
            st.session_state['strike_price'] = st.session_state.strike_price

        def strike_price_init():
            st.session_state['strike_price'] = st.session_state.strike_price_init

        if 'strike_price' not in st.session_state:
            selected_strike_price = st.number_input('Strike price', key = 'strike_price_init', on_change=strike_price_init)
            st.session_state['strike_price'] = selected_strike_price
        else:
            selected_strike_price = st.number_input('Strike price', value= st.session_state['strike_price'], key = 'strike_price', on_change=strike_price)

    #显示在Y轴的值
    # 定义回调函数，用于处理 st.session['target_value']
    with col6:
        def target_value():
            st.session_state['target_value'] = st.session_state.target_value

        def target_value_init():
            st.session_state['target_value'] = st.session_state.target_value_init

        if 'target_value' not in st.session_state:
            selected_target_value = st.selectbox('Target Value(y)', ['Volume','Open Int','OI Chg','IV','Bid', 'Midpoint', 'Ask', 'Last'], key = 'target_value_init', on_change=target_value_init)
            st.session_state['target_value'] = selected_target_value
        else:
            selected_target_value = st.selectbox("Target Value(y)", ['Volume','Open Int','OI Chg','IV','Bid', 'Midpoint', 'Ask', 'Last'], key='target_value', on_change= target_value, index=['Volume','Open Int','OI Chg','IV','Bid', 'Midpoint', 'Ask', 'Last'].index(st.session_state['target_value']))




    # 使用 Streamlit 的 columns 函数创建两列布局给 data_date_begin 和 data_date_end 并排使用
    col7, col8 = st.sidebar.columns(2)
    # 在第一列中放置第一个 selectbox
    # 定义回调函数，用于处理 st.session['data_date_begin']
    def data_date_begin():
        st.session_state['data_date_begin'] = st.session_state.data_date_begin

    def data_date_begin_init():
        st.session_state['data_date_begin'] = st.session_state.data_date_begin_init

    with col7:
        if 'data_date_begin' not in st.session_state:
            selected_data_date_begin = st.date_input('Data date begin', value=pd.Timestamp.now(tz=pytz.timezone('US/Eastern')).date(), key="data_date_begin_init", on_change=data_date_begin_init)
            st.session_state['data_date_begin'] = selected_data_date_begin
        else:
            selected_data_date_begin = st.date_input('Data date begin', value=st.session_state['data_date_begin'], key="data_date_begin", on_change=data_date_begin)

    # 在第二列中放置第二个 selectbox
    # 定义回调函数，用于处理 st.session['data_date_end']
    def data_date_end():
        st.session_state['data_date_end'] = st.session_state.data_date_end

    def data_date_end_init():
        st.session_state['data_date_end'] = st.session_state.data_date_end_init
    with col8:
        if 'data_date_end' not in st.session_state:
            selected_data_date_end = st.date_input('Data date end', value=pd.Timestamp.now(tz=pytz.timezone('US/Eastern')).date(), key="data_date_end_init", on_change=data_date_end_init)
            st.session_state['data_date_end'] = selected_data_date_end
        else:
            selected_data_date_end = st.date_input('Data date end', value=st.session_state['data_date_end'], key="data_date_end", on_change=data_date_end)


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

    # Check if df is None
    if df is not None:
        st.write(st.session_state)

        # 设置图表标题
        chart_title = f"{st.session_state['ticker_selected']} {st.session_state['strike_price']} {st.session_state['options_type']} - Expired date: {st.session_state['expired_date']} - date range: {st.session_state['data_date_begin']} to {st.session_state['data_date_end']}                  From: options.fomostop.com"
        plot_trend1 = df.hvplot.scatter(
                    title = f"FlowTrend of {st.session_state['target_value']} - {chart_title}",
                    y=st.session_state['target_value'],
                    hover_cols=['Price', 'Initiator', 'Last', 'Volume', 'Open Int', 'OI Chg', 'IV', 'Time'],
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
                hover_cols=['Price', 'Initiator', 'Last', 'Volume', 'Open Int', 'OI Chg', 'IV', 'Time'],
                height=680,
                width=980,
                rot=90,
            )
        
        plot_trend = plot_trend1*plot_trend2

        # 在Streamlit应用程序中显示图表
        st.bokeh_chart(hv.render(plot_trend, backend="bokeh"))
    else:
        # Handle the case where df is None, for example, display an error message
        st.info("Input or select proper parameters")




