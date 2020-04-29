#%%
# %load_ext autoreload
# %autoreload 2

#%%
import sys, os
from engine import Engine
from data_loader import get_tradeblazer_df, get_l2_df, df_to_tick_data
from strategy import BaseStrategy
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

#%%
trace = get_tradeblazer_df(os.path.join(os.path.dirname(__file__), '../data/IH888_Tick.csv'))
result = pd.read_csv(os.path.join(os.path.dirname(__file__), '../data/backtest.csv'), index_col=0)

# %%
lp = trace.iloc[1:]['lastPrice'].values
xs = range(len(lp))

fig = plt.figure()
ax = fig.add_subplot(111)

ax.plot(xs, lp, label='price', color='orange')

ax2 = ax.twinx()
ax2.plot(xs, result['asset'].values, label='asset')

# ask matplotlib for the plotted objects and their labels
lines, labels = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines + lines2, labels + labels2, loc=0)
plt.show()