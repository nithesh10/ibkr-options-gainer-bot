from ib_insync import *
from helpers.ib_func import login, top_gainer_subscription
from models.ib import IBWrapper


if __name__ == '__main__':
    ibkr=IBWrapper()
    ibkr.connect()
    top_gainer_subscription(ibkr.ib)