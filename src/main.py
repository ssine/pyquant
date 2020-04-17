import sys, os
from engine import Engine

eng = Engine()
eng.load_data('tb', os.path.join(os.path.dirname(__file__), '../data/i2005_Tick.csv'), 'i2005')
eng.load_data('tb', os.path.join(os.path.dirname(__file__), '../data/i2009_Tick.csv'), 'i2009')

eng.init_exchange()
eng.test()
