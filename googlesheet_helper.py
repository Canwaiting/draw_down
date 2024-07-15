import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from rich_helper import *

rh = RichHelper()

#---表头位置---
INDEX_SETUP_TIME                = 0  # 策略时间
INDEX_SYMBOL                    = 1  # 币种
INDEX_DIRECTION                 = 2  # 方向
INDEX_ENTRY_PRICE_LIST          = 3  # 入场点位
INDEX_WHEN_ENTRY_LIST           = 4  # 入场时间
INDEX_TAKE_PROFIT_PRICE_LIST    = 5  # 止盈点位
INDEX_WHEN_TAKE_PROFIT_LIST     = 6  # 止盈时间
INDEX_LOSS_PRICE                = 7  # 止损点位
INDEX_WHEN_LOSS                 = 8  # 止损时间
INDEX_IS_CLOSE                  = 9  # 是否结单
INDEX_IS_GET_MONEY              = 10 # 是否盈利
#---------

class GoogleSheetHelper:
    def __init__(self,rh, private_key_json_path,worksheets_to_open):
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(private_key_json_path, scope)
        self.rh = rh
        self.client = gspread.authorize(creds)
        self.worksheets = self.client.open(worksheets_to_open)
        self.title_list = []
        self.data = {}
        title_list_str = ""
        for sheet in self.worksheets:
            self.title_list.append(sheet.title)
            title_list_str += sheet.title
            title_list_str += "，"
        title_list_str = title_list_str[:-1]
        # self.first_row = self.get_last_update_time()
        # self.last_update_time = self.first_row[1]

    def get_data(self):
        '''将sheet数据转换成dict形式保存，博主-开单（二维列表）'''

        real_start_row = 2  # 实际开单数据的行号（从0开始数）
        for title in self.title_list:
            worksheet = self.worksheets.worksheet(title)
            all_values = worksheet.get_all_values() # 整个sheet的数据
            gs_data = all_values[real_start_row:]  # 截断后的数据
            self.data[title] = self.switch_gs_data_to_binance_data(gs_data)

    def switch_gs_data_to_binance_data(self,data):
        '''将gs上拉取的data转换成可以被拉取数据的data'''

        for row in data:
            for index,value in enumerate(row):
                # 币对，btc -> btcusdt
                if index == INDEX_SYMBOL:
                    row[index] += 'usdt'
                    continue
                # 入场点位 / 止盈点位 -> 浮点数数组
                if index == INDEX_ENTRY_PRICE_LIST or index == INDEX_TAKE_PROFIT_PRICE_LIST:
                    if value is None or value == '':
                        row[index] = []
                    else:
                        row[index] = [float(x) for x in value.split('\n')]
                    continue
                # 入场时间，止盈时间 -> 字符串数组
                if index == INDEX_WHEN_ENTRY_LIST or index == INDEX_WHEN_TAKE_PROFIT_LIST:
                    if value is None or value == '':
                        row[index] = []
                    else:
                        row[index] = value.split('\n')
                    continue
                # 止损 -> 浮点数
                if index == INDEX_LOSS_PRICE:
                    if value is None or value == '':
                        row[index] = 0.0
                    else:
                        row[index] = json.loads(value)
        return data

    def switch_binance_row_to_gs_row(self,data):
        '''将程序中为了方便计算的data转换成展示到googlesheet上的data'''

        for row in data:
            for index, value in enumerate(row):
                # 币对，btcusdt -> btc
                if index == INDEX_SYMBOL:
                    row[index] = row[index].replace('usdt', '')
                    continue
                # 入场点位 / 止盈点位 -> 字符串，用\n分隔
                if index == INDEX_ENTRY_PRICE_LIST or index == INDEX_TAKE_PROFIT_PRICE_LIST:
                    if value is None or value == []:
                        row[index] = ''
                    else:
                        row[index] = '\n'.join(map(str, value))
                    continue
                # 入场时间，止盈时间 -> 字符串，用\n分隔
                if index == INDEX_WHEN_ENTRY_LIST or index == INDEX_WHEN_TAKE_PROFIT_LIST:
                    if value is None or value == []:
                        row[index] = ''
                    else:
                        row[index] = '\n'.join(value)
                    continue
                # 止损 -> 字符串
                if index == INDEX_LOSS_PRICE:
                    if value is None or value == 0.0:
                        row[index] = ''
                    else:
                        row[index] = json.dumps(value)
        return data

    def save_data(self):
        for title in self.title_list:
            if title in self.data:
                self.save_data_to_row(title, self.data[title], 3)
        rh.log.info("成功保存数据到Excel中")

    def save_data_to_row(self, sheet_name, data, content_start_row):
        worksheet = self.worksheets.worksheet(sheet_name)
        new_data = self.switch_binance_row_to_gs_row(data)
        for i, row in enumerate(new_data):
            worksheet.update(f'A{content_start_row + i}', [row])

    # def save_last_update_time(self, sheet_name, row):
    #     worksheet = self.worksheets.worksheet(sheet_name)