# pyquant

This is my graduation project, a trading system focusing on accurate local backtesting.

## 主要模块

### 基础数据类型

此部分对期货交易过程中的基础数据类型进行了定义，例如买卖的多空方向这个枚举类 `Direction` ，订单类 `OrderData` 和 tick 数据类 `TickData` ，是整个程序的基础。 该部分参考了 `vnpy` 的数据结构。

### simulator

该部分对交易所的内部逻辑进行模拟，几个对象包括了基础的订单队列 `OrderQueue` ，期货 `Future` 用订单队列组成交易委托账本来管理单个期货的逻辑，以及内含多个期货的 `Exchange` 交易所。

该模块同样包括一个由 tick 数据生成模拟订单信息的工具函数 `get_tick_diff` 。

### data_loader

该部分负责读取不同来源的数据，并将其解析为程序内部的 `TickData` 。 目前支持 TradeBlazer 导出的数据以及老师提供的 l2 数据。

### strategy

strategy 定义了策略的接口。

### UI

`gui.py` 包含了对交易所内部结构的可视化，可以显示所有期货的交易委托账本，并区分历史订单与回测策略的订单。

![sample](https://media.githubusercontent.com/media/ssine/pyquant/master/image/gui.png)
