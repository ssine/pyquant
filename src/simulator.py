import pandas as pd
import numpy as np
import collections, sortedcontainers, datetime, sys
from tqdm import tqdm
from item import TickData, Snapshot, OrderData, Account, TradeData
from typing import List, Dict, Tuple
from inspect import isfunction
from constant import OrderType, Direction, Offset, Status

'''
TODO:
* consider last trade information(on event generation)
* visualization
'''

order_fill_list = []

class OrderQueue:
    '''
    in the bid/ask book, there is an order book for each price, consisted of
    all the orders on this price level.
    '''
    queue: List[Tuple[OrderData, List[OrderData]]]
    next_orders: List[OrderData]
    total_amount_var: float
    price: float

    def __init__(self, price: float):
        self.price = price
        self.queue = []
        self.next_orders = []
        self.total_amount_var = 0

    def __del__(self):
        self._consume_algo_order_list(self.next_orders, float('inf'))

    def add_order(self, order: OrderData):
        if order.is_history:
            self.queue.append([order, self.next_orders])
            self.next_orders = []
        else:
            self.next_orders.append(order)
        self.total_amount_var += order.remain()

    def _consume_algo_order_list(self, orders: List[OrderData], amount: float):
        global order_fill_list
        while len(orders) > 0:
            order = orders[0]
            if amount >= order.remain():
                trade_amount = order.remain()
                amount -= trade_amount
                order.traded += trade_amount
                self.total_amount_var -= trade_amount
                if hasattr(order, 'callback') and isfunction(order.callback):
                    order.callback()
                order_fill_list.append(TradeData(order.order_id, self.price, trade_amount))
                orders.pop(0)
            else:
                order.traded += amount
                order_fill_list.append(TradeData(order.order_id, self.price, amount))
                self.total_amount_var -= amount
                break

    def match_order(self, amount: float) -> float:
        '''
        match orders by given amount, return remaining amount that is not consumed.
        using FIFO algorithm currently
        '''
        hist_amount = amount
        while len(self.queue) > 0:
            hist_order, algo_orders = self.queue[0]
            if amount >= hist_order.remain():
                amount -= hist_order.remain()
                self._consume_algo_order_list(algo_orders, hist_order.remain())
                if len(algo_orders) > 0:
                    if len(self.queue) > 1:
                        self.queue[1][1] = algo_orders + self.queue[1][1]
                    else:
                        self.next_orders = algo_orders + self.next_orders
                self.queue.pop(0)
            else:
                hist_order.traded += amount
                self._consume_algo_order_list(algo_orders, amount)
                amount = 0
                break
        self.total_amount_var -= hist_amount - amount
        return amount

    def total_amount(self):
        return self.total_amount_var

    def history_amount(self):
        return sum(map(lambda tp: tp[0].remain(), self.queue))

    # get the total amount in gui for height calculation
    def gui_amount(self):
        algo_height = 0
        hist_height = 0
        for hist_order, algo_orders in self.queue:
            hist_height += hist_order.volume
            algo_height += sum(map(lambda o: o.volume, algo_orders))
            if algo_height < hist_height:
                algo_height = hist_height
        algo_height += sum(map(lambda o: o.volume, self.next_orders))
        return algo_height

    def cancel_data_order(self, amount: float):
        hist_amount = amount
        while len(self.queue) > 0:
            hist_order, algo_orders = self.queue[0]
            if amount >= hist_order.remain():
                amount -= hist_order.remain()
                if len(algo_orders) > 0:
                    if len(self.queue) > 1:
                        self.queue[1][1] = algo_orders + self.queue[1][1]
                    else:
                        self.next_orders = algo_orders + self.next_orders
                self.queue.pop(0)
            else:
                hist_order.volume -= amount
                amount = 0
                break
        self.total_amount_var -= hist_amount - amount
        return amount

    def cancel_algo_order(self, order_id: int):
        for hist, algos in self.queue:
            for idx, order in enumerate(algos):
                if order.order_id == order_id:
                    self.total_amount_var -= order.remain()
                    algos.pop(idx)
                    return

class Future:
    buy_book: Dict[float, OrderQueue]
    sell_book: Dict[float, OrderQueue]
    symbol: str

    def __init__(self, symbol: str, tick: TickData, max_depth: int):
        self.symbol = symbol
        self.max_depth = max_depth
        self.buy_book = sortedcontainers.SortedDict()
        self.sell_book = sortedcontainers.SortedDict()
        for idx in range(tick.data_depth):
            q = OrderQueue(tick.bid_price[idx])
            q.add_order(OrderData({'volume': tick.bid_volume[idx], 'is_history': True, 'traded': 0}))
            self.buy_book[tick.bid_price[idx]] = q
            q = OrderQueue(tick.ask_price[idx])
            q.add_order(OrderData({'volume': tick.ask_volume[idx], 'is_history': True, 'traded': 0}))
            self.sell_book[tick.ask_price[idx]] = q

    def place_order(self, order: OrderData):
        global order_fill_list
        if order.volume == 0:
            order.callback() if hasattr(order, 'callback') else None
            return
        if order.order_type == OrderType.LIMIT:
            if order.direction == Direction.LONG and order.offset == Offset.OPEN or order.direction == Direction.SHORT and order.offset == Offset.CLOSE:
                sell_prices = list(self.sell_book.keys())
                for sp in sell_prices:
                    if sp > order.price:
                        break
                    if not order.is_history:
                        order.callback() if hasattr(order, 'callback') else None
                        order_fill_list.append(TradeData(order.order_id, sp, order.volume))
                        order.volume = 0
                        break
                    order.volume = self.sell_book[sp].match_order(order.volume)
                    if self.sell_book[sp].history_amount() <= 0:
                        del self.sell_book[sp]
                    else:
                        break
                if order.volume > 0:
                    if order.price not in self.buy_book:
                        self.buy_book[order.price] = OrderQueue(order.price)
                    self.buy_book[order.price].add_order(order)
            elif order.direction == Direction.SHORT and order.offset == Offset.OPEN or order.direction == Direction.LONG and order.offset == Offset.CLOSE:
                buy_prices = list(reversed(self.buy_book.keys()))
                for bp in buy_prices:
                    if bp < order.price:
                        break
                    if not order.is_history:
                        order.callback() if hasattr(order, 'callback') else None
                        order_fill_list.append(TradeData(order.order_id, bp, order.volume))
                        order.volume = 0
                        break
                    order.volume = self.buy_book[bp].match_order(order.volume)
                    if self.buy_book[bp].history_amount() <= 0:
                        del self.buy_book[bp]
                    else:
                        break
                if order.volume > 0:
                    if order.price not in self.sell_book:
                        self.sell_book[order.price] = OrderQueue(order.price)
                    self.sell_book[order.price].add_order(order)
        elif order.order_type == OrderType.MARKET:
            pass
        else:
            pass

    def cancel_data_order(self, price: float, volume: float):
        if price in self.sell_book:
            self.sell_book[price].cancel_data_order(volume)
            if self.sell_book[price].history_amount() == 0:
                del self.sell_book[price]
        if price in self.buy_book:
            self.buy_book[price].cancel_data_order(volume)
            if self.buy_book[price].history_amount() == 0:
                del self.buy_book[price]

    def cancel_order(self, order_id: int):
        order = OrderData.get_order(order_id)
        if order.price in self.sell_book:
            self.sell_book[order.price].cancel_algo_order(order_id)
            if self.sell_book[order.price].history_amount() == 0:
                del self.sell_book[order.price]
        if order.price in self.buy_book:
            self.buy_book[order.price].cancel_algo_order(order_id)
            if self.buy_book[order.price].history_amount() == 0:
                del self.buy_book[order.price]

    def snapshot(self) -> TickData:
        sps = list(self.sell_book.keys())[:5]
        bps = list(reversed(self.buy_book.keys()))[:5]
        depth = min(len(sps), len(bps), self.max_depth)
        tick = TickData({'symbol': self.symbol})
        tick.set_data_depth(depth)
        for i in range(depth):
            tick.bid_price[i] = bps[i]
            tick.bid_volume[i] = self.buy_book[bps[i]].total_amount()
            tick.ask_price[i] = sps[i]
            tick.ask_volume[i] = self.sell_book[sps[i]].total_amount()
        return tick


class Exchange:
    accounts: Dict[str, Account]
    order_account: Dict[int, str]
    futures: Dict[str, Future]

    def __init__(self, snapshot: Snapshot, max_depth: int):
        self.futures = {}
        for k in snapshot.keys():
            self.futures[k] = Future(k, snapshot[k], max_depth)
        self.accounts = {}
        self.order_account = {}

    def add_account(self, name: str, balance: float = 0):
        self.accounts[name] = Account(name, balance)

    def get_accounts(self):
        return self.accounts
    
    def get_account(self, name):
        return self.accounts[name]

    def add_signal(self, symbol, order_type, price, volume):
        if symbol in self.futures:
            self.futures[symbol].add_signal(order_type, price, volume)
        else:
            print(f'future {symbol} not exist!')

    def place_order(self, d, account_name = None) -> OrderData:
        if 'is_history' not in d:
            d['is_history'] = False
        order = OrderData(d)
        order.submit_time = datetime.datetime.now()
        order.traded = 0
        order.status = Status.SUBMITTING
        symbol = order.symbol

        if symbol in self.futures:
            self.futures[symbol].place_order(order)
        else:
            print(f'future {symbol} not exist!')
            return

        if account_name is not None:
            if account_name not in self.accounts:
                print(f'account {account_name} not exist!')
            else:
                self.order_account[order.order_id] = account_name

        self._process_trade_data()
        return order

    def cancel_data_order(self, future: str, price: float, volume: float):
        self.futures[future].cancel_data_order(price, volume)

    def snapshot(self) -> Snapshot:
        ss = {}
        for symbol in self.futures:
            ss[symbol] = self.futures[symbol].snapshot()
        return ss

    def _process_trade_data(self):
        global order_fill_list
        for fill in order_fill_list:
            order_id = fill.order_id
            if order_id in self.order_account:
                account = self.accounts[self.order_account[order_id]]
                order = OrderData.get_order(order_id)
                if order.direction == Direction.LONG and order.offset == Offset.OPEN:
                    # print(f'long open, balance - {fill.fill_amount * fill.price}')
                    account.balance -= fill.fill_amount * fill.price
                    account.long_position += fill.fill_amount
                elif order.direction == Direction.LONG and order.offset == Offset.CLOSE:
                    # print(f'long close, balance + {fill.fill_amount * fill.price}')
                    account.balance += fill.fill_amount * fill.price
                    account.long_position -= fill.fill_amount
                elif order.direction == Direction.SHORT and order.offset == Offset.OPEN:
                    # print(f'short open, balance + {fill.fill_amount * fill.price}')
                    account.balance += fill.fill_amount * fill.price
                    account.short_position += fill.fill_amount
                elif order.direction == Direction.SHORT and order.offset == Offset.CLOSE:
                    # print(f'short close, balance - {fill.fill_amount * fill.price}')
                    account.balance -= fill.fill_amount * fill.price
                    account.short_position -= fill.fill_amount
        order_fill_list = []

def get_dict_from_tick(tick: TickData, type: str):
    d = {}
    if type == 'bid':
        for i in range(0, tick.data_depth):
            d[tick.bid_price[i]] = tick.bid_volume[i]
    else:
        for i in range(0, tick.data_depth):
            d[tick.ask_price[i]] = tick.ask_volume[i]
    return d


def get_tick_diff(ticks: List[TickData]):
    last_tick = ticks[0]
    data_length = len(ticks)
    tick_events = []

    for idx in range(1, data_length):
        tick = ticks[idx]

        events = []  # (time, price, direction, amount)

        last_buy_dict = get_dict_from_tick(last_tick, 'bid')
        last_sell_dict = get_dict_from_tick(last_tick, 'ask')
        buy_dict = get_dict_from_tick(tick, 'bid')
        sell_dict = get_dict_from_tick(tick, 'ask')

        if tick.bid_price[0] < last_tick.bid_price[0] or tick.bid_price[0] == last_tick.bid_price[
                0] and tick.bid_volume[0] < last_tick.bid_volume[0]:
            price = tick.bid_price[0] if tick.bid_price[0] == last_tick.bid_price[0] else float('inf')
            volume = last_tick.bid_volume[0] - tick.bid_volume[0] if tick.bid_price[0] == last_tick.bid_price[0] else 0
            for lbp in list(last_buy_dict.keys()):
                if lbp > tick.bid_price[0]:
                    volume += last_buy_dict[lbp]
                    price = min(price, lbp)
                    del last_buy_dict[lbp]
            events.append((tick.time, 'sell', price, volume))
            if tick.bid_price[0] == last_tick.bid_price[0]:
                del buy_dict[tick.bid_price[0]]
                del last_buy_dict[tick.bid_price[0]]

        if tick.ask_price[0] > last_tick.ask_price[0] or tick.ask_price[0] == last_tick.ask_price[
                0] and tick.ask_volume[0] < last_tick.ask_volume[0]:
            price = tick.ask_price[0] if tick.ask_price[0] == last_tick.ask_price[0] else -float('inf')
            volume = last_tick.ask_volume[0] - tick.ask_volume[0] if tick.ask_price[0] == last_tick.ask_price[0] else 0
            for lsp in list(last_sell_dict.keys()):
                if lsp < tick.ask_price[0]:
                    volume += last_sell_dict[lsp]
                    price = max(price, lsp)
                    del last_sell_dict[lsp]
            events.append((tick.time, 'buy', tick.ask_price[0], volume))
            if tick.ask_price[0] == last_tick.ask_price[0]:
                del sell_dict[tick.ask_price[0]]
                del last_sell_dict[tick.ask_price[0]]

        for bp in list(buy_dict.keys()):
            last_volume = 0
            if bp in last_buy_dict:
                last_volume = last_buy_dict[bp]
                del last_buy_dict[bp]
            if buy_dict[bp] > last_volume:
                events.append((tick.time, 'buy', bp, buy_dict[bp] - last_volume))
            elif buy_dict[bp] < last_volume:
                events.append((tick.time, 'cancel', bp, last_volume - buy_dict[bp]))
            del buy_dict[bp]
        for bp in last_buy_dict:
            events.append((tick.time, 'cancel', bp, last_buy_dict[bp]))

        for sp in list(sell_dict.keys()):
            last_volume = 0
            if sp in last_sell_dict:
                last_volume = last_sell_dict[sp]
                del last_sell_dict[sp]
            if sell_dict[sp] > last_volume:
                events.append((tick.time, 'sell', sp, sell_dict[sp] - last_volume))
            elif sell_dict[sp] < last_volume:
                events.append((tick.time, 'cancel', sp, last_volume - sell_dict[sp]))
            del sell_dict[sp]
        for sp in last_sell_dict:
            events.append((tick.time, 'cancel', sp, last_sell_dict[sp]))

        last_tick = tick
        tick_events.append(events)
    return tick_events
