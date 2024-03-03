# to install: 
# pip install pytrends
# pip install yfinance

# import
from datetime import date
from datetime import timedelta
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from pytrends.request import TrendReq
from sklearn.linear_model import LinearRegression
from sklearn.datasets import make_regression

''' 
helper function that produce a computer name that is more likely to be searched
'''
def smart_comp_name(comp_name):
  cn_list = comp_name.split(' ')
  smart = ''
  if len(cn_list) >= 2:
    if cn_list[1] == 'Inc' or cn_list[1] == 'Inc.':
      smart = cn_list[0]
    else:
      smart = cn_list[0] + " " + cn_list[1]
  else:
    smart = cn_list[0]
  return smart

'''
helper function that add a new row to data, fetch day in history (for example, if fetch day is from monday, then we fetch data from last friday)
  data: CompanyID Date LastPrice Word1 Word2 ... GrowthRate
  firm_struct: CompanyId CompanyName
  date: datetime instance
  word_list: list of words to fetch data from pytrends
  pytrends: TrendReq instance
  can fetch data from at most 1 month ago. If date is today, fetch data from yesterday
'''
def add_par_day_firm(data, firm_struct, fetch_date, word_list, pytrends):
  smart_name = smart_comp_name(firm_struct['CompanyName'])
  
  # get actual date (only if today), if time is before 9pm, return
  if fetch_date == date.today() and datetime.now().hour < 21:
    print("this function can only fetch data from yesterday or before")
    return

  # check if fetch date is already in data
  if fetch_date in data['Date']:
    print(firm_struct['CompanyName'] + " already has data for " + str(fetch_date))
    return
  
  # get stock price day before fetch date
  stock_info = yf.download(firm_struct['CompanyId'], str(fetch_date - timedelta(days = 7)), str(fetch_date + timedelta(days = 1)))
  if stock_info.empty:
    print(firm_struct['CompanyName'] + " has no stock price data")
    return
  
  #get stock price day after fetch date
  stock_reverse = stock_info.sort_index(ascending=False)
  if stock_reverse.iloc[0].name.date() != fetch_date:
    print(stock_reverse)
    print(firm_struct['CompanyName'] + " has no stock price data at fetch date " + str(fetch_date))
    return
  fetch_day_price = stock_reverse.iloc[0]['Close']
  last_day_price = stock_reverse.iloc[1]['Close']

  last_day = stock_reverse.iloc[1].name.date()
  
  # calculate growth rate
  growth_rate = (fetch_day_price - last_day_price) / last_day_price


  # fetch data for word list from pytrends
  search_list = ['"' + smart_name +  '" + "' + e + '"' for e in word_list]
  # if date is within 7 days, fetch data for 7 days
  if last_day > date.today() - timedelta(days = 7):
    fetch_timeframe = "now 7-d"
  elif last_day > date.today() - timedelta(days = 30):
    fetch_timeframe = "today 1-m"
  else:
    fetch_timeframe = "today 3-m"

  word_data_list = []
  
  for i in range(len(word_list)):
    sub_list = search_list[i:i+1]
    pytrends.build_payload(sub_list, cat=0, timeframe=fetch_timeframe, geo='US')
    trend = pytrends.interest_over_time()
    trend = trend.drop(['isPartial'], axis=1)
    trend = trend.resample('D').sum()
    trend_data = trend.loc[str(last_day):str(fetch_date - timedelta(days = 1))].mean()[0]
    word_data_list.append(trend_data)
  
  # insert new data into data
  to_insert = [firm_struct['CompanyId'], fetch_date, last_day_price] + word_data_list + [growth_rate]
  data.loc[len(data)] = to_insert

'''
'''
def update_monthly_data():
  return

'''
helper function that update data from a range of dates, maximum from 85 days ago.
  data: CompanyID Date LastPrice Word1 Word2 ... GrowthRate
  firms: list of firm_struct
  word_list: list of words to fetch data from pytrends
  bg_date: datetime instance of beginning date
  ed_date: datetime instance of ending date
  pytrends: TrendReq instance
'''
def update_data_in_date_range(data, firms, word_list, bg_date, ed_date, pytrends):
  if ed_date > date.today():
    print("cannot fetch data from future")
    return
  if ed_date < bg_date:
    print("end date cannot be before beginning date")
    return
  if bg_date < date.today() - timedelta(days = 85):
    print("can only fetch data from 85 days ago")
    return
  
  last_day = bg_date

  while last_day <= ed_date:
    for index, firm in firms.iterrows():
      add_par_day_firm(data, firm, last_day, word_list, pytrends)
    last_day = last_day + timedelta(days = 1)

'''
helper function that update data several days till today, maximum from 85 days ago.
'''
def update_data_till_today(data, firms, word_list, num_days, pytrends):
  if num_days > 85:
    print("can only fetch data from 85 days ago")
    return
  update_data_in_date_range(data, firms, word_list, date.today() - timedelta(days = num_days), date.today(), pytrends)

'''
update data for past 30 days, saving the data_path
'''
def update_data(data_path):
  # load data
  # word_list = ['valuable', 'successful', 'candid', 'organic', 'steadfast', 'talented', 'unique', 'interesting', 'functional', 'educated', 
  #              'ready', 'credible', 'substantial', 'workable', 'perfect', 'possible', 'supreme', 'focused', 'maintainable', 'threatening']
  word_list = ['valuable', 'successful', 'candid', 'organic']
  try:
    # Try to read the CSV file
    data = pd.read_csv(data_path)
  except FileNotFoundError:
    print("File not found. Creating a new DataFrame.")
    data = pd.DataFrame(columns = ['CompanyID', 'Date', 'LastPrice'] + word_list + ['GrowthRate'])

  firms = pd.read_csv('companies_data.csv')
  firms = firms[['CompanyId', 'CompanyName']]
  firms = firms.sample(n=1, random_state=1)
  pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25), retries=2, backoff_factor=0.1, requests_args={'verify':False})

  update_data_till_today(data, firms, word_list, 30, pytrends)

  # save data
  data.to_csv(data_path, index=False)

# def get_parx_day_firm(data, firm_struct, fetch_date, word_list, pytrends):

update_data('test_data.csv')

