import requests
from time import sleep
import numpy as np
#API Details
s = requests.Session()
s.headers.update({'X-API-key': 'GWD0TB2'}) # Make sure you use YOUR API Key
url = 'http://localhost:9999/v1' #replace number with port for API

def check_resp(resp, action): #function to call which checks whether a resp returned a valid code, and if it doesn't, prints the error code
    if resp.ok:
        return True
    else:
        print("{} failed with code {}".format(action, resp.status_code))
        return False

class Stock(): #defining the stock class
    trade_size = 25000 #may only be an even number to maintain parity
    #fix syntax for fixed variables
    def __init__(self, ticker, commission, rebate, weight = 1):
        self.ticker = ticker #string of the ticker
        self.commission = commission #what is the commission cost per unit
        self.rebate = rebate #what is the rebate per passive order filled
        self.weight = weight #weight of the stock for purpose of calculating limits
        self.bid_price = None
        self.ask_price = None
        self.net_position = 0
        self.trade_size = Stock.trade_size #remember to adjust any use of this for weights later

    #change following functions to update object values
    def GetBidAsk(self): #returns the bid and ask of the ticker
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
        
    
    def GetPosition(self): #updates the position of the stock
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

    def __init__(self, ticker, outputs, inputs, inputs_quant):
        self.ticker = ticker
        self.id = None
        self.outputs = outputs
        self.inputs = inputs
        self.inputs_quant = inputs_quant

    def Start(self): #starts the lease and defines the id of the lease
        resp = s.post(url + '/leases', params = {'ticker': self.ticker})
        check_resp(resp, "Starting Lease") #important that the ticker defined when setting up the object is correct
        
        resp = s.get(url + '/leases')
        if check_resp(resp, "Starting lease get"):
            leases = resp.json()
            self.id = next(item['id'] for item in leases if item['ticker'] == self.ticker) #sets self.id equal to the id of the lease we just created

    def Use(self, quantity = 100000):
        s.post(url + '/leases/' + str(self.id), params={'from1': self.inputs[0], 'quantity1': np.ceil(quantity * self.inputs_quant[0]), 'from2': self.inputs[1], 'quantity2': np.ceil(quantity * self.inputs_quant[1])})

#define our lease objects
CREATE = Lease('ETF-Creation', INDX, [RGLD, RFIN], [1, 1])
REDEEM = Lease('ETF-Redemption', [RGLD, RFIN], [INDX, CAD], [1, 0.0375])

def get_tick(): #gets the tick and status of the case
    resp = s.get(url + '/case')
    if resp.ok:
        case = resp.json()
        return case['tick'], case['status']
    
def update_pos(): #gets the net_position then gross_position
    for item in stocks: #go through each item in the components list and add them to the ticker, multiplying by the weight
        pos = item.get_position()
        net_position += pos * item.weight
        gross_position += abs(pos) * item.weight
    return net_position, gross_position

def spreads(): #updates spreads and updates item bid-asks (not in that order lol)
    #before calculating these spreads, we update the items in our components array
    for item in stocks:
        item.GetBidAsk()
    #first the long-arb logic, we are including the fees in here
    long_etf_spread = stocks[0].bid_price + stocks[1].bid_price - stocks[2].ask_price - 0.0625
    #now the short-arb logic, again including fees
    short_etf_spread = stocks[2].bid_price - stocks[0].ask_price - stocks[1].ask_price - 0.025
    return long_etf_spread, short_etf_spread

def long_etf(): #submits 3 orders, selling RGLD, then buying INDX, then selling RFIN -- no sleep built into it
    s.post(url + '/orders', params = {'ticker': RGLD.ticker, 'type': 'MARKET', 'quantity': RGLD.trade_size, 'action': 'SELL'})
    s.post(url + '/orders', params = {'ticker': INDX.ticker, 'type': 'MARKET', 'quantity': INDX.trade_size, 'action': 'BUY'})
    s.post(url + '/orders', params = {'ticker': RFIN.ticker, 'type': 'MARKET', 'quantity': RFIN.trade_size, 'action': 'SELL'})

def short_etf(): #inverse to above
    s.post(url + '/orders', params = {'ticker': RGLD.ticker, 'type': 'MARKET', 'quantity': RGLD.trade_size, 'action': 'BUY'})
    s.post(url + '/orders', params = {'ticker': INDX.ticker, 'type': 'MARKET', 'quantity': INDX.trade_size, 'action': 'SELL'})
    s.post(url + '/orders', params = {'ticker': RFIN.ticker, 'type': 'MARKET', 'quantity': RFIN.trade_size, 'action': 'BUY'})

def main(): #our main trading loop
    #first set up our leases
    CREATE.Start()
    REDEEM.Start()
    #now get the status and tick of the case to decide whether to launch into the while case
    tick, status = get_tick
    stable = 0
    while status == 'ACTIVE':
        #first check will be for position limits -- if we are in danger of exceeding our limits, we stop what we are doing!
        net_position, gross_position = update_pos()
        if net_position == 0 and gross_position <= 400000: #if safe to do so and it exists, execute arb oppportunity
            #next check will be if there is an arb position!
            long_etf, short_etf = spreads() #updates the values in me determining which if any arb strategy would be good
            if long_etf > 0:
                long_etf()
                stable = 0
            elif short_etf > 0:
                short_etf()
                stable = 0
            else:
                stable += 1
        if INDX.net_position >= 100000: #use the leases to neutralize gross position if it makes sense to do so
            REDEEM.Use()
            sleep(1.99)
            stable = 0
        elif INDX.net_position <= -100000:
            CREATE.Use()
            sleep(1.99)
            stable = 0
        else: # logic for if the price sits somewhere in a range that more than 3 cents away from an arb opportunity for EITHER direction, and our gross is not 0, use the converter
            long_etf, short_etf = spreads()
            if long_etf < -0.03 and short_etf < -0.03:
                if INDX.net_position > 0:
                    REDEEM.Use(INDX.net_position)
                    sleep(1.99)
                elif INDX.net_position < 0:
                    CREATE.Use(INDX.net_position)
                    sleep(1.99)
        sleep(0.01) #eep a little bit to prevent accidental overloading of the API when nothing is happening
        tick, status = get_tick()