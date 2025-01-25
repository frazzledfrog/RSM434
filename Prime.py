import requests
from time import sleep
import threading
import numpy as np

s = requests.Session()
s.headers.update({'X-API-key': '0CHUSTFW'}) # Need to replace this API key

#the max position & gross limits are set lower than what their actual values are, to prevent going over by less than 500 (the trade amt)
max_long_exposure = 24400
max_short_exposure = -24400
max_gross_position = 24400
order_limit = 500
pos_CNR = 0
pos_RY = 0
pos_AC = 0
ohlc_limit = 5 #change this to determine how far back the code reaches to calculate deviation
target_rate = 5
tip = 0
boundary_low = 0.1
boundary_high = 2

stop_event = threading.Event()

def scale_to_range(x, x_min=0, x_max=1, y_min=boundary_low, y_max=boundary_high):
    x = max(x_min, min(x, x_max))
    return y_min + (x - x_min) * (y_max - y_min) / (x_max - x_min)

def get_tick():
    resp = s.get('http://localhost:9999/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick'], case['status']

def get_bid_ask(ticker):
    payload = {'ticker': ticker}
    resp = s.get ('http://localhost:9999/v1/securities/book', params = payload)
    if resp.ok:
        book = resp.json()
        bid_side_book = book['bids']
        ask_side_book = book['asks']

        bid_prices_book = [item["price"] for item in bid_side_book]
        ask_prices_book = [item['price'] for item in ask_side_book]

        best_bid_price = bid_prices_book[0]
        best_ask_price = ask_prices_book[0]

        return best_bid_price, best_ask_price

def gap_finder(ticker):
    bid, ask = get_bid_ask(ticker)
    gap = ask - bid
    return gap

def get_time_sales(ticker):
    payload = {'ticker': ticker}
    resp = s.get ('http://localhost:9999/v1/securities/tas', params = payload)
    if resp.ok:
        book = resp.json()
        time_sales_book = [item["quantity"] for item in book]
        return time_sales_book

def get_gross():
    resp = s.get ('http://localhost:9999/v1/securities')
    if resp.ok:
        book = resp.json()
        return abs(book[0]['position']) + abs(book[1]['position']) + abs(book[2]['position'])
def get_position():
    resp = s.get ('http://localhost:9999/v1/securities')
    if resp.ok:
        book = resp.json()
        return book[0]['position'] + book[1]['position'] + book[2]['position']
def get_pos_CNR():
    resp = s.get ('http://localhost:9999/v1/securities')
    if resp.ok:
        book = resp.json()
        return book[0]['position']
def get_pos_RY():
    resp = s.get ('http://localhost:9999/v1/securities')
    if resp.ok:
        book = resp.json()
        return book[1]['position']
def get_pos_AC():
    resp = s.get ('http://localhost:9999/v1/securities')
    if resp.ok:
        book = resp.json()
        return book[2]['position']

def get_open_orders(ticker):
    payload = {'ticker': ticker}
    resp = s.get ('http://localhost:9999/v1/orders', params = payload)
    if resp.ok:
        orders = resp.json()
        buy_orders = [item for item in orders if item["action"] == "BUY"]
        sell_orders = [item for item in orders if item["action"] == "SELL"]
        return buy_orders, sell_orders

def get_order_status(order_id):
    resp = s.get ('http://localhost:9999/v1/orders' + '/' + str(order_id))
    if resp.ok:
        order = resp.json()
        return order['status']

def get_stdev(ticker):
    payload = {'ticker': ticker, 'limit': ohlc_limit}
    resp = s.get ('http://localhost:9999/v1/securities/history', params = payload)
    if resp.ok:
        ohlc = resp.json()
        opens = [item['open'] for item in ohlc]
        closes = [item['close'] for item in ohlc]
        stdev_opens = np.std(opens)
        stdev_closes = np.std(closes)
        avg_stdev = (stdev_opens + stdev_closes) / 2
        return avg_stdev




def data_updater():
    global tick, status
    tick, status = get_tick()
      while status == 'ACTIVE' and not stop_event.is_set():
        global pos_CNR, pos_RY, pos_AC, best_bid_CNR, best_ask_CNR, best_bid_RY, best_ask_RY, best_bid_AC, best_ask_AC, gross_position, net_position, sleep_CNR, sleep_RY, sleep_AC
        pos_CNR = get_pos_CNR()
        pos_RY = get_pos_RY()
        pos_AC = get_pos_AC()
        best_bid_CNR, best_ask_CNR = get_bid_ask('CNR')
        best_bid_RY, best_ask_RY = get_bid_ask('RY')
        best_bid_AC, best_ask_AC = get_bid_ask('AC')
        best_bid_AC += tip
        best_bid_CNR += tip
        best_bid_RY += tip
        best_ask_AC -= tip
        best_ask_RY -= tip
        best_ask_CNR -= tip
        gross_position = abs(pos_CNR) + abs(pos_RY) + abs(pos_AC)
        net_position = pos_CNR + pos_RY + pos_AC
        gap_CNR = gap_finder('CNR')
        sleep_CNR = scale_to_range(gap_CNR)
        gap_RY = gap_finder('RY')
        sleep_RY = scale_to_range(gap_RY)
        gap_AC = gap_finder('AC')
        sleep_AC = scale_to_range(gap_AC)
        sleep(0.02)
        tick, status = get_tick()

def CNR():
    while status == 'ACTIVE' and not stop_event.is_set():
        if gross_position < max_gross_position:
            if net_position < max_long_exposure:
                resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_CNR, 'action': 'BUY'})
            if net_position > max_short_exposure:
                resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_CNR, 'action': 'SELL'})
        if gross_position > max_gross_position and pos_CNR > 0:
            if net_position > max_short_exposure:
                resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_CNR, 'action': 'SELL'})
        if gross_position > max_gross_position and pos_CNR < 0:
            if net_position < max_long_exposure:
                resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_CNR, 'action': 'BUY'})
        sleep(sleep_CNR)


def RY():
    while status == 'ACTIVE' and not stop_event.is_set():
        if gross_position < max_gross_position:
            if net_position < max_long_exposure:
                resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_RY, 'action': 'BUY'})
            if net_position > max_short_exposure:
                resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_RY, 'action': 'SELL'})
        if gross_position > max_gross_position and pos_RY > 0:
            if net_position > max_short_exposure:
                resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_RY, 'action': 'SELL'})
        if gross_position > max_gross_position and pos_RY < 0:
            if net_position < max_long_exposure:
                resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_RY, 'action': 'BUY'})
        sleep(sleep_RY)


def AC():
    while status == 'ACTIVE' and not stop_event.is_set():
        if gross_position < max_gross_position:
            if net_position < max_long_exposure:
                resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_AC, 'action': 'BUY'})
            if net_position > max_short_exposure:
                resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_AC, 'action': 'SELL'})
        if gross_position > max_gross_position and pos_AC > 0:
            if net_position > max_short_exposure:
                resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_AC, 'action': 'SELL'})
        if gross_position > max_gross_position and pos_AC < 0:
            if net_position < max_long_exposure:
                resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_AC, 'action': 'BUY'})
        sleep(sleep_AC)


def stop():
    while not stop_event.is_set():
        try:
            sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping Threads...")
            stop_event.set()
    thread_data_updater.join()
    thread_CNR.join()
    thread_AC.join()
    thread_RY.join()
    thread_stop.join()
    print("All threads stopped.")


# Create threads for each function
thread_data_updater = threading.Thread(target=data_updater)
thread_CNR = threading.Thread(target=CNR)
thread_AC = threading.Thread(target=AC)
thread_RY = threading.Thread(target=RY)
thread_stop = threading.Thread(target=stop)


# Start each thread
thread_data_updater.start()
sleep(0.5)
thread_CNR.start()
thread_AC.start()
thread_RY.start()
thread_stop.start()
