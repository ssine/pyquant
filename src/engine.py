from data_loader import get_tradeblazer_df, get_l2_df, get_test_df, df_to_tick_data
from simulator import Exchange, get_tick_diff
from constant import OrderType, Direction, Offset, Status
from strategy import BaseStrategy
import datetime as dt
from inspect import isfunction
from tqdm import tqdm
import logging
import pandas as pd
from typing import List

logger = logging.getLogger('engine')

def empty_func():
    pass

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
        self.tracking_accounts = {} # balance, long pos, short pos
        self.tracking_account_symbols = {} # balance, long pos, short pos
        self.exchange = None
        self.strategy = None

    def load_data(self, tp: str, filename: str, symbol: str, opts = {}):
        df = None
        if tp == 'tb':
            df = get_tradeblazer_df(filename)
        elif tp == 'l2':
            df = get_l2_df(filename)
        elif tp == 'test':
            df = get_test_df(filename)
        else:
            print(f'data type {tp} not supported.')
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
        return df

    def init_exchange(self):
        self.exchange = Exchange({s: self.tick_data[s][0] for s in self.symbols}, 5)

    def place_order(self, d, account_name = None):
        order_id = self.exchange.place_order(d, account_name)
        return order_id

    def set_strategy(self, st: BaseStrategy):
        self.strategy = st
        self.strategy.set_engine(self)

    def track_account(self, name, symbols: List[str]):
        self.tracking_accounts[name] = []
        self.tracking_account_symbols[name] = symbols

    def account_trace_to_csv(self, account_name, filename):
        cols = ['balance', 'asset']
        for syn in self.tracking_account_symbols[account_name]:
            cols.append(f'{syn}_long')
            cols.append(f'{syn}_short')
        df = pd.DataFrame(self.tracking_accounts[account_name], columns=cols)
        df.to_csv(filename)

    def step(self):
        earlist_time = dt.datetime.now()
        earlist_symbol = ''
        next_evts = []
        for symbol in self.symbols:
            if len(self.tick_order[symbol]) <= self.tick_idx[symbol]:
                continue
            evts = self.tick_order[symbol][self.tick_idx[symbol]]
            if len(evts) == 0:
                earlist_symbol = symbol
                next_evts = evts
                break
            if evts[0][0] <= earlist_time:
                earlist_time = evts[0][0]
                earlist_symbol = symbol
                next_evts = evts
        if earlist_symbol == '':
            print('backtesting finished')
            return None
        self.tick_idx[earlist_symbol] += 1
        # logger.debug('-----------')
        # logger.debug(f'stepping {earlist_symbol}')
        # logger.debug('tick before:')
        # logger.debug(self.tick_data[earlist_symbol][self.tick_idx[earlist_symbol]-1].__dict__)
        for evt in next_evts:
            # logger.debug(evt)
            if evt[1] == 'buy' or evt[1] == 'sell':
                self.exchange.place_order({
                    'symbol': earlist_symbol,
                    'price': evt[2],
                    'volume': evt[3],
                    'direction': Direction.LONG if evt[1] == 'buy' else Direction.SHORT,
                    'is_history': True,
                    'order_type': OrderType.LIMIT,
                    'offset': Offset.OPEN,
                })
            elif evt[1] == 'cancel':
                self.exchange.cancel_data_order(earlist_symbol, evt[2], evt[3])
            else:
                print(f'unknown action type: {evt[1]}')
                return None
        tk = self.exchange.snapshot()
        tk = self.amend_tick_data(tk)
        for accn in self.tracking_accounts.keys():
            acc = self.exchange.accounts[accn]
            lst = [acc.balance, acc.balance]
            for sym in self.tracking_account_symbols[accn]:
                lst[1] += (acc.position[sym]['long'] - acc.position[sym]['short']) * tk[sym].last_price
                lst.append(acc.position[sym]['long'])
                lst.append(acc.position[sym]['short'])
            self.tracking_accounts[accn].append(lst)
        self.strategy.on_tick(tk)
        # logger.debug('tick after:')
        # logger.debug(self.tick_data[earlist_symbol][self.tick_idx[earlist_symbol]].__dict__)
        return tk

    def amend_tick_data(self, tick):
        # fill in last trade info in a tick
        for sym in self.symbols:
            if self.tick_idx[sym] > 0:
                original = self.tick_data[sym][self.tick_idx[sym]]
                setattr(tick[sym], 'last_price', original.last_price)
                setattr(tick[sym], 'last_volume', original.last_volume)
        return tick

    def verify_tick(self, tick):
        for sym in self.symbols:
            if self.tick_idx[sym] > 0:
                original = self.tick_data[sym][self.tick_idx[sym]]
                if original != tick[sym]:
                    return False
        return True

    def test(self):
        tick_count = 0
        for symbol in self.symbols:
            tick_count += len(self.tick_order[symbol])
        for idx in tqdm(range(tick_count), desc='correctness verification'):
        # for idx in range(tick_count):
            # print(idx)
            tk = self.step()
            if tk is None:
                return
            if not self.verify_tick(tk):
                print('verification error!')
                return

    def start(self):
        self.strategy.on_init()
        self.strategy.on_start()
        tick_count = 0
        for symbol in self.symbols:
            tick_count += len(self.tick_order[symbol])
        for idx in tqdm(range(tick_count), desc='backtest'):
            tk = self.step()
            if tk is None:
                return
            if tick_count - idx < 3:
                if tick_count - idx == 2:
                    # cover account forcebly
                    acc = self.exchange.accounts['test']
                    for sym in acc.position.keys():
                        self.exchange.place_order({
                            'symbol': sym,
                            'volume': acc.position[sym]['long'],
                            'is_history': False,
                            'order_type': OrderType.MARKET,
                            'direction': Direction.LONG,
                            'offset': Offset.CLOSE,
                        }, 'test')
                        self.exchange.place_order({
                            'symbol': sym,
                            'volume': acc.position[sym]['short'],
                            'is_history': False,
                            'order_type': OrderType.MARKET,
                            'direction': Direction.SHORT,
                            'offset': Offset.CLOSE,
                        }, 'test')
            else:
                self.strategy.on_tick(tk)
            if self.exchange.accounts['test'].balance < 200:
                print('no enough balance, break')
                break
            