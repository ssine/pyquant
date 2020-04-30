import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

filename = '../data/i_rb_aligned.csv'
asset_col = 'asset'
num_trade_day = 18

def calc_indicators():
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), filename), index_col=0)
    assets = df['asset'].values

    daily_return_ratios = assets[np.linspace(0, len(assets)-1, num_trade_day-1, dtype=np.int)[1:]] / assets[0] - 1
    annualized_return_ratio = daily_return_ratios[-1] / num_trade_day * 250
    volatility = np.sqrt(daily_return_ratios.var() * 250)
    sharp = annualized_return_ratio / volatility

    max_value = assets[0]
    max_drawdown = 0
    for a in assets:
        max_value = max(max_value, a)
        max_drawdown = max(max_drawdown, max_value - a)

    print('sharp ratio: ', sharp)
    print('max drawdown: ', max_drawdown)
    print('annualized return: ', annualized_return_ratio * assets[0])
    print('MAR: ', annualized_return_ratio * assets[0] / max_drawdown)


calc_indicators()
