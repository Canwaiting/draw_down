from datetime import datetime
from googlesheet_helper import *

class TimeHelper:
    '''
    这里要注意：统一都是以毫秒的形式，而不是秒，而且不能是浮点数
    '''
    @staticmethod
    def switch2timestamp(format_time:str) -> str:
        result = ''
        date_object = datetime.strptime(format_time, "%Y年%m月%d日 %H:%M")
        timestamp = date_object.timestamp()
        result = str(int(timestamp*1000))
        return result

    @staticmethod
    def switch2formattime(timestamp: str) -> str:
        date_object = datetime.fromtimestamp(int(timestamp)/1000)
        result = date_object.strftime("%Y年%m月%d日 %H:%M")
        return result

    @staticmethod
    def get_this_row_last_update_time_time_stamp(row) -> int:
        '''
        获取最后的更新
        逻辑为：用开单时间和记录的最后的入场/止盈时间，取最新的的时间
        '''
        result = int(TimeHelper.switch2timestamp(row[INDEX_SETUP_TIME]))

        for timestamp_str in row[INDEX_WHEN_ENTRY_LIST]:
            timestamp = int(TimeHelper.switch2timestamp(timestamp_str))
            if timestamp > result:
                result = timestamp

        for timestamp_str in row[INDEX_WHEN_TAKE_PROFIT_LIST]:
            timestamp = int(TimeHelper.switch2timestamp(timestamp_str))
            if timestamp > result:
                result = timestamp

        return result
