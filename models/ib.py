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

    def place_order(self, symbol, quantity, order_type='Market', action='BUY'):
        contract = Stock(symbol, 'SMART', 'USD')
        if order_type == 'Market':
            order = MarketOrder(action, quantity)
        else:
            raise ValueError("Unsupported order type")
        
        trade = self.ib.placeOrder(contract, order)
        return trade

    def get_fx_rate(self, pair):
        forex_contract = Forex(pair)
        ticker = self.ib.reqMktData(forex_contract, '', False, False)
        return ticker
