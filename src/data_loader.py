'''
本模块负责统一外部数据的格式，将它们读入为格式统一的 pandas DataFrame ，
并可以进一步将 DataFrame 数据转换为 TickData 数据格式。

External Source 1 \
External Source 2 -> DataFrame -> TickData object
Others...         /

DataFrame:
time(index), lastPrice, lastVolume, askPrice1, 2..., bidPrice1, 2..., askVolume1, 2..., bidVolume1, 2..., openInterest
TickData:
see `object.py`
'''
from item import TickData
import datetime
from tqdm import tqdm
from typing import List
import pandas as pd
import numpy as np

def get_tradeblazer_df(filename):
    df = pd.read_csv(filename, names=[
        'date', 'time', 'unk1', 'unk2', 'open_interest_inc', 'unk4',
        'lastVolume', 'lastPrice', 'askPrice1', 'bidPrice1', 'openInterest'])

    def get_row_datetime(row):
        date = str(row['date'])
        time = str(int(row['time'] * 10 ** 9))
        return datetime.datetime(
            int(date[:4]), int(date[4:6]), int(date[6:]),
            int(time[:-7]), int(time[-7:-5]), int(time[-5:-3]), int(time[-3:]) * 1000)

    df['time'] = df.apply(get_row_datetime, axis=1)
    df.drop(['date', 'open_interest_inc', 'unk1'], axis=1, inplace=True)
    df = df.shift(-1)[:-1]

    # I'm guessing
    df.rename(columns={
        'unk2': 'bidVolume1',
        'unk4': 'askVolume1',
    }, inplace=True)
    df.set_index('time', inplace=True)
    return df

# Time,Price,Volume,Amount,OpenInt,TotalVol,TotalAmount,Price2,Price3,LastClose,Open,High,Low,SP1,SP2,SP3,SP4,SP5,SV1,SV2,SV3,SV4,SV5,BP1,BP2,BP3,BP4,BP5,BV1,BV2,BV3,BV4,BV5,isBuy
def get_l2_df(filename):
    df = pd.read_csv(filename, parse_dates=['Time'])

    # time in csv is at second level, assign milliseconds to it
    delta = datetime.timedelta(milliseconds=250)
    df['Time'].iloc[(df['Time'] == df['Time'].shift(1)).values] += delta
    df['Time'].iloc[(df['Time'] == df['Time'].shift(1)).values] += delta
    df['Time'].iloc[(df['Time'] == df['Time'].shift(1)).values] += delta

    col_map = {
        'Time': 'time',
        'Price': 'lastPrice',
        'Volume': 'lastVolume',
        'SP1': 'askPrice1',
        'SP2': 'askPrice2',
        'SP3': 'askPrice3',
        'SP4': 'askPrice4',
        'SP5': 'askPrice5',
        'BP1': 'bidPrice1',
        'BP2': 'bidPrice2',
        'BP3': 'bidPrice3',
        'BP4': 'bidPrice4',
        'BP5': 'bidPrice5',
        'SV1': 'askVolume1',
        'SV2': 'askVolume2',
        'SV3': 'askVolume3',
        'SV4': 'askVolume4',
        'SV5': 'askVolume5',
        'BV1': 'bidVolume1',
        'BV2': 'bidVolume2',
        'BV3': 'bidVolume3',
        'BV4': 'bidVolume4',
        'BV5': 'bidVolume5',
        'OpenInt': 'openInterest',
    }
    df.rename(columns=col_map, inplace=True)
    df = df[list(col_map.values())]
    df.set_index('time', inplace=True)
    return df


def get_aligned_data(df, start_time, end_time, interval_ms, columns):
    '''
    Given a dataframe with ascending 'time' column, extract it's data
    to a dataframe with constant time interval `interval_ms`.
    '''
    time_index = pd.date_range(start_time, end_time, freq=f'{interval_ms}ms')
    ndf = pd.DataFrame(index=time_index, columns=columns)
    df.index = df.index.round(f'{interval_ms}ms')
    df = df.loc[~df.index.duplicated(keep='first')]
    inter_idx = ndf.index.intersection(df.index)
    ndf.loc[inter_idx] = df.loc[inter_idx][columns]
    ndf = ndf.ffill().bfill()
    return ndf

def get_aligned_day_data(df, year, month, day, columns):
    d1 = get_aligned_data(df,
        datetime.datetime(year, month, day, 9, 0),
        datetime.datetime(year, month, day, 10, 15),
        250, columns)
    d2 = get_aligned_data(df,
        datetime.datetime(year, month, day, 10, 30),
        datetime.datetime(year, month, day, 11, 30),
        250, columns)
    d3 = get_aligned_data(df,
        datetime.datetime(year, month, day, 13, 30),
        datetime.datetime(year, month, day, 15, 00),
        250, columns)
    return pd.concat([d1, d2, d3])


def df_to_tick_data(df: pd.DataFrame, symbol: str) -> List[TickData]:
    res = []
    for idx, row in tqdm(df.iterrows(), desc='get tick data', total=len(df)):
        td = TickData()
        td.symbol = symbol
        td.time = row.name
        td.last_price = row['lastPrice']
        td.last_volume = row['lastVolume']
        td.open_interest = row['openInterest']
        if 'askPrice5' in row:
            td.set_data_depth(5)
            td.bid_price[0] = row['bidPrice1']
            td.bid_price[1] = row['bidPrice2']
            td.bid_price[2] = row['bidPrice3']
            td.bid_price[3] = row['bidPrice4']
            td.bid_price[4] = row['bidPrice5']
            td.ask_price[0] = row['askPrice1']
            td.ask_price[1] = row['askPrice2']
            td.ask_price[2] = row['askPrice3']
            td.ask_price[3] = row['askPrice4']
            td.ask_price[4] = row['askPrice5']
            td.bid_volume[0] = row['bidVolume1']
            td.bid_volume[1] = row['bidVolume2']
            td.bid_volume[2] = row['bidVolume3']
            td.bid_volume[3] = row['bidVolume4']
            td.bid_volume[4] = row['bidVolume5']
            td.ask_volume[0] = row['askVolume1']
            td.ask_volume[1] = row['askVolume2']
            td.ask_volume[2] = row['askVolume3']
            td.ask_volume[3] = row['askVolume4']
            td.ask_volume[4] = row['askVolume5']
        else:
            td.set_data_depth(1)
            td.bid_price[0] = row['bidPrice1']
            td.ask_price[0] = row['askPrice1']
            td.bid_volume[0] = row['bidVolume1']
            td.ask_volume[0] = row['askVolume1']
        res.append(td)
    return res
