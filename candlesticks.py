from matplotlib.pyplot import close
from numpy import single
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
        #missing data
        #df['signal']=df['Open']*0
        result[s]=df
    return result

def csv_data(date_from):
    path=os.getcwd()
    path = path+ "\data_files"
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
    signals={}
    test_dates=df.index.tolist()
    for date in test_dates:
        tmp=single_candlestick_indicators(df,date)
        #if we found a signal add it to our results dictinary
        #No. of signals 
        if tmp !=None:
            signals.update(tmp)
    print(signals)
    return 0

def candlestick_indicators(df,date):

    return 0

def single_candlestick_indicators(df,date):
    
    #doji_dates=[]
    rb=real_body(df,date)
    ts=top_shadow(df,date)
    bs=bottom_shadow(df,date)

    signal={}
    signal[date]={}

    if dragonfly_doji(rb,bs,ts):
        # Symbol
        signal[date]["Indicator"]="Dragonfly Doji"
        #check if we have data for the next date
        index=df.index.get_loc(date) + 1
        if index < df.index.size:
            #close of today
            # stop loss is low of the day
            signal[date]["Entry Price"]=df.loc[df.index[index],'Open']
        else:
            ## Assume no volatility, as close to end of day 
            signal[date]["Entry Price"]=None

            #signal direction
            #{"Pattern"}=reversal
            #["Confirmation"]=0/1

        signal[date]["Signal"]="Long"

        #check for the next 10 days
        signal = test_buy_indication(df,date,signal)
        return signal

    return None

#test the long position indication for the next 10-days
def test_buy_indication(df, indication_date, result_dict ):

    #curent candles low
    stop_loss=result_dict[indication_date]["Entry Price"] * 0.95
    take_profit=result_dict[indication_date]["Entry Price"] * 1.1

    tmp_date= indication_date
    #3 months, 75 cuttoff - conditional exit 
    for i in range(10):
        index=df.index.get_loc(tmp_date) + 1
        if index < df.index.size:
            tmp_date=df.index[index]

            #check the next days highs and lows for exit condition
            if df.loc[tmp_date,'High']>take_profit:
                result_dict[indication_date]["ExitPrice"]=take_profit
                result_dict[indication_date]["Conclusion"]="Win"
                result_dict[indication_date]["Exit Date"]=tmp_date
                return result_dict #we don't need to check further


            #priority 
            # cannot be stop loss. 
            # open 
            # percentage gain- distributed 
            # days to exit for average return

            elif df.loc[tmp_date,'Low']<stop_loss:
                result_dict[indication_date]["Exit Price"]=stop_loss
                result_dict[indication_date]["Conclusion"]="Loss"
                result_dict[indication_date]["Exit Date"]=tmp_date
                return result_dict  #we don't need to check further


        # no further data to be checked index is past the data we have
        else:
            result_dict[indication_date]["Conclusion"]="Inconclusive"
            return result_dict

    # If we made it through 10 days without a sell signal or exitting
    # The indication was inconclusive
    result_dict[indication_date]["Conclusion"]="Inconclusive"
    return result_dict

#test the short position indication for the next 10-days
def test_sell_indication(df, indication_date, result_dict ):
    stop_loss=result_dict[indication_date]["Entry Price"] * 1.05
    take_profit=result_dict[indication_date]["Entry Price"] * 0.9

    tmp_date= indication_date
    for i in range(10):
        index=df.index.get_loc(tmp_date) + 1
        if index < df.index.size:
            tmp_date=df.index[index]

            #check the next days highs and lows for exit condition
            if df.loc[tmp_date,'High']>stop_loss:
                result_dict[indication_date]["Exit Price"]=stop_loss
                result_dict[indication_date]["Conclusion"]="Loss"
                result_dict[indication_date]["Exit Date"]=tmp_date
                return result_dict  #we don't need to check further

            elif df.loc[tmp_date,'Low']<take_profit:
                result_dict[indication_date]["ExitPrice"]=take_profit
                result_dict[indication_date]["Conclusion"]="Win"
                result_dict[indication_date]["Exit Date"]=tmp_date
                return result_dict #we don't need to check further


        # no further data to be checked index is past the data we have
        else:
            result_dict[indication_date]["Conclusion"]="Inconclusive"
            return result_dict

    # If we made it through 10 days without a sell signal or exitting
    # The indication was inconclusive
    result_dict[indication_date]["Conclusion"]="Inconclusive"
    return result_dict


#returns true if dragonfly doji is idicated
def dragonfly_doji(rb,bs,ts):
    # Cannot be random 
    # Trend- best fit line- updays vs down days - MA
    # Date and DF

    if rb<0.10 and bs!=0 and (ts/bs)<0.15:
        return 1

    return 0

#returns true if gravestone doji is idicated
def gravestone_doji(rb,bs,ts):
    if rb<0.10 and ts!=0 and (bs/ts)<0.15:
        return 1

    return 0


# Return the ratio of the real body to the total body
def real_body(data, date):

    op=data.loc[date,'Open']
    cl=data.loc[date,'Close']
    hi=data.loc[date,'High']
    lo=data.loc[date,'Low']

    if hi==lo:
        return 0
    rb = abs(op-cl)/(hi-lo)
    #print(op,cl,hi,lo,rb)

    return rb

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
    for st in stocks:
        backtest_stratergy(stocks[st])

    return 0

if __name__ == '__main__':
    main()

