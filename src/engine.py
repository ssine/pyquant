from data_loader import get_tradeblazer_df, get_l2_df, df_to_tick_data
from simulator import Exchange, get_tick_diff
from constant import OrderType, Direction, Offset, Status
from strategy import BaseStrategy
import datetime as dt
from tqdm import tqdm

class Engine:
    '''
    Engine aggregates basic functions, it loads data, drives simulator and
    supports strategies.
    '''
    def __init__(self):
        self.tick_data = {}
        self.tick_order = {}
        self.tick_idx = {}
        self.symbols = []
        self.exchange = None
        self.strategy = None

    def load_data(self, tp: str, filename: str, symbol: str, opts = {}):
        df = None
        if tp == 'tb':
            df = get_tradeblazer_df(filename)
        elif tp == 'l2':
            df = get_l2_df(filename)
        else:
            print('data type not supported.')
            return
        if 'start_date' in opts:
            df = df[df.index > opts['start_date']]
        if 'end_date' in opts:
            df = df[df.index < opts['end_date']]
        tick = df_to_tick_data(df, symbol)
        self.tick_data[symbol] = tick
        self.tick_order[symbol] = get_tick_diff(tick)
        self.tick_idx[symbol] = 0
        self.symbols.append(symbol)

    def init_exchange(self):
        self.exchange = Exchange({s: self.tick_data[s][0] for s in self.symbols}, 5)

    def set_strategy(self, st: BaseStrategy):
        self.strategy = st

    def test(self):
        idx = 0
        while True:
            earlist_time = dt.datetime.now()
            earlist_symbol = ''
            next_evts = []
            for symbol in self.symbols:
                if len(self.tick_order[symbol]) <= self.tick_idx[symbol]:
                    continue
                evts = self.tick_order[symbol][self.tick_idx[symbol]]
                if len(evts) == 0:
                    earlist_symbol = symbol
                    break
                if evts[0][0] <= earlist_time:
                    earlist_time = evts[0][0]
                    earlist_symbol = symbol
                    next_evts = evts
            if earlist_symbol == '':
                print('backtesting finished')
                return
            if idx % 1000 == 0:
                print(idx)
            idx += 1
            self.tick_idx[earlist_symbol] += 1
            for evt in next_evts:
                self.exchange.place_order({
                    'symbol': earlist_symbol,
                    'price': evt[2],
                    'volume': evt[3],
                    'direction': Direction.LONG if evt[1] == 'buy' else Direction.SHORT,
                    'is_history': True,
                    'order_type': OrderType.LIMIT,
                    'offset': Offset.OPEN,
                })
            self.exchange.snapshot()
    
    def start(self):
        tick_count = 0
        for symbol in self.symbols:
            tick_count += len(self.tick_order[symbol])
        for idx in tqdm(range(tick_count), desc='backtest'):
            earlist_time = dt.datetime.now()
            earlist_symbol = ''
            next_evts = []
            for symbol in self.symbols:
                if len(self.tick_order[symbol]) <= self.tick_idx[symbol]:
                    continue
                evts = self.tick_order[symbol][self.tick_idx[symbol]]
                if len(evts) == 0:
                    earlist_symbol = symbol
                    break
                if evts[0][0] <= earlist_time:
                    earlist_time = evts[0][0]
                    earlist_symbol = symbol
                    next_evts = evts
            if earlist_symbol == '':
                print('backtesting finished')
                return
            self.tick_idx[earlist_symbol] += 1
            for evt in next_evts:
                self.exchange.place_order({
                    'symbol': earlist_symbol,
                    'price': evt[2],
                    'volume': evt[3],
                    'direction': Direction.LONG if evt[1] == 'buy' else Direction.SHORT,
                    'is_history': True,
                    'order_type': OrderType.LIMIT,
                    'offset': Offset.OPEN,
                })
            tk = self.exchange.snapshot()
            self.strategy.on_tick(tk)
