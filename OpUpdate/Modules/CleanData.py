# Import required libraries
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
pd.options.mode.chained_assignment = None  # default='warn'

# Create the function for clean data acquire.
def get_data(date,types,DTE):
        """
         DTE is String type, 
         DTE can be 'min' or number of the DTE.(1,2,3,4......)
         types is String type, 
         types has two types, 'stocks' or 'etfs'
         date type is String , 
         date format is MM-DD-YYYY , for example '09-13-2022'
        """
        # acquire system path of the current file, join it with the related path of the csv file path.
        increase_path = os.path.join(os.path.dirname(__file__), f'../Data/Increase/{types}-increase-change-in-open-interest-{date}.csv')
        decrease_path = os.path.join(os.path.dirname(__file__), f'../Data/Decrease/{types}-decrease-change-in-open-interest-{date}.csv')
        
        #read csv files
        increase = pd.read_csv(Path(increase_path))
        decrease = pd.read_csv(Path(decrease_path))

        # Convert 'Strike' column to float64 in the Decrease DataFrame
        increase[['OI Chg', 'Strike']] = increase[['OI Chg', 'Strike']].replace({',': '', 'unch': '0', r'\*': ''}, regex=True).astype(float)
        decrease[['OI Chg', 'Strike']] = decrease[['OI Chg', 'Strike']].replace({',': '', 'unch': '0', r'\*': ''}, regex=True).astype(float)
        
        #combine increase and decrease data
        combine_df = increase.merge(decrease, how= 'outer')

        #Calculate DTE if there is no DTE in the dataframe
        # Only calculate DTE if the column does not already exist
        if 'DTE' not in combine_df.columns:
            # Convert the expiration date column to datetime objects
            combine_df['Exp Date'] = pd.to_datetime(combine_df['Exp Date'], format='%Y-%m-%d')

            # Get today's date (normalized to midnight, to match date granularity)
            today = pd.Timestamp.today().normalize()  # Or use datetime.today().date()

            # Calculate DTE (Days to Expiration) as the difference in days
            combine_df['DTE'] = (combine_df['Exp Date'] - today).dt.days
        
        #Select the DTE
        if DTE == 'min':
            combine_min_DTE = combine_df[combine_df['DTE'] == combine_df['DTE'].min()]
        elif DTE == 'max':
            combine_min_DTE = combine_df[combine_df['DTE'] <= combine_df['DTE'].max()]
        else:
            combine_min_DTE = combine_df[combine_df['DTE'] <= DTE]

        #Clean the NA data
        combine_min_DTE = combine_min_DTE.dropna()
        
        # Transfer columns 'OI Chg' and 'Strike' datatype from str to float.
        combine_min_DTE[['OI Chg', 'Strike']] = combine_min_DTE[['OI Chg', 'Strike']].replace({',': '', 'unch': '0', r'\*': ''}, regex=True).astype(float)

        
        #Transfer column 'IV'datatype from str to float.
        combine_min_DTE['IV'] = combine_min_DTE['IV'].str.replace('%', '').str.replace(',', '').astype(float)/100
        
        #Sorted by orders 'Symbol','Type','Strike','Open Int','Volume','OI Chg','IV'.
        combine_sort_df = combine_min_DTE.sort_values(['Symbol','Type','Strike','Open Int','Volume','OI Chg','IV'])

        # 5）Midpoint & pseudo‑Last utilized OI to micmic Last
        combine_sort_df['Midpoint'] = (combine_sort_df['Bid'] + combine_sort_df['Ask']) / 2
        # ---------- 生成 Last（按 OI Chg 强度在 [Bid,Ask] 连续插值，并保留两位小数） ----------
        max_abs_oi = combine_sort_df['OI Chg'].abs().max() or 1  # 防止除零
        combine_sort_df['Last'] = combine_sort_df.apply(lambda r: 
            round(
                (r['Midpoint'] + (abs(r['OI Chg'])/max_abs_oi)*(r['Ask']-r['Midpoint']))
                if r['OI Chg'] > 0
                else (
                    (r['Midpoint'] - (abs(r['OI Chg'])/max_abs_oi)*(r['Midpoint']-r['Bid']))
                    if r['OI Chg'] < 0
                    else r['Midpoint']
                )
            , 2)
        , axis=1)
        # -------------------------------------------------------------------
        
        # Rename Price~ to Price
        combine_sort_df = combine_sort_df.rename(columns={'Price~':'Price'})

        # Reorder columns
        column_order = ['Symbol', 'Price', 'Type', 'Strike', 'Exp Date', 'DTE', 'Bid', 'Midpoint', 'Ask', 'Last', 'Volume', 'Open Int', 'OI Chg', 'Delta', 'IV', 'Time']
        combine_sort_df = combine_sort_df[column_order]
        
        # return data
        return combine_sort_df
