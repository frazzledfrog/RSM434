#TO FIX:
    #Need to add in negative value/error handling for the sleepy scale function

import requests
from time import sleep
import threading
import numpy as np

s = requests.Session()
s.headers.update({'X-API-key': 'WL0SY69A'}) # Need to replace this API key

#the max position & gross limits are set lower than what their actual values are, to prevent going over by less than 500 (the trade amt)
max_long_exposure = 20000
max_short_exposure = -max_long_exposure
max_gross_position = max_long_exposure
order_limit = 5000
half = order_limit / 2 
pos_CNR = 0
pos_RY = 0
pos_AC = 0
tip = 0.05 #adjusts what % of the spread we offer as a premium on the current bid-ask spread. for no tip, put in 0
boundary_low = 0.01  #defines what we map our max-min spread value to
boundary_high = 1
midstop = 4000
highstop = 8000


stop_event = threading.Event()

def scale_to_range(x, x_min=1, x_max=100, y_min=boundary_low, y_max=boundary_high):
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
        AC_buff = gap_finder('AC')*tip
        CNR_buff = gap_finder('CNR')*tip
        RY_buff = gap_finder('RY')*tip
        best_bid_AC += AC_buff
        best_bid_CNR += CNR_buff
        best_bid_RY += RY_buff
        best_ask_AC -= AC_buff
        best_ask_RY -= RY_buff
        best_ask_CNR -= CNR_buff
        gross_position = abs(pos_CNR) + abs(pos_RY) + abs(pos_AC)
        net_position = pos_CNR + pos_RY + pos_AC
        gap_CNR = float(np.log((1/gap_finder('CNR'))+1)) #the pluses are here to ensure that there can be no negative values
        gap_RY = float(np.log((1/gap_finder('RY'))+1))
        gap_AC = float(np.log((1/gap_finder('AC'))+1))
        min_g = min(gap_AC, gap_CNR, gap_RY)
        ratio_AC = gap_AC/min_g
        ratio_RY = gap_RY/min_g
        ratio_CNR = gap_CNR/min_g
        min_s = 20/(ratio_AC + ratio_RY + ratio_CNR)
        sleep_AC = 1/(min_s * ratio_AC)
        sleep_RY = 1/(min_s * ratio_RY)
        sleep_CNR = 1/(min_s * ratio_CNR)
        
        
        sleep(0.01)
        tick, status = get_tick()

def CNR():
    while status == 'ACTIVE' and not stop_event.is_set():
    #     if gross_position < max_gross_position:
    #         if net_position < max_long_exposure:
    #             resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_CNR, 'action': 'BUY'})
    #         if net_position > max_short_exposure:
    #             resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_CNR, 'action': 'SELL'})
    #     if gross_position > max_gross_position and pos_CNR > 0:
    #         if net_position > max_short_exposure:
    #             resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_CNR, 'action': 'SELL'})
    #     if gross_position > max_gross_position and pos_CNR < 0:
    #         if net_position < max_long_exposure:
    #             resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_CNR, 'action': 'BUY'})
    #     sleep(sleep_CNR)
        
        if -midstop <= pos_CNR <= midstop:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_CNR, 'action': 'BUY'})    
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_CNR, 'action': 'SELL'})    
        elif -highstop <= pos_CNR < -midstop:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_CNR, 'action': 'BUY'})
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': half, 'price': best_ask_CNR, 'action': 'SELL'})
        elif midstop < pos_CNR <= highstop:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': half, 'price': best_bid_CNR, 'action': 'BUY'})
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_CNR, 'action': 'SELL'})
        elif pos_CNR > highstop:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_CNR, 'action': 'SELL'})
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_CNR, 'action': 'SELL'})
        else:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_CNR, 'action': 'BUY'})
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'CNR', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_CNR, 'action': 'BUY'})
        sleep(sleep_CNR)
        s.post('http://localhost:65535/v1/commands/cancel', params = {'ticker': 'CNR'})
def RY():
    while status == 'ACTIVE' and not stop_event.is_set():
        # if gross_position < max_gross_position:
        #     if net_position < max_long_exposure:
        #         resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_RY, 'action': 'BUY'})
        #     if net_position > max_short_exposure:
        #         resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_RY, 'action': 'SELL'})
        # if gross_position > max_gross_position and pos_RY > 0:
        #     if net_position > max_short_exposure:
        #         resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_RY, 'action': 'SELL'})
        # if gross_position > max_gross_position and pos_RY < 0:
        #     if net_position < max_long_exposure:
        #         resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_RY, 'action': 'BUY'})
        # sleep(sleep_RY)
        
        if -midstop <= pos_RY <= midstop:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_RY, 'action': 'BUY'})    
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_RY, 'action': 'SELL'})    
        elif -highstop <= pos_RY < -midstop:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_RY, 'action': 'BUY'})
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': half, 'price': best_ask_RY, 'action': 'SELL'})
        elif midstop < pos_RY <= highstop:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': half, 'price': best_bid_RY, 'action': 'BUY'})
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_RY, 'action': 'SELL'})
        elif pos_RY > highstop:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_RY, 'action': 'SELL'})
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_RY, 'action': 'SELL'})
        else:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_RY, 'action': 'BUY'})
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'RY', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_RY, 'action': 'BUY'})
        sleep(sleep_RY)
        s.post('http://localhost:65535/v1/commands/cancel', params = {'ticker': 'RY'})
def AC():
    while status == 'ACTIVE' and not stop_event.is_set():
        # if gross_position < max_gross_position:
        #     if net_position < max_long_exposure:
        #         resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_AC, 'action': 'BUY'})
        #     if net_position > max_short_exposure:
        #         resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_AC, 'action': 'SELL'})
        # if gross_position > max_gross_position and pos_AC > 0:
        #     if net_position > max_short_exposure:
        #         resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_AC, 'action': 'SELL'})
        # if gross_position > max_gross_position and pos_AC < 0:
        #     if net_position < max_long_exposure:
        #         resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_AC, 'action': 'BUY'})
        # sleep(sleep_AC)
        
        if -midstop <= pos_AC <= midstop:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_AC, 'action': 'BUY'})    
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_AC, 'action': 'SELL'})    
        elif -highstop <= pos_AC < -midstop:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_AC, 'action': 'BUY'})
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': half, 'price': best_ask_AC, 'action': 'SELL'})
        elif midstop < pos_AC <= highstop:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': half, 'price': best_bid_AC, 'action': 'BUY'})
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_AC, 'action': 'SELL'})
        elif pos_AC > highstop:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_AC, 'action': 'SELL'})
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_ask_AC, 'action': 'SELL'})
        else:
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_AC, 'action': 'BUY'})
            resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': 'AC', 'type': 'LIMIT', 'quantity': order_limit, 'price': best_bid_AC, 'action': 'BUY'})
        sleep(sleep_AC)
        s.post('http://localhost:65535/v1/commands/cancel', params = {'ticker': 'AC'})
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
