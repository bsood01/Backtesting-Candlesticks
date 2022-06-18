import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandas_datareader.data as pdr
from datetime import timedelta,datetime as dt
import time
import os
import glob

# threading 
#takes in the array of stocks and returns a Dataframe associated with each in a dictionary
def yahoo_data(symbol, date_from, date_to):
    
    #store each dataframe to be accessed by stock's symbol
    result={}
    for s in symbol:
        df = pdr.DataReader(s, 'yahoo', start=date_from, end=date_to)
        ##
        df.fillna(method="ffill")
        result[s]=df
    return result

def csv_data(date_from):
    path=os.getcwd()
    path = path+ "\\data_files"
    all_files = glob.glob(os.path.join(path, "*.csv"))

    col_list=["Date","Open","High","Low","Close","Volume"]
    result={}
    for f in all_files:
        df = pd.read_csv(f,usecols=col_list)
        #set date as index and make data frame after param date
        df.set_index("Date",inplace = True)
        df.index = pd.to_datetime(df.index)  
        df=df[(df.index > date_from)]
        #filling missing values using forward fill to avoid look-ahead bias
        df.fillna(method="ffill")

        #get the symbol for the dictionary to store data
        file_name=f.split("\\")[-1]
        symbol = file_name.split('.CSV')[0]
        result[symbol]=df

    return result

def backtest_stratergy(df):
    signals=[]
    test_dates=df.index.tolist()
    for date in test_dates:
        tmp=candlestick_indicators(df,date)
        #if we found a signal add it to our results dictinary
        #No. of signals 
        if tmp !=None:
            signals.append(tmp)
    #for d in signals:
        #pretty(d)
    return pd.DataFrame(signals)

     

def candlestick_indicators(df,date):

    # Volume???
    signal={}
    trend=line_trend(df,date)
    if dragonfly_doji(df, date) and trend==0:
        signal["Date"]=date
        signal["Indicator"]="Dragonfly Doji"
        signal["Reversal"]=True
        signal["ConfirmationRequired"]=False
        signal["NextCandle"]="NA"
        signal["EntryPrice"]=df.loc[date]["Close"]
        signal["TrendDirection"]="Down Trend"
        signal["StopLoss"]=df.loc[date]["Low"]
        #2:1 ratio for profit and stoploss
        signal["TakeProfit"]=signal["EntryPrice"]+2*(signal["EntryPrice"]-signal["StopLoss"])
        signal["Position"]="Long"
        test_long_indication(df,date,signal)

        return signal

    elif gravestone_doji(df,date) and trend==1:
        print(date)
        signal["Date"]=date
        signal["Indicator"]="Gravstone Doji"
        signal["Reversal"]=True
        signal["ConfirmationRequired"]=False
        signal["NextCandle"]="NA"
        signal["EntryPrice"]=df.loc[date]["Close"]
        signal["TrendDirection"]="Up Trend"
        signal["StopLoss"]=df.loc[date]["High"]
        #2:1 ratio for profit and stoploss
        signal["TakeProfit"]=signal["EntryPrice"]-2*(signal["StopLoss"]-signal["EntryPrice"])
        signal["Position"]="Short"
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
            if df.loc[tmp_date,'Open']<signal_dict["StopLoss"]:
                signal_dict["ExitPrice"]=df.loc[tmp_date,'Open']
                signal_dict["Win"]=False
                signal_dict["ExitDate"]=tmp_date
                return signal_dict
            elif df.loc[tmp_date,'Low']<signal_dict["StopLoss"]:
                signal_dict["ExitPrice"]=signal_dict["StopLoss"]
                signal_dict["Win"]=False
                signal_dict["ExitDate"]=tmp_date
                return signal_dict
            elif df.loc[tmp_date,'Open']>signal_dict["TakeProfit"]:
                signal_dict["ExitPrice"]=df.loc[tmp_date,'Open']
                signal_dict["Win"]=True
                signal_dict["ExitDate"]=tmp_date
                return signal_dict
            elif df.loc[tmp_date,'High']>signal_dict["TakeProfit"]:
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
    cur_date=date
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

#returns the trend based on line of best fit of closing price if last 10 days
def line_trend(df, date):

    x=[]
    y=[]
    cur_date=date
    for i in range(5):
        if cur_date in df.index:
            x.append(4-i)
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

    if doji(df,date) and df_doji:
        return 1

    return 0

#returns true if gravestone doji is idicated
def gravestone_doji(df, date):

    op=df.loc[date,'Open']
    cl=df.loc[date,'Close']
    lo=df.loc[date,'Low']

    #check for small top shadow
    gr_doji= (min(op,cl)-lo<=total_length(df,date)*0.1)

    if doji(df,date) and gr_doji:
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

def main():
    #a Dict with Data frames of all the stocks
    stocks=csv_data(date_from='2012-01-01')
    path=os.getcwd()
    path = path+ "\\backtest_results"
    if not os.path.exists(path):
        os.makedirs(path)
    for symbol in stocks:
        #date_time_str = '22/06/12 00:00:00'
        #date_time_obj = dt.strptime(date_time_str, '%d/%m/%y %H:%M:%S')
        #line_trend(stocks[symbol],date_time_obj)
        ema(stocks[symbol],10)
        #stocks[symbol].iloc[2100:2300]['Close'].plot(label = 'TCS', figsize = (15,7))
        #stocks[symbol].iloc[2100:2300]['EMA'].plot(label = "Infosys")
        #plt.show()
        backtest_stratergy(stocks[symbol]).to_csv(path+"\\"+symbol, encoding='utf-8', index=False)

    return 0

if __name__ == '__main__':
    main()
