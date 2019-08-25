import multiprocessing
from time import sleep
from datetime import datetime, time
from logging import INFO
import getpass

from vnpy.event import EventEngine, Event
from vnpy.trader.setting import SETTINGS
from vnpy.trader.engine import MainEngine
from vnpy.trader.utility import load_json

from vnpy.gateway.huobi import HuobiGateway
from vnpy.gateway.hbdm import HbdmGateway
from vnpy.gateway.okex import OkexGateway
from vnpy.gateway.okexf import OkexfGateway
from vnpy.gateway.binance import BinanceGateway

from vnpy.app.data_recorder import DataRecorderApp
from vnpy.app.data_recorder.engine import EVENT_RECORDER_LOG, EVENT_RECORDER_UPDATE


SETTINGS["log.active"] = True
SETTINGS["log.level"] = INFO
SETTINGS["log.console"] = True
SETTINGS["log.file"] = True

def process_log_event(event: Event):
    """"""
    log = event.data
    print(log)

def process_update_event(event: Event):
    """"""
    data = event.data
    print(f"已订阅K线: {data['bar']}")
    print(f"已订阅行情: {data['tick']}")

def init_engine():
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)

    main_engine.add_gateway(HuobiGateway)
    main_engine.add_gateway(HbdmGateway)
    main_engine.add_gateway(OkexGateway)
    main_engine.add_gateway(OkexfGateway)
    main_engine.add_gateway(BinanceGateway)

    main_engine.write_log("主引擎创建成功")

    log_engine = main_engine.get_engine("log")
    event_engine.register(EVENT_RECORDER_LOG, process_log_event)
    event_engine.register(EVENT_RECORDER_UPDATE, process_update_event)
    main_engine.write_log("注册日志事件监听")

    return main_engine

def connect_gateways(main_engine, passwd=None):
    gateway_names = main_engine.get_all_gateway_names()
    for gateway_name in gateway_names:
        filename = f"connect_{gateway_name.lower()}.json"
        setting = main_engine.get_default_setting(gateway_name)
        loaded_setting = load_json(filename, passwd)
        for field_name, field_value in setting.items():
            if field_name in loaded_setting:
                setting[field_name] = loaded_setting[field_name]
        
        main_engine.connect(setting, gateway_name)
        main_engine.write_log(f"连接{gateway_name}接口")

def subscribe(recorder_engine):
    vt_symbols = recorder_engine.tick_recordings.copy()
    vt_symbols.update(recorder_engine.bar_recordings)
    for vt_symbol in vt_symbols:
        contract = recorder_engine.main_engine.get_contract(vt_symbol)
        if contract:
            recorder_engine.write_log(f"订阅：{vt_symbol}")
            recorder_engine.subscribe(contract)


if __name__ == "__main__":
    # print('Start data recorder engine...')
    # passwd = getpass.getpass('Please enter the config file password: ')

    main_engine = init_engine()
    connect_gateways(main_engine, passwd)

    sleep(10)
    recorder_engine = main_engine.add_app(DataRecorderApp)
    subscribe(recorder_engine)
