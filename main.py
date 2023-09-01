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
def process_symbols_batch(symbols_batch,symbol_direction_dict):
    sym=""
    for symbol in symbols_batch:
        sym+=symbol+"_"
    logger(f"storage/{sym}")
    print(symbol_direction_dict)
    results = []
    ibkr = IBWrapper()
    ibkr.connect()
    if len(symbols_batch)!=0: 
        for symbol in symbols_batch:    
            contracts = get_options_chain(symbol, ibkr.ib)
            filtered_results = filter_contracts(ibkr.ib, contracts,symbol_direction_dict)
            if filtered_results:  # Check if the list is not empty
                results.extend(filtered_results)
                print("results extended")
    ibkr.disconnect()
    print("disconnected")
    return results
symbol_direction_dict={}
contract_direction_dict={}
def main_process(ibkr):
    global symbol_direction_dict
    ib = ibkr.ib
    #global symbol_direction_dict
    print(creds.direction)
    for code,n,dir in zip(creds.scan_code,creds.top_n,creds.direction):
        print(code,n,dir)
        symbols = top_gainer_subscription(ib,code)
        symbols=symbols[:n]
        for symbol in symbols:
            contract_direction_dict[symbol] = dir
            symbol_direction_dict[symbol.symbol]=dir
    print(symbol_direction_dict)
    symbols = list(contract_direction_dict.keys())

    top_option_list = []
    ibkr.disconnect()
    
    # Split symbols into batches of 4
    symbols_batches = [symbols[i:i+creds.batches] for i in range(0, len(symbols), creds.batches)]
    #symbols_batches=[symbols_batches[0],symbols_batches[1],symbols_batches[2]]
    # Using ProcessPoolExecutor to run process_symbols_batch in parallel
    with cf.ProcessPoolExecutor(max_workers=creds.workers) as executor:
        results = list(executor.map(process_symbols_batch, symbols_batches,([symbol_direction_dict]*len(symbols_batches))))
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
def count_digits_before_decimal(number):
		if isinstance(number, (int, float)):
			str_number = str(number)
			if '.' in str_number:
				digits_before_decimal = len(str_number.split('.')[0])
				digits_after_decimal = len(str_number.split('.')[1])
				return digits_before_decimal,digits_after_decimal
			else:
				return len(str_number),0
		else:
			raise ValueError("Input must be an integer or a float")

def get_valid_precision(price: float, min_tick: float) -> float:
	"""
	Convert the price into a valid tick size with precision\n
	"""
	valid_price = int(price / min_tick) * min_tick
	digits,decimals=count_digits_before_decimal(min_tick)
	valid_price=round(valid_price,decimals)
	print("valid price is",abs(valid_price),price)
	return valid_price
def trader(ib):
    top_option_df=pd.read_csv("options_final.csv")
    top_gainers = top_option_df.loc[top_option_df.groupby('symbol')['gain'].idxmax()]
    top_gainers = top_gainers[top_gainers['gain'] > 0]
    
    top_gainers.to_csv("gainers.csv")
    contracts=top_gainers["contract"].to_list()
    contracts=[eval(contract) for contract in contracts]
    contracts = ib.qualifyContracts(*contracts)
    for contract in contracts:
        details = ib.reqContractDetails(contract)
        min_tick=details[0].minTick
        print(min_tick)
        [ticker] = ib.reqTickers(contract)
        bid_price = ticker.bid
        ask_price = ticker.ask
        if(creds.mid_price==1):
            print(creds.mid_price)
            buy_order = Order(action='BUY',orderType="PEG MID",totalQuantity=creds.contracts_qty)  # Assuming you're buying 1 contract. Modify the quantity as needed.
        elif creds.mid_price==-1:
            mid_price = float((bid_price + ask_price) / 2)
            buy_order = LimitOrder('BUY', creds.contracts_qty,ask_price)
        else:
            buy_order = MarketOrder('BUY', creds.contracts_qty)
        buy_trade = ib.placeOrder(contract, buy_order)
        
        while not buy_trade.isDone():
            ib.sleep(1)
        # Get the fill price of the buy order
        print(buy_trade)
        fill_price = buy_trade.orderStatus.avgFillPrice
        # Create take profit order with OCA group
        take_profit_price = get_valid_precision(abs(fill_price) + ((creds.tp_perc/100)*abs(fill_price)),min_tick)  # Adjust for 20 cents

        tp_order = LimitOrder('SELL', creds.contracts_qty, take_profit_price)
        #tp_order.ocaGroup = 'TP_OCA_GROUP'
        #tp_order.ocaType = 1  # Cancel all remaining orders in the group when one fills
        
        tp_trade = ib.placeOrder(contract, tp_order)
        print("tp limit order placed")
    if "SELL" in creds.direction:
        top_losers = top_option_df.loc[top_option_df.groupby('symbol')['gain'].idxmin()]
        top_losers= top_losers[top_losers['gain'] < 0]
        top_losers.to_csv("losers.csv")
        contracts=top_losers["contract"].to_list()
        contracts=[eval(contract) for contract in contracts]
        contracts = ib.qualifyContracts(*contracts)
        for contract in contracts:
            details = ib.reqContractDetails(contract)
            min_tick=details[0].minTick
            
            [ticker] = ib.reqTickers(contract)
            bid_price = ticker.bid
            ask_price = ticker.ask
            if creds.mid_price==1:
                buy_order = Order(action='SELL',orderType="PEG MID",totalQuantity=creds.contracts_qty)
            elif creds.mid_price==-1:
                mid_price = float((bid_price + ask_price) / 2)
                print(mid_price)
                buy_order = LimitOrder('SELL', creds.contracts_qty,bid_price)  # Assuming you're buying 1 contract. Modify the quantity as needed.
            else:
                buy_order = MarketOrder('SELL', creds.contracts_qty)
            buy_trade = ib.placeOrder(contract, buy_order)
            
            while not buy_trade.isDone():
                ib.sleep(1)
            # Get the fill price of the buy order
            print(buy_trade)
            fill_price = buy_trade.orderStatus.avgFillPrice
            # Create take profit order with OCA group
            take_profit_price = get_valid_precision(abs(fill_price) - ((creds.tp_perc/100)*abs(fill_price)),min_tick)  # Adjust for 20 cents

            tp_order = LimitOrder('BUY', creds.contracts_qty, take_profit_price)
            #tp_order.ocaGroup = 'TP_OCA_GROUP'
            #tp_order.ocaType = 1  # Cancel all remaining orders in the group when one fills
            
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
            now=datetime.now()
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