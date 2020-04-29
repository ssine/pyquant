import numpy as np
import datetime as dt
from typing import List, Dict, Callable, Any
from constant import OrderType, Direction, Offset, Status
import logging

logger = logging.getLogger('item')

class Account:
    name: str
    balance: float
    position: Dict[str, Dict[str, float]]

    def __init__(self, name: str, balance = 0, symbols: List[str] = []):
        self.name = name
        self.balance = balance
        self.position = {}
        for s in symbols:
            self.position[s] = {'long': 0, 'short': 0}

class TickData:
    symbol: str
    time: dt.datetime

    last_price: float
    last_volume: float

    data_depth: int
    bid_price: List[float]
    ask_price: List[float]
    bid_volume: List[float]
    ask_volume: List[float]

    volume: float
    open_interest: float

    def __init__(self, d = {}):
        if d == {}:
            pass
        if 'data_depth' in d:
            self.set_data_depth(d['data_depth'])
        keys = ['symbol', 'time', 'last_price', 'last_volume', 'bid_price', 'ask_price', 'bid_volume', 'ask_volume', 'volume', 'open_interest']
        for k in keys:
            if k in d:
                setattr(self, k, d[k])

    def set_data_depth(self, data_depth):
        self.data_depth = data_depth
        self.bid_price = [0 for i in range(data_depth)]
        self.ask_price = [0 for i in range(data_depth)]
        self.bid_volume = [0 for i in range(data_depth)]
        self.ask_volume = [0 for i in range(data_depth)]

    def loose_eq(self, other):
        # fails on auto reload
        # if isinstance(other, TickData):
        ds = self.__dict__
        do = other.__dict__
        # logger.debug('comparing:')
        # logger.debug(ds)
        # logger.debug(do)
        if self.data_depth == 0 or other.data_depth == 0:
            return True
        for k in ds.keys() & do.keys():
            if ds[k] != do[k]:
                print(f'don\'t eq on key {k}: {ds[k]} | {do[k]}')
                # logger.debug(f'don\'t eq on key {k}: {ds[k]} | {do[k]}')
                return False
        return True
        # return False

    def __eq__(self, other):
        return self.loose_eq(other)
        if type(other) == type(self):
            return np.all([
                self.symbol == other.symbol,
                self.time == other.time,
                self.last_price == other.last_price,
                self.last_volume == other.last_volume,
                self.bid_price == other.bid_price,
                self.ask_price == other.ask_price,
                self.bid_volume == other.bid_volume,
                self.ask_volume == other.ask_volume,
                self.volume == other.volume,
                self.open_interest == other.open_interest
            ])
        return super(TickData, self).__eq__(other)

# exchange snapshot is a dict from symbols to tick data
Snapshot = Dict[str, TickData]

class OrderData:
    order_count: int = 0
    order_dict: Dict[int, 'OrderData'] = {}

    symbol: str
    is_history: bool
    order_id: int
    order_type: OrderType
    direction: Direction
    offset: Offset
    price: float
    volume: float
    traded: float
    status: Status
    submit_time: dt.datetime
    callback: Callable[['OrderData'], None]

    def __init__(self, d: Dict[str, Any]):
        keys = ['symbol', 'is_history', 'order_type', 'direction', 'offset', 'price', 'volume', 'traded', 'status', 'submit_time', 'callback']
        for k in keys:
            if k in d:
                setattr(self, k, d[k])
        OrderData.order_count += 1
        self.order_id = OrderData.order_count
        OrderData.order_dict[self.order_id] = self

    def remain(self):
        return self.volume - self.traded

    @staticmethod
    def get_order(order_id: int) -> 'OrderData':
        return OrderData.order_dict[order_id]

class TradeData():
    """
    Trade data contains information of a fill of an order. One order
    can have several trade fills.
    """
    order_id: int
    price: float
    fill_amount: float

    def __init__(self, order_id, price, fill_amount):
        self.order_id = order_id
        self.price = price
        self.fill_amount = fill_amount
