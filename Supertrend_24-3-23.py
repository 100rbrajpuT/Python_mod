#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# pip install pandas_ta


# In[3]:


import pandas as pd
import pandas_ta as ta


# In[ ]:


df = pd.read_csv("sbin.csv")


# In[ ]:


df


# In[ ]:


ta.supertrend(high=df['High'],low = df['Low'],close = df['Close'], period=7, multiplier=3)


# In[ ]:


df['sup'] = ta.supertrend(high=df['High'],low = df['Low'],close = df['Close'], period=7, multiplier=3)['SUPERT_7_3.0']


# In[ ]:


df


# In[ ]:


df.tail(20)


# In[ ]:


df


# In[ ]:


df["Buy_Signal"] = 0
df["Sell_Signal"] = 0


# In[ ]:


df


# In[ ]:


# df["Timestamp"][2][1124]


# In[ ]:


df.iloc[-1]["Timestamp"]


# In[ ]:


n=6
for i in range(n, len(df)):
    if df["Close"][i-1] <= df['sup'][i-1] and df['Close'][i]>df['sup'][i]:
        df["Buy_Signal"][i] = 1
    if df["Close"][i-1] >= df['sup'][i-1] and df['Close'][i]<df['sup'][i]:
        df["Sell_Signal"][i] = 1
    


# In[ ]:


df[(df["Buy_Signal"]>0) | (df["Sell_Signal"]>0) ]


# In[ ]:


df.iloc[-1]["Timestamp"].split("+")[0].replace("T"," ")


# In[ ]:


df_time = df.iloc[-1]["Timestamp"].split("+")[0].replace("T"," ")
df_time


# In[ ]:


from dateutil import parser
interval=2
import datetime
last_time= df_time
    #         call data
#     df=supertrend calculate
#     get last line
#     assin last time to last_time
# list_time = "2023-03-17T15:29:00+0530"
while True:
    if str(datetime.datetime.now())>last_time+str(datetime.timedelta(minutes=5)):
#     if datetime.datetime.now()>last_time+datetime.timedelta(minutes=5):
        #         call data
#     df=supertrend calculate
#     get last line
#     assin last time to last_time
    
        
        print('running',datetime.datetime.now(),last_time)
        


# In[9]:


def getData(token, fromm, to, time_frame):
    
    data=re.get(f"https://api.kite.trade/instruments/historical/{token}/{time_frame}?from={fromm}&to={to}",headers=headers)
    df=pd.DataFrame(data.json()['data']['candles'])
    df.columns = ["Timestamp", "Open", "High", "Low","Close","Volume"]
#     df=supertrend(high=df['High'],low = df['Low'],close = df['Close'], period=7, multiplier=3)
#     calculate supertrend
#     df=calculatesuper(df,a,b)
    return df.iloc[-1]
    


# In[11]:


from dateutil import parser
import requests as re
API_KEY="rfnqn5jyts2ljcq1"
ACCESS_TOKEN="VkjKYp51T2TgvvHNPukdY5K2gRttR3W7"
headers={"X-Kite-Version":'3','Authorization':"token "+API_KEY+":"+ACCESS_TOKEN}


interval=3
import datetime,time

from_date = datetime.datetime.now()-datetime.timedelta(days=90)
to_date = datetime.datetime.now()-datetime.timedelta(minutes=interval)
if interval==1:
    time_frame = 'minute'
else:
    time_frame = str(interval)+'minute'
    
last_row = getData(5097729,from_date, to_date, time_frame )
last_time=last_row.Timestamp
print('running',datetime.datetime.now(),last_time,last_row)



while True:
    time.sleep(1)
    if str(parser.parse(last_time.replace("T"," "))+datetime.timedelta(minutes=interval*2))<str(datetime.datetime.now()):
        
        from_date = datetime.datetime.now()-datetime.timedelta(days=90)
        to_date = datetime.datetime.now()-datetime.timedelta(minutes=interval)
        last_row = getData(5097729,from_date, to_date, time_frame )
        last_time=last_row.Timestamp
        print('running',datetime.datetime.now(),last_time,last_row)


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:


from dateutil import parser
interval=2
import datetime
last_time=datetime.datetime.now()
while True:
    if datetime.datetime.now()>last_time:
        datn=datetime.datetime.now()
        last_time=parser.parse(f'{datn.strftime("%Y-%m-%d %H:")}{abs((datn.minute%interval)-interval)+datn.minute}:00')
        print('running',datetime.datetime.now(), last_time)


# In[ ]:


from dateutil import parser
interval=2
import datetime,time
last_time=df_time
time.sleep(1)
while True:
    if datetime.datetime.now()>last_time:
        datn=datetime.datetime.now()
        minute = abs((datn.minute%interval)-interval)+datn.minute
        h = datn.hour
        if minute>59:
            h=h+1
            minute = 0
        last_time=parser.parse(f'{datn.strftime("%Y-%m-%d ")}{h}:{minute}:00')
        print('running',datetime.datetime.now(),last_time)


# In[ ]:


from dateutil import parser
interval=2
import datetime,time
last_time=datetime.datetime.now()
time.sleep(1)
while True:
    if datetime.datetime.now()>last_time:
        datn=datetime.datetime.now()
        minute = abs((datn.minute%interval)-interval)+datn.minute
        h = datn.hour
        if minute>59:
            h=h+1
            minute = 0
        last_time=parser.parse(f'{datn.strftime("%Y-%m-%d ")}{h}:{minute}:00')
        print('running',datetime.datetime.now(),last_time)


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:


# from dateutil import parser
# interval=2
# import datetime
# last_time=datetime.datetime.now()
# while True:
#     if datetime.datetime.now()>last_time:
#         datn=datetime.datetime.now()
#         last_time=parser.parse(f'{datn.strftime("%Y-%m-%d %H:")}{abs((datn.minute%interval)-interval)+datn.minute}:00')
#         print('running',datetime.datetime.now())


# In[ ]:


# from dateutil import parser
# interval=2
# import datetime
# last_time=datetime.datetime.now()
# while True:
#     if datetime.datetime.now()>last_time:
#         datn=datetime.datetime.now()
#         last_time=parser.parse(f'{datn.strftime("%Y-%m-%d %H:")}{abs((datn.minute%interval)-interval)+datn.minute}:00')
#         print('running',datetime.datetime.now())
#         tem = datetime.datetime.now()
        


# In[ ]:


tem


# In[ ]:


print(tem)


# In[ ]:





# In[ ]:




