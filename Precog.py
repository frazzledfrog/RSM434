# -*- coding: utf-8 -*-
"""
Created on Wed Feb  5 17:12:48 2025

@author: alxnd
"""

import requests
from time import sleep
import numpy as np
#API Details
s = requests.Session()
s.headers.update({'X-API-key': 'GWD0TB2'}) # Make sure you use YOUR API Key
url = 'http://localhost:9999/v1' #replace number with port for API

def check_resp(resp, action):
    if resp.ok:
        return True
    else:
        print("{} failed with code {}".format(action, resp.status_code))
        return False

class Stock(): #defining the stock class
    max_trade_size = 50000
    #fix syntax for fixed variables
    def __init__(self, ticker, commission, rebate, weight = 1):
        self.ticker = ticker #string of the ticker
        self.commission = commission #what is the commission cost per unit
        self.rebate = rebate #what is the rebate per passive order filled
        self.max_trade_size = Stock.max_trade_size #max trade size
        self.weight = weight #weight of the stock for purpose of calculating limits
        self.bid_price = None
        self.ask_price = None
        self.net_position = 0

    #change following functions to update object values
    def get_bid_ask(self): #returns the bid and ask of the ticker
        payload = {'ticker': self.ticker}
        resp = s.get (url + '/securities/book', params = payload) 
        if check_resp(resp, "get_bid_ask"):
            book = resp.json()

            bid_side_book = book['bids']
            ask_side_book = book['asks']
            
            bid_prices_book = [item["price"] for item in bid_side_book]
            ask_prices_book = [item['price'] for item in ask_side_book]
            
            self.bid_price = bid_prices_book[0]
            self.ask_price = ask_prices_book[0]
        
    
    def get_position(self): #returns the position of the stock
        payload = {'ticker': self.ticker}
        resp = s.get (url + '/securities', params = payload)
        if check_resp(resp, "get_position"):
            book = resp.json()
            self.net_position = book[0]["position"]

class Currency(Stock): #set up the currency class, a subclass of the Stock class
    def __init__(self, ticker):
        self.ticker = ticker
        self.net_position = 0

#set up the stock objects, dictating their commission fee, rebate amount, max-trade-size, etc.
RGLD = Stock('RGLD', 0.01, 0.0125)
RFIN = Stock('RFIN', 0.01, 0.0125)
INDX = Stock('INDX', 0.005, 0.0075, 2)
stocks = [RGLD, RFIN, INDX] #an array with each of the stock tickers in it
#set up currency object
CAD = Currency('CAD')

class Lease(): #defining the lease class, an object that holds the information for our leases

    def __init__(self, ticker, outputs, inputs):
        self.ticker = ticker
        self.id = None
        self.outputs = outputs
        self.inputs = inputs

    def start(self): #starts the lease and defines the id of the lease
        resp = s.post(url + '/leases', params = {'ticker': self.ticker})
        check_resp(resp, "Starting Lease") #important that the ticker defined when setting up the object is correct
        
        resp = s.get(url + '/leases')
        if check_resp(resp, "Starting lease get"):
            leases = resp.json()
            self.id = next(item['id'] for item in leases if item['ticker'] == self.ticker) #sets self.id equal to the id of the lease we just created
    

#define our lease objects
CREATE = Lease('ETF-Creation', INDX, [RGLD, RFIN],)
REDEEM = Lease('ETF-Redemption', [RGLD, RFIN], [INDX, CAD])

#start both leases in RIT and grab the IDs for the leases
CREATE.start()
REDEEM.start()


class Trader(): #defining the core class, an object which will hold all of the trader variables such as status, gross position, etc.
    def __init__(self, components, status = None, tick = None, net_position = 0, gross_position = 0):
        self.status = status
        self.tick = tick
        self.net_position = net_position
        self.gross_position = gross_position
        self.components = components

    def get_tick(self): #gets the tick and status of the case
        resp = s.get(url + '/case')
        if resp.ok:
            case = resp.json()
            self.tick, self.status = case['tick'], case['status']
    
    def update(self): #gets the current position of each stock, weighted according to case rules
        self.net_position = 0 #reset net_position
        self.gross_position = 0 #reset gross position
        for item in self.components: #go through each item in the components list and add them to the ticker, multiplying by the weight
            pos = item.get_position()
            self.net_position += pos * item.weight
            self.gross_position += abs(pos) * item.weight

#set up our core object
me = Trader(stocks)


""" 
def main():
tick, status = get_tick()
ticker_list = ['RGLD','RFIN','INDX']
market_prices = np.array([0.,0.,0.,0.,0.,0.])
market_prices = market_prices.reshape(3,2)

while tick < 298:
    
    lease_number_redemption, lease_number_creation = get_lease_tickers()
    
    for i in range(3):
        
        ticker_symbol = ticker_list[i]
        market_prices[i,0], market_prices[i,1] = get_bid_ask(ticker_symbol)
    
    gross_position, net_position = get_position()
        
    if gross_position < MAX_EXPOSURE_GROSS and net_position == 0:
        
            indx_position = abs(get_ticker_position('INDX'))
            
            # Trading behavior
                
                # If underlying is overpriced:
            if market_prices[0, 0] + market_prices[1, 0] >= market_prices[2, 1] + 0.07: # spread of 0.07+
                resp = s.post(base + '/orders', params = {'ticker': 'RGLD', 'type': 'MARKET', 'quantity': 10000, 'price': market_prices[0, 1], 'action': 'SELL'})
                resp = s.post(base + '/orders', params = {'ticker': 'RFIN', 'type': 'MARKET', 'quantity': 10000, 'price': market_prices[1, 1], 'action': 'SELL'})
                resp = s.post(base + '/orders', params = {'ticker': 'INDX', 'type': 'MARKET', 'quantity': 10000, 'price': market_prices[2, 0], 'action': 'BUY'})
                
                sleep(0.03)
                
                indx_position = abs(get_ticker_position('INDX'))

            # If underlying is underpriced    
            elif market_prices[0, 1] + market_prices[1, 1] <= market_prices[2, 0] - 0.03: # spread of 0.03+
                resp = s.post(base + '/orders', params = {'ticker': 'RGLD', 'type': 'MARKET', 'quantity': 10000, 'price': market_prices[0, 0], 'action': 'BUY'})
                resp = s.post(base + '/orders', params = {'ticker': 'RFIN', 'type': 'MARKET', 'quantity': 10000, 'price': market_prices[1, 0], 'action': 'BUY'})
                resp = s.post(base + '/orders', params = {'ticker': 'INDX', 'type': 'MARKET', 'quantity': 10000, 'price': market_prices[2, 1], 'action': 'SELL'})
                
                sleep(0.03)
                
                indx_position = abs(get_ticker_position('INDX'))
            

            # Convert/Redeem ETF after index position >= 100,000 shares
            if indx_position > 50000:
                
                etf_position = get_ticker_position('INDX')
                
                # Redeem ETF from the position
                if 100000 > etf_position > 50000:
                    quantity = 100000
                    resp = s.post(base + '/leases/' + str(lease_number_redemption), params = {
                        'from1': 'INDX',
                        'quantity1': int(quantity),
                        'from2': 'CAD',
                        'quantity2': int(quantity * 0.0375)})
                    
                    
                    indx_position = abs(get_ticker_position('INDX'))

                # Create ETF the position
                elif -100000 < etf_position < -50000:
                    quantity = 100000
                    resp = s.post(base + '/leases/' + str(lease_number_creation), params = {
                        'from1':'RGLD', 
                        'quantity1': int(quantity), 
                        'from2': 'RFIN', 
                        'quantity2': int(quantity)})
                    
                    
                    indx_position = abs(get_ticker_position('INDX'))
    tick, status = get_tick()
indx_position = abs(get_ticker_position('INDX'))
etf_position = get_ticker_position('INDX')

# Redeem ETF from the position
if etf_position > 0:
    quantity = min(etf_position,100000)
    resp = s.post(base + '/leases/' + str(lease_number_redemption), params = {
        'from1': 'INDX',
        'quantity1': int(quantity),
        'from2': 'CAD',
        'quantity2': int(quantity * 0.0375)})

# Create ETF the position
elif etf_position < 0:
    quantity = min(100000,-etf_position)
    resp = s.post(base + '/leases/' + str(lease_number_creation), params = {
        'from1':'RGLD', 
        'quantity1': int(quantity), 
        'from2': 'RFIN', 
        'quantity2': int(quantity)})
else:
    pass
    
    indx_position = abs(get_ticker_position('INDX'))

if __name__ == '__main__':
main()



 """