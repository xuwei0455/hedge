# -*- coding: utf-8 -*-

import sys

from vnpy.app import (cta, dr, rm)
from vnpy.engine.uiMainWindow import MainWindow
from vnpy.engine.uiQt import qApp
from vnpy.engine.vt.vtEngine import MainEngine
from vnpy.event.eventEngine import EventEngine2
from vnpy.gate import ctp


# ----------------------------------------------------------------------
def main():
    """主程序入口"""
    # 创建事件引擎
    ee = EventEngine2()

    # 创建主引擎
    me = MainEngine(ee)

    # 添加交易接口
    me.addGateway(ctp)

    # 添加上层应用
    me.addApp(cta)
    me.addApp(dr)
    me.addApp(rm)

    # 创建主窗口
    mw = MainWindow(me, ee)
    mw.showMaximized()

    # 在主线程中启动Qt事件循环
    sys.exit(qApp.exec_())


if __name__ == '__main__':
    main()