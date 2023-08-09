from ib_insync import *
import pandas as pd
from helpers.ib_func import get_options_chain, login, top_gainer_subscription,filter_contracts
from models.ib import IBWrapper
from concurrent.futures import ThreadPoolExecutor
import asyncio
import multiprocessing as mp
import concurrent.futures as cf
from itertools import chain
from datetime import datetime
def process_symbols_batch(symbols_batch):
    results = []
    ibkr = IBWrapper()
    ibkr.connect()
    for symbol in symbols_batch:    
        contracts = get_options_chain(symbol, ibkr.ib)
        results.extend(filter_contracts(ibkr.ib, contracts))
    ibkr.disconnect()
    return results
def main_process(ibkr):
    ib = ibkr.ib
    symbols = top_gainer_subscription(ib)
    top_option_list = []
    ibkr.disconnect()
    
    # Split symbols into batches of 4
    symbols_batches = [symbols[i:i+5] for i in range(0, len(symbols), 5)]
    #symbols_batches=[symbols_batches[0],symbols_batches[1],symbols_batches[2]]
    # Using ProcessPoolExecutor to run process_symbols_batch in parallel
    with cf.ProcessPoolExecutor(max_workers=7) as executor:
        results = list(executor.map(process_symbols_batch, symbols_batches))
    # Flatten the results
    top_option_list = list(chain.from_iterable(results))
    top_options_df = pd.DataFrame(top_option_list)
    # (Optional) Sort the DataFrame by gain
    top_options_df = top_options_df.sort_values('gain', ascending=False)
    print(top_options_df)
    top_options_df.to_csv("options_final.csv")

    print(top_option_list)
    print(sorted(top_option_list, key=lambda x: x['gain'], reverse=True))

if __name__ == '__main__':
    now=datetime.now()
    mp.set_start_method('spawn')
    ibkr = IBWrapper()
    ibkr.connect()
    main_process(ibkr)
    now2=datetime.now()
    print("Total Time Taken",now2-now)