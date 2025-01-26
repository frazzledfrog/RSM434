import requests
from time import sleep
import numpy as np

s = requests.Session()
s.headers.update({'X-API-key': 'GWD0TB2'})

# global variables
MAX_LONG_EXPOSURE_NET = 50000
MAX_SHORT_EXPOSURE_NET = -50000
MAX_EXPOSURE_NET = 50000
MAX_EXPOSURE_GROSS = 100000
ORDER_LIMIT = 10000
TRADE_BUFFER = 0.4
REBALANCE_BUFFER = 0.6
# BUFFER is to make sure that the mispricing covers the trading commission
# and takes into account of the price difference of using MARKET orders
TARGET_STOCK_TRACKER = None


def get_tick():
    resp = s.get('http://localhost:65535/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick'], case['status']


def get_news(eps_estimates, ownership_estimates, eps):
    resp = s.get('http://localhost:65535/v1/news', params = {'limit': 50}) # default limit is 20
    if resp.ok:
        news_query = resp.json()

        for i in news_query[::-1]: # iterating backwards through the list, news items are ordered newest to oldest
            if i['headline'].find("TP") > -1:

                if i['headline'].find("Analyst") > -1:

                    if i['headline'].find("#1") > -1:
                        eps_estimates[0, 0] = float(i['body'][i['body'].find("Q1:") + 5 : i['body'].find("Q1:") + 9 ])
                        eps_estimates[0, 1] = float(i['body'][i['body'].find("Q2:") + 5 : i['body'].find("Q2:") + 9 ])
                        eps_estimates[0, 2] = float(i['body'][i['body'].find("Q3:") + 5 : i['body'].find("Q3:") + 9 ])
                        eps_estimates[0, 3] = float(i['body'][i['body'].find("Q4:") + 5 : i['body'].find("Q4:") + 9 ])

                    elif i['headline'].find("#2") > -1:
                        eps_estimates[0, 1] = float(i['body'][i['body'].find("Q2:") + 5 : i['body'].find("Q2:") + 9 ])
                        eps_estimates[0, 2] = float(i['body'][i['body'].find("Q3:") + 5 : i['body'].find("Q3:") + 9 ])
                        eps_estimates[0, 3] = float(i['body'][i['body'].find("Q4:") + 5 : i['body'].find("Q4:") + 9 ])

                    elif i['headline'].find("#3") > -1:
                        eps_estimates[0, 2] = float(i['body'][i['body'].find("Q3:") + 5 : i['body'].find("Q3:") + 9 ])
                        eps_estimates[0, 3] = float(i['body'][i['body'].find("Q4:") + 5 : i['body'].find("Q4:") + 9 ])

                    elif i['headline'].find("#4") > -1:
                        eps_estimates[0, 3] = float(i['body'][i['body'].find("Q4:") + 5 : i['body'].find("Q4:") + 9 ])

                if i['headline'].find("institutional") > -1:

                    if i['headline'].find("Q1") > -1:
                        ownership_estimates[0, 0] = float(i['body'][i['body'].find("%") - 5 : i['body'].find("%")])

                    elif i['headline'].find("Q2") > -1:
                        ownership_estimates[0, 1] = float(i['body'][i['body'].find("%") - 5 : i['body'].find("%")])

                    elif i['headline'].find("Q3") > -1:
                        ownership_estimates[0, 2] = float(i['body'][i['body'].find("%") - 5 : i['body'].find("%")])

                    elif i['headline'].find("Q4") > -1:
                        ownership_estimates[0, 3] = float(i['body'][i['body'].find("%") - 5 : i['body'].find("%")])

            elif i['headline'].find("AS") > -1:

                if i['headline'].find("Analyst") > -1:

                    if i['headline'].find("#1") > -1:
                        eps_estimates[1, 0] = float(i['body'][i['body'].find("Q1:") + 5 : i['body'].find("Q1:") + 9 ])
                        eps_estimates[1, 1] = float(i['body'][i['body'].find("Q2:") + 5 : i['body'].find("Q2:") + 9 ])
                        eps_estimates[1, 2] = float(i['body'][i['body'].find("Q3:") + 5 : i['body'].find("Q3:") + 9 ])
                        eps_estimates[1, 3] = float(i['body'][i['body'].find("Q4:") + 5 : i['body'].find("Q4:") + 9 ])

                    elif i['headline'].find("#2") > -1:
                        eps_estimates[1, 1] = float(i['body'][i['body'].find("Q2:") + 5 : i['body'].find("Q2:") + 9 ])
                        eps_estimates[1, 2] = float(i['body'][i['body'].find("Q3:") + 5 : i['body'].find("Q3:") + 9 ])
                        eps_estimates[1, 3] = float(i['body'][i['body'].find("Q4:") + 5 : i['body'].find("Q4:") + 9 ])

                    elif i['headline'].find("#3") > -1:
                        eps_estimates[1, 2] = float(i['body'][i['body'].find("Q3:") + 5 : i['body'].find("Q3:") + 9 ])
                        eps_estimates[1, 3] = float(i['body'][i['body'].find("Q4:") + 5 : i['body'].find("Q4:") + 9 ])

                    elif i['headline'].find("#4") > -1:
                        eps_estimates[1, 3] = float(i['body'][i['body'].find("Q4:") + 5 : i['body'].find("Q4:") + 9 ])

                if i['headline'].find("institutional") > -1:

                    if i['headline'].find("Q1") > -1:
                        ownership_estimates[1, 0] = float(i['body'][i['body'].find("%") - 5 : i['body'].find("%")])

                    elif i['headline'].find("Q2") > -1:
                        ownership_estimates[1, 1] = float(i['body'][i['body'].find("%") - 5 : i['body'].find("%")])

                    elif i['headline'].find("Q3") > -1:
                        ownership_estimates[1, 2] = float(i['body'][i['body'].find("%") - 5 : i['body'].find("%")])

                    elif i['headline'].find("Q4") > -1:
                        ownership_estimates[1, 3] = float(i['body'][i['body'].find("%") - 5 : i['body'].find("%")])

            elif i['headline'].find("BA") > -1:

                if i['headline'].find("Analyst") > -1:

                    if i['headline'].find("#1") > -1:
                        eps_estimates[2, 0] = float(i['body'][i['body'].find("Q1:") + 5 : i['body'].find("Q1:") + 9 ])
                        eps_estimates[2, 1] = float(i['body'][i['body'].find("Q2:") + 5 : i['body'].find("Q2:") + 9 ])
                        eps_estimates[2, 2] = float(i['body'][i['body'].find("Q3:") + 5 : i['body'].find("Q3:") + 9 ])
                        eps_estimates[2, 3] = float(i['body'][i['body'].find("Q4:") + 5 : i['body'].find("Q4:") + 9 ])

                    elif i['headline'].find("#2") > -1:
                        eps_estimates[2, 1] = float(i['body'][i['body'].find("Q2:") + 5 : i['body'].find("Q2:") + 9 ])
                        eps_estimates[2, 2] = float(i['body'][i['body'].find("Q3:") + 5 : i['body'].find("Q3:") + 9 ])
                        eps_estimates[2, 3] = float(i['body'][i['body'].find("Q4:") + 5 : i['body'].find("Q4:") + 9 ])

                    elif i['headline'].find("#3") > -1:
                        eps_estimates[2, 2] = float(i['body'][i['body'].find("Q3:") + 5 : i['body'].find("Q3:") + 9 ])
                        eps_estimates[2, 3] = float(i['body'][i['body'].find("Q4:") + 5 : i['body'].find("Q4:") + 9 ])

                    elif i['headline'].find("#4") > -1:
                        eps_estimates[2, 3] = float(i['body'][i['body'].find("Q4:") + 5 : i['body'].find("Q4:") + 9 ])

                if i['headline'].find("institutional") > -1:

                    if i['headline'].find("Q1") > -1:
                        ownership_estimates[2, 0] = float(i['body'][i['body'].find("%") - 5 : i['body'].find("%")])

                    elif i['headline'].find("Q2") > -1:
                        ownership_estimates[2, 1] = float(i['body'][i['body'].find("%") - 5 : i['body'].find("%")])

                    elif i['headline'].find("Q3") > -1:
                        ownership_estimates[2, 2] = float(i['body'][i['body'].find("%") - 5 : i['body'].find("%")])

                    elif i['headline'].find("Q4") > -1:
                        ownership_estimates[2, 3] = float(i['body'][i['body'].find("%") - 5 : i['body'].find("%")])

            elif i['headline'].find("Earnings release") > -1:

                if i['headline'].find("Q1") > -1:
                    eps[0, 0] = float(i['body'][i['body'].find("TP Q1:") + 32 : i['body'].find("TP Q1:") + 36 ])
                    eps[1, 0] = float(i['body'][i['body'].find("AS Q1:") + 32 : i['body'].find("AS Q1:") + 36 ])
                    eps[2, 0] = float(i['body'][i['body'].find("BA Q1:") + 32 : i['body'].find("BA Q1:") + 36 ])

                elif i['headline'].find("Q2") > -1:
                    eps[0, 1] = float(i['body'][i['body'].find("TP Q2:") + 32 : i['body'].find("TP Q2:") + 36 ])
                    eps[1, 1] = float(i['body'][i['body'].find("AS Q2:") + 32 : i['body'].find("AS Q2:") + 36 ])
                    eps[2, 1] = float(i['body'][i['body'].find("BA Q2:") + 32 : i['body'].find("BA Q2:") + 36 ])

                elif i['headline'].find("Q3") > -1:
                    eps[0, 2] = float(i['body'][i['body'].find("TP Q3:") + 32 : i['body'].find("TP Q3:") + 36 ])
                    eps[1, 2] = float(i['body'][i['body'].find("AS Q3:") + 32 : i['body'].find("AS Q3:") + 36 ])
                    eps[2, 2] = float(i['body'][i['body'].find("BA Q3:") + 32 : i['body'].find("BA Q3:") + 36 ])

                elif i['headline'].find("Q4") > -1:
                    eps[0, 3] = float(i['body'][i['body'].find("TP Q4:") + 32 : i['body'].find("TP Q4:") + 36 ])
                    eps[1, 3] = float(i['body'][i['body'].find("AS Q4:") + 32 : i['body'].find("AS Q4:") + 36 ])
                    eps[2, 3] = float(i['body'][i['body'].find("BA Q4:") + 32 : i['body'].find("BA Q4:") + 36 ])

        return eps_estimates, ownership_estimates, eps


# functions from other cases
def get_bid_ask(ticker):
    payload = {'ticker': ticker}
    if ticker is not None:
        resp = s.get ('http://localhost:65535/v1/securities/book', params = payload)
        if resp.ok:
            book = resp.json()
            bid_side_book = book['bids']
            ask_side_book = book['asks']

            bid_prices_book = [item["price"] for item in bid_side_book]
            ask_prices_book = [item['price'] for item in ask_side_book]
            sleep(0.3)
            best_bid_price = bid_prices_book[0]
            best_ask_price = ask_prices_book[0]

            return best_bid_price, best_ask_price


# Own functions
def stock_position(ticker):
    resp = s.get('http://localhost:65535/v1/securities')
    if resp.ok:
        book = resp.json()
        for item in book:
            if item["ticker"] == ticker:
                return item["position"]


def get_position():
    resp = s.get ('http://localhost:65535/v1/securities')
    if resp.ok:
        book = resp.json()
        return abs(book[0]['position']) + abs(book[1]['position']) + abs(book[2]['position'])


def get_stock_with_position_1():
    resp = s.get ('http://localhost:65535/v1/securities')
    if resp.ok:
        book = resp.json()
        for item in book:
            if item['position'] != 0.0:
                return item['ticker']
        return None


def get_stock_with_position_2():
    resp = s.get ('http://localhost:65535/v1/securities')
    if resp.ok:
        book = resp.json()
        l = len(book)
        for i in range(l):
            if book[l - i - 1]['position'] != 0.0:
                return book[l - i]['ticker']
        return None


def get_long_position():
    resp = s.get ('http://localhost:65535/v1/securities')
    if resp.ok:
        book = resp.json()
        long_position = 0
        for i in range(3):
            if book[i]["position"] >= 0:
                long_position += book[i]["position"]
        return long_position


def get_short_position():
    resp = s.get ('http://localhost:65535/v1/securities')
    if resp.ok:
        book = resp.json()
        short_position = 0
        for i in range(3):
            if book[i]["position"] <= 0:
                short_position += book[i]["position"]
        return short_position


def get_order_status_response(order_id):
    resp = s.get('http://localhost:65535/v1/orders' + '/' + str(order_id))
    if resp.ok:
        return True
    return False


def get_price_range(estimate: float, tick: int) -> (float, float):
    lower_bound = estimate - ((300 - tick) / 50)
    upper_bound = estimate + ((300 - tick) / 50)
    return lower_bound, upper_bound


def update_price_range(prev, new_upper: float, new_lower: float):
    prev_upper = prev[1]
    prev_lower = prev[0]
    if prev_upper == prev_lower:
        return new_lower, new_upper
    elif new_upper < prev_lower:
        return max(prev_lower, new_lower), prev_upper
    elif new_lower > prev_upper:
        return prev_lower, min(prev_upper, new_upper)
    return max(prev_lower, new_lower), min(prev_upper, new_upper)


def target_stock_and_action(ticker_list, market_prices, TP_range, AS_range, BA_range):
    # Define the price ranges as a list of tuples
    price_ranges = [TP_range, AS_range, BA_range]

    # Initialize variables to track the max difference, corresponding ticker, and action
    max_difference = 0
    target_ticker = None
    action = None

    # Iterate over each asset
    for i in range(3):
        bid_price = market_prices[i, 0]
        ask_price = market_prices[i, 1]
        lower_bound = price_ranges[i][0]
        upper_bound = price_ranges[i][1]

        # Calculate the differences between the bid price and the lower bound,
        # and between the ask price and the upper bound.
        # buy at ask, sell at bid
        bid_difference = lower_bound - ask_price if ask_price < lower_bound else 0
        ask_difference = bid_price - upper_bound if bid_price > upper_bound else 0

        # Determine the largest difference for this asset
        current_difference = max(bid_difference, ask_difference)

        # Update max difference, target ticker, and action if the current difference is larger
        if current_difference > max_difference:
            max_difference = current_difference
            target_ticker = ticker_list[i]
            action = 'BUY' if current_difference == bid_difference else 'SELL'
    if max_difference < TRADE_BUFFER:
        return None, None
    return target_ticker, action


def get_target_stock_price_range(AS_range, BA_range, TP_range, target_stock):
    target_stock_range = None
    if target_stock == 'TP':
        target_stock_range = TP_range
    elif target_stock == 'AS':
        target_stock_range = AS_range
    elif target_stock == 'BA':
        target_stock_range = BA_range
    return target_stock_range


def news_len():
    resp = s.get('http://localhost:65535/v1/news', params = {'limit': 50})
    if resp.ok:
        return len(resp.json())


def get_current_quarter():
    resp = s.get('http://localhost:65535/v1/case')
    if resp.ok:
        case = resp.json()
        tick = case['tick']
        current_quarter = 0
        if tick < 60:
            current_quarter = 1
        elif tick < 120:
            current_quarter = 2
        elif tick < 180:
            current_quarter = 3
        elif tick < 240 or tick < 300:
            current_quarter = 4
        return current_quarter


def has_changed(target_stock, target_stock_tracker):
    # check if this is the first call and set the original value
    if target_stock_tracker is None:
        return False
    # target stock changed
    if target_stock != target_stock_tracker:
        return True
    # target stock remains the same
    return False


def has_open_orders():
    resp = s.get('http://localhost:65535/v1/orders')
    if resp.ok:
        orders = resp.json()
        return len(orders) != 0


def get_open_orders_info():
    resp = s.get('http://localhost:65535/v1/orders')
    if resp.ok:
        order = resp.json()[0]
        stock = order['ticker']
        price = order['price']
        action = order['action']
        return stock, price, action
        # use get_target_stock_range() to compare price and range values


# Refactor - Extracted Methods [update_valuation() & valuations()]
# for update_values() need to have diff version creating upper & lower range
def update_values(eps, eps_estimates, eps_val, own_val, ownership_estimates):
    for i in range(3):
        for j in range(4):
            if eps[i, j] != 0:
                eps_val[i, j] = eps[i, j]
            elif eps_estimates[i, j] != 0:
                eps_val[i, j] = eps_estimates[i, j]
            if ownership_estimates[i, j] != 0:
                own_val[i, 0] = ownership_estimates[i, j]
    print("--- EPS for Valuation ---")
    print(eps_val)
    print("--- Ownership for Valuation ---")
    print(own_val)


def update_upper_val(eps, upper_eps_estimates, upper_eps_val, ownership_estimates, upper_own_val):
    for i in range(3):
        stock_dev = 0.0
        ownership_dev = 0.0
        current_quarter = get_current_quarter()
        if i == 0:
            stock_dev = 0.02
            ownership_dev = 20.0
        elif i == 1:
            stock_dev = 0.04
            ownership_dev = 25.0
        elif i == 2:
            stock_dev = 0.06
            ownership_dev = 30.0

        for j in range(4):
            time_dev = j + 2
            price_error = stock_dev * (time_dev - current_quarter)
            ownership_error = ownership_dev - (j * 5.0)
            if eps[i, j] != 0:
                upper_eps_val[i, j] = eps[i, j]
            # update upper bonds
            elif upper_eps_estimates[i, j] != 0:
                upper_eps_val[i, j] = upper_eps_estimates[i, j] + price_error
            if ownership_estimates[i, j] != 0:
                upper_own_val[i, 0] = ownership_estimates[i, j] + ownership_error if (ownership_estimates[i, j] + ownership_error < 80) else 80
                # upper_own_val[i, 0] = ownership_estimates[i, j] * (1 + ownership_error) if (ownership_estimates[i, j] * (1 + ownership_error) < 100) else 100
    # print("--- Upper EPS for Valuation ---")
    # print(upper_eps_val)
    # print("--- Upper Ownership for Valuation ---")
    # print(upper_own_val)


def update_lower_val(eps, lower_eps_estimates, lower_eps_val, ownership_estimates, lower_own_val):
    for i in range(3):
        stock_dev = 0.0
        ownership_dev = 0.0
        current_quarter = get_current_quarter()
        if i == 0:
            stock_dev = 0.02
            ownership_dev = 20.0
        elif i == 1:
            stock_dev = 0.04
            ownership_dev = 25.0
        elif i == 2:
            stock_dev = 0.06
            ownership_dev = 30.0

        for j in range(4):
            time_dev = j + 2
            price_error = stock_dev * (time_dev - current_quarter)
            ownership_error = ownership_dev - (j * 5.0)
            if eps[i, j] != 0:
                lower_eps_val[i, j] = eps[i, j]
            # update lower bonds
            elif lower_eps_estimates[i, j] != 0:
                lower_eps_val[i, j] = lower_eps_estimates[i, j] - price_error
            if ownership_estimates[i, j] != 0:
                lower_own_val[i, 0] = ownership_estimates[i, j] - ownership_error if (ownership_estimates[i, j] - ownership_error > 20) else 20
                # lower_own_val[i, 0] = ownership_estimates[i, j] * (1 - ownership_error) if (ownership_estimates[i, j] * (1 - ownership_error) > 0) else 0
    # print("--- Lower EPS for Valuation ---")
    # print(lower_eps_val)
    # print("--- Lower Ownership for Valuation ---")
    # print(lower_own_val)


def valuations(eps_val, own_val) -> (float, float, float):
    TP_eps = eps_val.sum(axis = 1)[0]
    TP_g = (TP_eps / 1.43) - 1
    TP_div = TP_eps * 0.80
    TP_DDM = ((TP_div * (1 + TP_g)) / (0.05 - TP_g)) * (1 - ((1 + TP_g) / (1 + 0.05))**5 ) + ((TP_div * ((1 + TP_g)**5) * (1 + 0.02)) / (0.05 - 0.02)) / (1 + 0.05)**5
    TP_pe = TP_eps * 12
    TP_val = (own_val[0, 0] / 100) * TP_DDM + (1 - (own_val[0,0] / 100)) * TP_pe

    AS_eps = eps_val.sum(axis = 1)[1]
    AS_g = (AS_eps / 1.55) - 1
    AS_div = AS_eps * 0.50
    AS_DDM = ((AS_div * (1 + AS_g)) / (0.075 - AS_g)) * (1 - ((1 + AS_g) / (1 + 0.075))**5 ) + ((AS_div * ((1 + AS_g)**5) * (1 + 0.02)) / (0.075 - 0.02)) / (1 + 0.075)**5
    AS_pe = AS_eps * 16
    AS_val = (own_val[1, 0] / 100) * AS_DDM + (1 - (own_val[1,0] / 100)) * AS_pe

    BA_eps = eps_val.sum(axis = 1)[2]
    BA_g = (BA_eps / 1.50) - 1
    BA_pe_inst = 20 * (1 + BA_g) * BA_eps
    BA_pe_retail = BA_eps * 20
    BA_val = (own_val[2, 0] / 100) * BA_pe_inst + (1 - (own_val[2,0] / 100)) * BA_pe_retail
    # print("--- TP Valuation ---")
    # print(TP_val)
    # print("--- AS Valuation --")
    # print(AS_val)
    # print("--- BA Valuation ---")
    # print(BA_val)
    return TP_val, AS_val, BA_val


def get_open_order_price_quantity(stock_ticker, bid):
    """
    if bid == True, get bid. Else, get ask.
    return price, quantity.
    """
    payload = {'ticker': stock_ticker}
    resp = s.get('http://localhost:65535/v1/securities/book', params=payload)
    if resp.ok:
        if bid:
            book = resp.json()
            bid_side_book = book['bids']
            top_bid_price = bid_side_book[0]['price']
            top_bid_quantity = int(bid_side_book[0]['quantity'])
            return top_bid_price, top_bid_quantity
        else:
            book = resp.json()
            ask_side_book = book['asks']
            top_ask_price = ask_side_book[0]['price']
            top_ask_quantity = int(ask_side_book[0]['quantity'])
            return top_ask_price, top_ask_quantity


def book_not_empty(stock_ticker, bid):
    """
    if bid == True, get bid. Else, get ask.
    """
    payload = {'ticker': stock_ticker}
    resp = s.get('http://localhost:65535/v1/securities/book', params=payload)
    if resp.ok:
        if bid:
            book = resp.json()
            return len(book['bids']) != 0
        else:
            book = resp.json()
            return len(book['asks']) != 0


def main():

    global TARGET_STOCK_TRACKER, target_stock
    tick, status = get_tick()
    ticker_list = ['TP', 'AS', 'BA']
    target_stock = None
    market_prices = np.array([0.,0.,0.,0.,0.,0.])
    market_prices = market_prices.reshape(3,2)

    # variables for eps, ownership valuation calculations and estimates
    eps_estimates = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    eps_estimates = eps_estimates.reshape(3, 4)

    ownership_estimates = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    ownership_estimates = ownership_estimates.reshape(3, 4)

    eps = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    eps = eps.reshape(3, 4)

    # eps_estimates & eps from earnings release updates values in eps_val used in valuation
    eps_val = np.array([0.40, 0.33, 0.33, 0.37, 0.35, 0.45, 0.50, 0.25, 0.15, 0.50, 0.60, 0.25])
    eps_val = eps_val.reshape(3, 4)

    own_val = np.array([50.0, 50.0, 50.0])
    own_val = own_val.reshape(3, 1)

    # variables for range of eps estimate & values and range of ownership values
    upper_eps_estimates = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    upper_eps_estimates = upper_eps_estimates.reshape(3, 4)

    lower_eps_estimates = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    lower_eps_estimates = lower_eps_estimates.reshape(3, 4)

    upper_eps_val = np.array([0.40, 0.33, 0.33, 0.37, 0.35, 0.45, 0.50, 0.25, 0.15, 0.50, 0.60, 0.25])
    upper_eps_val = upper_eps_val.reshape(3, 4)

    lower_eps_val = np.array([0.40, 0.33, 0.33, 0.37, 0.35, 0.45, 0.50, 0.25, 0.15, 0.50, 0.60, 0.25])
    lower_eps_val = lower_eps_val.reshape(3, 4)

    upper_own_val = np.array([80.0, 80.0, 80.0])
    upper_own_val = upper_own_val.reshape(3, 1)

    lower_own_val = np.array([20.0, 20.0, 20.0])
    lower_own_val = lower_own_val.reshape(3, 1)

    # records the possible price ranges for the assets (low, high)
    TP_range = (0.0, 100.0)
    AS_range = (0.0, 100.0)
    BA_range = (0.0, 100.0)

    while status == "ACTIVE":

        eps_estimates, ownership_estimates, eps = get_news(eps_estimates, ownership_estimates, eps)
        # this is to update upper and lower eps_estimates from news
        upper_eps_estimates, ownership_estimates, eps = get_news(eps_estimates, ownership_estimates, eps)
        lower_eps_estimates, ownership_estimates, eps = get_news(eps_estimates, ownership_estimates, eps)

        # update eps & ownership values/estimates from get_news()
        # update_values(eps, eps_estimates, eps_val, own_val, ownership_estimates)
        update_upper_val(eps, upper_eps_estimates, upper_eps_val, ownership_estimates, upper_own_val)
        update_lower_val(eps, lower_eps_estimates, lower_eps_val, ownership_estimates, lower_own_val)
        # print("--- EPS Estimates from news ---")
        # print(eps_estimates)
        # print("--- Ownership Estimates from news ---")
        # print(ownership_estimates)
        # print("--- EPS from Earnings ---")
        # print(eps)
        # print(get_current_quarter())
        # calculate possible prices
        TP_val_1, AS_val_1, BA_val_1 = valuations(upper_eps_val, upper_own_val)
        TP_val_2, AS_val_2, BA_val_2 = valuations(upper_eps_val, lower_own_val)
        TP_val_3, AS_val_3, BA_val_3 = valuations(lower_eps_val, upper_own_val)
        TP_val_4, AS_val_4, BA_val_4 = valuations(lower_eps_val, lower_own_val)

        # update range for valuation for prices of TP, AS, BA
        upper_TP_val = max(TP_val_1, TP_val_2, TP_val_3, TP_val_4)
        upper_AS_val = max(AS_val_1, AS_val_2, AS_val_3, AS_val_4)
        upper_BA_val = max(BA_val_1, BA_val_2, BA_val_3, BA_val_4)
        lower_TP_val = min(TP_val_1, TP_val_2, TP_val_3, TP_val_4)
        lower_AS_val = min(AS_val_1, AS_val_2, AS_val_3, AS_val_4)
        lower_BA_val = min(BA_val_1, BA_val_2, BA_val_3, BA_val_4)
        # print("--- TP Valuation Range ---")
        # print(lower_TP_val, upper_TP_val)
        # print("--- AS Valuation Range --")
        # print(lower_AS_val, upper_AS_val)
        # print("--- BA Valuation Range---")
        # print(lower_BA_val, upper_BA_val)
        # update_price_range should be only after both eps and ownership are released
        # can use news_len()
        # if news_len() == 3 or news_len() == 4 or news_len() % 7 == 0:
        if news_len() >= 7:
            TP_range = update_price_range(TP_range, upper_TP_val, lower_TP_val)
            AS_range = update_price_range(AS_range, upper_AS_val, lower_AS_val)
            BA_range = update_price_range(BA_range, upper_BA_val, lower_BA_val)
        # print(TP_range)
        # print(AS_range)
        # print(BA_range)
        #
        # trade when you have estimates for all three stocks
        # print('tick: ' + str(tick))
        # while tick < 0:
        # while has_news(7):
        if news_len() >= 7:
            # get market bid ask
            for i in range(3):
                ticker_symbol = ticker_list[i]
                market_prices[i, 0], market_prices[i, 1] = get_bid_ask(ticker_symbol)

            # for loop to identify the largest spread btw mrkt price and valuation
            # identify the target stock and action
            # strategy: if bid < upper bound, buy. if ask > lower bound, sell.
            target_stock, target_action = target_stock_and_action(ticker_list, market_prices, TP_range, AS_range, BA_range)
            # print('target stock: ' + str(target_stock))
            target_stock_range = get_target_stock_price_range(AS_range, BA_range, TP_range, target_stock)

            # update open limit order price according to price range updates
            # print('Updating open limit orders: ' + str(has_open_orders()))
            # if has_open_orders():
            if has_open_orders():
                stock, price, action = get_open_orders_info()
                stock1 = get_stock_with_position_1()
                position = stock_position(stock1)
                price_range = get_target_stock_price_range(AS_range, BA_range, TP_range, stock1)
                if action == 'BUY':
                    if price != round(price_range[0], 2):
                        resp = s.post('http://localhost:65535/v1/commands/cancel', params = {'all': 1})
                        iteration = int(abs(stock_position(stock1)) // ORDER_LIMIT)
                        refill_x = int(abs(stock_position(stock1)) % ORDER_LIMIT)
                        for i in range(iteration):
                            resp = s.post('http://localhost:65535/v1/orders', params={'ticker': stock1, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': round(price_range[0], 2), 'action': action})
                        resp = s.post('http://localhost:65535/v1/orders', params={'ticker': stock1, 'type': 'LIMIT', 'quantity': refill_x, 'price': round(price_range[0], 2), 'action': action})
                elif action == 'SELL':
                    if price != round(price_range[1], 2):
                        resp = s.post('http://localhost:65535/v1/commands/cancel', params = {'all': 1})
                        iteration = int(abs(stock_position(stock1)) // ORDER_LIMIT)
                        refill_x = int(abs(stock_position(stock1)) % ORDER_LIMIT)
                        for i in range(iteration):
                            resp = s.post('http://localhost:65535/v1/orders', params={'ticker': stock1, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': round(price_range[1], 2), 'action': action})
                        resp = s.post('http://localhost:65535/v1/orders', params={'ticker': stock1, 'type': 'LIMIT', 'quantity': refill_x, 'price': round(price_range[1], 2), 'action': action})

            # Rebalance
            # print('Rebalancing: ' + str(target_stock) + ', ' + str(TARGET_STOCK_TRACKER))
            if target_stock is not None:
                # rebalance process:
                bid, ask = get_bid_ask(target_stock)
                mispriced_profit = 0.0
                if target_action == 'BUY':
                    mispriced_profit = target_stock_range[0] - ask
                elif target_action == 'SELL':
                    mispriced_profit = bid - target_stock_range[1]
                if mispriced_profit > REBALANCE_BUFFER:
                    if target_stock == 'TP':
                        rebalance('AS', AS_range, BA_range, TP_range)
                        rebalance('BA', AS_range, BA_range, TP_range)
                    elif target_stock == 'AS':
                        rebalance('TP', AS_range, BA_range, TP_range)
                        rebalance('BA', AS_range, BA_range, TP_range)
                    else:
                        rebalance('TP', AS_range, BA_range, TP_range)
                        rebalance('AS', AS_range, BA_range, TP_range)
                # # if target stock changed
                # if TARGET_STOCK_TRACKER is None:
                #     # check if its first iteration and sets tracker to target
                #     TARGET_STOCK_TRACKER = target_stock
                # if target_stock != TARGET_STOCK_TRACKER:

                # Handle orders for target stock
                # post orders for target stock, while satisfying the gross net limit
                # print('Trading: ' + str(((get_long_position() + get_short_position()) < MAX_EXPOSURE_NET)))
                if ((get_long_position() + get_short_position()) < MAX_EXPOSURE_NET) and news_len() >= 3:
                    best_bid, best_ask = get_bid_ask(target_stock)
                    quantity = (MAX_EXPOSURE_NET - abs((get_long_position() + get_short_position()))) // 2
                    iteration = int(quantity // ORDER_LIMIT)
                    clear_x = int(quantity % ORDER_LIMIT)
                    # limit order prices are the bounds of the valuation
                    upper_bound_price = round(target_stock_range[1], 2)
                    lower_bound_price = round(target_stock_range[0], 2)
                    if target_action == 'BUY':
                        market_order_price = best_bid
                        # post limit BUY orders
                        print((get_long_position() + get_short_position()) < MAX_EXPOSURE_NET)
                        print(book_not_empty(target_stock, False))
                        print(get_open_order_price_quantity(target_stock, False)[0] < lower_bound_price)
                        while ((get_long_position() + get_short_position()) < MAX_EXPOSURE_NET) and book_not_empty(target_stock, False) and get_open_order_price_quantity(target_stock, False)[0] < lower_bound_price - TRADE_BUFFER:
                            posted_price, posted_quantity = get_open_order_price_quantity(target_stock, False)
                            print(posted_quantity, posted_price)
                            if posted_quantity <= quantity:
                                resp = s.post('http://localhost:65535/v1/orders', params={'ticker': target_stock, 'type': 'LIMIT', 'quantity': posted_quantity, 'price': posted_price, 'action': target_action})
                            else:
                                fraction = quantity
                                resp = s.post('http://localhost:65535/v1/orders', params={'ticker': target_stock, 'type': 'LIMIT', 'quantity': fraction, 'price': posted_price, 'action': target_action})
                            sleep(0.1)
                        # post market BUY orders and limit SELL orders
                        # for i in range(iteration):
                        #     resp = s.post('http://localhost:65535/v1/orders', params={'ticker': target_stock, 'type': 'MARKET', 'quantity': ORDER_LIMIT, 'price': market_order_price, 'action': target_action})
                        #     # resp= = s.post('http://localhost:65535/v1/orders', params={'ticker': '', 'type': 'MARKET', 'quantity': 10000, 'price': 10.0, 'action':'BUY'})
                        #     resp1 = s.post('http://localhost:65535/v1/orders', params={'ticker': target_stock, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': upper_bound_price, 'action': 'SELL'})
                        #     order_id = resp.json()["order_id"] if "order_id" in resp.json() else 0
                        # resp = s.post('http://localhost:65535/v1/orders', params={'ticker': target_stock, 'type': 'MARKET', 'quantity': clear_x, 'price': market_order_price, 'action': target_action})
                        # resp1 = s.post('http://localhost:65535/v1/orders', params={'ticker': target_stock, 'type': 'LIMIT', 'quantity': clear_x, 'price': upper_bound_price, 'action': 'SELL'})
                    elif target_action == 'SELL':
                        market_order_price = best_ask
                        # post limit SELL orders
                        while ((get_long_position() + get_short_position()) < MAX_EXPOSURE_NET) and book_not_empty(target_stock, True) and get_open_order_price_quantity(target_stock, True)[0] > upper_bound_price + TRADE_BUFFER:
                            posted_price, posted_quantity = get_open_order_price_quantity(target_stock, True)
                            if posted_quantity <= quantity:
                                resp = s.post('http://localhost:65535/v1/orders', params={'ticker': target_stock, 'type': 'LIMIT', 'quantity': posted_quantity, 'price': posted_price, 'action': target_action})
                            else:
                                fraction = quantity
                                resp = s.post('http://localhost:65535/v1/orders', params={'ticker': target_stock, 'type': 'LIMIT', 'quantity': fraction, 'price': posted_price, 'action': target_action})
                            sleep(0.1)
                        # post market SELL orders and limit BUY orders
                        # for i in range(iteration):
                        #     resp = s.post('http://localhost:65535/v1/orders', params={'ticker': target_stock, 'type': 'MARKET', 'quantity': ORDER_LIMIT, 'price': market_order_price, 'action': target_action})
                        #     # resp= = s.post('http://localhost:65535/v1/orders', params={'ticker': '', 'type': 'MARKET', 'quantity': ORDER_LIMIT, 'price': 10, 'action': 'SELL'})
                        #     resp1 = s.post('http://localhost:65535/v1/orders', params={'ticker': target_stock, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': lower_bound_price, 'action': 'BUY'})
                        #     order_id = resp.json()["order_id"] if "order_id" in resp.json() else 0
                        #     # if order_id != 0:
                        #         # this might not be sufficient to deal with position update latency
                        #         # while get_order_status_response(order_id):
                        #         #     sleep(0.1)
                        # resp = s.post('http://localhost:65535/v1/orders', params={'ticker': target_stock, 'type': 'MARKET', 'quantity': clear_x, 'price': market_order_price, 'action': target_action})
                        # resp1 = s.post('http://localhost:65535/v1/orders', params={'ticker': target_stock, 'type': 'LIMIT', 'quantity': clear_x, 'price': lower_bound_price, 'action': 'BUY'})
        print("--- EPS Estimates from news ---")
        print(eps_estimates)
        print("--- Ownership Estimates from news ---")
        print(ownership_estimates)
        print("--- EPS from Earnings ---")
        print(eps)
        print(get_current_quarter())
        print("--- TP Valuation Range ---")
        print(lower_TP_val, upper_TP_val)
        print("--- AS Valuation Range --")
        print(lower_AS_val, upper_AS_val)
        print("--- BA Valuation Range---")
        print(lower_BA_val, upper_BA_val)
        print(TP_range)
        print(AS_range)
        print(BA_range)
        print('tick: ' + str(tick))
        print('target stock: ' + str(target_stock))
        print('Updating open limit orders: ' + str(has_open_orders()))
        print('Rebalancing: ' + str(target_stock) + ', ' + str(TARGET_STOCK_TRACKER))
        print('Trading: ' + str(((get_long_position() + get_short_position()) < MAX_EXPOSURE_NET)))
        sleep(0.5)
        tick, status = get_tick()


def rebalance(balance_stock, AS_range, BA_range, TP_range):
    # difference is big enough to cover commission and market movement
    # clear holding position and kill all orders
    position = abs(stock_position(balance_stock))
    upper, lower = get_target_stock_price_range(AS_range, BA_range, TP_range, balance_stock)
    clear_i = int(position // ORDER_LIMIT)
    clear_x = int(position % ORDER_LIMIT)
    if stock_position(balance_stock) > 0:
        sell_price = get_open_order_price_quantity(target_stock, True)[0]
        while (stock_position(balance_stock) != 0) and book_not_empty(balance_stock, True) and sell_price > lower + REBALANCE_BUFFER:
            posted_price, posted_quantity = get_open_order_price_quantity(target_stock, True)
            if posted_quantity < stock_position(balance_stock):
                resp = s.post('http://localhost:65535/v1/orders', params={'ticker': balance_stock, 'type': 'LIMIT', 'quantity': posted_quantity, 'price': sell_price, 'action': 'SELL'})
            else:
                fraction = int(stock_position(balance_stock) - posted_quantity)
                resp = s.post('http://localhost:65535/v1/orders', params={'ticker': balance_stock, 'type': 'LIMIT', 'quantity': fraction, 'price': sell_price, 'action': 'SELL'})

    elif stock_position(balance_stock) < 0:
        buy_price = get_open_order_price_quantity(target_stock, False)[0]
        while (stock_position(balance_stock) != 0) and book_not_empty(balance_stock, False) and buy_price < upper - REBALANCE_BUFFER:
            posted_price, posted_quantity = get_open_order_price_quantity(target_stock, False)
            if posted_quantity < stock_position(balance_stock):
                resp = s.post('http://localhost:65535/v1/orders', params={'ticker': balance_stock, 'type': 'LIMIT', 'quantity': posted_quantity, 'price': buy_price, 'action': 'BUY'})
            else:
                fraction = int(stock_position(balance_stock) - posted_quantity)
                resp = s.post('http://localhost:65535/v1/orders', params={'ticker': balance_stock, 'type': 'LIMIT', 'quantity': fraction, 'price': buy_price, 'action': 'BUY'})
    else:
        print('rebalancing stock ' + balance_stock + ' has a position of zero.')
    resp = s.post('http://localhost:65535/v1/commands/cancel', params={'all': 1})


if __name__ == '__main__':
    main()





