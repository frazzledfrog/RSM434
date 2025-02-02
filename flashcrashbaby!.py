
import requests
from time import sleep
import threading

#API setup stuff
s = requests.Session()
s.headers.update({'X-API-key': 'WL0SY69A'}) #replace this API key
base = 'http://localhost:9999/v1' #alter the port number here if needed

#setting up stop event
stop_event = threading.Event()

#define our global variables, our dials if you will
#these are not to be touched by any local loops
mod = 0
hard_lim = 1000 # this is on a per stock, the hard_lim should never exceed around 8000 -- though a higher value can allow for more trading, a lower hard lim lowers positional risk
def skew(position): #this function determines how strong the quantity corrective effect is. 
    pos = position
    if position < -hard_lim:
        pos = -hard_lim
    if position > hard_lim:
        pos = hard_lim
    m = (pos*abs(pos))/(hard_lim ** 2) #squared to make it scale nicer
    skew_buy = 1 - m
    skew_sell = 1 + m
    return skew_buy, skew_sell
sleep_time = 0.04


def get_tick():
    resp = s.get(base + '/case')
    if resp.ok:
        case = resp.json()
        return case['tick'], case['status']

def get_bid_ask(ticker):
    payload = {'ticker': ticker}
    resp = s.get (base + '/securities/book', params = payload)
    if resp.ok:
        book = resp.json()
        bid_side_book = book['bids']
        ask_side_book = book['asks']

        bid_prices_book = [item["price"] for item in bid_side_book]
        ask_prices_book = [item['price'] for item in ask_side_book]

        best_bid_price = bid_prices_book[0]
        best_ask_price = ask_prices_book[0]

        return best_bid_price, best_ask_price
    
def get_open_count(ticker):
    payload = {'ticker': ticker}
    resp = s.get (base + '/orders', params = payload)
    if resp.ok:
        orders = resp.json()
        open_orders = [item for item in orders if item['status'] == "OPEN"]
        return len(open_orders)

def get_position(ticker):
    payload =  {'ticker': ticker}
    resp = s.get (base + '/securities', params = payload)
    if resp.ok:
        book = resp.json()
        return book[0]['position']

def CNR():
    tick, status = get_tick()
    for i in range(500):
        resp = s.post(base + '/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': 50000, 'price': 1, 'action': 'SELL'})
        resp = s.post(base + '/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': 50000, 'price': 1, 'action': 'SELL'})
        resp = s.post(base + '/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': 50000, 'price': 1, 'action': 'SELL'})
        sleep(0.01)
    for i in range(500):
        bid, ask = get_bid_ask('CNR')
        resp = s.post(base + '/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': 50000, 'price': bid, 'action': 'BUY'})
        bid, ask = get_bid_ask('AC')
        resp = s.post(base + '/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': 50000, 'price': bid, 'action': 'BUY'})
        bid, ask = get_bid_ask('RY')
        resp = s.post(base + '/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': 50000, 'price': bid, 'action': 'BUY'})
        sleep(0.01)
CNR()




















