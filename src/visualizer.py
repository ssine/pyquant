import pandas as pd
import numpy as np
import matplotlib
import os
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import collections, sortedcontainers
from tqdm import tqdm

def i_rb_asset():
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), '../data/i_rb_aligned.csv'), index_col=0)

    lp = df['i9888_price'].values - df['rb888_price'].values
    print(lp.min(), lp.max())
    xs = range(len(lp))

    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.plot(xs, lp, label='rb - i', color='orange')

    ax2 = ax.twinx()
    ax2.plot(xs, df['asset'].values, label='asset')

    # ask matplotlib for the plotted objects and their labels
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc=0)
    plt.show()

def i_rb():
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), '../data/i_rb_aligned.csv'), index_col=0)

    lp = df['rb888_price'].values
    xs = range(len(lp))

    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.plot(xs, lp, label='rb', color='orange')

    ax2 = ax.twinx()
    ax2.plot(xs, df['i9888_price'].values, label='i')

    # ask matplotlib for the plotted objects and their labels
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc=0)
    plt.show()

i_rb_asset()