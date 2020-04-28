import pandas as pd
import datetime as dt
import math, os
from random import random

start_time = dt.datetime(2000, 1, 1, 0, 0, 0, 0)
time_step = dt.timedelta(milliseconds=500)
num_total_tick = 36000
avg_price = 20
price_step = 0.1
price_amplitude = 5
price_T = 50 # number of ticks per cycle
center_amount = 200
amount_jitter = 50
depth = 5

def pricify(p: float):
    return round(avg_price + round((p - avg_price) / price_step) * price_step, 1)

df = pd.DataFrame(columns=[
        'lastPrice',
        'lastVolume',
        'askPrice1',
        'askPrice2',
        'askPrice3',
        'askPrice4',
        'askPrice5',
        'bidPrice1',
        'bidPrice2',
        'bidPrice3',
        'bidPrice4',
        'bidPrice5',
        'askVolume1',
        'askVolume2',
        'askVolume3',
        'askVolume4',
        'askVolume5',
        'bidVolume1',
        'bidVolume2',
        'bidVolume3',
        'bidVolume4',
        'bidVolume5',
        'openInterest'],
    index=['time'])

cur_time = start_time
for idx in range(num_total_tick):
    d = {}
    d['lastPrice'] = pricify(avg_price + price_amplitude * math.cos((idx / price_T) * (2 * math.pi)))
    d['lastVolume'] = round(center_amount + amount_jitter * (random() - 0.5))
    for ordinal in range(1, depth + 1):
        d[f'askPrice{ordinal}'] = pricify(d['lastPrice'] + price_step * ordinal)
        d[f'askVolume{ordinal}'] = max(1, round(d['lastVolume'] / (depth + 1) * (depth + 1 -ordinal) + amount_jitter * (random() - 0.5)))
        d[f'bidPrice{ordinal}'] = pricify(d['lastPrice'] - price_step * ordinal)
        d[f'bidVolume{ordinal}'] = max(1, round(d['lastVolume'] / (depth + 1) * (depth + 1 -ordinal) + amount_jitter * (random() - 0.5)))
    d['openInterest'] = 0
    df = df.append(pd.Series(d, name=cur_time))
    cur_time += time_step

df = df.iloc[1:]

df.to_csv(os.path.join(os.path.dirname(__file__), '../data/grid_test.csv'))
