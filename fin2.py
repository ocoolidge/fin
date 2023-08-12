import pandas as pd
import os
from datetime import date
from datetime import timedelta
from dateutil.relativedelta import relativedelta 
from itertools import islice
import yfinance as yf
import matplotlib.pyplot as plt

def getPriceAtTime(ticker, dt, interval=7):
    dt = pd.to_datetime(dt)
    s = pd.to_datetime(dt) - timedelta(days=3)
    e = pd.to_datetime(dt) + timedelta(days=3)
    df = pd.DataFrame(yf.download(ticker, s, e, progress=False))[['Close']].copy()
    av = round((df['Close'].sum()/len(df['Close']))*100)/100
    return av

def readTaxLot(fileDir):
	df = pd.read_csv(fileDir, usecols=['UNITS', 'ACQUIRED', 'TICKER', 'UNITCOST'], header=3)
	df = df.dropna()
	df['ACQUIRED'] = pd.to_datetime(df['ACQUIRED'])
	df = df.sort_values(by = 'ACQUIRED')
	return df

class Folio:
	def __init__(self):
		self.df = pd.DataFrame(columns=['ticker', 'type', 'date', 'quantity', 'price', 'nominal', 'real'])
	def addEvent(self, ticker, type, dt, quantity, price):
		real = price
		real = getPriceAtTime(ticker, date.today())
		self.df.loc[len(self.df.index)] = [ticker, type, pd.to_datetime(dt), quantity, price, int(quantity*price), int(quantity*real)]
	def getNominalValue(self):
		vals = self.df['nominal']
		return vals.sum()
	def getRealValue(self):
		return -1
	def getCurrentBook(self):
		book = {}
		for ticker in list(self.df['ticker'].unique()):
			book[ticker] = 0
			for i, r in self.df[self.df['ticker'] == ticker].iterrows():
				book[ticker] += r['quantity']
		return book
	def getCurrentMarketValue(self):
		curBook = self.getCurrentBook()
		total = 0
		for asset in curBook:
			if asset is not None and asset != 'CASH':
				total += getPriceAtTime(asset, pd.to_datetime(date.today())) * curBook[asset]
			elif asset == 'cash':
				total += curBook[asset]
		return total
	

f = Folio()

lots = txt_files = [f for f in os.listdir('./taxLots') if f.endswith('.csv')]

outDF = pd.DataFrame(columns=['DATE', 'DF'])

for lot in lots:
    asof = ''
    with open('./taxLots/' + lot) as file:
        for line in islice(file, 1, 2):
            asof = pd.to_datetime(line[14:24])
    lot_df = pd.read_csv('./taxLots/' + lot, header=3)
    lot_df = lot_df.dropna()
    outDF.loc[len(outDF.index)] = [asof, lot_df]    

outDF.sort_values(by = 'DATE')
datt = pd.to_datetime('2020-07-01')
quarter = relativedelta(months=3)
week = relativedelta(weeks=1)

#getPriceAtTime()

outWeekDF = pd.DataFrame(columns = ['DATE', 'VALUE'])

while datt < pd.Timestamp.today():
    datt = datt + week
    relevant = outDF[((datt + quarter) > pd.to_datetime(outDF['DATE'])) & ((datt - quarter) < pd.to_datetime(outDF['DATE']))]
    accum = 0
    try:
        for i, r in relevant['DF'].iloc[0].iterrows():
            accum = accum + (getPriceAtTime(r['TICKER'], datt) * r['UNITS'])
        outWeekDF.loc[len(outWeekDF.index)] = [datt, accum]
        print(outWeekDF)
    except:
        print('exception')
    finally:
        print(outWeekDF)
        outWeekDF.to_csv('outWeekDF_to_.csv')
    
print(outWeekDF)
