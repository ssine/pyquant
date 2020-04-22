import sys, os, logging
from engine import Engine
from strategy import SampleStrategy

logging.basicConfig(filename='log.log',
                    filemode='w',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

eng = Engine()
eng.load_data('tb', os.path.join(os.path.dirname(__file__), '../data/i2005_Tick.csv'), 'i2005')
eng.load_data('tb', os.path.join(os.path.dirname(__file__), '../data/i2009_Tick.csv'), 'i2009')

eng.init_exchange()

st = SampleStrategy()
eng.set_strategy(st)

eng.start()
