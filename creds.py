port=7497      #7496 -paper trading #7497-live accounts

start_hour=9
start_minutes=15
end_hour=15
end_minutes=45


contracts_qty=10
tp_perc=10

mid_price=0 #[1]-mid [-1]-limit [0]-market
market_Data_type=1
#stock filter
scan_code=["TOP_OPEN_PERC_LOSE","TOP_OPEN_PERC_GAIN"]
top_n=[20,20] #analyse top n contracts from the filter (must be less than 50)
direction=["SELL","SELL"]
#"TOP_OPEN_PERC_GAIN" #HOT_BY_OPT_VOLUME #OPT_OPEN_INTEREST_MOST_ACTIVE #OPT_VOLUME_MOST_ACTIVE #TOP_OPT_IMP_VOLAT_GAIN
#'TOP_OPEN_PERC_GAIN', 'TOP_OPEN_PERC_LOSE', 'HIGH_OPEN_GAP', 'LOW_OPEN_GAP', 'TOP_AFTER_HOURS_PERC_GAIN', 'TOP_AFTER_HOURS_PERC_LOSE', 
# 'HIGH_OPT_IMP_VOLAT', 'LOW_OPT_IMP_VOLAT', 'TOP_OPT_IMP_VOLAT_GAIN', 'TOP_OPT_IMP_VOLAT_LOSE', 'HIGH_OPT_IMP_VOLAT_OVER_HIST', 'LOW_OPT_IMP_VOLAT_OVER_HIST', 'OPT_VOLUME_MOST_ACTIVE', 

strikes_range=20 #%
stock_price_above=75
stock_price_below=750
stock_option_volume=500

#options filter
option_contract_volume=500
option_max_price=15
option_min_price=1
options_days_to_Expiry=30
option_perc=75
bid_ask_diff=0.20
min_open_intrest=500

#parallelize
workers=8
batches=3 #symbols handled per worker