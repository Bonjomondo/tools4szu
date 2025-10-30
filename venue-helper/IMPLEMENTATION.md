# 深大体育场馆自动预约实现原理

## 概述

本文档详细说明了深大体育场馆自动预约系统的实现原理和工作流程。

## 系统架构

```
┌─────────────┐
│ settings.py │  配置文件：用户信息、Cookie、预约场次
└──────┬──────┘
       │
       ├──────────────┐
       │              │
       v              v
┌────────────┐  ┌─────────────┐
│ download.py│  │  main.py    │  主程序：自动预约逻辑
│ (可选)      │  └──────┬──────┘
└─────┬──────┘         │
      │                │
      v                v
┌──────────────────────────┐
│       apis.py            │  API接口层：与服务器交互
└──────────────────────────┘
      │
      v
┌──────────────────────────┐
│  深大体育场馆预约系统     │  https://ehall.szu.edu.cn
└──────────────────────────┘
```

## 核心实现原理

### 1. 认证机制

系统通过Cookie进行身份认证，不需要每次都输入用户名和密码：

- 用户首次登录深大统一身份认证系统
- 从浏览器开发者工具中获取Cookie
- 将Cookie配置到`settings.py`中
- 后续所有API请求都携带该Cookie进行认证

**关键代码** (`settings.py`):
```python
cookies = 'EMAP_LANG=zh; _WEU=172ad976'  # 从浏览器F12获取

# 自动将Cookie字符串转换为字典格式
if isinstance(cookies, str):
    cookie_list = cookies.split(';')
    cookies = {}
    for item in cookie_list:
        item = item.strip()
        items = item.split('=')
        cookies[items[0]] = items[1]
```

### 2. 预约配置

用户需要配置要预约的场地信息 (`settings.py`):

```python
courses = [{
    "CGDM": "008",        # 场馆代码
    "CDWID": "...",       # 场地ID（可选）
    "XMDM": "002",        # 项目代码（如羽毛球）
    "XQWID": "1",         # 校区ID（1:粤海, 2:丽湖）
    "KYYSJD": "20:00-21:00",  # 预约时间段
    "YYRQ": "2025-04-30",     # 预约日期
    "YYLX": "2.0"         # 预约类型（1.0:包场, 2.0:散场）
}]
```

### 3. 自动预约流程

#### 步骤1: 场地查询（如果未指定CDWID）

当用户没有指定具体场地ID时，系统会自动查询可用场地：

**关键代码** (`main.py`):
```python
if course.get("CDWID", None) is None:
    # 调用API获取指定时间段的所有可用场地
    rooms = getRoom(**{
        "XMDM": course["XMDM"],
        "YYRQ": course["YYRQ"],
        "YYLX": course["YYLX"],
        "KSSJ": course["KYYSJD"].split("-")[0],  # 开始时间
        "JSSJ": course["KYYSJD"].split("-")[1],  # 结束时间
        "XQDM": course["XQWID"],
    })
    
    # 遍历所有场地，找出可预约的（disabled=False）
    for room in rooms:
        if not room["disabled"]:
            course_copy = copy.deepcopy(course)
            course_copy["CDWID"] = room["WID"]
            datas.append(course_copy)  # 加入预约队列
```

**API实现** (`apis.py` - `getRoom`函数):
- 向服务器发送POST请求到`getOpeningRoom.do`接口
- 传递参数：项目代码、日期、时间段、校区等
- 返回该时间段所有场地的状态（是否可预约）

#### 步骤2: 循环预约

系统会进行多轮预约尝试，直到成功或达到最大轮次：

**关键代码** (`main.py`):
```python
for _ in range(counts):  # counts为预约总轮次（默认10次）
    i = 0
    while i < len(datas):  # 遍历所有待预约的场地
        course = datas[i]
        try:
            # 调用预约API
            ret = postBook(**course)
            
            # 如果预约成功
            if "成功" in ret:
                # 从待预约列表中移除该时间段的所有场地
                # 避免重复预约同一时间
                datas = [
                    item for item in datas 
                    if item["KYYSJD"] != course["KYYSJD"] 
                    or item["YYRQ"] != course["YYRQ"]
                ]
                i = 0  # 重新开始遍历
                continue
            
            # 失败则等待一段时间后继续尝试
            time.sleep(delay / 1000)
        except Exception as e:
            logger.error(f"预约失败: {e}")
        i += 1
```

#### 步骤3: 预约API调用

**关键代码** (`apis.py` - `postBook`函数):
```python
def postBook(CGDM, CDWID, XMDM, XQWID, KYYSJD, YYRQ, YYLX):
    data = {
        'DHID': '',
        'CYRS': '',          # 参与人数
        'YYRGH': stuid,      # 预约人工号（学号）
        'YYRXM': stuname,    # 预约人姓名
        'CGDM': CGDM,        # 场馆代码
        'CDWID': CDWID,      # 场地唯一标识
        'XMDM': XMDM,        # 项目代码
        'XQWID': XQWID,      # 校区唯一标识
        'KYYSJD': KYYSJD,    # 可预约时间段
        'YYRQ': YYRQ,        # 预约日期
        'YYLX': YYLX,        # 预约类型
        'PC_OR_PHONE': 'pc',
    }
    
    # 构造完整的开始和结束时间
    times = KYYSJD.split('-')
    data["YYKS"] = YYRQ + " " + times[0]  # 如：2025-04-30 20:00
    data["YYJS"] = YYRQ + " " + times[1]  # 如：2025-04-30 21:00
    
    # 发送预约请求
    ret = requests.post(
        "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/sportVenue/insertVenueBookingInfo.do",
        cookies=cookies,
        headers=headers,
        data=data
    )
    
    return json.loads(ret.text)
```

### 4. 辅助功能 - 数据下载

`download.py`提供了数据下载功能，帮助用户获取：

#### 获取场馆和项目信息

**关键代码** (`download.py` - `downloadSysConfig`):
```python
def downloadSysConfig():
    config = getSysConfig()  # 调用API获取系统配置
    
    # 提取包场场馆列表
    venues = []
    for v in config["packageVenueList"]:
        venues.append({
            "WID": v["WID"],
            "CGBM": v["CGBM"],
            "CGMC": v["CGMC"],
            "DCFS": "1.0",
        })
    
    # 提取散场场馆列表
    for v in config["dismissalVenueList"]:
        venues.append({
            "WID": v["WID"],
            "CGBM": v["CGBM"],
            "CGMC": v["CGMC"],
            "DCFS": "2.0",
        })
    
    # 保存为Excel文件
    pd.DataFrame(venues).to_excel("data/venues.xlsx", index=False)
    pd.DataFrame(activities).to_excel("data/activities.xlsx", index=False)
```

#### 获取可用场地列表

**关键代码** (`download.py` - `downloadRoom`):
```python
def downloadRoom(XMDM, YYRQ, YYLX, KSSJ, JSSJ, XQDM):
    ret = getRoom(XMDM, YYRQ, YYLX, KSSJ, JSSJ, XQDM)
    
    # 将场地信息保存为Excel文件
    pd.DataFrame(ret).to_excel("data/RoomList_xxx.xlsx", index=False)
```

## 关键技术点

### 1. 请求重试机制

系统采用循环重试策略：
- 外层循环：控制总预约轮次（`counts`参数）
- 内层循环：遍历所有待预约场地
- 失败后延迟一段时间（`delay`参数）再次尝试

### 2. 防止重复预约

一旦某个时间段预约成功，系统会自动移除该时间段的所有场地：
```python
datas = [
    item for item in datas 
    if item["KYYSJD"] != course["KYYSJD"] 
    or item["YYRQ"] != course["YYRQ"]
]
```

### 3. 日志记录

所有操作都会记录到`venue.log`文件：
- 预约尝试记录
- 成功/失败状态
- 错误信息
- API响应内容

### 4. 深拷贝机制

使用`copy.deepcopy()`避免修改原始配置：
```python
course_copy = copy.deepcopy(course)
course_copy["CDWID"] = room["WID"]
```

## API接口说明

### 1. getSysConfig
- **URL**: `https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/sportVenue/getSportVenueData.do`
- **功能**: 获取系统配置、场馆列表、项目列表
- **方法**: POST
- **返回**: 包含所有场馆和项目信息的JSON

### 2. getTimeList
- **URL**: `https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/sportVenue/getTimeList.do`
- **功能**: 获取指定日期的可预约时间段
- **方法**: POST
- **参数**: XQ（校区）、YYRQ（日期）、YYLX（类型）、XMDM（项目）

### 3. getRoom (getOpeningRoom)
- **URL**: `https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/modules/sportVenue/getOpeningRoom.do`
- **功能**: 获取指定时间段的可预约场地列表
- **方法**: POST
- **参数**: XMDM、YYRQ、YYLX、KSSJ、JSSJ、XQDM
- **返回**: 场地列表及其可预约状态

### 4. postBook (insertVenueBookingInfo)
- **URL**: `https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/sportVenue/insertVenueBookingInfo.do`
- **功能**: 提交预约请求
- **方法**: POST
- **参数**: 完整的预约信息（见上文）
- **返回**: 预约结果（成功/失败及原因）

## 使用流程

1. **获取Cookie**
   - 登录深大统一身份认证系统
   - 打开浏览器F12开发者工具
   - 找到Network标签，查看请求的Cookie
   - 复制完整Cookie字符串

2. **配置参数** (可选先运行download.py)
   - 运行`download.py`获取场馆和项目代码
   - 在`settings.py`中配置：
     - cookies（必须）
     - stuid、stuname（必须）
     - courses预约列表（必须）
     - delay、counts（可选，有默认值）

3. **运行预约**
   - 执行`python main.py`
   - 系统会自动循环预约
   - 查看控制台输出和`venue.log`日志

4. **缴费确认**
   - 登录ehall"体育场馆预约"
   - 在"我的预约"中查看预约记录
   - 完成缴费流程

## 注意事项

1. **Cookie有效期**: Cookie会过期，需要定期更新
2. **延迟设置**: `delay`不要设置过小，避免请求过于频繁被服务器限制
3. **预约时间**: 注意场馆的开放时间和预约规则
4. **网络环境**: 设置了`NO_PROXY`环境变量，确保直接访问ehall系统
5. **并发限制**: 当前实现是串行预约，避免并发请求导致问题

## 常见问题

### Q: 为什么预约失败？
A: 可能原因：
- Cookie过期需要更新
- 场地已被预约
- 不在预约时间范围内
- 账户余额不足
- 达到预约次数限制

### Q: 如何提高预约成功率？
A: 建议：
- 适当增加`counts`轮次
- 减小`delay`延迟（但不要太小）
- 配置多个备选场地（不指定CDWID）
- 在开放预约的准点时刻运行脚本

### Q: 可以同时预约多个时间段吗？
A: 可以，在courses列表中配置多个预约记录即可

## 扩展开发

如需扩展功能，可以考虑：
1. 添加定时任务功能（如使用cron或schedule库）
2. 添加微信/邮件通知功能
3. 添加图形界面
4. 优化并发预约逻辑
5. 添加智能重试策略（如指数退避）
