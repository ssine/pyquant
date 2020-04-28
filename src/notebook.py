#%%
%load_ext autoreload
%autoreload 2

#%%
import sys, os
from engine import Engine
from data_loader import get_tradeblazer_df, get_l2_df, df_to_tick_data
from strategy import BaseStrategy
import matplotlib.pyplot as plt

#%%
df = get_tradeblazer_df(os.path.join(os.path.dirname(__file__), '../data/IF888_Tick.csv'))

# %%
df['lastPrice']

# %%
plt.plot(range(len(df['lastPrice'])), df['lastPrice'])

# %%
