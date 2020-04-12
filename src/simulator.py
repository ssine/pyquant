import pandas as pd
import numpy as np
import collections, sortedcontainers, datetime
from tqdm import tqdm
from item import TickData, Snapshot, OrderData, make_order, get_order
from typing import List, Dict
from constant import OrderType, Direction, Offset, Status

# 一个对 simnow 模拟算法的改进方案：
#
# 1. 通过两个 tick 之间数据的变化推测出本次 tick 内的订单情况
# 2. 将模拟的订单插入 order book ，这样会有一个排队位置
# 3. 在其他订单 consume 当前队列时进行模拟成交
'''
TODO:
* support multiple futures
* consider last trade information(on event generation)
* shadow orders
  * 照常排队
  * 与实际订单同步执行
  * 在当前队列消耗完毕时强制成交
* 订单完成时如何通知算法?
  * 消息机制
  * 回调函数
'''


class OrderQueue:
    '''
    in the bid/ask book, there is an order book for each price, consisted of
    all the orders on this price level.
    '''
    queue: List[OrderData]

    def __init__(self):
        self.queue = []

    def add_order(self, order: OrderData):
        self.queue.append(order)

    def match_order(self, amount: float) -> float:
        '''
        match orders by given amount, return remaining amount that is not consumed.
        using FIFO algorithm currently
        '''
        last_idx = 0
        for idx in range(len(self.queue)):
            if amount <= self.queue[idx].volume:
                last_idx = idx
                if amount == self.queue[idx].volume:
                    last_idx += 1
                # TODO: callback order in queue[0:last_idx]
                self.queue = self.queue[last_idx:]
                return 0
            else:
                amount -= self.queue[idx].volume
        # TODO: callback order in queue
        self.queue = []
        return amount

    def total_amount(self):
        return sum(map(lambda o: o.volume, self.queue))

    def cancel_data_order(self, volume: float):
        # TODO: cancel order from history data
        pass

    def cancel_algo_order(self, order_id: int):
        # TODO: cancel order from backtesting quant strategy
        pass

class Future:
    buy_book: Dict[float, OrderQueue]
    sell_book: Dict[float, OrderQueue]
    order_dict: Dict[int, OrderData]

    def __init__(self, symbol: str, tick: TickData, max_depth: int):
        self.symbol = symbol
        self.max_depth = max_depth
        self.buy_book = sortedcontainers.SortedDict()
        self.sell_book = sortedcontainers.SortedDict()
        for idx in range(tick.data_depth):
            q = OrderQueue()
            q.add_order(make_order({'volume': tick.bid_volume[idx]}))
            self.buy_book[tick.bid_price[idx]] = q
            q = OrderQueue()
            q.add_order(make_order({'volume': tick.ask_volume[idx]}))
            self.sell_book[tick.ask_price[idx]] = q

    def place_order(self, order: OrderData):
        if order.volume == 0:
            return
        if order.order_type == OrderType.LIMIT:
            if order.direction == Direction.LONG and order.offset == Offset.OPEN or order.direction == Direction.SHORT and order.offset == Offset.CLOSE:
                sell_prices = list(self.sell_book.keys())
                for sp in sell_prices:
                    if sp > order.price:
                        break
                    order.volume = self.sell_book[sp].match_order(order.volume)
                    if order.volume > 0:
                        del self.sell_book[sp]
                    else:
                        break
                if order.volume > 0:
                    if order.price not in self.buy_book:
                        self.buy_book[order.price] = OrderQueue()
                    self.buy_book[order.price].add_order(order)
            elif order.direction == Direction.SHORT and order.offset == Offset.OPEN or order.direction == Direction.LONG and order.offset == Offset.CLOSE:
                buy_prices = list(reversed(self.buy_book.keys()))
                for bp in buy_prices:
                    if bp < price:
                        break
                    order.volume = self.buy_book[bp].match_order(order.volume)
                    if order.volume > 0:
                        del self.buy_book[sp]
                    else:
                        break
                if order.volume > 0:
                    if order.price not in self.sell_book:
                        self.sell_book[order.price] = OrderQueue()
                    self.sell_book[order.price].add_order(order)
        elif order.order_type == OrderType.MARKET:
            pass
        else:
            pass

    def cancel_data_order(self, price: float, volume: float):
        if price in self.sell_book:
            self.sell_book[price].cancel_data_order(volume)
            if self.sell_book[price].total_amount() == 0:
                del self.sell_book[price]
        if price in self.buy_book:
            self.buy_book[price].cancel_data_order(volume)
            if self.buy_book[price].total_amount() == 0:
                del self.buy_book[price]

    def cancel_order(self, order_id: int):
        order = get_order(order_id)
        if order.price in self.sell_book:
            self.sell_book[order.price].cancel_algo_order(order_id)
            if self.sell_book[order.price].total_amount() == 0:
                del self.sell_book[order.price]
        if order.price in self.buy_book:
            self.buy_book[order.price].cancel_algo_order(order_id)
            if self.buy_book[order.price].total_amount() == 0:
                del self.buy_book[order.price]

    def snapshot(self) -> TickData:
        sps = list(self.sell_book.keys())[:5]
        bps = list(reversed(self.buy_book.keys()))[:5]
        depth = min(len(sps), len(bps), self.max_depth)
        tick = TickData()
        tick.set_data_depth(depth)
        for i in range(depth):
            tick.bid_price[i] = bps[i]
            tick.bid_volume[i] = self.buy_book[bps[i]].total_amount()
            tick.ask_price[i] = sps[i]
            tick.ask_volume[i] = self.sell_book[sps[i]].total_amount()
        return tick


class Exchange:
    def __init__(self, snapshot: Snapshot, max_depth: int):
        self.futures = {}
        for k in snapshot.keys():
            self.futures[k] = Future(k, snapshot[k], max_depth)

    def add_signal(self, symbol, order_type, price, volume):
        if symbol in self.futures:
            self.futures[symbol].add_signal(order_type, price, volume)
        else:
            print(f'future {symbol} not exist!')

    def place_order(self, symbol: str, order_type: OrderType, direction: Direction, offset: Offset, price: float,
                    volume: float) -> OrderData:
        order = make_order({
            'symbol': symbol,
            'order_type': order_type,
            'direction': direction,
            'offset': offset,
            'price': price,
            'volume': volume
        })
        order.submit_time = datetime.datetime.now()
        order.traded = 0
        order.status = Status.SUBMITTING

        if symbol in self.futures:
            self.futures[symbol].place_order(order)
        else:
            print(f'future {symbol} not exist!')

        return order

    def snapshot(self) -> Snapshot:
        ss = {}
        for symbol in self.futures:
            ss[symbol] = self.futures[symbol].snapshot()
        return ss


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

    for idx in tqdm(range(1, data_length), desc='generate tick diff'):
        tick = ticks[idx]

        events = []  # (price, direction, amount)

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
            events.append(('sell', price, volume))
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
            events.append(('buy', tick.ask_price[0], volume))
            if tick.ask_price[0] == last_tick.ask_price[0]:
                del sell_dict[tick.ask_price[0]]
                del last_sell_dict[tick.ask_price[0]]

        for bp in list(buy_dict.keys()):
            last_volume = 0
            if bp in last_buy_dict:
                last_volume = last_buy_dict[bp]
                del last_buy_dict[bp]
            if buy_dict[bp] > last_volume:
                events.append(('buy', bp, buy_dict[bp] - last_volume))
            elif buy_dict[bp] < last_volume:
                events.append(('cancel', bp, last_volume - buy_dict[bp]))
            del buy_dict[bp]
        for bp in last_buy_dict:
            events.append(('cancel', bp, last_buy_dict[bp]))

        for sp in list(sell_dict.keys()):
            last_volume = 0
            if sp in last_sell_dict:
                last_volume = last_sell_dict[sp]
                del last_sell_dict[sp]
            if sell_dict[sp] > last_volume:
                events.append(('sell', sp, sell_dict[sp] - last_volume))
            elif sell_dict[sp] < last_volume:
                events.append(('cancel', sp, last_volume - sell_dict[sp]))
            del sell_dict[sp]
        for sp in last_sell_dict:
            events.append(('cancel', sp, last_sell_dict[sp]))

        last_tick = tick
        tick_events.append(events)
    return tick_events