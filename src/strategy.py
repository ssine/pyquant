from item import TickData
from engine import Engine
from constant import OrderType, Direction, Offset, Status

class BaseStrategy:
    eng: Engine

    def __init__(self):
        self.eng = None

    def set_engine(self, eng):
        self.eng = eng

    def on_init(self):
        pass
    def on_start(self):
        pass
    def on_stop(self):
        pass
    def on_tick(self, tk: TickData):
        pass
    def on_trade(self):
        pass
    def on_order(self):
        pass

    def buy(self, symbol: str, price: float, volume: float):
        self.eng.place_order({
            'symbol': symbol,
            'price': price
            'volume': volume,
            'is_history': False,
            'order_type': OrderType.LIMIT,
            'direction': Direction.LONG,
            'offset': Offset.OPEN,
        })

    def sell(self):
        self.eng.place_order({
            'symbol': symbol,
            'price': price
            'volume': volume,
            'is_history': False,
            'order_type': OrderType.LIMIT,
            'direction': Direction.LONG,
            'offset': Offset.CLOSE,
        })

    def short(self):
        self.eng.place_order({
            'symbol': symbol,
            'price': price
            'volume': volume,
            'is_history': False,
            'order_type': OrderType.LIMIT,
            'direction': Direction.SHORT,
            'offset': Offset.OPEN,
        })

    def cover(self):
        self.eng.place_order({
            'symbol': symbol,
            'price': price
            'volume': volume,
            'is_history': False,
            'order_type': OrderType.LIMIT,
            'direction': Direction.LONG,
            'offset': Offset.CLOSE,
        })

    def cancel_order(self):
        pass
    def cancel_all(self):
        pass