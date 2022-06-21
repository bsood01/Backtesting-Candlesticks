import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandas_datareader.data as pdr
from datetime import timedelta,datetime as dt
import time
import os
import glob
import threading


# threading 
#takes in the array of stocks and returns a Dataframe associated with each in a dictionary
def yahoo_data(symbol, date_from, date_to):
    
    #store each dataframe to be accessed by stock's symbol
    result={}
    for s in symbol:
        df = pdr.DataReader(s, 'yahoo', start=date_from, end=date_to)
        #Remove rows where stock data is missing 
        df.dropna()
        result[s]=df
    return result

def csv_data(date_from, stock_list):
    path=os.getcwd()
    path = path+ "\\historical_data"
    all_files = glob.glob(os.path.join(path, "*.csv"))
    #file name
    col_list=["Date","Open","High","Low","Close"]
    result={}
    for f in all_files:
        #get the symbol for the dictionary to store data
        file_name=f.split("\\")[-1]
        symbol = file_name.split('.csv')[0]
        if symbol in stock_list:
            df = pd.read_csv(f,usecols=col_list)
            #set date as index and make data frame after param date
            df.set_index("Date",inplace = True)
            df.index = pd.to_datetime(df.index)  
            df=df[(df.index > date_from)]
            #Remove rows where stock data is missing 
            df.dropna()

            result[symbol]=df


    return result
#backtest for a single stock for the indicators
def backtest_stratergy(df,symbol,signal_list):
    signals=[]
    test_dates=df.index.tolist()
    for date in test_dates:
        tmp=candlestick_indicators(df,date,symbol)
        #if we found a signal add it to our results dictinary
        if tmp !=None:
            signals.append(tmp)
    signals_list.extend(signals)
    return 

     

def candlestick_indicators(df,date, symbol):

    signal={}
    trend=line_trend(df,date,20)
    signal["Symbol"]=symbol
    if trend==0 and dragonfly_doji(df, date):
        signal["Date"]=date
        signal["Indicator"]="Dragonfly Doji"
        signal["Reversal"]=True
        signal["ConfirmationRequired"]=True
        signal["NextCandle"]="HigherOpen"
        signal["EntryPrice"]=df.loc[date]["Close"]
        signal["TrendDirection"]="Down Trend"
        signal["StopLoss"]=df.loc[date]["Low"]
        signal["TakeProfit"]=signal["EntryPrice"]+2*(signal["EntryPrice"]-signal["StopLoss"])
        signal["Position"]="Long"
        signal["Variant"]=["SlopeTrend","2:1ProfitRatio","NoConfirmation","SL-Low"]
        test_long_indication(df,date,signal)

        return signal

    elif trend==1 and gravestone_doji(df,date):
        signal["Date"]=date
        signal["Indicator"]="Gravstone Doji"
        signal["Reversal"]=True
        signal["ConfirmationRequired"]=True
        signal["NextCandle"]="LowerOpen"
        signal["EntryPrice"]=df.loc[date]["Close"]
        signal["TrendDirection"]="Up Trend"
        signal["StopLoss"]=df.loc[date]["High"]
        signal["TakeProfit"]=signal["EntryPrice"]-2*(signal["StopLoss"]-signal["EntryPrice"])
        signal["Position"]="Short"
        signal["Variant"]=["SlopeTrend","2:1ProfitRatio","NoConfirmation","SL-High"]
        test_short_indication(df,date,signal)

        return signal

    return None

def test_long_indication(df, indication_date, signal_dict ):
    tmp_date= indication_date
    #3 months, 75 day cuttoff - conditional exit 
    # percentage gain- distributed 
    # days to exit for average return
    for i in range(75):
        index=df.index.get_loc(tmp_date) + 1
        if index < df.index.size:
            tmp_date=df.index[index]
            if df.loc[tmp_date,'Open']<=signal_dict["StopLoss"]:
                signal_dict["ExitPrice"]=df.loc[tmp_date,'Open']
                signal_dict["Win"]=False
                signal_dict["ExitDate"]=tmp_date
                return signal_dict
            elif df.loc[tmp_date,'Low']<=signal_dict["StopLoss"]:
                signal_dict["ExitPrice"]=signal_dict["StopLoss"]
                signal_dict["Win"]=False
                signal_dict["ExitDate"]=tmp_date
                return signal_dict
            elif df.loc[tmp_date,'Open']>=signal_dict["TakeProfit"]:
                signal_dict["ExitPrice"]=df.loc[tmp_date,'Open']
                signal_dict["Win"]=True
                signal_dict["ExitDate"]=tmp_date
                return signal_dict
            elif df.loc[tmp_date,'High']>=signal_dict["TakeProfit"]:
                signal_dict["ExitPrice"]=signal_dict["TakeProfit"]
                signal_dict["Win"]=True
                signal_dict["ExitDate"]=tmp_date
                return signal_dict
        #we dont have further data
        else:
            return signal_dict

    #exit after 75 days
    signal_dict["ExitPrice"]=df.loc[tmp_date,'Close']
    signal_dict["Win"]=signal_dict["ExitPrice"]>signal_dict["EntryPrice"]
    signal_dict["ExitDate"]=tmp_date
    return signal_dict

def test_short_indication(df, indication_date, signal_dict ):
    tmp_date= indication_date
    #3 months, 75 day cuttoff - conditional exit 
    # percentage gain- distributed 
    # days to exit for average return
    for i in range(75):
        index=df.index.get_loc(tmp_date) + 1
        if index < df.index.size:
            tmp_date=df.index[index]
            if df.loc[tmp_date,'Open']>signal_dict["StopLoss"]:
                signal_dict["ExitPrice"]=df.loc[tmp_date,'Open']
                signal_dict["Win"]=False
                signal_dict["ExitDate"]=tmp_date
                return signal_dict
            elif df.loc[tmp_date,'High']>signal_dict["StopLoss"]:
                signal_dict["ExitPrice"]=signal_dict["StopLoss"]
                signal_dict["Win"]=False
                signal_dict["ExitDate"]=tmp_date
                return signal_dict
            elif df.loc[tmp_date,'Open']<signal_dict["TakeProfit"]:
                signal_dict["ExitPrice"]=df.loc[tmp_date,'Open']
                signal_dict["Win"]=True
                signal_dict["ExitDate"]=tmp_date
                return signal_dict
            elif df.loc[tmp_date,'Low']<signal_dict["TakeProfit"]:
                signal_dict["ExitPrice"]=signal_dict["TakeProfit"]
                signal_dict["Win"]=True
                signal_dict["ExitDate"]=tmp_date
                return signal_dict
        #we dont have further data
        else:
            return signal_dict

    #exit after 75 days
    signal_dict["ExitPrice"]=df.loc[tmp_date,'Close']
    signal_dict["Win"]=signal_dict["ExitPrice"]<signal_dict["EntryPrice"]
    return signal_dict


    return 0
    
# Calculates trend based on updays vs downdays
def up_down_trend(df,date):
    ccur_date=df.index[df.index.get_loc(date)-1]
    up_days=0
    down_days=0
    for i in range(10):
        prev_row=df.index.get_loc(cur_date)-1
        if(prev_row>=0):
            prev_date=df.index[prev_row]
            if(df.loc[cur_date]["Close"]>df.loc[prev_date]["Close"]):
                up_days+=1
            elif(df.loc[cur_date]["Close"]>df.loc[prev_date]["Close"]):
                down_days+=1

        #update to previous date for next loop
        cur_date=df.index[df.index.get_loc(cur_date)-1]
    if(up_days>down_days):
        return 1
    elif(up_days<down_days):
        return 0
    else:
        return 2

#returns the trend based on line of best fit of closing price if last x days
def line_trend(df, date, days):

    x=[]
    y=[]
    cur_date=df.index[df.index.get_loc(date)-1]
    for i in range(days):
        if cur_date in df.index:
            x.append(days-1-i)
            y.append(df.loc[cur_date]["Close"])
            cur_date=df.index[df.index.get_loc(cur_date)-1]

    slope, intercept= np.polyfit(x, y, 1)
    if slope>0:
        return 1
    elif slope<0:
        return 0
    else:
        return 2

# Calculates the EMA based on the closing price and period (Eg. 10days)
def ema(df, period ):
    #picking alpha=2
    multiplier=2/(period+1)
    sum=0
    ema_list=[]
    #first EMA is simple moving average of firdt 10 values
    for i in range(period):
        sum+=df.iloc[i]["Close"]
        ema_list.append(0)
    ema_list[period-1]=sum/period    

    for i in range(period,len(df.index)):
        #EMA = Closing price x multiplier + EMA (previous day) x (1-multiplier)
        ema=(df.iloc[i]["Close"]*multiplier)+(ema_list[i-1]*(1-multiplier))
        ema_list.append(ema)

    df["EMA"]=ema_list   
    return df

def doji(df, date):
    rb = real_body(df,date)
    tl=total_length(df,date)
    if rb<0.1*tl:
        return 1 
    return 0 

#returns true if dragonfly doji is idicated
def dragonfly_doji(df, date):

    op=df.loc[date,'Open']
    cl=df.loc[date,'Close']
    hi=df.loc[date,'High']

    #check for small top shadow
    df_doji= (hi-max(op,cl)<=total_length(df,date)*0.1)

    #and opperator
    if df_doji and doji(df,date):
        return 1

    return 0

#returns true if gravestone doji is idicated
def gravestone_doji(df, date):

    op=df.loc[date,'Open']
    cl=df.loc[date,'Close']
    lo=df.loc[date,'Low']

    #check for small top shadow
    gr_doji= (min(op,cl)-lo<=total_length(df,date)*0.1)

    if   gr_doji and doji(df,date):
        return 1

    return 0

# Return the real body of a particular date
def real_body(data, date):

    op=data.loc[date,'Open']
    cl=data.loc[date,'Close']

    return abs(op-cl)

# Return the total lenght of a particular date
def total_length(data, date):
    hi=data.loc[date,'High']
    lo=data.loc[date,'Low']

    return hi-lo

# Return the ratio of the top shadow to the total body
def top_shadow(data, date):
    op=data.loc[date,'Open']
    cl=data.loc[date,'Close']
    hi=data.loc[date,'High']
    lo=data.loc[date,'Low']

    if hi==lo:
        return 0
    ts = (hi-max(op,cl))/(hi-lo)
    return ts

# Return the ratio of the bottom shadow to the total body
def bottom_shadow(data, date):

    op=data.loc[date,'Open']
    cl=data.loc[date,'Close']
    hi=data.loc[date,'High']
    lo=data.loc[date,'Low']

    if hi==lo:
        return 0
    bs = abs(lo-min(op,cl))/(hi-lo)
    return bs

def pretty(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key))
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print('\t' * (indent+1) + str(value))    

#global variable for threading
signals_list=[]

def main():
    #nifty 50
    #threads
    df = pd.read_csv("nifty50list.csv",encoding= 'unicode_escape')
    stock_list=df["Symbol"].values.tolist()
    '''df = pd.read_csv("allstocks.csv",encoding= 'unicode_escape')
    for index, row in df.iterrows():
        if row['N']==True:
            stock_list.append(row['NSESymbol'])'''
    st=[]
    for i in range(3,7):
        st.append(stock_list[i])
    #a Dict with Data frames of all the stocks
    start_time = time.time()
    stocks=csv_data(date_from='2012-01-01', stock_list=st)
    print("--- %s seconds ---" % (time.time() - start_time))

    path=os.getcwd()
    path = path+ "\\backtest_results"
    if not os.path.exists(path):
        os.makedirs(path)
    start_time = time.time()
    threads = []
    for symbol in stocks:
        thread = threading.Thread(target=backtest_stratergy,args=(stocks[symbol],symbol,signals_list))
        threads.append(thread)
        thread.start()
    #wait for them to finish
    for t in threads:
        t.join()
    print("--- %s seconds ---" % (time.time() - start_time))
    pd.DataFrame(signals_list).to_csv(path+"\\results.csv", encoding='utf-8', index=False)

    return 0

if __name__ == '__main__':
    main()
