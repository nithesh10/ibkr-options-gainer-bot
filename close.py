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
ibkr = IBWrapper()
ibkr.connect()
close_all_positions(ibkr.ib)


