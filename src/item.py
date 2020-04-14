import numpy as np
import datetime as dt
from typing import List, Dict, Callable, Any
from constant import OrderType, Direction, Offset, Status

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

    def __init__(self):
        pass

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
        if self.data_depth == 0 or other.data_depth == 0:
            return True
        for k in ds.keys() & do.keys():
            if ds[k] != do[k]:
                print(f'dont eq on key {k}: {ds[k]} | {do[k]}')
                return False
        return True
        # return False

    def __eq__(self, other):
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
        keys = ['symbol', 'is_history', 'order_type', 'direction', 'offset', 'price', 'volume', 'traded', 'status', 'submit_time']
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
