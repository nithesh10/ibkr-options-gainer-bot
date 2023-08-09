from ib_insync import *
from helpers.ib_func import get_options_chain, login, top_gainer_subscription,filter_contracts
from models.ib import IBWrapper
from concurrent.futures import ThreadPoolExecutor
import asyncio
import multiprocessing as mp
import concurrent.futures as cf
def process_symbol(symbol):
    ibkr = IBWrapper()
    ibkr.connect()
    contracts = get_options_chain(symbol, ibkr.ib)
    return filter_contracts(ibkr.ib, contracts)
def main_process(ib):
    symbols = top_gainer_subscription(ib)
    top_option_list = []

    # Using ProcessPoolExecutor to run process_symbol in parallel
    with cf.ProcessPoolExecutor(max_workers=25) as executor:
        results = list(executor.map(process_symbol, [(symbol) for symbol in symbols]))

    for result in results:
        top_option_list.extend(result)

    print(top_option_list)
    print(sorted(top_option_list, key=lambda x: x['gain'], reverse=True))
if __name__ == '__main__':
    mp.set_start_method('spawn')
    ibkr = IBWrapper()
    ibkr.connect()
    main_process(ibkr.ib)