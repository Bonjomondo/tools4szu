import logging
import time
import copy  # 添加深拷贝支持
from apis import postBook, getRoom
from settings import courses, delay, counts

logger = logging.getLogger(__name__)
CDWIDs = []
datas = []  # 存储所有待预约的场地信息

if __name__ == '__main__':
    # 第一阶段：预处理courses，获取所有可预约的场地ID
    while len(courses):
        course = courses[0]
        # 如果用户没有指定场地ID（CDWID），则自动查询该时间段所有可用场地
        if course.get("CDWID", None) is None:
            # 调用API获取指定时间段的所有场地信息
            rooms = getRoom(**{
                "XMDM": course["XMDM"],      # 项目代码（如羽毛球）
                "YYRQ": course["YYRQ"],      # 预约日期
                "YYLX": course["YYLX"],      # 预约类型（包场/散场）
                "KSSJ": course["KYYSJD"].split("-")[0],  # 开始时间
                "JSSJ": course["KYYSJD"].split("-")[1],  # 结束时间
                "XQDM": course["XQWID"],     # 校区代码
            })
            time.sleep(0.2)  # 避免请求过快
            if rooms is None:
                continue
            flag = False
            # 遍历所有场地，找出可以预约的（disabled=False表示可预约）
            for room in rooms:
                if not room["disabled"]:  # disabled=False表示该场地可以预约
                    flag = True
                    # 深拷贝避免修改原始配置，为每个可用场地创建独立的预约记录
                    course_copy = copy.deepcopy(course)
                    course_copy["CDWID"] = room["WID"]  # 填充场地ID
                    datas.append(course_copy)  # 加入待预约队列
            if not flag:
                logger.error(f"没有可预约的场地: {course}")
                print(f"没有可预约的场地: {course}")
        else:
            # 如果用户已指定场地ID，直接加入待预约队列
            datas.append(copy.deepcopy(course))
        courses.pop(0)  # 处理完一个配置后移除
    
    # 第二阶段：循环预约，直到成功或达到最大轮次
    # counts控制总共尝试多少轮，每轮都会遍历所有待预约的场地
    for _ in range(counts):
        i = 0
        while i < len(datas):  # 遍历所有待预约的场地
            course = datas[i]
            try:
                logger.info(f"开始预约: {course}")
                ret = postBook(**course)
                if "成功" in ret:
                    logger.info(f"预约成功: {course}")
                    print(f"预约成功: {course}")
                    # 预约成功后，移除该时间段的所有场地，避免重复预约
                    # 同一个时间段只需要一个场地即可
                    datas = [
                        item for item in datas 
                        if item["KYYSJD"] != course["KYYSJD"] or item["YYRQ"] != course["YYRQ"]
                    ]
                    i = 0  # 重置索引，从头开始遍历新的列表
                    continue
                # 预约失败，等待指定时间后继续尝试
                time.sleep(delay / 1000)  # delay单位是毫秒，转换为秒
            except Exception as e:
                logger.error(f"预约失败: {e}")
            i += 1
