from item import TickData
from constant import OrderType, Direction, Offset, Status

class BaseStrategy:

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

    def get_account(self):
        return self.eng.exchange.accounts['test']

    def buy(self, symbol: str, price: float, volume: float, callback = None):
        self.eng.place_order({
            'symbol': symbol,
            'price': price,
            'volume': volume,
            'is_history': False,
            'order_type': OrderType.LIMIT,
            'direction': Direction.LONG,
            'offset': Offset.OPEN,
            'callback': callback,
        }, 'test')

    def sell(self, symbol: str, price: float, volume: float, callback = None):
        self.eng.place_order({
            'symbol': symbol,
            'price': price,
            'volume': volume,
            'is_history': False,
            'order_type': OrderType.LIMIT,
            'direction': Direction.LONG,
            'offset': Offset.CLOSE,
            'callback': callback,
        }, 'test')

    def short(self, symbol: str, price: float, volume: float, callback = None):
        self.eng.place_order({
            'symbol': symbol,
            'price': price,
            'volume': volume,
            'is_history': False,
            'order_type': OrderType.LIMIT,
            'direction': Direction.SHORT,
            'offset': Offset.OPEN,
            'callback': callback,
        }, 'test')

    def cover(self, symbol: str, price: float, volume: float, callback = None):
        self.eng.place_order({
            'symbol': symbol,
            'price': price,
            'volume': volume,
            'is_history': False,
            'order_type': OrderType.LIMIT,
            'direction': Direction.LONG,
            'offset': Offset.CLOSE,
            'callback': callback,
        }, 'test')

    def cancel_order(self):
        pass
    def cancel_all(self):
        pass


class SampleStrategy(BaseStrategy):
    def on_tick(self, tk):
        self.buy('i2009', 100, 10)