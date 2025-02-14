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

# global variables
MAX_LONG_EXPOSURE_NET = 25000
MAX_SHORT_EXPOSURE_NET = -MAX_LONG_EXPOSURE_NET
MAX_EXPOSURE_GROSS = 475000
ORDER_LIMIT = 12500

class stock():

    def __init__(self, ticker, commission, rebate, max_trade_size, weight = 1):
        self.ticker = ticker #string of the ticker
        self.commission = commission #what is the commission cost per unit
        self.rebate = rebate #what is the rebate per passive order filled
        self.max_trade_size = max_trade_size #max trade size
        self.weight = weight #weight of the stock for purpose of calculating limits
    
    def get_bid_ask(self): #returns the bid and ask of the ticker
        payload = {'ticker': self.ticker}
        resp = s.get (url + '/securities/book', params = payload)
        if resp.ok:
            book = resp.json()
            bid_side_book = book['bids']
            ask_side_book = book['asks']
            
            bid_prices_book = [item["price"] for item in bid_side_book]
            ask_prices_book = [item['price'] for item in ask_side_book]
            
            best_bid_price = bid_prices_book[0]
            best_ask_price = ask_prices_book[0]
    
            return best_bid_price, best_ask_price
    
    def get_position(self): #returns the position of the stock
        payload = self.ticker
        resp = s.get (url + '/securities', params = payload)
        if resp.ok:
            book = resp.json()
            net_position = net_position[0]
            return net_position

#set up the stock objects, dictating their commission fee, rebate amount, max-trade-size, etc.
RGLD = stock('RGLD', 0.01, 0.0125, 50000)
RFIN = stock('RFIN', 0.01, 0.0125, 50000)
INDX = stock('INDX', 0.005, 0.0075, 50000, 2)
stocks = [RGLD, RFIN, INDX] #an array with each of the stock tickers in it

class core():
    def __init__(self, components, status = None, tick = None, net_position = None, gross_position = None):
        self.status = status
        self.tick = tick
        self.net_position = net_position
        self.gross_position = gross_position
        self.components = components

    def get_tick(self):
        resp = s.get(url + '/case')
        if resp.ok:
            case = resp.json()
            self.tick, self.status = case['tick'], case['status']

def get_position(ticker):
payload = ticker
resp = s.get (base + '/securities', params=payload)
if resp.ok:
    book = resp.json()
    net_position = net_position[0]
    return net_position

def get_order_status(order_id):
resp = s.get (base + '/orders' + '/' + str(order_id))
if resp.ok:
    order = resp.json()
    return order['status']
    
def get_lease_tickers():
resp = s.get(base + '/leases')
if resp.ok:
    lease = resp.json()
    lease_id_redemption = lease[0]['id']
    lease_id_creation = lease[1]['id']
    return lease_id_redemption, lease_id_creation  

#initialize leases and wait a second for them to come online    
resp = s.post(base + '/leases', params = {'ticker': 'ETF-Redemption'})         
resp = s.post(base + '/leases', params = {'ticker': 'ETF-Creation'})    
sleep(0.5)

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



