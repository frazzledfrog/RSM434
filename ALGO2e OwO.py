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
        self.volume = None

    def GetBidAsk(self): #update the bid and ask of the ticker
        payload = {'ticker': self.ticker}
        resp = s.get(url + '/securities/book', params = payload)
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
        resp = s.get(url + '/securities', params = payload)
        book = resp.json()
        self.net_position = book[0]["position"]

    def GetVolume(self): #returns the volume of the stock over the last tick
        payload = {'ticker': self.ticker, 'limit': 1}
        resp = s.get(url + '/securities/tas', params= payload)
        tas = resp.json()
        volumes = tas.get('quantity', [])
        self.volume = 0
        for volume in volumes:
            self.volume += int(volume['quantity'])


class Inventory(): #the inventory object is merely a way to do operations to a group of Stock objects
    def __init__(self, tickers):
        self.tickers = tickers
        self.gross_position = 0
        self.skew = 0 #a value from 0 to 1 defining how strong our corrective effect should be
    
    def Position(self): #updates gross position
        self.gross_position = 0 #reset to zero
        for item in self.tickers: #update the information
            item.GetPosition()
            self.gross_position += abs(item.position)
    
    def Skew(self):
        self.skew = self.gross_position / 25000 #what % of our gross position limit are we at?
             


#functions


#object defines
CNR = Stock("CNR", 0.0027, 0.005)
RY = Stock("RY", -0.0014, -0.0034) #actually better to be executing active orders for RY
AC = Stock("AC", 0.0015, 0.0026)
STORES = Inventory([CNR, RY, AC])

CNR.GetVolume()

print(CNR.volume)