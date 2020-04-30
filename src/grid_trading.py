from item import TickData
from strategy import BaseStrategy

class GridTrading(BaseStrategy):
    def __init__(self, symbol: str, low_price: float, high_price: float, step_price: float, profit: float, amount: float, min_balance: float):
        super().__init__()
        self.grids = []
        self.low_price = low_price
        self.high_price = int((high_price - low_price) / step_price + 1) * step_price + low_price
        self.step_price = step_price
        self.profit = profit
        self.amount = amount
        self.symbol = symbol
        self.min_balance = min_balance
        for idx in range(int((high_price - low_price) / step_price) + 1):
            self.grids.append({
                'price': round(low_price + step_price * idx, 1),
                'amount': amount,
                'state': 'idle', # pending / cover / idle
                'cover_price': round(low_price + step_price * idx + profit, 1),
                'orderId': -1
            })

    def on_tick(self, snapshot):
        tk: TickData = snapshot[self.symbol]
        if tk.last_price < self.low_price or self.high_price < tk.last_price:
            return
        idx = int((tk.last_price - self.low_price) / self.step_price)
        if idx < 0 or idx >= len(self.grids):
            return
        cell = self.grids[idx]
        if cell['state'] != 'idle':
            return
        acc = self.get_account()
        if acc.balance < self.min_balance:
            print('no enough balance, stop putting order.')
            return

        def on_cover_order_finish():
            cell['state'] = 'idle'

        def on_buy_order_finish():
            cell['state'] = 'cover'
            self.sell(self.symbol, cell['cover_price'], self.amount, on_cover_order_finish)

        cell['state'] = 'pending'
        self.buy(self.symbol, cell['price'], self.amount, on_buy_order_finish)

class HedgedGridTrading(BaseStrategy):
    def __init__(self, symbol_1: str, symbol_2: str, low_price: float, high_price: float, step_price: float, profit: float, amount: float, min_balance: float):
        super().__init__()
        self.grids = []
        self.low_price = low_price
        self.high_price = int((high_price - low_price) / step_price + 1) * step_price + low_price
        self.step_price = step_price
        self.profit = profit
        self.amount = amount
        self.symbol_1 = symbol_1
        self.symbol_2 = symbol_2
        self.min_balance = min_balance
        for idx in range(int((high_price - low_price) / step_price) + 1):
            self.grids.append({
                'price': round(low_price + step_price * idx, 1),
                'amount': amount,
                'state': 'idle', # pending / cover / idle
                'cover_price': round(low_price + step_price * idx + profit, 1),
                'orderId': -1
            })

    def on_tick(self, snapshot):
        tk_1: TickData = snapshot[self.symbol_1]
        tk_2: TickData = snapshot[self.symbol_2]
        price_diff = tk_1.last_price - tk_2.last_price
        if price_diff < self.low_price or self.high_price < price_diff:
            return
        idx = int((price_diff - self.low_price) / self.step_price)
        if idx < 0 or idx >= len(self.grids):
            return
        cell = self.grids[idx]
        if cell['state'] != 'idle':
            return
        acc = self.get_account()
        if acc.balance < self.min_balance:
            print('no enough balance, stop putting order.')
            return

        open_finish_count = 0
        close_finish_count = 0

        def on_close_order_finish():
            nonlocal close_finish_count
            close_finish_count += 1
            if close_finish_count == 2:
                cell['state'] = 'idle'

        def on_open_order_finish():
            nonlocal open_finish_count
            open_finish_count += 1
            if open_finish_count == 2:
                cell['state'] = 'cover'
                self.sell(self.symbol_1, tk_1.last_price + self.profit, self.amount, on_close_order_finish)
                self.cover(self.symbol_2, tk_2.last_price - self.profit, self.amount, on_close_order_finish)

        cell['state'] = 'pending'
        self.buy(self.symbol_1, tk_1.last_price, self.amount, on_open_order_finish)
        self.short(self.symbol_2, tk_2.last_price, self.amount, on_open_order_finish)
