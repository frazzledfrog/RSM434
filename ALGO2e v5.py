import requests
from time import sleep

s = requests.Session()
s.headers.update({'X-API-key': 'GWD0TB2'})

MAX_EXPOSURE = 24500
MAX_ORDER_LIMIT = 5000


def get_tick():
    resp = s.get('http://localhost:65535/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick'], case['status']

def get_bid_ask(ticker):
    payload = {'ticker': ticker}
    resp = s.get ('http://localhost:65535/v1/securities/book', params = payload)
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
    resp = s.get ('http://localhost:65535/v1/securities/tas', params = payload)
    if resp.ok:
        book = resp.json()
        time_sales_book = [item["quantity"] for item in book]
        return time_sales_book

def get_position():
    resp = s.get ('http://localhost:65535/v1/securities')
    if resp.ok:
        book = resp.json()
        return abs(book[0]['position']) + abs(book[1]['position']) + abs(book[2]['position']) 

def get_open_orders(ticker): 
    payload = {'ticker': ticker}
    resp = s.get ('http://localhost:65535/v1/orders', params = payload)
    if resp.ok:
        orders = resp.json()
        buy_orders = [item for item in orders if item["action"] == "BUY"]
        sell_orders = [item for item in orders if item["action"] == "SELL"]
        return buy_orders, sell_orders

def get_order_status(order_id): 
    resp = s.get ('http://localhost:65535/v1/orders' + '/' + str(order_id))
    if resp.ok:
        order = resp.json()
        return order['status']
    
def calculate_order_limit(position):
    remaining_exposure = MAX_EXPOSURE - position
    return min(MAX_ORDER_LIMIT, remaining_exposure)

def get_ticker_position(ticker):
    resp = s.get ('http://localhost:65535/v1/securities')
    if resp.ok:
        book = resp.json()
        return next(value['position'] for value in book if value['ticker'] == ticker)
                    
def main():
    tick, status = get_tick() 
    ticker_list = ['RY']

    while status == 'ACTIVE':      

        for i in range(1):
            
            ticker_symbol = ticker_list[i]
            
            position = get_position()
            best_bid_price, best_ask_price = get_bid_ask(ticker_symbol)
            order_limit = calculate_order_limit(position)
    
            
            ticker_position = get_ticker_position(ticker_symbol)

        # Long Inventory Trading Behavior
            if ticker_position > 2000 and position < MAX_EXPOSURE:
                resp = s.post('http://localhost:65535/v1/orders', params = {
                    'ticker': ticker_symbol,
                    'type': 'LIMIT',
                    'quantity': order_limit,
                    'price': best_bid_price * 0.97, # Discourage buying by setting bid prices well below market
                    'action': 'BUY'})
                
                order_id = resp.json()['order_id']
                get_order_status(order_id)          
                
                resp = s.post('http://localhost:65535/v1/orders', params = {
                    'ticker': ticker_symbol,
                    'type': 'LIMIT',
                    'quantity': order_limit, 
                    'price': best_ask_price - 0.01, # Encourage selling by setting marketable limit sells
                    'action': 'SELL'})

                sleep(0.5)
                
                s.post('http://localhost:65535/v1/commands/cancel', params = {'ticker': ticker_symbol})
                
        # Short Inventory Trading Behavior
            elif ticker_position < -2000 and position < MAX_EXPOSURE:
                resp = s.post('http://localhost:65535/v1/orders', params = {
                    'ticker': ticker_symbol,
                    'type': 'LIMIT',
                    'quantity': order_limit,
                    'price': best_bid_price + 0.01, # Encourage buying by setting marketable limit buys
                    'action': 'BUY'})
                
                order_id = resp.json()['order_id']
                get_order_status(order_id)          
                
                resp = s.post('http://localhost:65535/v1/orders', params = {
                    'ticker': ticker_symbol,
                    'type': 'LIMIT',
                    'quantity': order_limit, 
                    'price': best_ask_price * 1.03, # Discourage further selling by setting ask prices well above the market
                    'action': 'SELL'})

                sleep(0.5)
                
                s.post('http://localhost:65535/v1/commands/cancel', params = {'ticker': ticker_symbol})
        
        # Normal Trading Behavior
            elif position < MAX_EXPOSURE and ((best_bid_price - best_ask_price) != 0.00): 
                resp = s.post('http://localhost:65535/v1/orders', params = {
                    'ticker': ticker_symbol,
                    'type': 'LIMIT',
                    'quantity': order_limit,
                    'price': best_bid_price - 0.02, # Small spread to maximize profits
                    'action': 'BUY'})
                
                order_id = resp.json()['order_id']
                get_order_status(order_id)          
                
                resp = s.post('http://localhost:65535/v1/orders', params = {
                    'ticker': ticker_symbol,
                    'type': 'LIMIT',
                    'quantity': order_limit, 
                    'price': best_ask_price + 0.02, # Small spread to maximize profits
                    'action': 'SELL'})

                sleep(0.5)
                
                s.post('http://localhost:65535/v1/commands/cancel', params = {'ticker': ticker_symbol})  

        sleep(0.05) 
        
        tick, status = get_tick()

if __name__ == '__main__':
    main()



