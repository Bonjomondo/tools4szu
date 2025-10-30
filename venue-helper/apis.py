#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @File    : apis.py
"""
体育场馆预约API模块

本模块封装了与深大体育场馆预约系统的所有API交互：
1. getSysConfig: 获取系统配置（场馆列表、项目列表）
2. getTimeList: 获取指定日期的可预约时间段
3. getRoom: 获取指定时间段的可用场地列表
4. postBook: 提交预约请求

所有API请求都需要携带有效的Cookie进行身份认证
"""
import json
import logging
import os

import requests

from settings import cookies, headers, stuid, stuname

# 设置NO_PROXY环境变量，确保直接访问深大服务器，不通过代理
os.environ['NO_PROXY'] = 'ehall.szu.edu.cn'

# 配置日志系统，同时输出到文件和控制台
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("venue.log"),  # 日志文件
        logging.StreamHandler()            # 控制台输出
    ]
)
logger = logging.getLogger(__name__)


def getSysConfig():
    """
    获取系统配置信息
    
    该接口返回体育场馆预约系统的基础配置信息，包括：
    - 所有可预约的场馆列表（包场和散场）
    - 所有运动项目列表（羽毛球、篮球等）
    - 项目对应的场馆信息
    
    返回数据示例：
    {
      "packageVenueList": [...],     # 包场场馆列表
      "dismissalVenueList": [...],   # 散场场馆列表
      "xmList": [                    # 项目列表
        {
          "XMDM": "001",             # 项目代码
          "XMMC": "羽毛球",           # 项目名称
          "DCFS": "1.0",             # 订场方式（1.0:包场, 2.0:散场）
          "XQDM": "1"                # 校区代码（1:粤海, 2:丽湖）
        }
      ]
    }
    
    Returns:
        dict: 系统配置数据，失败返回None
    """
    try:
        ret = requests.post(
            "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/sportVenue/getSportVenueData.do",
            cookies=cookies,
            headers=headers,
        )
        logger.info(f"获取系统配置成功: {ret.text}")
        ret = json.loads(ret.text)
        return ret
    except requests.exceptions.RequestException as e:
        logger.error(f"获取系统配置失败: {e}")
    return None


def getTimeList(XQ, YYRQ, YYLX, XMDM):
    """
    获取指定日期的可预约时间段列表
    
    该接口查询指定条件下所有可预约的时间段，用户可根据返回结果选择预约时间。
    
    Args:
        XQ (str): 校区代码（"1":粤海, "2":丽湖）
        YYRQ (str): 预约日期，格式：YYYY-MM-DD，如 "2025-01-01"
        YYLX (str): 预约类型（"1.0":包场, "2.0":散场）
        XMDM (str): 项目代码，如 "001" 表示羽毛球
    
    Returns:
        list: 时间段列表，每个元素包含时间段信息，失败返回None
    """
    try:
        data = {
            'XQ': XQ,
            'YYRQ': YYRQ,
            'YYLX': YYLX,
            'XMDM': XMDM
        }
        ret = requests.post(
            "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/sportVenue/getTimeList.do",
            cookies=cookies,
            headers=headers,
            data=data
        )
        logger.info(f"获取时间列表成功: {ret.text}")
        ret = json.loads(ret.text)
        return ret
    except requests.exceptions.RequestException as e:
        logger.error(f"获取时间列表失败: {e}")
    except KeyError as e:
        logger.error(f"获取时间列表失败: {e}")
    return None


def getRoom(XMDM, YYRQ, YYLX, KSSJ, JSSJ, XQDM):
    """
    获取指定时间段的可用场地列表
    
    该接口是自动预约的核心接口，用于查询特定时间段内所有场地的状态。
    返回的场地列表中，disabled=False表示该场地可以预约。
    
    Args:
        XMDM (str): 项目代码，如 "001" 表示羽毛球
        YYRQ (str): 预约日期，格式：YYYY-MM-DD，如 "2025-01-01"
        YYLX (str): 预约类型（"1.0":包场, "2.0":散场）
        KSSJ (str): 开始时间，格式：HH:MM，如 "08:00"
        JSSJ (str): 结束时间，格式：HH:MM，如 "09:00"
        XQDM (str): 校区代码（"1":粤海, "2":丽湖）
    
    Returns:
        list: 场地列表，每个场地包含以下信息：
            - WID: 场地唯一标识（即CDWID）
            - CDMC: 场地名称
            - disabled: 是否不可预约（False表示可预约）
            失败返回None
    """
    try:
        data = {
            'XMDM': XMDM,
            'YYRQ': YYRQ,
            'YYLX': YYLX,
            'KSSJ': KSSJ,
            'JSSJ': JSSJ,
            'XQDM': XQDM,
        }
        ret = requests.post(
            "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/modules/sportVenue/getOpeningRoom.do",
            cookies=cookies,
            headers=headers,
            data=data
        )
        ret = json.loads(ret.text)
        ret = ret["datas"]["getOpeningRoom"]["rows"]
        logger.info(f"获取场地列表成功: {ret}")
        return ret
    except requests.exceptions.RequestException as e:
        logger.error(f"获取场地列表失败: {e}")
    except KeyError as e:
        logger.error(f"获取场地列表失败: {ret}")
    return None


def postBook(CGDM, CDWID, XMDM, XQWID, KYYSJD, YYRQ, YYLX):
    """
    提交场地预约请求
    
    这是预约系统的核心API，提交完整的预约信息到服务器。
    成功预约后，需要在规定时间内登录系统缴费，否则预约会被自动取消。
    
    Args:
        CGDM (str): 场馆代码，如 "001"
        CDWID (str): 场地唯一标识（十六进制字符串）
        XMDM (str): 项目代码，如 "001" 表示羽毛球
        XQWID (str): 校区唯一标识（"1":粤海, "2":丽湖）
        KYYSJD (str): 可预约时间段，格式：HH:MM-HH:MM，如 "20:00-21:00"
        YYRQ (str): 预约日期，格式：YYYY-MM-DD，如 "2025-01-01"
        YYLX (str): 预约类型（"1.0":包场, "2.0":散场）
    
    Returns:
        dict: 预约结果，通常包含成功/失败信息，失败返回None
            成功时返回：{"code": "success", "msg": "预约成功"}
            失败时返回：{"code": "error", "msg": "失败原因"}
    """
    try:
        # 构造预约请求数据
        data = {
            'DHID': '',              # 订单ID（新预约时为空）
            'CYRS': '',              # 参与人数（可选）
            'YYRGH': stuid,          # 预约人工号（学号）
            'YYRXM': stuname,        # 预约人姓名
            'CGDM': CGDM,            # 场馆代码
            'CDWID': CDWID,          # 场地唯一标识
            'XMDM': XMDM,            # 项目代码
            'XQWID': XQWID,          # 校区唯一标识
            'KYYSJD': KYYSJD,        # 可预约时间段
            'YYRQ': YYRQ,            # 预约日期
            'YYLX': YYLX,            # 预约类型
            'PC_OR_PHONE': 'pc',     # 预约来源（pc或phone）
        }
        # 将时间段拆分并构造完整的开始和结束时间
        # 例如：KYYSJD="20:00-21:00", YYRQ="2025-04-30"
        # 则：YYKS="2025-04-30 20:00", YYJS="2025-04-30 21:00"
        times = KYYSJD.split('-')
        data["YYKS"] = YYRQ + " " + times[0]  # 预约开始时间
        data["YYJS"] = YYRQ + " " + times[1]  # 预约结束时间
        '''
        data = {
        'DHID': '',
        'YYRGH': '2100271001',
        'CYRS': '',
        'YYRXM': '张三',
        'CGDM': '001',
        'CDWID': '0ea473755da04a588ebea78af2e8ef9b',
        'XMDM': '001',
        'XQWID': '1',
        'KYYSJD': '19:00-20:00',
        'YYRQ': '2025-04-28',
        'YYLX': '1.0',
        'YYKS': '2025-04-28 19:00',
        'YYJS': '2025-04-28 20:00',
        'PC_OR_PHONE': 'pc',
        }
        '''
        ret = requests.post(
            "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/sportVenue/insertVenueBookingInfo.do",
            cookies=cookies,
            headers=headers,
            data=data
        )
        logger.info(f"预约结果: {ret.text}")
        ret = json.loads(ret.text)
        return ret
    except requests.exceptions.RequestException as e:
        logger.error(f"预约失败: {e}")
    return None
