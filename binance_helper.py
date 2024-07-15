import json
import time
import requests
from datetime import datetime
from googlesheet_helper import *
from rich_helper import *
from time_helper import TimeHelper

rh = RichHelper()

# 所有接口拉取的价格都是合约的价格
class BinanceHelper:
    def __init__(self,rh):
        self.rh = rh

    def get_symbol_price(self, symbol):
        '''
        获取币对的价格
        :param symbol: 币对（btcusdt)
        :return: 价格
        '''
        url = f"https://fapi.binance.com/fapi/v1/ticker/price"
        params = {"symbol": symbol}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return float(response.json()['price'])

    @rh.with_status(status_text=f'{rh.white("正在拉取k线数据...")}')
    def get_klines(self,symbol,interval,start_timestamp,end_timestamp):
        '''
        获取币对的历史k线
        :param symbol: 币对（btcusdt)
        :param interval: k的时间间隔（1m）
        :param start_timestamp: 开始时间
        :param end_timestamp: 结束时间
        :return:
        '''

        data_list = []
        while True:
            url = 'https://fapi.binance.com/fapi/v1/klines'
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': start_timestamp,
                'endTime': end_timestamp,
                'limit': 1500 #最大可以拉1500条
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data_list.extend(response.json())
            last_one_time_stamp = data_list[len(data_list)-1][0]
            if last_one_time_stamp >= int(float(end_timestamp)):
                break
            else:
                start_timestamp = last_one_time_stamp
        return data_list

    def draw_down(self,row):
        # 拉取k线
        kline_list = self.get_klines(symbol=row[INDEX_SYMBOL],
            interval='1m',
            start_timestamp=TimeHelper.switch2timestamp(row[INDEX_SETUP_TIME]),
            end_timestamp=TimeHelper.switch2timestamp(datetime.now().strftime("%Y年%m月%d日 %H:%M")))

        # 回测
        new_row = self.update_row(row,kline_list)

        return new_row

    @rh.with_status(status_text=f'{rh.white("正在根据k线数据计算回撤...")}')
    def update_row(self,row,kline_list):
        '''回测，同时更新对应的数据'''

        highest_price = 0
        lowest_price = 9999999
        record_time_stamp = 0

        for kline in kline_list :
            if row[INDEX_IS_CLOSE] == '是':
                break

            high_price = float(kline[2])
            low_price = float(kline[3])
            open_time_time_stamp = kline[0]
            open_time = TimeHelper.switch2formattime(open_time_time_stamp)

            if self.can_we_entry(row,low_price,high_price,open_time) == True:
                row = self.update_entry(row, open_time)

            if self.did_we_entry(row) == False:
                continue

            # TODO 其实可以放到最开始拉k线的时候去计算
            this_row_last_update_time_time_stamp = TimeHelper.get_this_row_last_update_time_time_stamp(row)
            if  this_row_last_update_time_time_stamp >= open_time_time_stamp:
                continue

            if self.is_hit_the_loss(row,low_price,high_price,open_time) == True:
                row = self.update_hit_the_loss(row,low_price,high_price,open_time)
                break

            if self.can_we_take_profit(row,low_price,high_price,open_time) == True:
                row = self.update_take_profit(row, open_time)
        return row

    def update_take_profit(self,row, open_time):
        row[INDEX_WHEN_TAKE_PROFIT_LIST].append(open_time)
        row[INDEX_IS_GET_MONEY] = '是'
        if len(row[INDEX_TAKE_PROFIT_PRICE_LIST]) <= len(row[INDEX_WHEN_TAKE_PROFIT_LIST]):
            row[INDEX_IS_CLOSE] = '是'
            rh.log.info("止盈全部完成，这一单已关闭")
        return row

    def can_we_take_profit(self,row,low_price,high_price,open_time):
        # 先获取还没有止盈的点
        take_profit_times = len(row[INDEX_WHEN_TAKE_PROFIT_LIST])
        if len(row[INDEX_TAKE_PROFIT_PRICE_LIST]) <= take_profit_times:
            return False
        take_profit_price = row[INDEX_TAKE_PROFIT_PRICE_LIST][take_profit_times]

        if low_price <= take_profit_price <= high_price:
            rh.log.info(f"命中止盈点：{take_profit_price} | 最低价：{low_price} 最高价:{high_price} | 时间：{open_time} | 所有止盈点：{row[INDEX_TAKE_PROFIT_PRICE_LIST]}")
            return True
        else:
            return False


    def update_entry(self,row, open_time):
        row[INDEX_WHEN_ENTRY_LIST].append(open_time)
        return row

    def can_we_entry(self,row,low_price,high_price,open_time):
        '''TODO
        现在暂时只考虑了一个点，实际上如果挂单点位比较近，行情闪崩（做多的情况），命中了多个点位
        那么这里就会漏了

        而且还没有考虑现价直接进的情况
        '''

        # 先获取当前还没有进场的点
        entry_times = len(row[INDEX_WHEN_ENTRY_LIST])
        if len(row[INDEX_ENTRY_PRICE_LIST]) <= entry_times:
            return False
        entry_price = row[INDEX_ENTRY_PRICE_LIST][entry_times]

        if low_price <= entry_price <= high_price:
            rh.log.info(f"命中进场点：{entry_price} | 最低价：{low_price} 最高价:{high_price} | 时间：{open_time} | 所有进场点：{row[INDEX_ENTRY_PRICE_LIST]}")
            return True
        else:
            return False


    def did_we_entry(self,row):
        return len(row[INDEX_WHEN_ENTRY_LIST]) > 0

    def is_hit_the_loss(self,row,low_price,high_price,open_time):
        return low_price <= row[INDEX_LOSS_PRICE] <= high_price

    def update_hit_the_loss(self,row,low_price,high_price,open_time):
        rh.log.info(f"命中止损点：{row[INDEX_LOSS_PRICE]} | 最低价：{low_price} 最高价:{high_price} | 时间：{open_time}")
        rh.log.info(f"已经结单，本单已止损")
        row[INDEX_WHEN_LOSS] = open_time
        row[INDEX_IS_CLOSE] = '是'
        row[INDEX_IS_GET_MONEY] = '否'
        return row


class JsonHelper:
    @staticmethod
    def switch2list(list_str :str):
        if list_str == '':
            list_str = '[]'
        return json.loads(list_str)
