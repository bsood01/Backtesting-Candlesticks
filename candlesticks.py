import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandas_datareader.data as pdr
from datetime import timedelta,datetime as dt
import time
import os
import glob
import multiprocessing
import statistics

date_from='2012-01-01'
slope_days=15

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

def csv_data(symbol):
    path=os.getcwd()
    path = path+ "\\historical_data"
    data = glob.glob(os.path.join(path, symbol+".csv"))
    #file name
    col_list=["Date","Open","High","Low","Close"]
    #get the symbol for the dictionary to store data
    df = pd.read_csv(data[0],usecols=col_list)
    #set date as index and make data frame after param date
    df.set_index("Date",inplace = True)
    df.index = pd.to_datetime(df.index)  
    df=df[(df.index > date_from)]
    #Remove rows where stock data is missing 
    df.dropna()
    return df
#backtest for a single stock for the indicators
def backtest_stratergy(symbol,variants_dict):
    signals=[]
    df=csv_data(symbol)
    test_dates=df.index.tolist()
    for date in test_dates:
        for shadow in variants_dict["MaxShadow"]:
            for body in variants_dict["MaxBody"]:
                trend=line_trend(df,date,slope_days)
                if trend==0 and dragonfly_doji(df,date,shadow,body):
                    for pt_ratio in variants_dict["PTWinRatio"]:
                        for sl in variants_dict["SLAdjuster"]:
                            for confirm in  variants_dict["Confirmation"]:
                                tmp=candlestick_indicators(df,date,symbol,"Dragonfly Doji",
                                    pt_ratio,sl,confirm)
                                #if we found a signal add it to our results dictinary
                                if tmp!=None:
                                    tmp["MaxShadow"]=shadow
                                    tmp["MaxBody"]=body
                                    tmp["PTWinRatio"]=pt_ratio
                                    tmp["SLRatio"]=sl
                                    tmp["Confirmation"]=confirm
                                    signals.append(tmp)
                elif trend==1 and gravestone_doji(df,date,shadow,body):
                    for pt_ratio in variants_dict["PTWinRatio"]:
                        for sl in variants_dict["SLAdjuster"]:
                            for confirm in  variants_dict["Confirmation"]:
                                tmp=candlestick_indicators(df,date,symbol,"Gravestone Doji",
                                    pt_ratio,sl,confirm)
                                if tmp!=None:
                                    tmp["MaxShadow"]=shadow
                                    tmp["MaxBody"]=body
                                    tmp["PTWinRatio"]=pt_ratio
                                    tmp["SLRatio"]=sl
                                    tmp["Confirmation"]=confirm
                                    signals.append(tmp)

    return signals

     

def candlestick_indicators(df,date,symbol,indicator, pt_ratio,sl_ratio,con_req):

    signal={}
    signal["Symbol"]=symbol
    if indicator=="Dragonfly Doji":
        signal["Date"]=date
        signal["Indicator"]="Dragonfly Doji"
        if not con_req:
            signal["EntryPrice"]=df.loc[date]["Close"]
            
        #confirmation is required and check for higher open 
        else:
            next_date=df.index[df.index.get_loc(date)+1]
            if df.loc[next_date]["Open"]>df.loc[date]["Close"]:
                signal["EntryPrice"]=df.loc[next_date]["Open"]
            else:
                return None
        signal["StopLoss"]=df.loc[date]["Low"]*(1-sl_ratio)
        signal["TakeProfit"]=signal["EntryPrice"]+pt_ratio*(signal["EntryPrice"]-signal["StopLoss"])
        signal["Position"]="Long"
        test_long_indication(df,date,signal)
        signal["ReturnsPercent"]=(signal["ExitPrice"]-signal["EntryPrice"])/signal["EntryPrice"]
        return signal

    elif indicator =="Gravestone Doji":
        signal["Date"]=date
        signal["Indicator"]="Gravstone Doji"
        if not con_req:
            signal["EntryPrice"]=df.loc[date]["Close"]
        #confirmation is required and check for lower open 
        else:
            next_date=df.index[df.index.get_loc(date)+1]
            if df.loc[next_date]["Open"]<df.loc[date]["Close"]:
                signal["EntryPrice"]=df.loc[next_date]["Open"]
            else:
                return None
        signal["StopLoss"]=df.loc[date]["High"]*(1+sl_ratio)
        signal["TakeProfit"]=signal["EntryPrice"]-pt_ratio*(signal["StopLoss"]-signal["EntryPrice"])
        signal["Position"]="Short"
        test_short_indication(df,date,signal)
        signal["ReturnsPercent"]=(signal["EntryPrice"]-signal["ExitPrice"])/signal["EntryPrice"]
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
            signal_dict["ExitPrice"]=df.loc[tmp_date,'Close']
            signal_dict["Win"]=signal_dict["ExitPrice"]>signal_dict["EntryPrice"]
            signal_dict["ExitDate"]=tmp_date
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
            signal_dict["ExitPrice"]=df.loc[tmp_date,'Close']
            signal_dict["Win"]=signal_dict["ExitPrice"]>signal_dict["EntryPrice"]
            signal_dict["ExitDate"]=tmp_date
            return signal_dict

    #exit after 75 days
    signal_dict["ExitPrice"]=df.loc[tmp_date,'Close']
    signal_dict["Win"]=signal_dict["ExitPrice"]<signal_dict["EntryPrice"]
    return signal_dict

    
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

def doji(df, date, max_body):
    rb = real_body(df,date)
    tl=total_length(df,date)
    if rb<max_body*tl:
        return 1 
    return 0 

#returns true if dragonfly doji is idicated
def dragonfly_doji(df, date, max_shadow, max_body):

    op=df.loc[date,'Open']
    cl=df.loc[date,'Close']
    hi=df.loc[date,'High']

    #check for small top shadow
    df_doji= (hi-max(op,cl)<=total_length(df,date)*max_shadow)

    #and opperator
    if df_doji and doji(df,date,max_body):
        return 1

    return 0

#returns true if gravestone doji is idicated
def gravestone_doji(df, date, max_shadow, max_body):

    op=df.loc[date,'Open']
    cl=df.loc[date,'Close']
    lo=df.loc[date,'Low']

    #check for small top shadow
    gr_doji= (min(op,cl)-lo<=total_length(df,date)*max_shadow)

    if   gr_doji and doji(df,date,max_body):
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

#only the main procs writes to the signals_list
def log_result(signals): 
    if signals!=None:
        return signals_list.extend(signals)
    return

def calculate_metrics(signals_list, variants_dict):
    results_dict={}
    
    for shadow in variants_dict["MaxShadow"]:
        for body in variants_dict["MaxBody"]:
            for pt_ratio in variants_dict["PTWinRatio"]:
                for sl in variants_dict["SLAdjuster"]:
                    for confirm in  variants_dict["Confirmation"]:
                        variant=str(shadow)+"/"+str(body)+"/"+str(pt_ratio)+"/"+str(sl)+"/"+str(confirm)+"/"+"Dragonfly Doji"
                        results_dict[variant]={"MaxShadow":shadow,
                                            "MaxBody":body,
                                            "PTWinRatio":pt_ratio,
                                            "SLAdjuster":sl,
                                            "Confirmation":confirm,
                                            "NumWins":0,
                                            "TotalSignals":0,
                                            "Returns":[]
                                         }
                        variant=str(shadow)+"/"+str(body)+"/"+str(pt_ratio)+"/"+str(sl)+"/"+str(confirm)+"/"+"Gravestone Doji"
                        results_dict[variant]={ "MaxShadow":shadow,
                                        "MaxBody":body,
                                        "PTWinRatio":pt_ratio,
                                        "SLAdjuster":sl,
                                        "Confirmation":confirm,
                                        "NumWins":0,
                                        "TotalSignals":0,
                                        "Returns":[]
                        }
    for signal in signals_list:
        variant=str(signal["MaxShadow"])+"/"+str(signal["MaxBody"])+"/"+\
            str(signal["PTWinRatio"])+"/"+str(signal["SLRatio"])+"/"+str(signal["Confirmation"])+"/"+signal["Indicator"]
        if variant in results_dict:
            if signal["Win"]:
                results_dict[variant]["NumWins"]+=1
            results_dict[variant]["TotalSignals"]+=1
            results_dict[variant]["Returns"].append(signal["ReturnsPercent"])
                
    for variant in results_dict:
        if len(results_dict[variant]["Returns"])>=2:
            results_dict[variant]["AvgReturn"]=statistics.mean(results_dict[variant]["Returns"])
            results_dict[variant]["Median"]=statistics.median(results_dict[variant]["Returns"])
            results_dict[variant]["StdDev"]=statistics.stdev(results_dict[variant]["Returns"])
            results_dict[variant]["WinRatio"]=results_dict[variant]["NumWins"]/results_dict[variant]["TotalSignals"]
            results_dict[variant]["MaxWin"]=max(results_dict[variant]["Returns"])
            results_dict[variant]["MaxLoss"]=min(results_dict[variant]["Returns"])
        else:
            results_dict[variant]["AvgReturn"]=None
            results_dict[variant]["Median"]=None
            results_dict[variant]["StdDev"]=None
            results_dict[variant]["WinRatio"]=None
            results_dict[variant]["MaxWin"]=None
            results_dict[variant]["MaxLoss"]=None

        del results_dict[variant]["Returns"]
    return results_dict


#global variable for multiprocessing
signals_list=[]
def main():
    #nifty 50
    df = pd.read_csv("nifty50list.csv",encoding= 'unicode_escape')
    stock_list=df["Symbol"].values.tolist()
    st=[]
    for i in range(3,4):
        st.append(stock_list[i])

    path=os.getcwd()
    path = path+ "\\backtest_results"
    if not os.path.exists(path):
        os.makedirs(path)
    variants={"PTWinRatio":[1,2,3,1/2,1/3],
              "Confirmation":[True,False],
              "MaxShadow":[0.05,0.075,0.1,0.125,0.15],
              "MaxBody":[0.05,0.075,0.1,0.125,0.15],
              "SLAdjuster":[0,0.01,0.02,0.03,0.04,0.05]
    }

    #start_time = time.time()
    num_procs = multiprocessing.cpu_count()  
    pool = multiprocessing.Pool(num_procs-2)
    for symbol in stock_list:
        pool.apply_async(backtest_stratergy,args=(symbol,variants),callback=log_result)
    #wait for them to finish
    pool.close()
    pool.join()
    #print("--- %s seconds ---" % (time.time() - start_time))
    #pd.DataFrame(signals_list).to_csv(path+"\\results.csv", encoding='utf-8', index=False)
    result=pd.DataFrame.from_dict(calculate_metrics(signals_list, variants)).T
    result.index.name = 'Variant'
    result.to_csv(path+"\\metrics.csv", encoding='utf-8',index=False)
    #
    #Variant: [MaxShadow]/[MaxBody]/[PTWinRatio]/[SLRatio]/[Confirmation]/[Indicator]
    #
    return 0

if __name__ == '__main__':
    main()
