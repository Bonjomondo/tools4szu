#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @File    : settings.py
"""
体育场馆预约配置文件

本文件包含所有预约所需的配置参数：
1. cookies: 身份认证Cookie（必须）
2. stuid: 学号（必须）
3. stuname: 姓名（必须）
4. courses: 预约场次列表（必须）
5. counts: 预约轮次（可选，默认10）
6. delay: 请求延迟（可选，默认200ms）

配置说明：
- CGDM: 场馆代码
- CDWID: 场地ID（可选，不填则自动查询所有可用场地）
- XMDM: 项目代码（001:羽毛球, 002:篮球等）
- XQWID: 校区唯一标识（1:粤海, 2:丽湖）
- KYYSJD: 可预约时间段（格式：HH:MM-HH:MM）
- YYRQ: 预约日期（格式：YYYY-MM-DD）
- YYLX: 预约类型（1.0:包场, 2.0:散场）
"""

# 预约场次列表示例：
# courses=[{"CGDM":"001","CDWID":"6fbd613382ef48db9d2a2d214e47bae3","XMDM":"001","XQWID":"1","KYYSJD":"20:00-21:00","YYRQ":"2025-04-29","YYLX":"1.0"}]

# 预约总轮次：系统会尝试多少轮预约，每轮都会遍历所有场地
counts = 10

# 当前配置的预约场次（不指定CDWID会自动查询所有可用场地）
courses=[{"CGDM":"008","XMDM":"002","XQWID":"1","KYYSJD":"20:00-21:00","YYRQ":"2025-04-30","YYLX":"2.0"}]

# 每次预约请求之间的延迟时间（单位：毫秒）
# 建议不要设置过小，避免请求过于频繁被服务器限制
delay = 200

# 学号和姓名（必须与Cookie对应的账户一致）
stuid = 2025101011
stuname = "张xx"

# Cookie字符串（从浏览器F12开发者工具中获取）
# 登录深大统一身份认证后，在Network标签中找到任意请求，复制Cookie值
cookies = 'EMAP_LANG=zh; _WEU=172ad976'

# Cookie自动解析逻辑
# 支持字符串格式的Cookie，自动转换为字典格式供requests库使用
if isinstance(cookies, str):
    cookie_list = cookies.split(';')
    cookies = {}
    for item in cookie_list:
        item = item.strip()
        items = item.split('=')
        cookies[items[0]] = items[1]

# 验证Cookie格式
if not isinstance(cookies, dict):
    raise ValueError("invalid cookie!")

# HTTP请求头配置
# 模拟浏览器行为，确保请求能被服务器正确识别和处理
headers = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://ehall.szu.edu.cn',
    'Pragma': 'no-cache',
    'Referer': 'https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do?t_s=1745831680729',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}
