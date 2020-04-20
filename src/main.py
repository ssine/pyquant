import sys, os
from engine import Engine
from strategy import BaseStrategy

eng = Engine()
eng.load_data('tb', os.path.join(os.path.dirname(__file__), '../data/i2005_Tick.csv'), 'i2005')
eng.load_data('tb', os.path.join(os.path.dirname(__file__), '../data/i2009_Tick.csv'), 'i2009')

eng.init_exchange()

st = BaseStrategy()
eng.set_strategy(st)

eng.start()
