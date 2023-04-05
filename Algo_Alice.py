import sys
import os
import time
import threading
import math
import json
import calendar
from csv import writer
import base64
import dateutil.parser
from ta import add_all_ta_features
from ta.utils import dropna

import pandas_ta as ta
              
from tabulate import tabulate

from pya3 import *
import configparser
import datetime
import requests
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta, FR
import time

import ctypes


######################################
#       Initialise variables
######################################
INI_FILE = "Settings.ini"              # Set .ini file name used for storing config info.
# Load parameters from the config file
cfg = configparser.ConfigParser()
cfg.read(INI_FILE)


strAdminChatID = cfg.get("tokens", "admin_chat_id")    
strChatID = cfg.get("tokens", "chat_id")
strBotToken = ("bot"+cfg.get("tokens", "bot_token"))
strBotTokenWObot = cfg.get("tokens", "bot_token") 

Send_Telegram = int(cfg.get("general", "send_telegram"))

# Enable logging to file 
log_file_name = cfg.get("tokens", "log_file_name")

strLogText = f"{log_file_name} Started. Don't Close this Window."
print("{}|{}".format(datetime.datetime.now(),strLogText),flush=True)

strLogText = f"Refer ./log/{log_file_name}_{datetime.datetime.now().strftime('%Y%m%d')}.log for Continuous Update"
print("{}|{}".format(datetime.datetime.now(),strLogText),flush=True)

try:
    ctypes.windll.kernel32.SetConsoleTitleW(log_file_name)
except:
    pass
sys.stdout = sys.stderr = open(r"./log/" + log_file_name + "_" + datetime.datetime.now().strftime("%Y%m%d") +".log" , "a")

# Custom logging: Default Info=1, data =0
def iLog(strLogText,LogType=1,sendTeleMsg=False):

    '''0=data, 1=Info, 2-Warning, 3-Error, 4-Abort, 5-Signal(Buy/Sell) ,6-Activity/Task done
        Do not use special characters like #,& etc  
    '''
    if Send_Telegram ==0:
        sendTeleMsg=False   ## Weekend Testing

    print("{}|{}|{}".format(datetime.datetime.now(),LogType,strLogText),flush=True)
    
    if sendTeleMsg :
        try:
            requests.get("https://api.telegram.org/"+strBotToken+"/sendMessage?chat_id="+strChatID+"&text="+strLogText)
        except:
            iLog(" Telegram message failed."+strLogText,3)
    

class TradeLog:

    try:    
        def __init__(self, folder="log",
                     filename=log_file_name + "_" + "Trade_Report_" +  datetime.datetime.today().strftime("%d-%m-%Y") + ".txt"):
            self.filepath = os.path.join(os.getcwd(), folder, filename)
            self.columns = ['Time','Symbol','Buy/Sell', 'Quantity','Average_Price', 'Order ID','order_status','return_status']
            if not os.path.exists(folder):
                os.makedirs(folder)
            else:
                pass
            if not os.path.exists(self.filepath):
                df = pd.DataFrame(columns=self.columns)
                df.to_csv(self.filepath, index=False)
            else:
                pass

        def update_csv(self, symbol, trade_type, quantity, average_price, order_id,status1,status2):
            _time=datetime.datetime.now().strftime("%H:%M:%S")
            data = [ _time,symbol, trade_type,quantity,average_price, order_id,status1,status2]
            df = pd.read_csv(self.filepath)
            df1 = pd.DataFrame([list(pd.Series(data))], columns=self.columns)
            result = pd.concat([df, df1])
            result.to_csv(self.filepath, index=False)
    except Exception as ex:
        iLog("Tradelog Class Exception occured = " + str(ex),3,sendTeleMsg=True)         

def set_config_value(section,key,value):
    '''Set the config file (.ini) value. Applicable for setting only one parameter value. 
    All parameters are string

    section=info/realtime,key,value
    '''
    cfg.set(section,key,value)
    try:
        with open(INI_FILE, 'w') as configfile:
            cfg.write(configfile)
            configfile.close()
    except Exception as ex:
        iLog("Exception writing to config. section={},key={},value={},ex={}".format(section,key,value,ex),2,sendTeleMsg=True)


def savedata(flgUpdateConfigFile=True):
    #flgUpdateConfigFile = True Updates datafilename in the .ini file for nextday reload.
    
    try:
        if flgUpdateConfigFile :
            with open(INI_FILE, 'w') as configfile:
                cfg.write(configfile)
                configfile.close()

    except Exception as ex:
        iLog("In savedata(). Exception occured = " + str(ex),3,sendTeleMsg=True)


######################################
#       Initialise variables
######################################

strMsg = " Initialising " + __file__
iLog(strMsg,4,sendTeleMsg=True)


susr = cfg.get("tokens", "uid")
spassword = cfg.get("tokens", "pwd")

tl = TradeLog()
place_orders = True
order_count = 0

### Algo Parameters

papertrade = int(cfg.get("algo", "papertrade")) 

if papertrade==1:
    strMsg = " Paper Trade Enabled. Orders will not be placed"
    iLog(strMsg,6,sendTeleMsg=True)
if papertrade==0:
    strMsg = " Live Trade Enabled. Orders will be placed. Monitor your trades closely"
    iLog(strMsg,2,sendTeleMsg=True)
    
no_of_lots = int(cfg.get("algo", "no_of_lots"))
ExitTradenow = int(cfg.get("algo", "exittradenow"))

Trade_Nifty = int(cfg.get("algo", "trade_nifty"))
Trade_BankNifty = int(cfg.get("algo", "trade_banknifty"))

CheckTime = int(cfg.get("algo", "checktime"))
EntryTime = int(cfg.get("algo", "entrytime"))
                                                   
ExitTime = int(cfg.get("algo", "exitTime"))

entry_price = float(cfg.get("algo", "entry_price"))
entry_price_buffer = float(cfg.get("algo", "entry_price_buffer"))

buy_sl_points = float(cfg.get("algo", "buy_sl_points"))
buy_target_points = float(cfg.get("algo", "buy_target_points"))

enable_sl_trail = int(cfg.get("algo", "enable_sl_trail"))
sl_threshold = int(cfg.get("algo", "sl_threshold"))
sl_lock = int(cfg.get("algo", "sl_lock"))
sl_x = int(cfg.get("algo", "sl_x"))
sl_y = int(cfg.get("algo", "sl_y"))


### General Parameters
log_interval = int(cfg.get("general", "log_interval"))
ltp_not_updating_exit  = int(cfg.get("general", "ltp_not_updating_exit"))
ltp_not_updating_limit_secs = int(cfg.get("general", "ltp_not_updating_limit_secs"))


lst_Index_ltp = []

dateFormat = "%Y-%m-%d"
timeFormat = "%H:%M:%S"
dateTimeFormat = "%Y-%m-%d %H:%M:%S"

socket_opened = False
First_Straddle = False

Check_Condition_Met = False
Entry_Condition_Met = False
CE_Entry_Triggered = False
PE_Entry_Triggered = False

CE_Buy_Entry_Triggered = False
PE_Buy_Entry_Triggered = False
CE_Sell_Entry_Triggered = False
PE_Sell_Entry_Triggered = False

CE_Buy_Exit_Triggered = False
PE_Buy_Exit_Triggered = False
CE_Sell_Exit_Triggered = False
PE_Sell_Exit_Triggered = False

CE_Buy_Entry_Price = 0
PE_Buy_Entry_Price = 0
CE_Sell_Entry_Price = 0
PE_Sell_Entry_Price = 0

CE_Buy_Exit_Price = 0
PE_Buy_Exit_Price = 0
CE_Sell_Exit_Price = 0
PE_Sell_Exit_Price = 0

CE_SL_New = 0
CE_SL_Level1 = False

PE_SL_New = 0
PE_SL_Level1 = False

CE_LTP_Update_Count = 0
PE_LTP_Update_Count = 0
CE_LTP_old = 0
PE_LTP_old = 0

CE_Buy_Price = 1000
PE_Buy_Price = 1000

Starting_LTP = 35000


dict_ltp = {}       #Will contain dictionary of token and ltp pulled from websocket

param = '/export?format=csv&gid=0'

# lst_nifty = []  
cur_min = 0
algo_min = 0
log_min = 0
ST_min = 0


a=int(datetime.datetime.now().strftime("%Y%m%d"))
Paper_MTM = 0.0
Paper_MTM_old = 0.0
Last_Traded_PE_Price = 0.0
Last_Traded_CE_Price = 0.0
PE_Entry_Price = 0.0
CE_Entry_Price = 0.0

Paper_MTM_Booked = 0.0

MTM = 0.0                 
MTM_BANK = 0.0
MTM_Index = 0.0
pos_bank = 0    
MTM_NIFTY = 0.0
pos_nifty = 0                    

b=int(a*6)

processIndexExitTradenow = False

d=60662445

key = '124'



CE_Leg_SL = 1000
PE_Leg_SL = 1000

CE_Leg_Target = 0
PE_Leg_Target = 0

token_Index_ce = 1111           
token_Index_pe = 2222

token_Index_ce_old = 1122
token_Index_pe_old = 2233

Index_CE_atm=0
Index_PE_atm=0


#lst_Index_ltp = 0.0
ltp_Index_ATM_CE  = 0.0            # Last traded price for ATM CE
ltp_Index_ATM_PE  = 0.0             # Last traded price for ATM PE



c=int(b/2)
f=susr

link = 'https://docs.google.com/spreadsheets/d/'



K_Direction     = 0

url = link+key+param
#dfurl = pd.read_csv(url)


lic = int(datetime.datetime.now().strftime("%Y%m%d"))


############################################################################
#       Functions
############################################################################

def getHolidays():
    with open('holidays.json', 'r') as holidays:
        holidaysData = json.load(holidays)
        return holidaysData


def isHoliday(datetimeObj):
    dayOfWeek = calendar.day_name[datetimeObj.weekday()]
    if dayOfWeek == 'Saturday' or dayOfWeek == 'Sunday':
        return True

    dateStr = convertToDateStr(datetimeObj)
    holidays = getHolidays()
    if (dateStr in holidays):
        return True
    else:
        return False


def isTodayHoliday():
    return isHoliday(datetime.datetime.now())

def convertToDateStr(datetimeObj):
    return datetimeObj.strftime(dateFormat)

def get_realtime_config():
    '''This procedure can be called during execution to get realtime values from the .ini file'''

    global papertrade,no_of_lots,lot_size,EntryTime,ExitTime,ExitTradenow,log_interval\
        ,cfg,Index_qty,place_orders,Trade_Nifty,Trade_BankNifty,CheckTime\
        ,ltp_not_updating_exit,ltp_not_updating_limit_secs,entry_price,entry_price_buffer\
        ,buy_sl_points,buy_target_points,enable_sl_trail,sl_threshold,sl_lock,sl_x,sl_y,strategy_sec_key_ce,strategy_sec_key_pe,websiteurl
        

    cfg.read(INI_FILE)
    Send_Telegram = int(cfg.get("general", "send_telegram"))

    ExitTradenow = int(cfg.get("algo", "exittradenow"))

    CheckTime = int(cfg.get("algo", "checktime"))
    EntryTime = int(cfg.get("algo", "entrytime"))

    ExitTime = int(cfg.get("algo", "exitTime"))

    entry_price = float(cfg.get("algo", "entry_price"))
    entry_price_buffer = float(cfg.get("algo", "entry_price_buffer"))

    buy_sl_points = float(cfg.get("algo", "buy_sl_points"))
    buy_target_points = float(cfg.get("algo", "buy_target_points"))

    strategy_sec_key_ce = str(cfg.get("tokens", "strategy_sec_key_ce"))
    strategy_sec_key_pe = str(cfg.get("tokens", "strategy_sec_key_pe"))
    websiteurl = str(cfg.get("tokens", "websiteurl"))

    enable_sl_trail = int(cfg.get("algo", "enable_sl_trail"))
    sl_threshold = int(cfg.get("algo", "sl_threshold"))
    sl_lock = int(cfg.get("algo", "sl_lock"))
    sl_x = int(cfg.get("algo", "sl_x"))
    sl_y = int(cfg.get("algo", "sl_y"))
    
    ### General Parameters
    log_interval = int(cfg.get("general", "log_interval"))  #3
    ltp_not_updating_exit  = int(cfg.get("general", "ltp_not_updating_exit"))
    ltp_not_updating_limit_secs = int(cfg.get("general", "ltp_not_updating_limit_secs"))

##################################################
########## Order Management    ###################
###################################################


import requests as re
def place_order (transaction_type,symbol,qty):
    global strategy_sec_key_pe,strategy_sec_key_ce, websiteurl,Trade_Nifty
    print('order',datetime.datetime.now())
    try:
        if Trade_Nifty==1:
            ticker="NIFTY"
        else:
            ticker="BANKNIFTY"
        side='BUY' if symbol.name[-2:]=='CE' else "SELL"
        pos=1 if transaction_type=="BUY" else 0
        print(transaction_type,symbol,qty)
        if side=='BUY' :
            strategy_sec_key=strategy_sec_key_ce
        else:
            strategy_sec_key=strategy_sec_key_pe
        data={"secToken": strategy_sec_key, "exchange": "NFO", "ticker": ticker, "side": side, "ltp": int(symbol.name[-7:-2]), "pos": pos, "quantity": str(qty), "pticker": "NIFTY FUTURE"}
        a=re.post(websiteurl,json=data)
    except Exception as e:
        print('error',e)
    time.sleep(5)
        
    order_id = None
    return order_id

def get_order_status(order_id):
    global alice
    status = None
                                     
    for i in range(0, 5):
        try:
            status = alice.get_order_history(order_id)
            #print(status)
            status = status['Status']
                                                
            break
        except Exception as e:
            iLog("Exception occured in get_order_status():"+str(e),3,sendTeleMsg=True)
            time.sleep(1)
            continue
    return status

def get_order_price(order_id):
    global alice
    average_price = 0
                  
    for i in range(0, 5):
        try:
            average_price = alice.get_order_history(order_id)
            #print(average_price)
            average_price = float(average_price['Avgprc'])
            break
        except Exception as e:
            iLog("Exception occured in get_order_price():"+str(e),3,sendTeleMsg=True)
            time.sleep(1)
            continue
    return average_price

def get_order_symbol(order_id):
    global alice
    Symbol = "No Position"
    for i in range(0, 5):
        try:
            Symbol = alice.get_order_history(order_id)
            #print(Symbol)
            Symbol = Symbol['Trsym']
            break
        except Exception as e:
            iLog("Exception occured in get_order_symbol():"+str(e),3,sendTeleMsg=True)
            time.sleep(1)
            continue
    return Symbol

def get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date='22022022', is_fut=False, strike=37000, is_CE = True): 

    exch  = 'NFO'
    expiry_date= expiry_date.strftime("%d%b%y").upper()

    if is_fut:
        query =f"{symbol}{expiry_date}C{strike}"
    else:
        if is_CE:
            query =f"{symbol}{expiry_date}C{strike}"
        else:
            query = f"{symbol}{expiry_date}P{strike}"
    
    strike_symbol = api.searchscrip(exchange=exch, searchtext=query)['values'][0]
    dictList=[]
    for value in strike_symbol.values():
        dictList.append((value))
    
    return dictList

def get_lot_size(symbol = 'BANKNIFTY', expiry_date='22022022', is_fut=False, strike=37000, is_CE = True): 

    exch  = 'NFO'
    expiry_date= expiry_date.strftime("%d%b%y").upper()

    if is_fut:
        query =f"{symbol}{expiry_date}C{strike}"
    else:
        if is_CE:
            query =f"{symbol}{expiry_date}C{strike}"
        else:
            query = f"{symbol}{expiry_date}P{strike}"
    
    lot_size = api.searchscrip(exchange=exch, searchtext=query)['values'][0]['ls']
    
    return lot_size

def get_instrument_by_symbol(exchange = 'NSE',symbol = 'NIFTY BANK'): 
    strike_symbol = api.searchscrip(exchange, symbol)['values'][0]
    dictList=[]
    for value in strike_symbol.values():
        dictList.append((value))
    
    return dictList

def get_instrument_by_token(exchange = 'NFO',token = 260105): 
    strike_symbol = api.get_quotes(exchange, token)['tsym']
    # dictList=[]
    # for value in strike_symbol.values():
    #     dictList.append((value))
    
    return strike_symbol

def getLTP(exchange , tradingsymbol):
    global alice
    a = 0
    while a < 5:
        try:
            #qRes = api.get_quotes(exchange, tradingsymbol)
            #ltp = float(qRes['lp'])
            qRes = alice.get_scrip_info(tradingsymbol)
            # iLog(f"{qRes}")
            ltp = float(qRes['LTP'])
            break
        except:
            time.sleep(1)
            if a>3:
                strMsg = f" can't get quotes..retrying"
                iLog(strMsg,4,sendTeleMsg=True)
            a+=1
    return ltp


def closest(lst,K):
    lst = np.asarray(lst)
    idx=(np.abs(lst-K)).argmin()
    return lst[idx]


def get_token_by_symbol(exchange = 'NSE',symbol = 'NIFTY BANK'): 
    strike_symbol = api.searchscrip(exchange, symbol)['values'][0]['token']
    return strike_symbol


def get_ce_strike(symbol = 'NIFTY',strike= 33000,premium = 75, exp = '01SEP22'):
    #iLog(f" calling CE Strike {symbol},{strike},{premium},{exp}")
    ITM_length = 5
    OTM_length = 10
    #exp= exp.strftime("%d%b%y").upper()
    if symbol == 'NIFTY':
        mult = 50
    else:
        mult = 100
    strike_level=OTM_length*mult
    strike_level_ITM=ITM_length*mult
    ltpu=[]
    ltpd=[]
    dictt={}
    for i in range(strike-strike_level_ITM,strike+strike_level,mult):
        try:
            ins_temp = alice.get_instrument_for_fno(exch='NFO',symbol = symbol, expiry_date=exp.isoformat(), is_fut=False, strike=float(i), is_CE = True)
            ltp = round(float(getLTP('NFO',ins_temp)),2)
            ltpu.append(float(ltp))
            dictt[i]=ltp
            #iLog(f" CE Strike {strike_ce} : {ltp}")
        except:
            iLog(f" {i} CE Skipped due to error in getting LTP")
            pass

    ce_value=float(closest(ltpu,premium))
    for key,value in dictt.items():
        if float(value)==ce_value:
            strike_ce=key
    iLog(f" CE Strike : {strike_ce}")
    iLog(f" CE value : {ce_value}")
    return strike_ce

def get_pe_strike(symbol = 'NIFTY',strike= 33000,premium = 75, exp = '01SEP22'):
    #iLog(f" calling PE Strike {symbol},{strike},{premium},{exp}")
    ITM_length = 5
    OTM_length = 10
    if symbol == 'NIFTY':
        mult = 50
    else:
        mult = 100
    strike_level=OTM_length*mult
    strike_level_ITM=ITM_length*mult
    ltpu=[]
    ltpd=[]
    dictt={}
    for i in range(strike+strike_level_ITM,strike-strike_level,-mult):
        try:
            ins_temp = alice.get_instrument_for_fno(exch='NFO',symbol = symbol, expiry_date=exp.isoformat(), is_fut=False, strike=float(i), is_CE = False)
            ltp = round(float(getLTP('NFO',ins_temp)),2)
            ltpu.append(float(ltp))
            dictt[i]=ltp
            #iLog(f" PE Strike {strike_pe} : {ltp}")
        except:
            iLog(f" {i} PE Skipped due to error in getting LTP")
            pass
    
    pe_value=float(closest(ltpu,premium))
    for key,value in dictt.items():
        if float(value)==pe_value:
            strike_pe=key
    iLog(f" PE Strike : {strike_pe}")
    iLog(f" PE value : {pe_value}")
    return strike_pe


def subscribe_ins():
    global alice,ins_Index,ins_Index_ce,ins_Index_pe

    try:
        subscribe_list = [ins_Index,ins_Index_ce,ins_Index_pe]
        alice.subscribe(subscribe_list)

        
    except Exception as ex:
        iLog(" subscribe_ins(): Exception="+ str(ex),3,sendTeleMsg=True)

    iLog(" subscribe_ins().")
    
    
def get_option_tokens(Index_Option="ALL"):
    '''This procedure sets the current option tokens to the latest ATM tokens
    Pass - ALL,CE,PE
    '''

    iLog(f" In get_option_tokens():{Index_Option}")

    #WIP
    global token_Index_ce, token_Index_pe, ins_Index_ce, ins_Index_pe,Index_CE_atm,Index_PE_atm\
            ,expiry_date,lot_size,strike_ce,strike_pe\
            ,lst_Index_ltp,ltp_Index_ATM_CE,ltp_Index_ATM_PE\
            ,strike_offset,entry_price,entry_price_buffer
                        
    if Index_Option=="ALL":
        if len(lst_Index_ltp)>0:
            IndexLTP = int(lst_Index_ltp[-1])
            iLog(f" IndexLTP {IndexLTP}")

            if Trade_Nifty==1:

                Index_CE_atm = int(50*round(int(IndexLTP)/50,0))
                Index_PE_atm = int(50*round(int(IndexLTP)/50,0))

            if Trade_BankNifty==1:
                Index_CE_atm = int(100*round(int(IndexLTP)/100,0))
                Index_PE_atm = int(100*round(int(IndexLTP)/100,0))

            if Trade_Nifty ==1:
                strike_ce = float(get_ce_strike(symbol = 'NIFTY',strike= Index_CE_atm,premium = entry_price, exp = expiry_date)) #OTM Options
                strike_pe = float(get_pe_strike(symbol = 'NIFTY',strike= Index_PE_atm,premium = entry_price, exp = expiry_date)) #OTM Options

            if Trade_BankNifty ==1:
                strike_ce = float(get_ce_strike(symbol = 'BANKNIFTY',strike= Index_CE_atm,premium = entry_price, exp = expiry_date)) #OTM Options
                strike_pe = float(get_pe_strike(symbol = 'BANKNIFTY',strike= Index_PE_atm,premium = entry_price, exp = expiry_date)) #OTM Options

            strMsg = f" CE/PE Strike Price = ({strike_ce},{strike_pe})" 
            iLog(strMsg,1,sendTeleMsg=True)

            if Trade_Nifty==1:
                ins_Index_ce = alice.get_instrument_for_fno(exch='NFO',symbol = 'NIFTY', expiry_date=expiry_date.isoformat(), is_fut=False, strike=strike_ce, is_CE = True)
                ins_Index_pe = alice.get_instrument_for_fno(exch='NFO',symbol = 'NIFTY', expiry_date=expiry_date.isoformat(), is_fut=False, strike=strike_pe, is_CE = False)
                

            if Trade_BankNifty==1:
                ins_Index_ce = alice.get_instrument_for_fno(exch='NFO',symbol = 'BANKNIFTY', expiry_date=expiry_date.isoformat(), is_fut=False, strike=strike_ce, is_CE = True)
                ins_Index_pe = alice.get_instrument_for_fno(exch='NFO',symbol = 'BANKNIFTY', expiry_date=expiry_date.isoformat(), is_fut=False, strike=strike_pe, is_CE = False)
                
            #print(ins_Index_ce)
            lot_size =int(ins_Index_ce[5])
            token_Index_ce = int(ins_Index_ce[1])
            token_Index_pe = int(ins_Index_pe[1])

            alice.subscribe([ins_Index_ce,ins_Index_pe])
            time.sleep(2)
            strMsg = f" (CE,PE) Premium Price = ({ltp_Index_ATM_CE},{ltp_Index_ATM_PE})" 
            iLog(strMsg,1,sendTeleMsg=True)


        else:
            strMsg = f" len(lst_Index_ltp) = {len(lst_Index_ltp)}" 
            iLog(strMsg,1,sendTeleMsg=True)

########################################################################
#       Events
########################################################################
def event_handler_quote_update(message):
    global dict_ltp, lst_Index_ltp,ltp_Index_ATM_CE,ltp_Index_ATM_PE,Index_CE_atm,Index_PE_atm\
            ,token_Index_ce_old,token_Index_pe_old\
            ,token_Index_ce,token_Index_pe,ins_Index
       
    feed_message = json.loads(message)
    # iLog(feed_message)
    if feed_message["t"]=='tk' or feed_message["t"]=='tf':
        if(feed_message["tk"]==str(token_Index_ce)):
            ltp_Index_ATM_CE = float(feed_message['lp'] if 'lp' in feed_message else ltp_Index_ATM_CE)

        if(feed_message["tk"]==str(token_Index_pe)):
            ltp_Index_ATM_PE = float(feed_message['lp'] if 'lp' in feed_message else ltp_Index_ATM_PE)

        if(feed_message["tk"]==str(ins_Index[1])):
            if 'lp' in feed_message:
                lst_Index_ltp.append(float(feed_message['lp']))
                                             
        #Update the ltp for all the tokens
        if 'lp' in feed_message:
            dict_ltp.update({feed_message["tk"]:float(feed_message['lp'])})
    # iLog(f"{ltp_Index_ATM_CE},{ltp_Index_ATM_PE}")
    # iLog(f"{token_Index_ce}{token_Index_pe}")

                         
def open_callback():
    global socket_opened
    socket_opened = True
    iLog(" In open_callback().")
    # Call the instrument subscription, Hope this will resolve the tick discontinuation issue
    subscribe_ins()   # 2020-08-13 moving this to main call
    # 2020-08-14 Didnt worked So upgraded the alice_blue package. Lets observe on monday 

def error_callback(error):
    iLog(" In error_callback(). {}".format(error),3)

def close_callback():
    iLog(" In close_callback().")

    
########################################################################
# Main program starts from here...
########################################################################

iLog(" User = " + susr)

with open('holidays.json', 'r') as holidays:
    holidaysData = json.load(holidays)

expiry_date = datetime.date.today() + datetime.timedelta( (3-datetime.date.today().weekday()) % 7 )

# Reduce one day if thurshday is a holiday
if str(expiry_date) in holidaysData :
    expiry_date = expiry_date - datetime.timedelta(days=1)

if str(expiry_date) in holidaysData :
    expiry_date = expiry_date - datetime.timedelta(days=1)

if str(expiry_date) in holidaysData :
    expiry_date = expiry_date - datetime.timedelta(days=1)                                                    


cur_HHMM = int(datetime.datetime.now().strftime("%H%M"))
if isTodayHoliday():
    strMsg = " Today is market holiday. Stopping Algo for the day"
    iLog(strMsg,4,sendTeleMsg=True)
    iLog(" Shutter down... Calling sys.exit() @ " + str(cur_HHMM),4,sendTeleMsg=True)
    sys.exit()

cur_HHMM = int(datetime.datetime.now().strftime("%H%M"))
if no_of_lots ==0:
    strMsg = " no of lots set to zero. No trading for the day"
    iLog(strMsg,4,sendTeleMsg=True)
    iLog(" Shutter down... Calling sys.exit() @ " + str(cur_HHMM),4,sendTeleMsg=True)
    sys.exit()

cur_HHMM = int(datetime.datetime.now().strftime("%H%M"))
if Trade_Nifty+Trade_BankNifty !=1:
    strMsg = " Only one of these flag should be set to 1, check settings and restart: Trade_Nifty,Trade_BankNifty"
    iLog(strMsg,4,sendTeleMsg=True)
    iLog(" Shutter down... Calling sys.exit() @ " + str(cur_HHMM),4,sendTeleMsg=True)
    sys.exit()

# Get access token
# pya3

iLog(" Reading Config file.")
cfg = configparser.ConfigParser()
cfg.read(INI_FILE)

strToken = "tokens"

susr = cfg.get(strToken, "uid")
spassword = cfg.get(strToken, "pwd")
sapi_secret = cfg.get(strToken, "api_secret")
stwoFA = cfg.get(strToken, "twoFA")
totp = cfg.get(strToken, "totp")

alice = Aliceblue(user_id=susr,api_key=sapi_secret)
session_id = alice.get_session_id() # Get Session ID

#iLog(f"session_id={session_id}")

alice.get_contract_master("INDICES")
alice.get_contract_master("NSE")
alice.get_contract_master("NFO")

try:
    if Trade_Nifty==1:
        ins_Index = alice.get_instrument_by_symbol("INDICES", "Nifty 50")
     
    if Trade_BankNifty==1:                       
        ins_Index = alice.get_instrument_by_symbol("INDICES", "Nifty Bank")
      

except Exception as ex:
    iLog(" get_instrument_by_symbol: Exception="+ str(ex),3,sendTeleMsg=True)
    iLog(" Exiting Algo",4,sendTeleMsg=True)
    sys.exit()


# Temp assignment for CE/PE instrument tokens
instrument = ins_Index

ins_Index_ce = ins_Index
ins_Index_pe = ins_Index
ins_Index_opt = ins_Index

time.sleep(3)


iLog(f"{ins_Index}")

temp_price = round(float(getLTP(ins_Index[0],ins_Index)),2)

iLog(f"{temp_price}")

# Start Websocket
strMsg = " Starting Websocket."
iLog(strMsg,sendTeleMsg=True)
alice.start_websocket(socket_open_callback=open_callback, socket_close_callback=close_callback,
                      socket_error_callback=error_callback, subscription_callback=event_handler_quote_update, run_in_background=True)

# Check with Websocket open status
while(socket_opened==False):
    pass

time.sleep(2)

get_realtime_config()
if ExitTradenow ==1:
    set_config_value("algo","ExitTradenow","0")
    savedata()

try:
    get_option_tokens("ALL")
except:
    time.sleep(5)
    try:
        get_option_tokens("ALL")
    except Exception as ex:
        iLog(" get_option_tokens(): Exception="+ str(ex),3,sendTeleMsg=True)
        iLog(" Exiting Algo",4,sendTeleMsg=True)
        sys.exit()

if len(lst_Index_ltp)==0:
    alice.start_websocket(socket_open_callback=open_callback, socket_close_callback=close_callback,
                      socket_error_callback=error_callback, subscription_callback=event_handler_quote_update, run_in_background=True)

    # Check with Websocket open status
    while(socket_opened==False):
        pass
    time.sleep(4)
    try:
        get_option_tokens("ALL")
    except:
        time.sleep(5)
        try:
            get_option_tokens("ALL")
        except Exception as ex:
            iLog(" get_option_tokens(): Exception="+ str(ex),3,sendTeleMsg=True)
            iLog(" Exiting Algo",4,sendTeleMsg=True)
            sys.exit()
            
Index_qty=int(lot_size*no_of_lots)

strMsg = " Waiting for First Entry time"
iLog(strMsg,1,sendTeleMsg=True)

# Process tick data/indicators and generate buy/sell and execute orders
while True:
    get_realtime_config()
    
    if papertrade==1:
        place_orders = False

    cur_HHMM = int(datetime.datetime.now().strftime("%H%M"))                                             

# ####################################################
#           Short Straddle Order Generation
# ####################################################
    
    if cur_HHMM >= CheckTime:
        if Check_Condition_Met==False:
            iLog(" Waiting for Check conditions within price buffer limits",6,sendTeleMsg=True)
        
        while Check_Condition_Met==False:
            cur_HHMM = int(datetime.datetime.now().strftime("%H%M"))
            get_realtime_config()
            if ExitTradenow ==1 or cur_HHMM>=ExitTime:
                set_config_value("algo","ExitTradenow","0")
                savedata()
                iLog(" ExitTradenow/Exit Time Triggered",4,sendTeleMsg=True)
                iLog(" Shutter down... Calling sys.exit() @ " + str(cur_HHMM),4,sendTeleMsg=True)
                sys.exit()

            try:
                get_option_tokens("ALL")
            except:
                time.sleep(5)
                try:
                    get_option_tokens("ALL")
                except Exception as ex:
                    iLog(" get_option_tokens(): Exception="+ str(ex),3,sendTeleMsg=True)
                    iLog(" Exiting Algo",4,sendTeleMsg=True)
                    sys.exit()
            

            Check_Condition_Met = True
            Temp_CE_Price = ltp_Index_ATM_CE
            Temp_PE_Price = ltp_Index_ATM_PE

            CE_Buy_Price = Temp_CE_Price + entry_price_buffer
            PE_Buy_Price = Temp_PE_Price + entry_price_buffer

            strMsg = f" Check_Condition_Met : CE (LTP,buy_price) : ({Temp_CE_Price},{CE_Buy_Price}), PE (LTP,buy_price) : ({Temp_PE_Price},{PE_Buy_Price}) "
            iLog(strMsg,6,sendTeleMsg=True)


        cur_HHMM = int(datetime.datetime.now().strftime("%H%M"))                                             

        if cur_HHMM >=EntryTime and Check_Condition_Met ==True and Entry_Condition_Met == False:
            Entry_Condition_Met =True
            strMsg = f" Entry_Condition_Met : Waiting for First Entry: {strike_ce} CE (LTP,buy_price) : ({ltp_Index_ATM_CE},{CE_Buy_Price}), {strike_pe} PE (LTP,buy_price) : ({ltp_Index_ATM_PE},{PE_Buy_Price})"
            iLog(strMsg,6,sendTeleMsg=True)            

# ####################################################
#           CE Leg Buy code
# ####################################################

        if Entry_Condition_Met == True and ltp_Index_ATM_CE>=CE_Buy_Price and CE_Buy_Entry_Triggered == False:
            CE_Buy_Entry_Price=ltp_Index_ATM_CE
            if papertrade == 1:
                place_order("BUY",ins_Index_ce,Index_qty)
                strMsg = f" Place CE Buy Market order Stike: {strike_ce} ATM CE={CE_Buy_Entry_Price}, Qty ={Index_qty}"
                iLog(strMsg,5,sendTeleMsg=True)
            if papertrade == 0:
                order_id_CE = place_order(TransactionType.Buy,ins_Index_ce,Index_qty)
                CE_Buy_Entry_Price=ltp_Index_ATM_CE
                order_id = order_id_CE['NOrdNo']
                Symbol = get_order_symbol(order_id)
                Placed_Status = order_id_CE['stat']
                Return_Status = get_order_status(order_id)
                if Return_Status.upper() == "COMPLETE":
                    average_price = get_order_price(order_id)
                if Return_Status.upper() == "REJECTED":
                    strMsg = f" Error in Order Placement Ord_ID = {order_id}, Ord_STS = {Placed_Status}, Ret_STS = {Return_Status}.Exiting Algo"
                    iLog(strMsg,4,sendTeleMsg=True)
                    sys.exit()

                if average_price>0 and Return_Status.upper() == "COMPLETE":
                    CE_Buy_Entry_Price=average_price
                strMsg = f" Placed CE Buy Market order Stike: {strike_ce} ATM CE={average_price}, Qty ={Index_qty}, Ord_ID = {order_id}, Ord_STS = {Placed_Status}, Ret_STS = {Return_Status}"
                iLog(strMsg,5,sendTeleMsg=True)

            CE_SL = round((CE_Buy_Entry_Price-buy_sl_points),2)
            CE_TGT = round((CE_Buy_Entry_Price+buy_target_points),2)
            CE_Entry_Triggered = True
            CE_Buy_Entry_Triggered = True

# ####################################################
#           PE Leg Buy code
# ####################################################

        if Entry_Condition_Met == True and ltp_Index_ATM_PE>=PE_Buy_Price and PE_Buy_Entry_Triggered == False:
            PE_Buy_Entry_Price=ltp_Index_ATM_PE
            if papertrade == 1:
                place_order("BUY",ins_Index_pe,Index_qty)
                strMsg = f" Place PE Buy Market order Stike: {strike_pe} ATM PE={PE_Buy_Entry_Price}, Qty ={Index_qty}"
                iLog(strMsg,5,sendTeleMsg=True)
            if papertrade == 0:
                order_id_PE = place_order(TransactionType.Buy,ins_Index_pe,Index_qty)
                PE_Buy_Entry_Price=ltp_Index_ATM_PE
                order_id = order_id_PE['NOrdNo']
                Symbol = get_order_symbol(order_id)
                Placed_Status = order_id_PE['stat']
                Return_Status = get_order_status(order_id)
                if Return_Status.upper() == "COMPLETE":
                    average_price = get_order_price(order_id)
                if Return_Status.upper() == "REJECTED":
                    strMsg = f" Error in Order Placement Ord_ID = {order_id}, Ord_STS = {Placed_Status}, Ret_STS = {Return_Status}.Exiting Algo"
                    iLog(strMsg,4,sendTeleMsg=True)
                    sys.exit()

                if average_price>0 and Return_Status.upper() == "COMPLETE":
                    PE_Buy_Entry_Price=average_price
                strMsg = f" Placed PE Buy Market order Stike: {strike_pe} ATM PE={average_price}, Qty ={Index_qty}, Ord_ID = {order_id}, Ord_STS = {Placed_Status}, Ret_STS = {Return_Status}"
                iLog(strMsg,5,sendTeleMsg=True)

            PE_SL = round((PE_Buy_Entry_Price-buy_sl_points),2)
            PE_TGT = round((PE_Buy_Entry_Price+buy_target_points),2)
            PE_Entry_Triggered = True
            PE_Buy_Entry_Triggered = True



        if CE_Buy_Entry_Triggered==True and CE_Buy_Exit_Triggered == False:

            if enable_sl_trail == 0:
                CE_SL_New = 0
                CE_SL_Level1 = False

            if enable_sl_trail == 1:
                if (ltp_Index_ATM_CE-CE_Buy_Entry_Price)>=(sl_threshold) and CE_SL_Level1 ==False:
                    CE_SL_Level1 = True
                    CE_SL = round((CE_SL+sl_lock),2)
                    CE_SL_New = sl_x

                if (ltp_Index_ATM_CE-CE_Buy_Entry_Price)>=(sl_threshold+CE_SL_New) and CE_SL_Level1 ==True:
                    CE_SL = round((CE_SL+sl_y),2)
                    CE_SL_New = CE_SL_New + sl_x

        if PE_Buy_Entry_Triggered==True and PE_Buy_Exit_Triggered == False:

            if enable_sl_trail == 0:
                PE_SL_New = 0
                PE_SL_Level1 = False

            if enable_sl_trail == 1:
                if (ltp_Index_ATM_PE-PE_Buy_Entry_Price)>=(sl_threshold) and PE_SL_Level1 ==False:
                    PE_SL_Level1 = True
                    PE_SL = round((PE_SL+sl_lock),2)
                    PE_SL_New = sl_x

                if (ltp_Index_ATM_PE-PE_Buy_Entry_Price)>=(sl_threshold+PE_SL_New) and PE_SL_Level1 ==True:
                    PE_SL = round((PE_SL+sl_y),2)
                    PE_SL_New = PE_SL_New + sl_x


# ####################################################
#           CE Leg Buy Exit code
# ####################################################
        cur_HHMM = int(datetime.datetime.now().strftime("%H%M"))
        if CE_Buy_Entry_Triggered==True and CE_Buy_Exit_Triggered == False and (ltp_Index_ATM_CE<=CE_SL or ltp_Index_ATM_CE>=CE_TGT or ExitTradenow==1 or cur_HHMM>=ExitTime):
            CE_Buy_Exit_Price=ltp_Index_ATM_CE
            if papertrade == 1:
                place_order("SELL",ins_Index_ce,Index_qty)
                strMsg = f" Place CE Sell Market order Stike: {strike_ce} ATM CE={CE_Buy_Exit_Price}, Qty ={Index_qty}"
                iLog(strMsg,5,sendTeleMsg=True)
            if papertrade == 0:
                order_id_CE = place_order(TransactionType.Sell,ins_Index_ce,Index_qty)
                CE_Buy_Exit_Price=ltp_Index_ATM_CE
                order_id = order_id_CE['NOrdNo']
                Symbol = get_order_symbol(order_id)
                Placed_Status = order_id_CE['stat']
                Return_Status = get_order_status(order_id)
                if Return_Status.upper() == "COMPLETE":
                    average_price = get_order_price(order_id)
                if Return_Status.upper() == "REJECTED":
                    strMsg = f" Error in Order Placement Ord_ID = {order_id}, Ord_STS = {Placed_Status}, Ret_STS = {Return_Status}.Exiting Algo"
                    iLog(strMsg,4,sendTeleMsg=True)
                    if ExitTradenow ==1:
                        set_config_value("algo","ExitTradenow","0")
                        savedata()
                    sys.exit()

                if average_price>0 and Return_Status.upper() == "COMPLETE":
                    CE_Buy_Exit_Price=average_price
                strMsg = f" Placed CE Sell Market order Stike: {strike_ce} ATM CE={average_price}, Qty ={Index_qty}, Ord_ID = {order_id}, Ord_STS = {Placed_Status}, Ret_STS = {Return_Status}"
                iLog(strMsg,5,sendTeleMsg=True)

            CE_Buy_Exit_Triggered = True
            Paper_MTM_Booked = round((Paper_MTM_Booked + Index_qty*(CE_Buy_Exit_Price-CE_Buy_Entry_Price)),0)
            Paper_MTM = Paper_MTM_Booked
            strMsg = f" Paper_MTM_Booked = {Paper_MTM_Booked}"
            iLog(strMsg,sendTeleMsg=True)

# ####################################################
#           PE Leg Buy Exit code
# ####################################################
        cur_HHMM = int(datetime.datetime.now().strftime("%H%M"))
        if PE_Buy_Entry_Triggered==True and PE_Buy_Exit_Triggered == False and (ltp_Index_ATM_PE<=PE_SL or ltp_Index_ATM_PE>=PE_TGT or ExitTradenow==1 or cur_HHMM>=ExitTime):
            PE_Buy_Exit_Price=ltp_Index_ATM_PE
            if papertrade == 1:
                place_order("SELL",ins_Index_pe,Index_qty)
                strMsg = f" Place PE Sell Market order Stike: {strike_pe} ATM PE={PE_Buy_Exit_Price}, Qty ={Index_qty}"
                iLog(strMsg,5,sendTeleMsg=True)
            if papertrade == 0:
                order_id_PE = place_order(TransactionType.Sell,ins_Index_pe,Index_qty)
                PE_Buy_Exit_Price=ltp_Index_ATM_PE
                order_id = order_id_PE['NOrdNo']
                Symbol = get_order_symbol(order_id)
                Placed_Status = order_id_PE['stat']
                Return_Status = get_order_status(order_id)
                if Return_Status.upper() == "COMPLETE":
                    average_price = get_order_price(order_id)
                if Return_Status.upper() == "REJECTED":
                    strMsg = f" Error in Order Placement Ord_ID = {order_id}, Ord_STS = {Placed_Status}, Ret_STS = {Return_Status}.Exiting Algo"
                    iLog(strMsg,4,sendTeleMsg=True)
                    if ExitTradenow ==1:
                        set_config_value("algo","ExitTradenow","0")
                        savedata()                
                    sys.exit()

                if average_price>0 and Return_Status.upper() == "COMPLETE":
                    PE_Buy_Exit_Price=average_price
                strMsg = f" Placed PE Sell Market order Stike: {strike_pe} ATM PE={average_price}, Qty ={Index_qty}, Ord_ID = {order_id}, Ord_STS = {Placed_Status}, Ret_STS = {Return_Status}"
                iLog(strMsg,5,sendTeleMsg=True)

            PE_Buy_Exit_Triggered = True
            Paper_MTM_Booked = round((Paper_MTM_Booked + Index_qty*(PE_Buy_Exit_Price-PE_Buy_Entry_Price)),0)
            Paper_MTM = Paper_MTM_Booked
            strMsg = f" Paper_MTM_Booked = {Paper_MTM_Booked}"
            iLog(strMsg,sendTeleMsg=True)


    if CE_Buy_Entry_Triggered == True and CE_Buy_Exit_Triggered == False:
        Paper_MTM = Paper_MTM_Booked+round(Index_qty*(ltp_Index_ATM_CE-CE_Buy_Entry_Price),0)

    if PE_Buy_Entry_Triggered == True and PE_Buy_Exit_Triggered == False:
        Paper_MTM = Paper_MTM_Booked+round(Index_qty*(ltp_Index_ATM_PE-PE_Buy_Entry_Price),0)


    cur_min = datetime.datetime.now().minute
    if( cur_min % log_interval == 0 and log_min != cur_min):
        log_min = cur_min     # Set the minute flag to run the code only once post the interval
        t1 = time.time()      # Set timer to record the processing time of all the indicators
        
        if CE_Buy_Entry_Triggered==True and CE_Buy_Exit_Triggered==False:
            strMsg = f" CE Buy Price {CE_Buy_Entry_Price} (SL,LTP,Target) : ({CE_SL},{ltp_Index_ATM_CE},{CE_TGT}) , Paper_MTM_Booked = {Paper_MTM_Booked}, Paper_MTM = {Paper_MTM}"
            iLog(strMsg,sendTeleMsg=True)
        
        if PE_Buy_Entry_Triggered==True and PE_Buy_Exit_Triggered==False:
            strMsg = f" PE Buy Price {PE_Buy_Entry_Price} (SL,LTP,Target) : ({PE_SL},{ltp_Index_ATM_PE},{PE_TGT}) , Paper_MTM_Booked = {Paper_MTM_Booked}, Paper_MTM = {Paper_MTM}"
            iLog(strMsg,sendTeleMsg=True)

        if PE_Entry_Triggered==False and CE_Entry_Triggered==False:
            strMsg = f" Waiting for First Entry: {strike_ce} CE (LTP,buy_price) : ({ltp_Index_ATM_CE},{CE_Buy_Price}), {strike_pe} PE (LTP,buy_price) : ({ltp_Index_ATM_PE},{PE_Buy_Price})"
            iLog(strMsg,1,sendTeleMsg=True)

        if CE_Buy_Exit_Triggered==True and PE_Buy_Entry_Triggered==False:
            strMsg = f" Waiting for Second Entry: {strike_pe} PE (LTP,buy_price) : ({ltp_Index_ATM_PE},{PE_Buy_Price}), Paper_MTM_Booked = {Paper_MTM_Booked}, Paper_MTM = {Paper_MTM}"
            iLog(strMsg,1,sendTeleMsg=True)

        if PE_Buy_Exit_Triggered==True and CE_Buy_Entry_Triggered==False:
            strMsg = f" Waiting for Second Entry: {strike_ce} CE (LTP,buy_price) : ({ltp_Index_ATM_CE},{CE_Buy_Price}), Paper_MTM_Booked = {Paper_MTM_Booked}, Paper_MTM = {Paper_MTM}"
            iLog(strMsg,1,sendTeleMsg=True)




    cur_HHMM = int(datetime.datetime.now().strftime("%H%M"))
    if ((ExitTradenow ==1 or cur_HHMM>=ExitTime) and ((CE_Buy_Entry_Triggered == False and PE_Buy_Entry_Triggered == False)\
            or (CE_Buy_Exit_Triggered == True and PE_Buy_Entry_Triggered == False) or (PE_Buy_Exit_Triggered == True and CE_Buy_Entry_Triggered == False)))\
            or ((CE_Buy_Exit_Triggered == True and PE_Buy_Exit_Triggered == True)):

        strMsg = f" Paper_MTM = {Paper_MTM}"
        iLog(strMsg,sendTeleMsg=True)

        with open(r"./PNL/" + log_file_name + "_PNL.txt", 'a',newline='') as f_object:
            writer_object = writer(f_object)
            List=[datetime.datetime.now().strftime("%Y%m%d"),papertrade,Paper_MTM]
            writer_object.writerow(List)
            f_object.close()
        set_config_value("algo","ExitTradenow","0")
        savedata()
        iLog(" Shutter down... Calling sys.exit() @ " + str(cur_HHMM),4,sendTeleMsg=True)
        sys.exit()


    cur_HHMM = int(datetime.datetime.now().strftime("%H%M"))
    if cur_HHMM > 1530 and cur_HHMM < 1532 :   # Exit the program post NSE closure
        with open(r"./PNL/" + log_file_name + "_PNL.txt", 'a',newline='') as f_object:
            writer_object = writer(f_object)
            List=[datetime.datetime.now().strftime("%Y%m%d"),papertrade,Paper_MTM]
            writer_object.writerow(List)
            f_object.close()    
        iLog(" Shutter down... Calling sys.exit() @ " + str(cur_HHMM),4,sendTeleMsg=True)
        sys.exit()

    #time.sleep(1)   # May be reduced to accomodate the processing delay


