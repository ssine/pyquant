import pandas as pd
import numpy as np
import matplotlib
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import collections, sortedcontainers
from tqdm import tqdm

def draw_order_book(all_data):
    price_data = all_data[['SP1', 'SP2', 'SP3', 'SP4', 'SP5', 'BP1', 'BP2', 'BP3', 'BP4', 'BP5']]
    volumn_data = all_data[['SV1', 'SV2', 'SV3', 'SV4', 'SV5', 'BV1', 'BV2', 'BV3', 'BV4', 'BV5']]
    min_price = price_data.min().min()
    max_price = price_data.max().max()
    
    def price_idx(price):
        return int((price - min_price) * 2) 
    
    price_interval = max_price - min_price
    
    norm = matplotlib.colors.Normalize(vmin=volumn_data.min().min(), vmax=volumn_data.max().max(), clip=True)
    buy_mapper = cm.ScalarMappable(norm=norm, cmap=cm.Reds)
    sell_mapper = cm.ScalarMappable(norm=norm, cmap=cm.Blues)

    matrix = np.ones((int(price_interval * 2) + 1, price_data.shape[0], 3))
    idx = 0
    for _, row in all_data.iterrows():
        for i in range(1, 6):
            matrix[price_idx(row[f'BP{i}']), idx] = buy_mapper.to_rgba(row[f'BV{i}'])[:-1]
            matrix[price_idx(row[f'SP{i}']), idx] = sell_mapper.to_rgba(row[f'SV{i}'])[:-1]
        idx += 1
    plt.imshow(matrix, cmap=plt.get_cmap('Blues'))
    plt.gca().invert_yaxis()
    plt.show()
