import time
import configparser
from rich_helper import RichHelper
from binance_helper import BinanceHelper
from googlesheet_helper import *

rh = RichHelper()
worksheets_to_open = ''
private_key_json_path = ''
bh = BinanceHelper(rh)
gsh = None

@rh.with_status(status_text=f'{rh.white("正在读取配置文件...")}')
def load_config():
    global worksheets_to_open
    global private_key_json_path

    config = configparser.ConfigParser()
    with open('./config.ini', 'r', encoding='utf-8') as f:
        config.read_file(f)
    worksheets_to_open    = config.get('GoogleSheet', 'worksheets_to_open')
    private_key_json_path = config.get('GoogleSheet', 'private_key_json_path')
    rh.log.success(f"成功读取配置文件 | 需要打开的文档：{rh.yellow(worksheets_to_open)} | 私钥存储路径：{rh.yellow(private_key_json_path)}")

@rh.with_status(status_text=f'{rh.white("正在拉取谷歌文档数据...")}')
def initial_googlesheet():
    global gsh
    gsh = GoogleSheetHelper(rh, private_key_json_path, worksheets_to_open)
    gsh.get_data()
    rh.log.success(f"成功读取谷歌文档数据 | 文档：{rh.yellow(worksheets_to_open)} | 表数量：{rh.yellow(len(gsh.data))}")

rh.log.success("成功启动")
load_config()
initial_googlesheet()

if __name__ == "__main__":
    rh.log.info(f"博主总数：{rh.yellow(len(gsh.data))}")
    i = 0

    # 循环每个sheet（通常一个sheet放置一个博主的单）
    for key,value in gsh.data.items():
        i = i+1
        rh.log.info(f"博主{rh.yellow(i)}：{rh.yellow(key)}，总单子数:{rh.yellow(len(value))}")

        # 循环每个博主中的每个单子（通常一行一单）
        j = 0
        for row in value:
            j = j+1
            # 跳过已关闭的订单
            if row[INDEX_IS_CLOSE] == '是':
                rh.log.info(f"单{rh.yellow(j)}已关闭，不计算回撤")
                continue
            rh.log.info(f"开始计算回撤... | 单{rh.yellow(j)} 时间：{rh.yellow(row[INDEX_SETUP_TIME])} | "
                        f"币对：{rh.yellow(row[INDEX_SYMBOL])} "
                        f"方向：{rh.yellow(row[INDEX_DIRECTION])}")

            new_row = bh.draw_down(row) # 回测
            gsh.data[key][j-1] = new_row # 覆盖

    rh.log.info("成功完成回撤")
    gsh.save_data()