import sys, os, logging
from engine import Engine
from strategy import SampleStrategy
from grid_trading import GridTrading, HedgedGridTrading

eng = Engine()
eng.load_data('tb', os.path.join(os.path.dirname(__file__), '../data/j9888_Tick.csv'), 'i9888')
eng.load_data('tb', os.path.join(os.path.dirname(__file__), '../data/jm888_Tick.csv'), 'rb888')

eng.init_exchange()
eng.exchange.add_account('test', 10000000)
eng.track_account('test', ['i9888', 'rb888'])

# st = GridTrading('test', 16, 24, 0.3, 0.3, 1000, 200)
# st = GridTrading('IF888', df['lastPrice'].min() + 1, df['lastPrice'].max() - 1, 0.2, 5, 50, 200)
# st = HedgedGridTrading('rb888', 'i9888', 2570, 2800, 1, 5, 50, 200)
st = HedgedGridTrading('i9888', 'rb888', 540, 630, 1, 5, 500, 200)
eng.set_strategy(st)
eng.start()
eng.account_trace_to_csv('test', os.path.join(os.path.dirname(__file__), '../data/i_rb_aligned.csv'))
