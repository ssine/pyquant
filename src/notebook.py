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
eng = Engine()
df = eng.load_data('tb', os.path.join(os.path.dirname(__file__), '../data/IF888_Tick.csv'), 'IF888')


# %%
df

# %%
df['lastPrice'].max()

# %%
df['lastPrice'].min()


# %%
