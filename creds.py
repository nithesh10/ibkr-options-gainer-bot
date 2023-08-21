port=7497      #7496 -paper trading #7497-live accounts

start_hour=9
start_minutes=30
end_hour=16
end_minutes=0


contracts_qty=1
tp_perc=20
top_n=35 #analyse top n contracts from the filter (must be less than 50)

market_Data_type=1
#stock filter
scan_code="TOP_OPT_IMP_VOLAT_GAIN" 
#"TOP_OPEN_PERC_GAIN" #HOT_BY_OPT_VOLUME #OPT_OPEN_INTEREST_MOST_ACTIVE #OPT_VOLUME_MOST_ACTIVE #TOP_OPT_IMP_VOLAT_GAIN

strikes_range=20 #%
stock_price_above=75
stock_price_below=750
stock_option_volume=500

#options filter
option_contract_volume=500
option_max_price=25
options_days_to_Expiry=30
option_perc=20