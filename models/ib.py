from ib_insync import IB, Stock, Forex, util
import creds
from helpers.ib_func import login

class IBWrapper:
    def __init__(self):
        self.ib = IB()
    
    def connectAsync(self):
        self.ib=login()
    def connect(self):
        self.ib=login()
        
    def disconnect(self):
        self.ib.disconnect()
        
    def get_account_summary(self):
        return self.ib.accountSummary()
        
    def get_positions(self):
        return self.ib.positions()

    def get_fx_rate(self, pair):
        forex_contract = Forex(pair)
        ticker = self.ib.reqMktData(forex_contract, '', False, False)
        return ticker
