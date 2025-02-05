import requests
from time import sleep
import numpy as np
import threading

s = requests.Session()
s.headers.update({'X-API-key': 'GWD0TB2'}) # Make sure you use YOUR API Key
base = 'http://localhost:9999/v1' #replace the port '9999' with alternate port if there is an issue

# global variables
MAX_EXPOSURE_GROSS = 450000 #we need to set this super low bc RIT is fucking stupid and when the lease object creates our 100K of the index/stock it counts it as momentarily having 400K of gross value outside of any 
order_quantity = 10000 #fuck trying to make this go to 25K, just do 10K bc we are limited by the lease asset not anything else
thresh = 0 #the point at which the resetter resets :3
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

def get_time_sales(ticker):
    payload = {'ticker': ticker}
    resp = s.get (base + '/securities/tas', params = payload)
    if resp.ok:
        book = resp.json()
        time_sales_book = [item["quantity"] for item in book]
        return time_sales_book

def get_position():
    resp = s.get (base + '/securities')
    if resp.ok:
        book = resp.json()
        gross_position = abs(book[1]['position']) + abs(book[2]['position']) + 2 * abs(book[3]['position'])
        net_position = abs(book[1]['position'] + book[2]['position'] + 2 * book[3]['position'])
        return gross_position, net_position

def check():
    resp = s.get(base + '/securities')
    if resp.ok:
        book = resp.json()
        try:
            return book[1]['position'] + book[2]['position'] == -2 * book[3]['position']
        except (IndexError, KeyError):
            return False  # Default to False if missing keys

def get_open_orders(ticker):
    payload = {'ticker': ticker}
    resp = s.get (base + '/orders', params = payload)
    if resp.ok:
        orders = resp.json()
        buy_orders = [item for item in orders if item["action"] == "BUY"]
        sell_orders = [item for item in orders if item["action"] == "SELL"]
        return buy_orders, sell_orders

def get_order_status(order_id):
    resp = s.get (base + '/orders' + '/' + str(order_id))
    if resp.ok:
        order = resp.json()
        return order['status']

def get_ticker_position(ticker):
    resp = s.get (base + '/securities')
    if resp.ok:
        book = resp.json()
        return next(value['position'] for value in book if value['ticker'] == ticker)

def get_lease_tickers():
    resp = s.get(base + '/leases')
    if resp.ok:
        lease = resp.json()
        lease_id_redemption = lease[0]['id']
        lease_id_creation = lease[1]['id']
        return lease_id_redemption, lease_id_creation

resp = s.post(base + '/leases', params = {'ticker': 'ETF-Redemption'})
resp = s.post(base + '/leases', params = {'ticker': 'ETF-Creation'})
sleep(1) #so that these get initialized before we try to access them
lease_number_redemption, lease_number_creation = get_lease_tickers()

def main():
    tick, status = get_tick()
    ticker_list = ['RGLD','RFIN','INDX']
    market_prices = np.array([0.,0.,0.,0.,0.,0.])
    market_prices = market_prices.reshape(3,2)

    while status == 'ACTIVE':

        for i in range(3):
            ticker_symbol = ticker_list[i]
            market_prices[i,0], market_prices[i,1] = get_bid_ask(ticker_symbol)
        
        gross_position, net_position = get_position()

        if gross_position < MAX_EXPOSURE_GROSS and flag == 0: #only send through the next trade if my current position is 0

                    # If underlying is overpriced:
                if market_prices[0, 0] + market_prices[1, 0] > market_prices[2, 1] + 0.0625: # spread of 0.0375 + 0.01 + 0.01 + 0.005 = 0.0625
                    resp = s.post(base + '/orders', params = {'ticker': 'RGLD', 'type': 'MARKET', 'quantity': order_quantity, 'action': 'SELL'})
                    resp = s.post(base + '/orders', params = {'ticker': 'INDX', 'type': 'MARKET', 'quantity': order_quantity, 'action': 'BUY'})
                    resp = s.post(base + '/orders', params = {'ticker': 'RFIN', 'type': 'MARKET', 'quantity': order_quantity, 'action': 'SELL'})
                    sleep(0.05)

                    # If underlying is underpriced
                elif market_prices[0, 1] + market_prices[1, 1] < market_prices[2, 0] - 0.025: # spread of 0.01 + 0.01 + 0.005 = 0.025
                    resp = s.post(base + '/orders', params = {'ticker': 'RGLD', 'type': 'MARKET', 'quantity': order_quantity, 'action': 'BUY'})
                    resp = s.post(base + '/orders', params = {'ticker': 'INDX', 'type': 'MARKET', 'quantity': order_quantity, 'action': 'SELL'})
                    resp = s.post(base + '/orders', params = {'ticker': 'RFIN', 'type': 'MARKET', 'quantity': order_quantity, 'action': 'BUY'})
                    sleep(0.05)
def reset():
    global flag
    flag = 0
    tick, status = get_tick()
    while status == 'ACTIVE':
        quantity = get_ticker_position('INDX')
        # Redeem ETF from the position
        if quantity > thresh:
            amt = min(100000,quantity)
            resp = s.post(base + '/leases/' + str(lease_number_redemption), params = {
                'from1': 'INDX',
                'quantity1': int(amt),
                'from2': 'CAD',
                'quantity2': int(np.ceil(amt * 0.0375))})
        # Create ETF the position
        elif quantity < thresh:
            amt = min(100000,abs(quantity))
            resp = s.post(base + '/leases/' + str(lease_number_creation), params = {
                'from1':'RGLD',
                'quantity1': int(abs(amt)),
                'from2': 'RFIN',
                'quantity2': int(abs(amt))})
        flag = 1
        sleep(2)
        flag = 0
        tick, status = get_tick()

main_thread = threading.Thread(target = main, daemon = True)
reset_thread = threading.Thread(target = reset, daemon = True)

main_thread.start()
reset_thread.start()

while True:
    sleep(1)
