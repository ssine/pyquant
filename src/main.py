import sys, os, logging
from engine import Engine
from strategy import SampleStrategy
from grid_trading import GridTrading

# logging.basicConfig(filename='log.log',
#                     filemode='w',
#                     format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
#                     datefmt='%H:%M:%S',
#                     level=logging.DEBUG)

# eng = Engine()
# eng.load_data('tb', os.path.join(os.path.dirname(__file__), '../data/i2005_Tick.csv'), 'i2005')
# eng.load_data('tb', os.path.join(os.path.dirname(__file__), '../data/i2009_Tick.csv'), 'i2009')

# eng.init_exchange()

# st = SampleStrategy()
# eng.set_strategy(st)

# eng.start()

eng = Engine()
# eng.load_data('tb', os.path.join(os.path.dirname(__file__), '../data/i2005_Tick.csv'), 'i2005')
# eng.load_data('tb', os.path.join(os.path.dirname(__file__), '../data/i2009_Tick.csv'), 'i2009')
# eng.load_data('test', os.path.join(os.path.dirname(__file__), '../data/grid_test.csv'), 'test')
df = eng.load_data('tb', os.path.join(os.path.dirname(__file__), '../data/IH888_Tick.csv'), 'IF888')

eng.init_exchange()
eng.exchange.add_account('test', 100000000)
eng.track_account('test', ['IF888'])

# st = GridTrading('test', 16, 24, 0.3, 0.3, 1000, 200)
st = GridTrading('IF888', df['lastPrice'].min() + 1, df['lastPrice'].max() - 1, 0.2, 5, 50, 200)
eng.set_strategy(st)
eng.start()
eng.account_trace_to_csv('test', os.path.join(os.path.dirname(__file__), '../data/backtest.csv'))
