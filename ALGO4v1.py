#imports
import requests
from time import sleep
import numpy as np

#API Details
s = requests.Session()
s.headers.update({'X-API-key': 'GWD0TB2'}) # Make sure you use YOUR API Key
url = 'http://localhost:9999/v1' #replace number with port for API

#define classes
class Stock():
    def __init__(self, ticker, commission, rebate, weight = 1):
        self.ticker = ticker #string of the ticker
        self.commission = commission #what is the commission cost per unit
        self.rebate = rebate #what is the rebate per passive order filled
        self.weight = weight #weight of the stock for purpose of calculating limits
        self.bid_price = None
        self.ask_price = None
        self.position = 0

    def GetBidAsk(self): #update the bid and ask of the ticker
        payload = {'ticker': self.ticker}
        resp = s.get (url + '/securities/book', params = payload) 
        book = resp.json()
        bid_side_book = book['bids']
        ask_side_book = book['asks']
        bid_prices_book = [item["price"] for item in bid_side_book]
        ask_prices_book = [item['price'] for item in ask_side_book]
        self.bid_price = bid_prices_book[0]
        self.ask_price = ask_prices_book[0]
        
    def GetPosition(self): #updates the position of the stock
        payload = {'ticker': self.ticker}
        resp = s.get (url + '/securities', params = payload)
        book = resp.json()
        self.position = book[0]["position"]
    
    def Trade(self, direction, quantity): #executes a trade at the given quantity
        s.post(url + '/orders', params = {'ticker': self.ticker, 'type': 'MARKET', 'quantity': quantity, 'action': direction})
    
class Currency(Stock): #set up the currency class, a simple subclass of the Stock object
    def __init__(self, ticker):
        self.ticker = ticker
        self.net_position = 0

class Portfolio():
    def __init__(self, stocks): #where tickers is an array of stock objects
        self.stocks = stocks
        self.gross_position = 0
        self.net_position = 0
        self.local = 0

    def GetBidAsk(self):
        for item in self.stocks:
            item.GetBidAsk()

    def UpdatePos(self):
        self.gross_position = 0
        self.net_position = 0
        for item in self.stocks:
            item.GetPosition()
            pos = item.position
            w = item.weight
            self.net_position += (pos * w)
            self.gross_position += (abs(pos) * w)

    def spreads(self): #change this to changee thresholds for trading behaviour
        self.GetBidAsk()
        long_etf_spread = self.stocks[0].bid_price + self.stocks[1].bid_price - self.stocks[2].ask_price - 0.0625
        short_etf_spread = self.stocks[2].bid_price - self.stocks[0].ask_price - self.stocks[1].ask_price - 0.025
        return long_etf_spread, short_etf_spread

class Lease(): #defining the lease class, an object that holds the information for our leases
    def __init__(self, ticker, outputs, inputs, inputs_quant):
        self.ticker = ticker
        self.id = None
        self.outputs = outputs
        self.inputs = inputs
        self.inputs_quant = inputs_quant

    def Start(self): #starts the lease and defines the id of the lease
        resp = s.post(url + '/leases', params = {'ticker': self.ticker}) #important that the ticker defined when setting up the object is correct
        sleep(0.5)
        resp = s.get(url + '/leases')
        leases = resp.json()
        self.id = next(item['id'] for item in leases if item['ticker'] == self.ticker) #sets self.id equal to the id of the lease we just created
        
    def Use(self, quantity = 100000):
        s.post(url + '/leases/' + str(self.id), params={'from1': self.inputs[0], 'quantity1': np.ceil(quantity * self.inputs_quant[0]), 'from2': self.inputs[1], 'quantity2': np.ceil(quantity * self.inputs_quant[1])})

#define general functions
def get_tick(): #gets the tick and status of the case
    resp = s.get(url + '/case')
    case = resp.json()
    return case['tick'], case['status']

def main(): #our main trading loop
    RGLD = Stock('RGLD', 0.01, 0.0125)
    RFIN = Stock('RFIN', 0.01, 0.0125)
    INDX = Stock('INDX', 0.005, 0.0075, 2)
    portfolio = Portfolio([RGLD, RFIN, INDX]) #an array with each of the stock objects in it
    CAD = Currency('CAD')
    CREATE = Lease('ETF-Creation', 'INDX', ['RGLD', 'RFIN'], [1, 1])
    REDEEM = Lease('ETF-Redemption', ['RGLD', 'RFIN'], ['INDX', 'CAD'], [1, 0.0375])
    CREATE.Start()
    REDEEM.Start()
    tick, status = get_tick()
    quantity = 25000 #placeholder while we work on live updates
    while status == 'ACTIVE':
        portfolio.UpdatePos()
        if portfolio.net_position == 0 and portfolio.local <= 100000: #if safe to do so and it exists, execute arb oppportunity
            long_etf, short_etf = portfolio.spreads() #updates the values in me determining which if any arb strategy would be good
            if long_etf > 0:
                RGLD.Trade('SELL', quantity)
                INDX.Trade('BUY', quantity)
                RFIN.Trade('SELL', quantity)
                portfolio.local += 25000
                print("exploiting pricing inaccuracies ✧♡(◕‿◕✿)")
            elif short_etf > 0:
                RGLD.Trade('BUY', quantity)
                INDX.Trade('SELL', quantity)
                RFIN.Trade('BUY', quantity)
                portfolio.local -= 25000
                print("exploiting pricing inaccuracies ✧♡(◕‿◕✿)")
            else:
                print("nothing to do (◕︿◕✿)")
                
        if portfolio.local >= 100000: #use the leases to neutralize gross position if it makes sense to do so
            REDEEM.Use()
            portfolio.local -= 100000
            print("neutralizing position...")
            sleep(2)
            
        elif portfolio.local <= -100000:
            CREATE.Use()
            portfolio.local += 100000
            print("neutralizing position... 乁༼☯‿☯✿༽ㄏ")
            sleep(2)

        else: #logic for if the price sits somewhere in a range that more than 3 cents away from an arb opportunity for EITHER direction, and our gross is not 0, use the converter
            long_etf, short_etf = portfolio.spreads()
            if long_etf < -0.03 and short_etf < -0.03:
                if portfolio.local > 0:
                    REDEEM.Use(portfolio.local)
                    portfolio.local = 0
                    print("neutralizing position...")
                    sleep(2)
                elif portfolio.local < 0:
                    CREATE.Use(abs(portfolio.local))
                    portfolio.local = 0
                    print("neutralizing position...")
                    sleep(2)
        
        tick, status = get_tick()

main()