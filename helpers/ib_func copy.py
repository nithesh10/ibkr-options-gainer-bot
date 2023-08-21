from datetime import datetime
import random
from ib_insync import *
import pytz
import creds
import time
import threading
import pandas as pd
from concurrent.futures import ThreadPoolExecutor,as_completed
timeZ_Ny = pytz.timezone('America/New_York')
lock = threading.Lock()
def login():
        with lock:
            print("trying to login")
            while True:  
                try:
                    random_id = random.randint(0, 9999)
                    ib=IB()
                    ibs=ib.connect('127.0.0.1', creds.port, clientId=random_id)
                    print(datetime.now(timeZ_Ny) ," : ","connected ")
                    return ibs
                except Exception as e:
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
def top_gainer_subscription(ib):
    sub = ScannerSubscription(
    instrument='STK',
    locationCode='STK.US.MAJOR',
    scanCode=creds.scan_code)

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
    ib.reqMarketDataType(1)
    chains = ib.reqSecDefOptParams(contract.symbol, '', contract.secType, contract.conId)
    util.df(chains)
    chains = next(c for c in chains)
    current_date = datetime.now()
    [ticker] = ib.reqTickers(contract)
    spxValue = ticker.marketPrice()
    strikes = [strike for strike in chains.strikes
        if strike % 5 == 0
        and spxValue - 20 < strike < spxValue + 20]
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
    return contracts
def process_ticker(ticker, contract,ib):
    if ((ticker.volume < creds.option_contract_volume) or (str(ticker.volume) == "nan")):
        return None
    current_price = ticker.last
    if current_price > creds.option_max_price:
        return None
    print("price is", current_price, "volume is ", ticker.volume)
    # Calculate the percentage change
    bars = ib.reqHistoricalData(contract, endDateTime='', durationStr='1 D', barSizeSetting='1 min', whatToShow='TRADES', useRTH=True)
    open_price = bars[0].open
    percentage_change = ((current_price - open_price) / open_price) * 100
    if percentage_change >= creds.option_perc:
        return {
            'symbol': contract.symbol,
            'contract': contract,
            'gain': percentage_change}
    return None

def filter_contracts(ib, contracts):
    selected = []
    prices = ib.reqTickers(*contracts)
    
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = [executor.submit(process_ticker, ticker, contract,ib) for ticker, contract in zip(prices, contracts)]
        for future in as_completed(futures):
            result = future.result()
            if result:
                selected.append(result)
    
    print(selected)
    top_options_df = pd.DataFrame(selected)
    
    with lock:
        try:
            existing_df = pd.read_csv("options.csv")
        except pd.errors.EmptyDataError:
            existing_df = pd.DataFrame(columns=['symbol', 'contract', 'gain'])
        final_df = pd.concat([existing_df, top_options_df], ignore_index=True)
        final_df.to_csv("options.csv", index=False)

    return selected