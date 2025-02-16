import requests
from time import sleep
import numpy as np
#API Details
s = requests.Session()
s.headers.update({'X-API-key': 'GWD0TB2'}) # Make sure you use YOUR API Key
url = 'http://localhost:9999/v1' #replace number with port for API

class Stock(): #defining the stock class
    trade_size = 25000 #may only be an even number to maintain parity ALEX U MAY WANT TO TAKE THIS OUT AS IM DUPLICATRING IT IN MAIN RN
    #fix syntax for fixed variables
    def __init__(self, ticker, commission, rebate, weight = 1):
        self.ticker = ticker #string of the ticker
        self.commission = commission #what is the commission cost per unit
        self.rebate = rebate #what is the rebate per passive order filled
        self.weight = weight #weight of the stock for purpose of calculating limits
        self.bid_price = None
        self.ask_price = None
        self.net_position = 0

    #change following functions to update object values
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
        
    
    def GetPosition(self): #updates the position of the stock
        payload = {'ticker': self.ticker}
        resp = s.get (url + '/securities', params = payload)
        if check_resp(resp, "get_position"):
            book = resp.json()
            self.net_position = book[0]["position"]
    
    def Trade(self, dir, quantity = trade_size):
        s.post(url + '/orders', params = {'ticker': self.ticker, 'type': 'MARKET', 'quantity': quantity, 'action': dir})

class Portfolio():

    def __init__(self, stocks): #where tickers is an array of stock objects
        self.stocks = stocks
        self.gross_position = 0
        self_net_position = 0

    def GetBidAsk(self):
        for item in self.stocks:
            item.GetBidAsk

    def update_pos(self):
        for item in self.stocks:
            pos = item.get_position()
            net_position += pos * item.weight
            gross_position += abs(pos) * item.weight

    def spreads(self): #updates spreads and updates item bid-asks (not in that order lol)
        #before calculating these spreads, we update the items in our components array
        self.GetBidAsk()

        #first the long-arb logic, we are including the fees in here
        long_etf_spread = self.stocks[0].bid_price + self.stocks[1].bid_price - self.stocks[2].ask_price - 0.0625
        
        #now the short-arb logic, again including fees
        short_etf_spread = self.stocks[2].bid_price - self.stocks[0].ask_price - self.stocks[1].ask_price - 0.025
        
        return long_etf_spread, short_etf_spread




class Currency(Stock): #set up the currency class, a subclass of the Stock class
    def __init__(self, ticker):
        self.ticker = ticker
        self.net_position = 0

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

def check_resp(resp, action): #function to call which checks whether a resp returned a valid code, and if it doesn't, prints the error code
    if resp.ok:
        return True
    else:
        print("{} failed with code {}".format(action, resp.status_code))
        return False


def get_tick(): #gets the tick and status of the case
    resp = s.get(url + '/case')
    if check_resp(resp, "get_tick"):
        case = resp.json()
        return case['tick'], case['status']
    

def get_trade_size(spread):
    #a function that does some math
    max_spread = 1000
    uncertainty = min(1-(spread/max_spread), 1)

    trade_size = (25000 * (1-uncertainty))%2 #round to the nearest even number

    return trade_size


def main(): #our main trading loop

    #set up the stock objects, dictating their commission fee, rebate amount, max-trade-size, etc.
    RGLD = Stock('RGLD', 0.01, 0.0125)
    RFIN = Stock('RFIN', 0.01, 0.0125)
    INDX = Stock('INDX', 0.005, 0.0075, 2)
    portfolio = Portfolio([RGLD, RFIN, INDX]) #an array with each of the stock objects in it

    #set up currency object
    CAD = Currency('CAD')
    
    #define our lease objects
    CREATE = Lease('ETF-Creation', INDX, [RGLD, RFIN], [1, 1])
    REDEEM = Lease('ETF-Redemption', [RGLD, RFIN], [INDX, CAD], [1, 0.0375])

    #first set up our leases
    CREATE.Start()
    REDEEM.Start()

    #now get the status and tick of the case to decide whether to launch into the while case
    tick, status = get_tick
    start_trading = 0


    while status == 'ACTIVE':
        #first check will be for position limits -- if we are in danger of exceeding our limits, we stop what we are doing!
        net_position, gross_position = portfolio.update_pos()
        if tick>start_trading:
            if net_position == 0 and gross_position <= 400000: #if safe to do so and it exists, execute arb oppportunity
                #next check will be if there is an arb position!
                long_etf, short_etf = portfolio.spreads() #updates the values in me determining which if any arb strategy would be good
                
                if long_etf > 0:
                    quantity = get_trade_size(long_etf)
                    RGLD.Trade('SELL', quantity)
                    INDX.Trade('BUY', quantity)
                    RFIN.Trade('SELL', quantity)

                elif short_etf > 0:
                    quantity = get_trade_size(short_etf)
                    RGLD.Trade('BUY', quantity)
                    INDX.Trade('SELL', quantity)
                    RFIN.Trade('BUY', quantity)

            if INDX.net_position >= 100000: #use the leases to neutralize gross position if it makes sense to do so
                REDEEM.Use()
                #sleep(1.99)
                start_trading = get_tick()+2
            elif INDX.net_position <= -100000:
                CREATE.Use()
                #sleep(1.99)
                start_trading = get_tick()+2

            else: #logic for if the price sits somewhere in a range that more than 3 cents away from an arb opportunity for EITHER direction, and our gross is not 0, use the converter
                long_etf, short_etf = spreads()
                if long_etf < -0.03 and short_etf < -0.03:
                    if INDX.net_position > 0:
                        REDEEM.Use(INDX.net_position)
                        #sleep(1.99)
                        start_trading = get_tick()+2

                    elif INDX.net_position < 0:
                        CREATE.Use(INDX.net_position)
                        #sleep(1.99)
                        start_trading = get_tick()+2
                
        sleep(0.01) #eep a little bit to prevent accidental overloading of the API when nothing is happening
        tick, status = get_tick()