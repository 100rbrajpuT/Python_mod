def SuperTrend(data , period = 10, multiplier=3, ohlc=['open', 'high', 'low', 'close']):
        global supertrend
        data['tr0'] = abs(data["high"] - data["low"])
        data['tr1'] = abs(data["high"] - data["close"].shift(1))
        data['tr2'] = abs(data["low"]- data["close"].shift(1))
        data["TR"] = round(data[['tr0', 'tr1', 'tr2']].max(axis=1),2)
        data["ATR"]=0.00
        data['BUB']=0.00
        data["BLB"]=0.00
        data["final_ub"]=0.00
        data["final_lb"]=0.00
        data["ST"]=0.00
        for i, row in data.iterrows():
            if i == 0:
                data.loc[i,'ATR'] = 0.00#data['ATR'].iat[0]
            else:
                data.loc[i,'ATR'] = ((data.loc[i-1,'ATR'] * (period-1))+data.loc[i,'TR'])/period
        data['BUB'] = round(((data["high"] + data["low"]) / 2) + (multiplier * data["ATR"]),2)
        data['BLB'] = round(((data["high"] + data["low"]) / 2) - (multiplier * data["ATR"]),2)
        for i, row in data.iterrows():
            if i==0:
                data.loc[i,"final_ub"]=0.00
            else:
                if (data.loc[i,"BUB"]<data.loc[i-1,"final_ub"])|(data.loc[i-1,"close"]>data.loc[i-1,"final_ub"]):
                    data.loc[i,"final_ub"]=data.loc[i,"BUB"]
                else:
                    data.loc[i,"final_ub"]=data.loc[i-1,"final_ub"]

        for i, row in data.iterrows():
            if i==0:
                data.loc[i,"final_lb"]=0.00
            else:
                if (data.loc[i,"BLB"]>data.loc[i-1,"final_lb"])|(data.loc[i-1,"close"]<data.loc[i-1,"final_lb"]):
                    data.loc[i,"final_lb"]=data.loc[i,"BLB"]
                else:
                    data.loc[i,"final_lb"]=data.loc[i-1,"final_lb"]

        for i, row in data.iterrows():
            if i==0:
                data.loc[i,"ST"]=0.00
            elif (data.loc[i-1,"ST"]==data.loc[i-1,"final_ub"]) & (data.loc[i,"close"]<=data.loc[i,"final_ub"]):
                data.loc[i,"ST"]=data.loc[i,"final_ub"]
            elif (data.loc[i-1,"ST"]==data.loc[i-1,"final_ub"])&(data.loc[i,"close"]>data.loc[i,"final_ub"]):
                data.loc[i,"ST"]=data.loc[i,"final_lb"]
            elif (data.loc[i-1,"ST"]==data.loc[i-1,"final_lb"])&(data.loc[i,"close"]>=data.loc[i,"final_lb"]):
                data.loc[i,"ST"]=data.loc[i,"final_lb"]
            elif (data.loc[i-1,"ST"]==data.loc[i-1,"final_lb"])&(data.loc[i,"close"]<data.loc[i,"final_lb"]):
                data.loc[i,"ST"]=data.loc[i,"final_ub"]

        # Buy Sell Indicator
        for i, row in data.iterrows():
            if i==0:
                data["STX"]="NA"
            elif (data.loc[i,"ST"]<data.loc[i,"close"]) :
                data.loc[i,"STX"]="green"
            else:
                data.loc[i,"STX"]="red"
        data.drop(['tr0', 'tr1', 'tr2', 'TR','BUB', 'BLB'], inplace=True, axis=1)
        return data