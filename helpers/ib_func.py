from datetime import datetime
import random
from ib_insync import *
import pytz
import creds
import time
import threading
import pandas as pd
from concurrent.futures import ThreadPoolExecutor,as_completed
from joblib import Parallel, delayed
timeZ_Ny = pytz.timezone('America/New_York')
lock = threading.Lock()


def close_all_positions(ib):
    print("closing all positions")
    for position in ib.positions():
        contract = position.contract
        [contract]=ib.qualifyContracts(contract)
        size = position.position
        if size > 0:  # Long position
            order = MarketOrder('SELL', abs(size))
        else:  # Short position
            order = MarketOrder('BUY', abs(size))
        trade = ib.placeOrder(contract, order)
        print(trade)
def login():
            print("trying to login")
            while True:  
                try:
                    random_id = random.randint(0, 9999)
                    ib=IB()
                    lock.acquire()
                    ibs=ib.connect('127.0.0.1', creds.port, clientId=random_id)
                    print(datetime.now(timeZ_Ny) ," : ","connected ")
                    lock.release()
                    return ibs
                except Exception as e:
                    lock.release()
                    print(e)
                    print(datetime.now(timeZ_Ny) ," : ","retrying to login in 60 seconds")
                    time.sleep(65)
                    pass
            
def isconnected(ib):
    if(ib.isConnected()):
        print(datetime.now(timeZ_Ny) ," : ","connected")
        ibs=ib
    else:
        ibs=login()
    return ibs
def get_random():
    random_id = random.randint(0, 9999)
    return random_id
def top_gainer_subscription(ib,scancode):
    sub = ScannerSubscription(
    instrument='STK',
    locationCode='STK.US.MAJOR',
    scanCode=scancode
    )
    tagValues = [
        #TagValue("changePercAbove", "5"),
        TagValue('hasOptionsIs', "true"),
        TagValue('priceAbove', creds.stock_price_above),
        TagValue('priceBelow', creds.stock_price_below),
        TagValue('optVolumeAbove', creds.stock_option_volume)]

    # the tagValues are given as 3rd argument; the 2nd argument must always be an empty list
    # (IB has not documented the 2nd argument and it's not clear what it does)
    print("scanning market")
    scanData = ib.reqScannerData(sub, [], tagValues)
    symbols = [sd.contractDetails.contract for sd in scanData]
    print(len(symbols))
    return symbols
def get_options_chain(contract,ib):
    ib.reqMarketDataType(creds.market_Data_type)
    chains = ib.reqSecDefOptParams(contract.symbol, '', contract.secType, contract.conId)
    util.df(chains)
    chains = next(c for c in chains)
    current_date = datetime.now()
    [ticker] = ib.reqTickers(contract)
    spxValue = ticker.marketPrice()
    
    strikes = [strike for strike in chains.strikes
        if strike % 5 == 0
        and spxValue - (creds.strikes_range*spxValue/100) < strike < spxValue + (creds.strikes_range*spxValue/100)]
    expirations = [
        exp for exp in chains.expirations
        if (datetime.strptime(exp, '%Y%m%d') - current_date).days <= creds.options_days_to_Expiry
    ]
    expirations = sorted(expirations)
    rights = ['P', 'C']

    contracts = [Option(contract.symbol, expiration, strike, right, 'SMART')
            for right in rights
            for expiration in expirations
            for strike in strikes]

    contracts = ib.qualifyContracts(*contracts)
    print(contract.symbol,len(contracts))
    if(len(contracts)>300):
         contracts=contracts[:300]
    return contracts

def check_perc_change(ib,contract,ticker,direction):
        current_price = ticker.last
        bars = ib.reqHistoricalData(contract, endDateTime='', durationStr='1 D', barSizeSetting='1 min', whatToShow='TRADES', useRTH=True)
        if len(bars)>0:
            open_price = bars[0].open
            percentage_change = ((current_price - open_price) / open_price) * 100
            #percentage_change=100
            if str(direction)=="BUY":
                if percentage_change >= creds.option_perc:
                        return ({
                        'symbol':contract.symbol,
                        'contract': contract,
                        'gain': percentage_change})
            else:
                print("direction is",direction," and percentage change is ",percentage_change)
                if percentage_change <= creds.option_perc:
                        return ({
                        'symbol':contract.symbol,
                        'contract': contract,
                        'gain': percentage_change})
        return None
def filter_contracts(ib, contracts,symbol_direction_dict):
    def process_ticker(contract, ticker):
        if ((ticker.volume < creds.option_contract_volume) or (str(ticker.volume) == "nan")):
            print(str(ticker.volume),"volume condition not met")
            return None
        current_price = ticker.last
        if current_price > creds.option_max_price:
            if current_price<creds.option_min_price:
                print("price condition not met",current_price)
                return None
        print("price is", current_price, "volume is ", ticker.volume)
        bid_price=ticker.bid #test
        ask_price=ticker.ask #test
        if(abs(ask_price-bid_price)>creds.bid_ask_diff):
             print("bid ask condition not met:- ",abs(ask_price-bid_price))
             return None
        
        open_interest = ticker.futuresOpenInterest
        if(open_interest != "nan"):
            print("OI is ",open_interest)
            if(open_interest>creds.max_open_intrest):
                return None
        print("filter passed")
        return (contract, ticker)

    def process_selected_item(process,symbol_direction_dict):
        contract, ticker = process
        print(contract)
        
        symbol=contract.symbol
        direction = symbol_direction_dict.get(symbol)
        print(symbol,direction)
        result = check_perc_change(ib, contract, ticker,direction)
        if result:
            return result
        return None

    prices = ib.reqTickers(*contracts)

    with ThreadPoolExecutor() as executor:
        selected = list(executor.map(process_ticker, contracts, prices))
        selected = [item for item in selected if item]  # Filter out None values
    print("length of selected is",len(selected))
    final=[]
    for item in selected:
        i=process_selected_item(item,symbol_direction_dict)
        if i:
            print(i,"%")
            final.append(i)
    #with ThreadPoolExecutor(max_workers=10) as executor:
    #    final = list(executor.map(process_selected_item, selected))
    #    final = [item for item in final if item]  # Filter out None values

    print(final)
    #process_selected(final)
    return final

def process_selected(selected):
    top_options_df = pd.DataFrame(selected)
    with lock:
        try:
            existing_df = pd.read_csv("options.csv")
        except pd.errors.EmptyDataError:
            existing_df = pd.DataFrame(columns=['symbol', 'contract', 'gain'])
        final_df = pd.concat([existing_df, top_options_df], ignore_index=True)
        final_df.to_csv("options.csv", index=False)

    