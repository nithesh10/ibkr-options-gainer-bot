import datetime
import random
from ib_insync import *
import pytz
import creds
import time
timeZ_Ny = pytz.timezone('America/New_York')


def login():
        while True:
            try:
                random_id = random.randint(0, 9999)
                ib=IB()
                ibs=ib.connect('127.0.0.1', creds.port, clientId=random_id)
                print(datetime.now(timeZ_Ny) ," : ","connected")
                return ibs
            except:
                print(datetime.now(timeZ_Ny) ," : ","retrying to login in 5 seconds")
                time.sleep(5)
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
    scanCode='TOP_PERC_GAIN')

    tagValues = [
        TagValue("changePercAbove", "20"),
        TagValue('priceAbove', 5),
        TagValue('priceBelow', 50)]

    # the tagValues are given as 3rd argument; the 2nd argument must always be an empty list
    # (IB has not documented the 2nd argument and it's not clear what it does)
    scanData = ib.reqScannerData(sub, [], tagValues)

    symbols = [sd.contractDetails.contract.symbol for sd in scanData]
    print(symbols)