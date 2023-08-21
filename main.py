import time
from ib_insync import *
import pandas as pd
from helpers.ib_func import close_all_positions, get_options_chain, login, top_gainer_subscription,filter_contracts
from models.ib import IBWrapper
from concurrent.futures import ThreadPoolExecutor
import asyncio
import multiprocessing as mp
import concurrent.futures as cf
from itertools import chain
from datetime import datetime
import creds
import pytz
from helpers.log import logger
eastern = pytz.timezone('US/Eastern')
def process_symbols_batch(symbols_batch):
    results = []
    ibkr = IBWrapper()
    ibkr.connect()
    if len(symbols_batch)!=0: 
        for symbol in symbols_batch:    
            contracts = get_options_chain(symbol, ibkr.ib)
            filtered_results = filter_contracts(ibkr.ib, contracts)
            if filtered_results:  # Check if the list is not empty
                results.extend(filtered_results)
                print("results extended")
    ibkr.disconnect()
    print("disconnected")
    return results
def main_process(ibkr):
    ib = ibkr.ib
    symbols = top_gainer_subscription(ib)
    symbols=symbols[:35]
    top_option_list = []
    ibkr.disconnect()
    
    # Split symbols into batches of 4
    symbols_batches = [symbols[i:i+5] for i in range(0, len(symbols), 5)]
    #symbols_batches=[symbols_batches[0],symbols_batches[1],symbols_batches[2]]
    # Using ProcessPoolExecutor to run process_symbols_batch in parallel
    with cf.ProcessPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(process_symbols_batch, symbols_batches))
    print("got all results")
    # Flatten the results
    top_option_list = list(chain.from_iterable(results))
    top_options_df = pd.DataFrame(top_option_list)
    print(top_options_df)
    # (Optional) Sort the DataFrame by gain
    #top_options_df = top_options_df.sort_values('gain', ascending=False)
    print(top_options_df)
    top_options_df.to_csv("options_final.csv")
    #print(sorted(top_option_list, key=lambda x: x['gain'], reverse=True))
def trader(ib):
    top_option_df=pd.read_csv("options_final.csv")
    top_gainers = top_option_df.loc[top_option_df.groupby('symbol')['gain'].idxmax()]
    top_gainers.to_csv("options.csv")
    contracts=top_gainers["contract"].to_list()
    contracts=[eval(contract) for contract in contracts]
    print(contracts)
    contracts = ib.qualifyContracts(*contracts)
    for contract in contracts:
        buy_order = MarketOrder('BUY', creds.contracts_qty)  # Assuming you're buying 1 contract. Modify the quantity as needed.
        buy_trade = ib.placeOrder(contract, buy_order)
        
        while not buy_trade.isDone():
            ib.sleep(1)
        # Get the fill price of the buy order
        print(buy_trade)
        fill_price = buy_trade.orderStatus.avgFillPrice
        # Create take profit order with OCA group
        take_profit_price = fill_price + (creds.tp_perc/100)  # Adjust for 20 cents
        tp_order = LimitOrder('SELL', creds.contracts_qty, take_profit_price)
        tp_order.ocaGroup = 'TP_OCA_GROUP'
        tp_order.ocaType = 1  # Cancel all remaining orders in the group when one fills
        
        tp_trade = ib.placeOrder(contract, tp_order)
        print("tp limit order placed")
def check_close_time(ib):
    
    local_now = datetime.now()
    ny_time = local_now.astimezone(eastern)

    close_time = ny_time.replace(hour=creds.end_hour, minute=creds.end_minutes, second=0, microsecond=0)

    # Wait till the close time
    while local_now.astimezone(eastern) < close_time:
        ib.sleep(1)
        print("waiting for bot close time")
        local_now = datetime.now()
    close_all_positions(ib)
if __name__ == '__main__':
    logger("storage")
    while True:
        local_now=datetime.now()
        ny_time = local_now.astimezone(eastern)
        if(ny_time>=ny_time.replace(hour=creds.start_hour,minute=creds.start_minutes)):
            print("time is:-",ny_time)
            mp.set_start_method('spawn')
            ibkr = IBWrapper()
            ibkr.connect()
            main_process(ibkr)
            now2=datetime.now()
            print("Total Time Taken to scan is",now2-now)
            ibkr.connect()
            trader(ibkr.ib)
            check_close_time(ibkr.ib)
            exit()
        else:
            time.sleep(1)