import sys, os, math
import tkinter as tk
from simulator import Exchange
from data_loader import get_tradeblazer_df, df_to_tick_data, get_aligned_day_data
from constant import OrderType, Direction, Offset, Status
from item import TickData

class GUI:
    root: tk.Tk
    cv: tk.Canvas
    current_future: str
    ex: Exchange

    SCALE = 40
    WIDTH = 16 * SCALE # x
    HEIGHT = 9 * SCALE # y
    SIDEBAR_WIDTH = 4 * SCALE
    SIDEBAR_ITEM_HEIGHT = 1 * SCALE
    ORDERBOOK_MIDPOINT = (10 * SCALE, 8 * SCALE)

    SELECT_COLOR = '#c8bfe7'
    BID_COLOR = '#99d9ea'
    ASK_COLOR = '#ffaec9'
    BID_ALGO_COLOR = '#45c7ea'
    ASK_ALGO_COLOR = '#ff4a86'
    TRADED_COLOR = '#c3c3c3'

    def __init__(self, ex: Exchange):
        self.ex = ex
        self.root = tk.Tk()
        self.root.title('pyquant')

        self.cv = tk.Canvas(self.root, width=GUI.WIDTH, height=GUI.HEIGHT)
        self.cv.pack()
        self.cv.bind("<Button-1>", self.oncanvasclick)
        self.current_future = list(ex.futures.keys())[0]

        self.draw_exchange()
        self.draw_order_maker()

        self.test_orders = []
        self.test_order_idx = 0

    def start(self):
        tk.mainloop()

    def set_test_orders(self, orders):
        self.test_orders = orders

    def draw_exchange(self):
        SCALE = GUI.SCALE
        WIDTH = GUI.WIDTH
        HEIGHT = GUI.HEIGHT
        SIDEBAR_WIDTH = GUI.SIDEBAR_WIDTH
        SIDEBAR_ITEM_HEIGHT = GUI.SIDEBAR_ITEM_HEIGHT
        ORDERBOOK_MIDPOINT = GUI.ORDERBOOK_MIDPOINT
        cv = self.cv
        ex = self.ex
        cv.create_rectangle(0, 0, WIDTH, HEIGHT, fill='white', width=0)
        cv.create_rectangle(0, 0, SIDEBAR_WIDTH, HEIGHT + 10, fill='white')
        for idx, k in enumerate(ex.futures.keys()):
            color = 'white'
            if k == self.current_future:
                color = GUI.SELECT_COLOR
            cv.create_rectangle(0, idx * SIDEBAR_ITEM_HEIGHT, SIDEBAR_WIDTH, (idx + 1) * SIDEBAR_ITEM_HEIGHT, fill=color)
            cv.create_text(SIDEBAR_WIDTH / 2, (idx + 0.5) * SIDEBAR_ITEM_HEIGHT, text=k)
        cv.create_line(SIDEBAR_WIDTH + SCALE/2, ORDERBOOK_MIDPOINT[1], WIDTH - SCALE/2, ORDERBOOK_MIDPOINT[1], arrow=tk.LAST)
        fut = ex.futures[self.current_future]
        ORDERBOOK_HEIGHT = ORDERBOOK_MIDPOINT[1] - SCALE
        max_amount = max(map(lambda q: q.gui_amount(), fut.buy_book.values()))
        max_amount = max(max_amount, max(map(lambda q: q.gui_amount(), fut.sell_book.values())))
        ORDER_HEIGHT_SCALE = ORDERBOOK_HEIGHT / (2 ** math.ceil(math.log(max_amount, 2)))

        for idx, p in enumerate(reversed(fut.buy_book.keys())):
            LB = ORDERBOOK_MIDPOINT[0] - (idx + 1) * SCALE, ORDERBOOK_MIDPOINT[1]
            cv.create_text(LB[0] + SCALE/2, LB[1] + SCALE/2, text=str(p))
            HIST_Y = LB[1]
            ALGO_Y = LB[1]
            algo_cmds = [] # draw algo order after history to avoid overlapping
            for hist_order, algo_orders in fut.buy_book[p].queue:
                prev_y = HIST_Y
                HIST_Y -= hist_order.volume * ORDER_HEIGHT_SCALE
                cv.create_rectangle(LB[0], HIST_Y, LB[0] + SCALE, prev_y, fill=GUI.BID_COLOR)
                if hist_order.traded > 0:
                    cv.create_rectangle(LB[0], HIST_Y + hist_order.remain() * ORDER_HEIGHT_SCALE, LB[0] + SCALE, prev_y, fill=GUI.TRADED_COLOR)
                for order in algo_orders:
                    prev_y = ALGO_Y
                    ALGO_Y -= order.volume * ORDER_HEIGHT_SCALE
                    algo_cmds.append([LB[0], ALGO_Y, LB[0] + SCALE/2, prev_y, GUI.BID_ALGO_COLOR])
                    if order.traded > 0:
                        algo_cmds.append([LB[0], ALGO_Y + order.remain() * ORDER_HEIGHT_SCALE, LB[0] + SCALE/2, prev_y, GUI.TRADED_COLOR])
                ALGO_Y = min(ALGO_Y, HIST_Y)
            for cmd in algo_cmds:
                cv.create_rectangle(*cmd[:-1], fill=cmd[-1])
            for order in fut.buy_book[p].next_orders:
                prev_y = ALGO_Y
                ALGO_Y -= order.volume * ORDER_HEIGHT_SCALE
                cv.create_rectangle(LB[0], ALGO_Y, LB[0] + SCALE/2, prev_y, fill=GUI.BID_ALGO_COLOR)
                if order.traded > 0:
                    cv.create_rectangle(LB[0], ALGO_Y + order.remain() * ORDER_HEIGHT_SCALE, LB[0] + SCALE/2, prev_y, fill=GUI.TRADED_COLOR)

            cv.create_text(LB[0] + SCALE/2, ALGO_Y - SCALE/2, text=str((LB[1]-ALGO_Y)/ORDER_HEIGHT_SCALE))

        for idx, p in enumerate(fut.sell_book.keys()):
            LB = ORDERBOOK_MIDPOINT[0] + idx * SCALE, ORDERBOOK_MIDPOINT[1]
            cv.create_text(LB[0] + SCALE/2, LB[1] + SCALE/2, text=str(p))
            HIST_Y = LB[1]
            ALGO_Y = LB[1]
            algo_cmds = []
            for hist_order, algo_orders in fut.sell_book[p].queue:
                prev_y = HIST_Y
                HIST_Y -= hist_order.volume * ORDER_HEIGHT_SCALE
                cv.create_rectangle(LB[0], HIST_Y, LB[0] + SCALE, prev_y, fill=GUI.ASK_COLOR)
                if hist_order.traded > 0:
                    cv.create_rectangle(LB[0], HIST_Y + hist_order.remain() * ORDER_HEIGHT_SCALE, LB[0] + SCALE, prev_y, fill=GUI.TRADED_COLOR)
                for order in algo_orders:
                    prev_y = ALGO_Y
                    ALGO_Y -= order.volume * ORDER_HEIGHT_SCALE
                    algo_cmds.append([LB[0], ALGO_Y, LB[0] + SCALE/2, prev_y, GUI.ASK_ALGO_COLOR])
                    if order.traded > 0:
                        algo_cmds.append([LB[0], ALGO_Y + order.remain() * ORDER_HEIGHT_SCALE, LB[0] + SCALE/2, prev_y, GUI.TRADED_COLOR])
                ALGO_Y = min(ALGO_Y, HIST_Y)
            for cmd in algo_cmds:
                cv.create_rectangle(*cmd[:-1], fill=cmd[-1])
            for order in fut.sell_book[p].next_orders:
                prev_y = ALGO_Y
                ALGO_Y -= order.volume * ORDER_HEIGHT_SCALE
                cv.create_rectangle(LB[0], ALGO_Y, LB[0] + SCALE/2, prev_y, fill=GUI.ASK_ALGO_COLOR)
                if order.traded > 0:
                    cv.create_rectangle(LB[0], ALGO_Y + order.remain() * ORDER_HEIGHT_SCALE, LB[0] + SCALE/2, prev_y, fill=GUI.TRADED_COLOR)
            cv.create_text(LB[0] + SCALE/2, ALGO_Y - SCALE/2, text=str((LB[1]-ALGO_Y)/ORDER_HEIGHT_SCALE))

    def oncanvasclick(self, event):
        if event.x < GUI.SIDEBAR_WIDTH:
            idx = int(event.y / GUI.SIDEBAR_ITEM_HEIGHT)
            if idx < len(self.ex.futures.keys()):
                self.current_future = list(self.ex.futures.keys())[idx]
        self.draw_exchange()

    def draw_order_maker(self):
        order_frame = tk.Frame(self.root)
        order_frame.pack(side=tk.TOP)

        tk.Label(order_frame, text='First Name').grid(row=0)
        tk.Label(order_frame, text='Last Name').grid(row=1)
        e1 = tk.Entry(order_frame)
        e2 = tk.Entry(order_frame)
        e1.grid(row=0, column=1)
        e2.grid(row=1, column=1)

        def cb():
            print(e1.get(), e2.get())

        button = tk.Button(order_frame, text='submit order', command=cb)
        button.grid(row=2)

        button = tk.Button(order_frame, text='next order', command=self.put_next_test_order)
        button.grid(row=2, column=1)

    def put_next_test_order(self):
        self.ex.place_order(self.test_orders[self.test_order_idx])
        self.test_order_idx += 1
        self.draw_exchange()

if __name__ == '__main__':
    ta = TickData({
        'symbol': 'a',
        'data_depth': 3,
        'bid_price': [10.1, 10.2, 10.3],
        'ask_price': [10.4, 10.5, 10.6],
        'bid_volume': [20, 30, 40],
        'ask_volume': [50, 20, 30],
    })
    tb = TickData({
        'symbol': 'b',
        'data_depth': 3,
        'bid_price': [10.1, 10.2, 10.3],
        'ask_price': [10.4, 10.5, 10.6],
        'bid_volume': [50, 80, 10],
        'ask_volume': [30, 70, 20],
    })
    tc = TickData({
        'symbol': 'c',
        'data_depth': 3,
        'bid_price': [10.1, 10.2, 10.3],
        'ask_price': [10.4, 10.5, 10.6],
        'bid_volume': [60, 40, 54],
        'ask_volume': [46, 69, 36],
    })
    ex = Exchange({
        'a': ta,
        'b': tb,
        'c': tc,
    }, 3)

    gui = GUI(ex)
    gui.set_test_orders([
        {'price': 10.3, 'volume': 30, 'direction': Direction.LONG, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 20, 'direction': Direction.LONG, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 40, 'direction': Direction.LONG, 'is_history': True, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 40, 'direction': Direction.LONG, 'is_history': True, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 15, 'direction': Direction.LONG, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 10, 'direction': Direction.SHORT, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 10, 'direction': Direction.SHORT, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 10, 'direction': Direction.SHORT, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 10, 'direction': Direction.SHORT, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 10, 'direction': Direction.SHORT, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 10, 'direction': Direction.SHORT, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 10, 'direction': Direction.SHORT, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 10, 'direction': Direction.SHORT, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 10, 'direction': Direction.SHORT, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 10, 'direction': Direction.SHORT, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 10, 'direction': Direction.SHORT, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 10, 'direction': Direction.SHORT, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
        {'price': 10.3, 'volume': 10, 'direction': Direction.SHORT, 'is_history': False, 'order_type': OrderType.LIMIT, 'offset': Offset.OPEN, 'symbol': 'a'},
    ])
    gui.start()
