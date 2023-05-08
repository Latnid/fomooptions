import os
from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
import holoviews as hv
from CleanData import get_data

# Set page configuration
st.set_page_config(
    page_title="Daily options flow|Options fLow analyze|FOMOSTOP",
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
selected_date = st.sidebar.date_input("Select data date", value=pd.Timestamp.now(tz=pytz.timezone('US/Eastern')).date())
selected_data_type = st.sidebar.selectbox("Select data type", ["stocks", "etfs"])
selected_data_period = st.sidebar.selectbox('Days to expiration', ['min', 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,365])


# Get data based on user input
option_change = None

try:
    option_change = get_data(selected_date.strftime("%m-%d-%Y"), selected_data_type, selected_data_period)
    #Ticker selected
    ticker_options = option_change['Symbol'].unique().tolist()
    if 'ticker_selected' not in st.session_state:
        ticker_selected = st.sidebar.selectbox('Ticker', options=ticker_options)
        st.session_state['ticker_selected'] = ticker_selected

    elif st.session_state['ticker_selected'] not in option_change['Symbol'].unique():
        ticker_selected = st.sidebar.selectbox('Ticker', options=ticker_options)
        st.session_state['ticker_selected'] = ticker_selected

    else:
        ticker_selected = st.sidebar.selectbox('Ticker', options=ticker_options, index=ticker_options.index(st.session_state['ticker_selected']))
        st.session_state['ticker_selected'] = ticker_selected

    tz = pytz.timezone('US/Eastern')
    last_update_time = datetime.fromtimestamp(os.path.getmtime(os.path.join(os.path.dirname(__file__),f"../Data/Increase/stocks-increase-change-in-open-interest-{selected_date.strftime('%m-%d-%Y')}.csv")), tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    st.sidebar.write(f"Last update: {last_update_time}")


except FileNotFoundError:
    # Display a streamlit animation to notify the user that data is still being prepared
    st.warning("Data will be updated during market hours, see you later.")
    st.snow()

if option_change is not None:
    # Create DataFrame for all the required columns
    option_change_required = option_change[["Symbol", "Type", "Strike", "DTE", "Open Int", "OI Chg", "Volume", "Price", "IV"]]

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
    chart_title = '                                                            options.fomostop.com'
    # Top 20 symbols ranked by total open interest，Call / Put Open Interest comparation
    
    plot_top20OI = option_change_required_top_20.hvplot.bar(
        height=280,
        width=900,
        x="Symbol",
        xlabel="Symbol by Type",
        y="Open Int",
        ylabel="Open Interest",
        by="Type",
        hue=["Call","Put"], 
        color=['#FF5635', '#0AA638'], 
        hover_cols=["Strike", "DTE"],
        rot=90,
        yformatter="%0f",
        title=f"Total Open Interest(Call+Put) Top 20 {chart_title}",
        
        

    )# Top 20 Open Interest change
    plot_top20OI_chg = option_change_required_top_20.hvplot.bar(
        y="OI Chg",
        by="Type",
        hue=["Call","Put"], 
        color=['#FF5635', '#0AA638'],
        stacked=False,
        height=280,
        width=900,
        yformatter="%0f",
        rot=90,
        hover_cols=["Strike", "DTE"],
        xlabel="Tickers by Call and Put",
        ylabel="Open Interest Change",
        title= f"Tickers Call / Put Open Interests Change comparation {chart_title}",
    )


    #Open Int call put in one ticker
    plot_one_tickerOI = option_change[option_change['Symbol'] == ticker_selected].hvplot.bar(
        by='Type',
        hue=["Call","Put"], 
        color=['#0AA638','#FF5635'],
        x = 'Strike',
        y = 'Open Int',
        title = f'Open Int base on strike price - {ticker_selected} {chart_title}',
        hover_cols = ['Strike','DTE'],
        height=280,
        width=900, 
        rot = 90,
    )
    
    #Open Int call put in one ticker
    plot_one_tickerOI_change = option_change[option_change['Symbol'] == ticker_selected].hvplot.bar(
        x = 'Strike',
        y='OI Chg',
        by='Type',
        hue=["Call","Put"], 
        color=['#0AA638','#FF5635'],
        stacked=False,
        height=280,
        width=900, 
        yformatter='%0f',
        rot=90,
        hover_cols = ['Strike','DTE'],
        xlabel='Tickers by Call and Put',
        ylabel = 'Open Interest Change',
        title = f"Call / Put OI changed - {ticker_selected} {chart_title}"
    )


    # Show the Bokeh figure using st.bokeh_chart
    st.bokeh_chart(hv.render(plot_top20OI, backend="bokeh", use_container_width=True))
    st.bokeh_chart(hv.render(plot_top20OI_chg, backend="bokeh",use_container_width=True))
    st.bokeh_chart(hv.render(plot_one_tickerOI, backend="bokeh", use_container_width=True))
    st.bokeh_chart(hv.render(plot_one_tickerOI_change, backend="bokeh", use_container_width=True))
    
    
#Shows weblink if error happen.
else:
    st.markdown("[Fomostop.com](https://www.fomostop.com)")
