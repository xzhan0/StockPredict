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

# helper
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

  
# set up
companies = pd.read_csv("companies_data.csv")
companies = companies.sample(n=100, random_state=1) #sampling

pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25), retries=2, backoff_factor=0.1, requests_args={'verify':False})

# emotion_list = ['accessible', 'pleasing', 'candid', 'agreeable', 'balanced']
# emotion_list = ['accessible', 'pleasing']
emotion_list = ['valuable', 'successful', 'candid', 'organic', 'steadfast', 'talented', 'unique', 'interesting', 'functional', 'educated', 
            'ready', 'credible', 'substantial', 'workable', 'perfect', 'possible', 'supreme', 'focused', 'maintainable', 'threatening']

train_columns = ['CompanyID', 'Price'] + emotion_list + ['GrowthRate']
train_set = pd.DataFrame([], columns=train_columns)
predict_columns = ['CompanyID', 'Price'] + emotion_list
predict_set = pd.DataFrame([], columns=predict_columns)

# data making
end_day = date.today() - timedelta(days = 1)
for index, company in companies.iterrows():
  smart_name = smart_comp_name(company['CompanyName'])
  print("processing " + smart_name)
  search_list = ['"' + smart_name +  '" + "' + e + '"' for e in emotion_list]
  pytrends.build_payload(search_list, cat=0, timeframe="now 7-d", geo='US')
  trend = pytrends.interest_over_time()
  trend = trend.drop(['isPartial'], axis=1)
  trend = trend.resample('D').sum()
  stock = yf.download(company['CompanyId'], str(end_day - timedelta(days = 7)), str(end_day))
  # predict_set
  stock = yf.download(company['CompanyId'], str(end_day - timedelta(days = 7)), str(end_day))
  if stock.empty:
    print("fetch failed")
    continue
  if date.today() - timedelta(days = 1) != stock.last('D').index.date:
    print("no stock price for new prediction")
    continue
  predict_insert = [company['CompanyId'], stock['Close'].last('D').values[0]] + trend.last('D').values.tolist()[0]
  predict_set.loc[len(predict_set)] = predict_insert

  trend = trend.drop(end_day)
  stock_reverse = stock.sort_index(ascending=False)
  for i, stock_row in stock_reverse.iterrows():
    try:
      next_stock_row = stock.iloc[[np.searchsorted(stock.index, i - timedelta(days = 1))]]
      next_trend = trend.loc[next_stock_row.index].squeeze()
      ns_price = next_stock_row['Close'].values[0]
      growth_rate = (stock_row['Close'] - ns_price) / ns_price
      if growth_rate == 0:
        continue
      to_insert = [company['CompanyId'], ns_price] + next_trend.tolist() + [growth_rate]
      train_set.loc[len(train_set)] = to_insert
    except:
      break

# model making and predict
# generate regression dataset
X = train_set.iloc[:, 1:len(list(train_set)) - 1].copy()
y = train_set.iloc[:, len(list(train_set)) - 1].copy()
# # fit final model
model = LinearRegression()
model.fit(X, y)
# # new instances where we do not know the answer
Xnew = predict_set.iloc[:, 1:].copy()
# # make a prediction
ynew = model.predict(Xnew)
print(ynew)

# output
final_list = predict_set[['CompanyID', 'Price']]
final_list['GrowthRate'] = ynew

print(final_list)