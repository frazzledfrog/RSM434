#imports
import requests
from time import sleep
import numpy as np
#api setup
s = requests.Session()
s.headers.update({'X-API-key':'key-goes-here'})
url = 'http://localhost:9999/v1'
#class defines
class Stock():
    def __init__(self, ticker, fee, rebate):
        self.ticker = ticker
        self.fee = fee
        self.rebate = rebate
        self.bid = None
        self.ask = None
        self.spread = None
        self.position = 0

    def GetBidAsk(self): #update the bid and ask of the ticker
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
            self.spread = self.ask - self.bid

    def GetPosition(self): #updates the position of the stock
            payload = {'ticker': self.ticker}
            resp = s.get (url + '/securities', params = payload)
            if check_resp(resp, "get_position"):
                book = resp.json()
                self.net_position = book[0]["position"]

class Inventory(): #the inventory object is merely a way to do operations to a group of Stock objects
    def __init__(self, tickers):
        self.tickers = tickers
        self.gross_position = 0
        self.net_position = 0
        self.weights = [0, 0, 0]
    
    def Update(self): #also does an update to the position and bid-ask of each ticker
        self.gross_position = 0 #reset to zero
        self.net_position = 0
        #update the information
        for item in self.tickers:
            item.GetPosition()
            item.GetBidAsk()
            self.gross_position += abs(item.position)
            self.net_position += item.position
    
    def target(self): #we will target the best performing of the tickers, accept an array as an input
        max_spread = max(self.tickers, key = lambda stock: stock.spread)
        return max_spread.ticker


#functions
def check_resp(resp, action): #function to call which checks whether a resp returned a valid code, and if it doesn't, prints the error code
    if resp.ok:
        return True
    else:
        print("{} failed with code {}".format(action, resp.status_code))
        return False

