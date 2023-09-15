import os
import sys
from enum import Enum
from datetime import datetime

if getattr(sys, 'frozen', False):
    # 判断当前环境是否为打包环境
    base_path = sys._MEIPASS
else:
    # base_path = os.path.dirname(os.path.abspath("."))
    base_path = os.path.abspath(".")

today_time = f'{datetime.now().strftime("%Y-%m-%d")}.json'


class ResourcePath(Enum):

    ResourceDirectory = os.path.join(base_path, 'resource')
    JsAesEncryptFilePath = os.path.join(base_path, os.path.join('resource', 'AesEncrypt.js'))
    SuccessJsonFilePath = os.path.join(base_path, os.path.join('resource', 'answerSucceed.json'))
    YkIcoPath = os.path.join(base_path, os.path.join('resource', 'yk.ico'))
    # YkUiPath = os.path.join(base_path, os.path.join('resource', 'yk.ui'))
    YkUiPath = os.path.join(base_path, os.path.join('resource', 'yk_new.ui'))
    WxImgPath = os.path.join(base_path, os.path.join('resource', 'wx.jpg'))
    CsdnImgPath = os.path.join(base_path, os.path.join('resource', 'csdn.png'))

    TokenPath = os.path.join(base_path, os.path.join('resource/everyday_token', f"{today_time}.json"))

