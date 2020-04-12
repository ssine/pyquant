#%%
# %load_ext autoreload
# %autoreload 2

#%%
from data_loader import get_tradeblazer_df, df_to_tick_data, get_aligned_day_data
from simulator import Exchange, get_tick_diff
from item import TickData
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import numpy as np
plt.rcParams['figure.figsize'] = (20.0, 9.0)

# %%
df = get_tradeblazer_df('i2005_Tick.csv')

# %%
ticks = df_to_tick_data(df, 'i2005')

# %%
df = get_aligned_day_data(df, 2020, 3, 25, df.columns)

# %%
evts = get_tick_diff(ticks)

# %%
ex = Exchange(ticks[0], 1)
for idx, tkev in enumerate(evts):
    for ev in tkev:
        ex.add_signal(*ev)
    t = ex.snapshot()
    if not ticks[idx+1].loose_eq(t):
        print(idx)
        print('previous: ', ticks[idx].__dict__)
        print('events: ', tkev)
        print('should: ', ticks[idx+1].__dict__)
        print('but: ', t.__dict__)
        break


# %%


# %%
