# -*- coding: utf-8 -*-

"""
通过VT_setting.json加载全局配置
"""

import json
import traceback

from vnpy.utils.vtFunction import findConfPath

globalSetting = {}      # 全局配置字典


try:
    with open(findConfPath('VT_setting.json')) as f:
        globalSetting = json.load(f)
except:
    traceback.print_exc()
