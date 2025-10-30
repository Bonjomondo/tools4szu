#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @File    : getData.py
"""
数据下载辅助模块

本模块提供数据下载功能，帮助用户获取配置所需的参数：
1. downloadSysConfig: 下载系统配置（场馆列表和项目列表）
2. downloadTimeList: 下载指定日期的可预约时间段
3. downloadRoom: 下载指定时间段的可用场地列表

使用流程：
1. 先在settings.py中配置好cookies
2. 运行本脚本获取所需参数
3. 根据下载的Excel文件配置courses
4. 运行main.py进行自动预约
"""
import os

import pandas as pd

from apis import getSysConfig, getTimeList, getRoom


def downloadSysConfig():
    """
    下载系统配置信息
    
    该函数会下载并保存以下信息到data目录：
    1. venues.xlsx: 所有场馆信息（包场和散场）
    2. activities.xlsx: 所有项目信息（羽毛球、篮球等）
    
    这些信息用于配置courses时查找对应的代码
    """
    config = getSysConfig()
    if config is None:
        print("获取系统配置失败")
        exit(1)
    
    # 提取包场场馆信息
    venues = []
    for v in config["packageVenueList"]:
        venues.append({
            "WID": v["WID"],
            "SSXQ": v["SSXQ"],
            "XM": v["XM"],
            "CGBM": v["CGBM"],
            "CGMC": v["CGMC"],
            "DCFS": "1.0",  # 包场方式
        })
    # 提取散场场馆信息
    for v in config["dismissalVenueList"]:
        venues.append({
            "WID": v["WID"],
            "SSXQ": v["SSXQ"],
            "XM": v["XM"],
            "CGBM": v["CGBM"],
            "CGMC": v["CGMC"],
            "DCFS": "2.0",  # 散场方式
        })
    # 提取项目信息
    activities = []
    for xm in config["xmList"]:
        activities.append({
            "XMDM": xm["XMDM"],
            "XMMC": xm["XMMC"],
            "DCFS": xm["DCFS"],
            "XQDM": xm["XQDM"],  # 校区代码
        })
    # 创建data目录（如果不存在）
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    # 保存为Excel文件，方便查看和使用
    pd.DataFrame(venues).to_excel(os.path.join(os.path.dirname(__file__), "data", "venues.xlsx"), index=False)
    pd.DataFrame(activities).to_excel(os.path.join(os.path.dirname(__file__), "data", "activities.xlsx"), index=False)
    print("获取数据成功")


def downloadTimeList(XQ, YYRQ, YYLX, XMDM):
    """
    下载可预约时间段列表
    
    Args:
        XQ (str): 校区代码（"1":粤海, "2":丽湖）
        YYRQ (str): 预约日期，格式：YYYY-MM-DD
        YYLX (str): 预约类型（"1.0":包场, "2.0":散场）
        XMDM (str): 项目代码，如 "001"
    
    功能：
        查询指定条件下所有可预约的时间段，保存为Excel文件
    """
    ret = getTimeList(XQ, YYRQ, YYLX, XMDM)
    if ret is None:
        print("获取时间列表失败")
        exit(1)
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    filename = "TimeList" + "_".join([YYRQ, YYLX, XMDM, XQ]) + ".xlsx"
    pd.DataFrame(ret).to_excel(os.path.join(os.path.dirname(__file__), "data", filename), index=False)


def downloadRoom(XMDM, YYRQ, YYLX, KSSJ, JSSJ, XQDM):
    """
    下载可用场地列表
    
    Args:
        XMDM (str): 项目代码，如 "001"
        YYRQ (str): 预约日期，格式：YYYY-MM-DD
        YYLX (str): 预约类型（"1.0":包场, "2.0":散场）
        KSSJ (str): 开始时间，格式：HH:MM
        JSSJ (str): 结束时间，格式：HH:MM
        XQDM (str): 校区代码（"1":粤海, "2":丽湖）
    
    功能：
        查询指定时间段的所有场地及其可预约状态，保存为Excel文件
        Excel中包含CDWID字段，可用于配置courses
    """
    ret = getRoom(XMDM, YYRQ, YYLX, KSSJ, JSSJ, XQDM)
    if ret is None:
        print("获取场地列表失败")
        exit(1)
    # 将WID字段重命名为CDWID，与配置格式保持一致
    for room in ret:
        room["CDWID"] = room["WID"]
        del room["WID"]
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    filename = "RoomList" + "_".join([YYRQ, YYLX, XMDM]) + ".xlsx"
    pd.DataFrame(ret).to_excel(os.path.join(os.path.dirname(__file__), "data", filename), index=False)


if __name__ == '__main__':
    # 下载系统配置：场馆列表和项目列表
    downloadSysConfig()
    
    # 下载指定时间段的场地列表（根据需要修改参数）
    # 参数说明：项目代码, 日期, 预约类型, 开始时间, 结束时间, 校区
    # 示例：查询2025-05-01粤海校区20:00-21:00的羽毛球包场场地
    # downloadTimeList("1", "2025-05-01", "1.0", "001")
    downloadRoom("001", "2025-05-01", "1.0", "20:00", "21:00", "1")
