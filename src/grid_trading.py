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
        cell = self.grids[idx]
        if cell['state'] != 'idle':
            return
        acc = self.get_account()
        if acc.balance < self.min_balance:
            print('no enough balance, stop putting order.')
            return
        # print(f'price fall in cell {cell["price"]}, buying')
        def order_finish_callback():
            nonlocal cell
            def on_cover_order_finish():
                nonlocal cell
                cell['state'] = 'idle'
            # print(f'buy order at price {cell["price"]} finished, putting cover order at {cell["cover_price"]}')
            cell['state'] = 'cover'
            self.cover(self.symbol, cell['cover_price'], self.amount, on_cover_order_finish)
        cell['state'] = 'pending'
        self.buy(self.symbol, cell['price'], self.amount, order_finish_callback)
        # print(f'account balance: {acc.balance}')
