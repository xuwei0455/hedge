# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import json
import os

import pandas as pd
import pymongo


def load_path(path_dir=None, path_dirs=None):
    if not path_dirs:
        path_dirs = []

    if path_dir:
        path_dirs.insert(0, path_dir)

    if not path_dirs:
        raise AssertionError("must set path_dir or path_dirs")

    return path_dirs


def filter_main_contract(path_dirs):
    m_files = []

    for path in path_dirs:
        try:
            all_files = os.listdir(path)
        except WindowsError:
            all_files = []
        all_files = filter(lambda _f: "MI_" in _f, all_files)
        m_files.extend([os.path.join(path, _file) for _file in all_files])

    return m_files


class TradingLoader(object):
    def __init__(self, db, path_dir=None, path_dirs=None):

        self.db = db

        self.dir = load_path(path_dir, path_dirs)
        self.files = filter_main_contract(self.dir)

    @staticmethod
    def read_csv(file_name):
        df = pd.read_csv(file_name, header=0, encoding="gbk", parse_dates={"datetime": [0, 1]},
                         names=["date", "time", "lastPrice", "volume", "total_volume", "change_volume",
                                "bidPrice1", "bidVolume1", "bidPrice2", "bidVolume2", "bidPrice3", "bidVolume3",
                                "askPrice1", "askVolume1", "askPrice2", "askVolume2", "askPrice3", "askVolume3",
                                "BS"])

        symbol = file_name.split(os.sep)[-1].split("_")[0]
        df["symbol"] = df["vtSymbol"] = symbol
        df["exchange"] = "UNKNOWN"
        return df

    @staticmethod
    def convert_to_mongo(df):
        df["openInterest"] = df["change_volume"].cumsum()
        del df["change_volume"]
        df["volume"] = df["volume"].cumsum()

        df['date'], df['time'] = df['datetime'].astype(str).str.split(' ', 1).str

        df["datetime"] = df["datetime"].astype(str)
        return df

    @staticmethod
    def to_mongo(db, df):
        records = json.loads(df.T.to_json()).values()
        for item in records:
            item["datetime"] = datetime.datetime.strptime(item["datetime"], "%Y-%m-%d %H:%M:%S")

        getattr(db, item["symbol"]).insert_many(records)

    def run(self):
        for file_name in self.files:
            df = self.read_csv(file_name)
            df = self.convert_to_mongo(df)
            self.to_mongo(self.db, df)


if __name__ == '__main__':
    client = pymongo.MongoClient("localhost", 27017)
    db = client["BackTest"]
    tl = TradingLoader(db, path_dirs=["C:\\Users\\ExV\\Desktop\\data\\201608%s" % str(d+1).zfill(2) for d in range(31)])
    tl.run()
