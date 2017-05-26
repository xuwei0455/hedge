# -*- coding: utf-8 -*-

"""
TripleThrust交易策略
"""

from datetime import time

from vnpy.utils.vtConstant import EMPTY_STRING
from vnpy.engine.cta.ctaTemplate import CtaTemplate


########################################################################
class TripleThrustStrategy(CtaTemplate):
    """TripleThrust交易策略"""
    className = 'TripleThrustStrategy'
    author = u'william'

    # 策略参数
    k1 = 0.8
    k2 = 0.8

    initBars = 30

    # 策略变量
    bar = None  # K线对象
    barTime = None
    barMinute = EMPTY_STRING  # K线当前的分钟
    barList = []  # K线对象的列表

    SectionOpen = 0
    SectionHigh = 0
    SectionLow = 0

    range = 0
    longEntry = 0
    shortEntry = 0
    dealRange = [
        (time(hour=0, minute=0), time(hour=2, minute=25)),
        (time(hour=8, minute=55), time(hour=14, minute=55)),
        (time(hour=20, minute=55), time(hour=23, minute=59))
    ]

    initStrategy = False
    long_point = None
    short_point = None

    orderList = []  # 保存委托代码的列表

    barInfo = {}
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'k1',
                 'k2']

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'range',
               'longEntry',
               'shortEntry',
               'exitTime']

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(TripleThrustStrategy, self).__init__(ctaEngine, setting)

        self.barList = []

    # ----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' % self.name)
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' % self.name)
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' % self.name)
        self.putEvent()

    # ----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        # 计算K线
        tickMinute = tick.datetime.second

        if tick.datetime.second % 1 == 0:
            if self.bar:
                self.onBar(self.bar)

            bar = CtaBarData()
            bar.vtSymbol = tick.vtSymbol
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange

            bar.open = tick.lastPrice
            bar.high = tick.lastPrice
            bar.low = tick.lastPrice
            bar.close = tick.lastPrice

            bar.openVolume = tick.volume
            bar.volume = 0
            bar.openInterest = tick.openInterest

            bar.date = tick.date
            bar.time = tick.time
            bar.datetime = tick.datetime  # K线的时间设为第一个Tick的时间

            self.bar = bar  # 这种写法为了减少一层访问，加快速度
            self.barMinute = tickMinute  # 更新当前的分钟
        else:  # 否则继续累加新的K线
            bar = self.bar  # 写法同样为了加快速度

            bar.high = max(bar.high, tick.lastPrice)
            bar.low = min(bar.low, tick.lastPrice)
            bar.close = tick.lastPrice

            bar.volume += (tick.volume - bar.openVolume)
            bar.openInterest = tick.openInterest

    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        for orderID in self.orderList:
            # 撤销之前发出的尚未成交的委托（包括限价单和停止单）
            self.cancelOrder(orderID)

        self.orderList = []

        # 处理开市
        if self.barTime and (bar.datetime - self.barTime).seconds > 3600:
            self.barList = []

        self.barTime = bar.datetime

        # 计算指标数值
        self.barList.append(bar)

        if len(self.barList) <= self.initBars:
            return

        # 计算需要的参数
        high_high, low_close = [], []
        high_close, low_low = [], []
        for _bar in self.barList:
            high_high.append(_bar.high)
            low_low.append(_bar.low)
            high_close.append(_bar.close)
            low_close.append(_bar.close)
        self.range = max(max(high_high) - min(low_close), max(high_close) - min(low_low))

        firstBar = self.barList.pop(0)
        self.long_point = firstBar.open + self.k1 * self.range
        self.short_point = firstBar.open - self.k2 * self.range

        if any([start <= bar.datetime.time() <= end for (start, end) in self.dealRange]):
            #
            # exchange = round(float(bar.volume) / bar.openInterest * 100, 2) > 1

            if bar.close > self.long_point:
                if self.pos == 0:
                    vtOrderID = self.buy(self.long_point, 1, stop=True)
                    self.orderList.append(vtOrderID)
                elif self.pos < 0:
                    vtOrderID = self.cover(self.long_point, 1, stop=True)
                    self.orderList.append(vtOrderID)

                    vtOrderID = self.buy(self.long_point, 1, stop=True)
                    self.orderList.append(vtOrderID)

            if bar.close < self.short_point:
                if self.pos == 0:
                    vtOrderID = self.short(self.short_point, 1, stop=True)
                    self.orderList.append(vtOrderID)

                elif self.pos > 0:
                    vtOrderID = self.sell(self.short_point, 1, stop=True)
                    self.orderList.append(vtOrderID)

                    vtOrderID = self.short(self.short_point, 1, stop=True)
                    self.orderList.append(vtOrderID)

        # 收盘平仓
        else:
            if self.pos > 0:
                vtOrderID = self.sell(bar.close * 0.99, abs(self.pos))
                self.orderList.append(vtOrderID)
            elif self.pos < 0:
                vtOrderID = self.cover(bar.close * 1.01, abs(self.pos))
                self.orderList.append(vtOrderID)

        # 发出状态更新事件
        self.putEvent()

    # ----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    # ----------------------------------------------------------------------
    def onTrade(self, trade):
        # 发出状态更新事件
        self.putEvent()


if __name__ == '__main__':
    # 提供直接双击回测的功能
    # 导入PyQt4的包是为了保证matplotlib使用PyQt4而不是PySide，防止初始化出错
    from vnpy.engine.cta.ctaBackTesting import *

    # 创建回测引擎
    engine = BackTestingEngine()

    # 设置引擎的回测模式为K线
    engine.setBackTestingMode(engine.TICK_MODE)

    # 设置回测用的数据起始日期
    engine.setStartDate('20160801', initDays=0)
    engine.setEndDate('20160810')

    # 设置产品相关参数
    engine.setSlippage(1)  # 滑点
    engine.setRate(0.3 / 10000)  # 费率
    engine.setSize(10)  # 合约大小
    engine.setPriceTick(1)  # 价格最小变动

    # 设置使用的历史数据库
    engine.setDatabase("BackTest", 'RBMI')

    # 在引擎中创建策略对象
    engine.initStrategy(TripleThrustStrategy, {})

    # 开始跑回测
    engine.runBackTesting()

    # 显示回测结果
    engine.showBackTestingResult()

    ## 跑优化
    # setting = OptimizationSetting()                 # 新建一个优化任务设置对象
    # setting.setOptimizeTarget('capital')            # 设置优化排序的目标是策略净盈利
    # setting.addParameter('atrLength', 12, 20, 2)    # 增加第一个优化参数atrLength，起始11，结束12，步进1
    # setting.addParameter('atrMa', 20, 30, 5)        # 增加第二个优化参数atrMa，起始20，结束30，步进1
    # setting.addParameter('rsiLength', 5)            # 增加一个固定数值的参数

    ## 性能测试环境：I7-3770，主频3.4G, 8核心，内存16G，Windows 7 专业版
    ## 测试时还跑着一堆其他的程序，性能仅供参考
    # import time
    # start = time.time()

    ## 运行单进程优化函数，自动输出结果，耗时：359秒
    # engine.runOptimization(TripleThrustStrategy, setting)

    ## 多进程优化，耗时：89秒
    # engine.runParallelOptimization(TripleThrustStrategy, setting)

    # print u'耗时：%s' %(time.time()-start)