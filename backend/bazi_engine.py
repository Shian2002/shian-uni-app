#!/usr/bin/env python3
"""八字排盘核心引擎 — 问真八字风格，纯Python本地计算

遵循规则：
  1. 立春分界年柱（非春节）
  2. 节令分界月柱（非农历初一）
  3. 夜子时不换日柱（23:00-00:00用当日干支）
  4. 大运顺逆：阳年男/阴年女→顺，阴年男/阳年女→逆
  5. 起运岁数：3天=1岁，1天=4个月，1时辰=10天

依赖: sxtwl (寿星天文历), ephem (天文计算), lunarcalendar (农历转换)
"""

import math
import os
import logging
from datetime import datetime, timedelta

# 加载 .env 环境变量（app.py 主进程已加载，此处为独立使用引擎时的降级）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 结构化日志
logger = logging.getLogger('xuancetai.engine')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# ═══════════════════════════════════════════════════════════════
# 常量定义
# ═══════════════════════════════════════════════════════════════

# WZ API 超时时间（秒），可通过环境变量 WZ_API_TIMEOUT 调整
WZ_API_TIMEOUT = int(os.environ.get('WZ_API_TIMEOUT', '10'))

# WZ API 缓存设置
_WZ_CACHE = {}  # 内存缓存: key=(year,month,day,hour,minute,gender) → (data, timestamp)
_WZ_CACHE_TTL = int(os.environ.get('WZ_CACHE_TTL', '86400'))  # 默认24小时(秒)

# WZ API 健康检查
_WZ_HEALTH = {'available': True, 'last_check': 0, 'fail_count': 0}
_WZ_HEALTH_CHECK_INTERVAL = int(os.environ.get('WZ_HEALTH_INTERVAL', '300'))  # 默认5分钟检查一次
_WZ_HEALTH_FAIL_THRESHOLD = int(os.environ.get('WZ_HEALTH_FAIL_THRESHOLD', '3'))  # 连续失败次数阈值

TIAN_GAN = list('甲乙丙丁戊己庚辛壬癸')
DI_ZHI = list('子丑寅卯辰巳午未申酉戌亥')

# 五行映射
GAN_WUXING = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
ZHI_WUXING = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}

# 阴阳
GAN_YINYANG = {'甲':'阳','乙':'阴','丙':'阳','丁':'阴','戊':'阳','己':'阴','庚':'阳','辛':'阴','壬':'阳','癸':'阴'}
ZHI_YINYANG = {'子':'阳','丑':'阴','寅':'阳','卯':'阴','辰':'阳','巳':'阴','午':'阳','未':'阴','申':'阳','酉':'阴','戌':'阳','亥':'阴'}

# 十二时辰对应小时
ZHI_HOUR = {'子':(23,1),'丑':(1,3),'寅':(3,5),'卯':(5,7),'辰':(7,9),'巳':(9,11),
            '午':(11,13),'未':(13,15),'申':(15,17),'酉':(17,19),'戌':(19,21),'亥':(21,23)}

# 藏干表
CANG_GAN = {
    '子':['癸'], '丑':['己','癸','辛'], '寅':['甲','丙','戊'], '卯':['乙'],
    '辰':['戊','乙','癸'], '巳':['丙','庚','戊'], '午':['丁','己'], '未':['己','丁','乙'],
    '申':['庚','壬','戊'], '酉':['辛'], '戌':['戊','辛','丁'], '亥':['壬','甲']
}

# 六十甲子纳音表
NAYIN = [
    '海中金','海中金','炉中火','炉中火','大林木','大林木',     # 0-5
    '路旁土','路旁土','剑锋金','剑锋金','山头火','山头火',     # 6-11
    '涧下水','涧下水','城头土','城头土','白蜡金','白蜡金',     # 12-17
    '杨柳木','杨柳木','泉中水','泉中水','屋上土','屋上土',     # 18-23
    '霹雳火','霹雳火','松柏木','松柏木','长流水','长流水',     # 24-29
    '沙中金','沙中金','山下火','山下火','平地木','平地木',     # 30-35
    '壁上土','壁上土','金箔金','金箔金','覆灯火','覆灯火',     # 36-41
    '天河水','天河水','大驿土','大驿土','钗钏金','钗钏金',     # 42-47
    '桑柘木','桑柘木','大溪水','大溪水','沙中土','沙中土',     # 48-53
    '天上火','天上火','石榴木','石榴木','大海水','大海水',     # 54-59
]

# 五虎遁年起月诀：年干→寅月天干起始
# 甲己→丙寅, 乙庚→戊寅, 丙辛→庚寅, 丁壬→壬寅, 戊癸→甲寅
WU_HU_DUN = {0:2, 1:4, 2:6, 3:8, 4:0, 5:2, 6:4, 7:6, 8:8, 9:0}  # 天干序号→寅月天干序号

# 五鼠遁日起时诀：日干→子时天干起始
# 甲己→甲子, 乙庚→丙子, 丙辛→戊子, 丁壬→庚子, 戊癸→壬子
WU_SHU_DUN = {0:0, 1:2, 2:4, 3:6, 4:8, 5:0, 6:2, 7:4, 8:6, 9:8}  # 天干序号→子时天干序号

# 十二节令（用于月柱分界，注意是"节"不是"气"）
JIE_ORDER = ['立春','惊蛰','清明','立夏','芒种','小暑',
             '立秋','白露','寒露','立冬','大雪','小寒']

# 节令对应月支
JIE_ZHI = {'立春':'寅','惊蛰':'卯','清明':'辰','立夏':'巳','芒种':'午',
           '小暑':'未','立秋':'申','白露':'酉','寒露':'戌','立冬':'亥',
           '大雪':'子','小寒':'丑'}

# 月支顺序（从寅开始）
MONTH_ZHI = ['寅','卯','辰','巳','午','未','申','酉','戌','亥','子','丑']

# 空亡表：旬首→空亡地支
XUN_KONG = {'甲子':'戌亥','甲戌':'申酉','甲申':'午未','甲午':'辰巳','甲辰':'寅卯','甲寅':'子丑'}

# 十神关系
# 以日干为中心：同我=比劫, 我生=食伤, 生我=印, 我克=财, 克我=官杀
# 阴阳相同=偏, 阴阳不同=正
SHI_SHEN_MAP = {
    ('木','木','同'): '比肩', ('木','木','异'): '劫财',
    ('木','火','同'): '食神', ('木','火','异'): '伤官',
    ('木','土','同'): '偏财', ('木','土','异'): '正财',
    ('木','金','同'): '偏官', ('木','金','异'): '正官',  # 七杀=偏官
    ('木','水','同'): '偏印', ('木','水','异'): '正印',
    ('火','火','同'): '比肩', ('火','火','异'): '劫财',
    ('火','土','同'): '食神', ('火','土','异'): '伤官',
    ('火','金','同'): '偏财', ('火','金','异'): '正财',
    ('火','水','同'): '偏官', ('火','水','异'): '正官',
    ('火','木','同'): '偏印', ('火','木','异'): '正印',
    ('土','土','同'): '比肩', ('土','土','异'): '劫财',
    ('土','金','同'): '食神', ('土','金','异'): '伤官',
    ('土','水','同'): '偏财', ('土','水','异'): '正财',
    ('土','木','同'): '偏官', ('土','木','异'): '正官',
    ('土','火','同'): '偏印', ('土','火','异'): '正印',
    ('金','金','同'): '比肩', ('金','金','异'): '劫财',
    ('金','水','同'): '食神', ('金','水','异'): '伤官',
    ('金','木','同'): '偏财', ('金','木','异'): '正财',
    ('金','火','同'): '偏官', ('金','火','异'): '正官',
    ('金','土','同'): '偏印', ('金','土','异'): '正印',
    ('水','水','同'): '比肩', ('水','水','异'): '劫财',
    ('水','木','同'): '食神', ('水','木','异'): '伤官',
    ('水','火','同'): '偏财', ('水','火','异'): '正财',
    ('水','土','同'): '偏官', ('水','土','异'): '正官',
    ('水','金','同'): '偏印', ('水','金','异'): '正印',
}

# 神煞规则
# 天乙贵人
TIAN_YI_GUI_REN = {
    '甲': ['丑','未'], '乙': ['子','申'], '丙': ['亥','酉'],
    '丁': ['亥','酉'], '戊': ['丑','未'], '己': ['子','申'],
    '庚': ['丑','未'], '辛': ['寅','午'], '壬': ['卯','巳'],
    '癸': ['卯','巳']
}

# 驿马（日支定）
YIMA = {
    '申':'寅','子':'寅','辰':'寅',    # 申子辰→寅
    '寅':'申','午':'申','戌':'申',     # 寅午戌→申
    '巳':'亥','酉':'亥','丑':'亥',     # 巳酉丑→亥
    '亥':'巳','卯':'巳','未':'巳'      # 亥卯未→巳
}

# 桃花（日支定）
TAOHUA = {
    '申':'酉','子':'酉','辰':'酉',     # 申子辰→酉
    '寅':'卯','午':'卯','戌':'卯',     # 寅午戌→卯
    '巳':'午','酉':'午','丑':'午',     # 巳酉丑→午
    '亥':'子','卯':'子','未':'子'       # 亥卯未→子
}

# 将星（日支定）
JIANG_XING = {
    '申':'子','子':'子','辰':'子',
    '寅':'午','午':'午','戌':'午',
    '巳':'酉','酉':'酉','丑':'酉',
    '亥':'卯','卯':'卯','未':'卯'
}

# 华盖（日支定）
HUA_GAI = {
    '申':'辰','子':'辰','辰':'辰',
    '寅':'戌','午':'戌','戌':'戌',
    '巳':'丑','酉':'丑','丑':'丑',
    '亥':'未','卯':'未','未':'未'
}

# 文昌
WEN_CHANG = {
    '甲':'巳','乙':'午','丙':'申','丁':'酉','戊':'申',
    '己':'酉','庚':'亥','辛':'子','壬':'寅','癸':'卯'
}

# 羊刃
YANG_REN = {
    '甲':'卯','乙':'辰','丙':'午','丁':'未','戊':'午',
    '己':'未','庚':'酉','辛':'戌','壬':'子','癸':'丑'
}

# 禄神
LU_SHEN = {
    '甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳',
    '己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'
}

# 太极贵人
TAI_JI = {'甲':['子','午'], '乙':['子','午'], '丙':['卯','酉'],
           '丁':['卯','酉'], '戊':['辰','戌','丑','未'], '己':['辰','戌','丑','未'],
           '庚':['寅','亥'], '辛':['寅','亥'], '壬':['巳','申'], '癸':['巳','申']}

# 天德贵人
TIAN_DE = {1:'丁',2:'申',3:'壬',4:'辛',5:'亥',6:'甲',
            7:'癸',8:'寅',9:'丙',10:'乙',11:'巳',12:'庚'}

# 月德贵人
YUE_DE = {1:'丙',2:'甲',3:'壬',4:'庚',5:'丙',6:'甲',
           7:'壬',8:'庚',9:'丙',10:'甲',11:'壬',12:'庚'}

# 孤辰寡宿（日支定）
GU_CHEN = {'子':'寅','丑':'寅','寅':'巳','卯':'巳','辰':'巳','巳':'申',
           '午':'申','未':'申','申':'亥','酉':'亥','戌':'亥','亥':'寅'}
GUA_SU = {'子':'戌','丑':'戌','寅':'丑','卯':'丑','辰':'丑','巳':'辰',
          '午':'辰','未':'辰','申':'未','酉':'未','戌':'未','亥':'戌'}

# 亡神（日支定）
WANG_SHEN = {'申':'亥','子':'亥','辰':'亥',
             '寅':'巳','午':'巳','戌':'巳',
             '巳':'寅','酉':'寅','丑':'寅',
             '亥':'申','卯':'申','未':'申'}

# 劫煞（日支定）
JIE_SHA = {'申':'巳','子':'巳','辰':'巳',
           '寅':'亥','午':'亥','戌':'亥',
           '巳':'申','酉':'申','丑':'申',
           '亥':'寅','卯':'寅','未':'寅'}

# 天罗地网（纳音定，仅男看天罗女看地网）
TIAN_LUO = ['戌','亥']  # 纳音火命男忌
DI_WANG = ['辰','巳']    # 纳音水/土命女忌

# 学堂
XUE_TANG = {
    '木':'亥','火':'寅','土':'寅','金':'巳','水':'申'
}

# 红艳煞
HONG_YAN = {'甲':'午','乙':'申','丙':'寅','丁':'未','戊':'辰','己':'辰','庚':'戌','辛':'酉','壬':'子','癸':'申'}

# 福星贵人
FU_XING = {'甲':'寅','乙':'丑','丙':'子','丁':'酉','戊':'未','己':'未','庚':'午','辛':'巳','壬':'辰','癸':'卯'}

# 金舆
JIN_YU = {
    '甲':'辰','乙':'巳','丙':'未','丁':'申','戊':'未',
    '己':'申','庚':'戌','辛':'亥','壬':'丑','癸':'寅'
}

# ── 以下为问真八字缺失神煞补全 ──

# 十灵日（日柱查）：甲辰、乙亥、丙辰、丁酉、戊午、庚寅、辛亥、壬寅、癸未
SHI_LING_RI = ['甲辰','乙亥','丙辰','丁酉','戊午','庚寅','辛亥','壬寅','癸未']

# 孤鸾煞（日柱查）：甲寅、乙巳、丙午、丁巳、戊申、辛亥、壬子、癸亥
GU_LUAN_SHA = ['甲寅','乙巳','丙午','丁巳','戊申','辛亥','壬子','癸亥']

# 月德合（月令查天干）：月德之合干
# 月德：丙/甲/壬/庚 → 合干：辛/己/丁/乙
YUE_DE_HE = {1:'辛',2:'己',3:'丁',4:'乙',5:'辛',6:'己',
             7:'丁',8:'乙',9:'辛',10:'己',11:'丁',12:'乙'}

# 德秀贵人（三合局查法：以月令地支查德和秀的天干）
# 口诀：寅午戌月丙戊期，申子辰月壬甲奇，巳酉丑月庚丁至，亥卯未月甲丁随
# 德=三合局五行之禄干，秀=三合局五行之秀气干(食神/官星/伤官)
DE_XIU_MAP = {
    '寅': ('丙', '戊'), '午': ('丙', '戊'), '戌': ('丙', '戊'),
    '巳': ('庚', '丁'), '酉': ('庚', '丁'), '丑': ('庚', '丁'),
    '申': ('壬', '甲'), '子': ('壬', '甲'), '辰': ('壬', '甲'),
    '亥': ('甲', '丁'), '卯': ('甲', '丁'), '未': ('甲', '丁'),
}

# 灾煞（年支查，与将星对冲的前一位）
# 申子辰→午, 寅午戌→子, 巳酉丑→卯, 亥卯未→酉
ZAI_SHA = {'申':'午','子':'午','辰':'午',
           '寅':'子','午':'子','戌':'子',
           '巳':'卯','酉':'卯','丑':'卯',
           '亥':'酉','卯':'酉','未':'酉'}

# 丧门（年支前两位）
SANG_MEN = {'子':'寅','丑':'卯','寅':'辰','卯':'巳','辰':'午','巳':'未',
            '午':'申','未':'酉','申':'戌','酉':'亥','戌':'子','亥':'丑'}

# 勾绞煞（年支查）：勾=年支前三位，绞=年支后三位
GOU_JIAO = {}
for _i, _zhi in enumerate(DI_ZHI):
    _gou = DI_ZHI[(_i + 3) % 12]
    _jiao = DI_ZHI[(_i - 3) % 12]
    GOU_JIAO[_zhi] = {'勾': _gou, '绞': _jiao}

# 红鸾（年支查，与丧门对冲）
# 子→卯, 丑→寅, 寅→丑, 卯→子, 辰→亥, 巳→戌, 午→酉, 未→申, 申→未, 酉→午, 戌→巳, 亥→辰
HONG_LUAN = {'子':'卯','丑':'寅','寅':'丑','卯':'子','辰':'亥','巳':'戌',
             '午':'酉','未':'申','申':'未','酉':'午','戌':'巳','亥':'辰'}

# 天医（月支查，月支前一位为天医位，四柱地支见之为天医入命）
# 子→亥, 丑→子, 寅→丑, 卯→寅, 辰→卯, 巳→辰, 午→巳, 未→午, 申→未, 酉→申, 戌→酉, 亥→戌
TIAN_YI_YI = {'子':'亥','丑':'子','寅':'丑','卯':'寅','辰':'卯','巳':'辰',
              '午':'巳','未':'午','申':'未','酉':'申','戌':'酉','亥':'戌'}

# 天喜（年支查，与红鸾对冲位）
# 子→酉, 丑→申, 寅→未, 卯→午, 辰→巳, 巳→辰, 午→卯, 未→寅, 申→丑, 酉→子, 戌→亥, 亥→戌
TIAN_XI = {'子':'酉','丑':'申','寅':'未','卯':'午','辰':'巳','巳':'辰',
           '午':'卯','未':'寅','申':'丑','酉':'子','戌':'亥','亥':'戌'}

# 天罗地网（纳音五行+性别查）
# 男忌天罗(戌亥)，女忌地网(辰巳)
# 判断标准：四柱地支中有对应地支且纳音为对应五行
# 简化判定：男命日支或年支在戌亥→天罗，女命日支或年支在辰巳→地网
# 更精确：纳音火命男忌戌亥，纳音水/土命女忌辰巳

# 城市经度表
CITY_LNG = {
    # 直辖市
    '北京': 116.4, '上海': 121.5, '天津': 117.2, '重庆': 106.5,
    # 省会
    '广州': 113.3, '深圳': 114.1, '杭州': 120.2, '南京': 118.8,
    '武汉': 114.3, '成都': 104.1, '西安': 108.9, '长沙': 113.0,
    '郑州': 113.7, '济南': 117.0, '沈阳': 123.4, '哈尔滨': 126.6,
    '长春': 125.3, '昆明': 102.7, '贵阳': 106.7, '南宁': 108.3,
    '福州': 119.3, '合肥': 117.3, '南昌': 115.9, '太原': 112.5,
    '石家庄': 114.5, '兰州': 103.8, '西宁': 101.8, '银川': 106.3,
    '呼和浩特': 111.7, '乌鲁木齐': 87.6, '拉萨': 91.1, '海口': 110.3,
    # 常见城市
    '苏州': 120.6, '无锡': 120.3, '宁波': 121.6, '温州': 120.7,
    '东莞': 113.7, '佛山': 113.1, '珠海': 113.6, '厦门': 118.1,
    '青岛': 120.4, '大连': 121.6, '烟台': 121.4, '泉州': 118.6,
    '常州': 119.9, '徐州': 117.2, '绍兴': 120.6, '嘉兴': 120.7,
    '金华': 119.6, '台州': 121.4, '中山': 113.4, '惠州': 114.4,
    '汕头': 116.7, '湛江': 110.4, '桂林': 110.3, '三亚': 109.5,
    '洛阳': 112.4, '潍坊': 119.1, '保定': 115.5, '唐山': 118.2,
    '邯郸': 114.5, '秦皇岛': 119.6, '包头': 109.8, '大庆': 125.1,
    '齐齐哈尔': 123.9, '吉林': 126.5, '鞍山': 123.0, '抚顺': 123.9,
    '宜昌': 111.3, '襄阳': 112.1, '岳阳': 113.1, '常德': 111.7,
    '绵阳': 104.7, '宜宾': 104.6, '遵义': 106.9, '曲靖': 103.8,
    '大理': 100.2, '丽江': 100.2, '咸阳': 108.7, '宝鸡': 107.1,
    '天水': 105.7, '兰州': 103.8, '西宁': 101.8,
    # 省份模糊匹配
    '广东': 113.3, '浙江': 120.2, '江苏': 118.8, '山东': 117.0,
    '河南': 113.7, '河北': 114.5, '湖南': 113.0, '湖北': 114.3,
    '四川': 104.1, '福建': 119.3, '安徽': 117.3, '江西': 115.9,
    '陕西': 108.9, '山西': 112.5, '辽宁': 123.4, '吉林': 125.3,
    '黑龙江': 126.6, '云南': 102.7, '贵州': 106.7, '广西': 108.3,
    '甘肃': 103.8, '海南': 110.3, '内蒙古': 111.7, '新疆': 87.6,
    '西藏': 91.1, '青海': 101.8, '宁夏': 106.3,
}


# ═══════════════════════════════════════════════════════════════
# 时间校准
# ═══════════════════════════════════════════════════════════════

# 经度查询缓存: addr → (longitude, timestamp)
_LNG_CACHE = {}
_LNG_CACHE_TTL = 86400 * 7  # 7天缓存


def _fetch_longitude_from_api(addr):
    """通过高德地图API获取经度

    高德Web服务API地理编码接口（免费额度5000次/天）
    需要环境变量 AMAP_API_KEY，未设置则跳过API调用

    Returns:
        float 经度，或 None（API不可用时）
    """
    amap_key = os.environ.get('AMAP_API_KEY', '')
    if not amap_key:
        return None

    try:
        import json as _json
        import urllib.request
        import urllib.parse
        import time as _time

        url = f"https://restapi.amap.com/v3/geocode/geo?key={amap_key}&address={urllib.parse.quote(addr)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = _json.loads(resp.read().decode('utf-8'))

        if data.get('status') == '1' and data.get('geocodes'):
            location = data['geocodes'][0].get('location', '')
            if location and ',' in location:
                lng = float(location.split(',')[0])
                return lng
    except Exception as e:
        logger.error(f"高德API经度查询失败: {e}")

    return None


def get_longitude(addr):
    """从地址获取经度

    查询优先级：
    1. 内存缓存（7天有效期）
    2. 内置城市经度表（模糊匹配）
    3. 高德地图API（需设置 AMAP_API_KEY 环境变量）
    4. 默认东经120°（北京时间标准经度）

    Args:
        addr: 地址字符串，如 '北京'、'四川省成都市'

    Returns:
        float 经度
    """
    if not addr:
        return 120.0

    import time as _time

    # 1. 检查内存缓存
    if addr in _LNG_CACHE:
        cached_lng, cached_ts = _LNG_CACHE[addr]
        if _time.time() - cached_ts < _LNG_CACHE_TTL:
            return cached_lng

    # 2. 内置城市经度表（模糊匹配）
    for city, lng in CITY_LNG.items():
        if city in addr:
            _LNG_CACHE[addr] = (lng, _time.time())
            return lng

    # 3. 高德地图API
    api_lng = _fetch_longitude_from_api(addr)
    if api_lng is not None:
        _LNG_CACHE[addr] = (api_lng, _time.time())
        return api_lng

    # 4. 默认东经120°
    _LNG_CACHE[addr] = (120.0, _time.time())
    return 120.0


def true_solar_time(dt, longitude=120.0):
    """计算真太阳时

    Args:
        dt: datetime (北京时间)
        longitude: 当地经度（东经正数）
    Returns:
        datetime (真太阳时)
    """
    # 经度修正：每度4分钟
    lng_offset_min = (longitude - 120.0) * 4.0

    # 均时差（Equation of Time）近似公式
    day_of_year = dt.timetuple().tm_yday
    b = 2.0 * math.pi / 365.0 * (day_of_year - 81)
    eot_min = 9.87 * math.sin(2*b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)

    total_offset_min = lng_offset_min + eot_min
    return dt + timedelta(minutes=total_offset_min)


# ═══════════════════════════════════════════════════════════════
# 节气计算（用于年柱立春分界 + 月柱节令分界）
# ═══════════════════════════════════════════════════════════════

def _get_jieqi_times(year):
    """获取指定年份所有节气的精确时刻（使用ephem）

    使用逐日→逐小时→逐分钟三级搜索，确保所有节气都能正确计算。

    Returns: dict {节气名: datetime}
    """
    import ephem

    # 24节气太阳黄经角度
    jieqi_angles = [
        ('小寒',285),('大寒',300),('立春',315),('雨水',330),('惊蛰',345),('春分',0),
        ('清明',15),('谷雨',30),('立夏',45),('小满',60),('芒种',75),('夏至',90),
        ('小暑',105),('大暑',120),('立秋',135),('处暑',150),('白露',165),('秋分',180),
        ('寒露',195),('霜降',210),('立冬',225),('小雪',240),('大雪',255),('冬至',270),
    ]

    result = {}

    for name, target_lon in jieqi_angles:
        try:
            precise_dt = _find_jieqi_precise(year, name, target_lon)
            if precise_dt:
                result[name] = precise_dt
        except Exception as e:
            logger.error(f"节气计算异常({name} {year}): {e}")

    return result


def _get_solar_lon(dt_float):
    """获取指定时刻的太阳黄经（度）"""
    import ephem
    sun = ephem.Sun(dt_float)
    eq = ephem.Equatorial(sun.ra, sun.dec, epoch=dt_float)
    ec = ephem.Ecliptic(eq)
    lon = float(ec.lon) * 180 / math.pi
    if lon < 0:
        lon += 360
    return lon


def _find_jieqi_precise(year, name, target_lon):
    """精确搜索指定节气时刻

    三级搜索：逐日→逐小时→逐分钟
    """
    import ephem

    # 节气近似日期：每月的5-8日左右
    approx_month = _jieqi_approx_month(name)
    # 从上月20日开始搜索，覆盖节气可能的所有日期范围
    search_start = datetime(year, approx_month, 1) - timedelta(days=12)

    # 第一级：逐日搜索，找到黄经跨越target_lon的那一天
    found_day = None
    test_date = search_start
    for _ in range(50):  # 搜索50天足够
        try:
            # 比较当天0时和24时(次日0时)的太阳黄经
            dt_start = ephem.Date(f'{test_date.year}/{test_date.month}/{test_date.day} 0:00:00')
            lon_start = _get_solar_lon(dt_start)

            next_date = test_date + timedelta(days=1)
            dt_end = ephem.Date(f'{next_date.year}/{next_date.month}/{next_date.day} 0:00:00')
            lon_end = _get_solar_lon(dt_end)

            # 判断在这一天内是否跨越了target角度
            if _angle_before(lon_start, target_lon) and not _angle_before(lon_end, target_lon):
                found_day = test_date
                break
        except:
            pass
        test_date += timedelta(days=1)

    if found_day is None:
        # 扩大搜索：从更早开始
        test_date = datetime(year, approx_month, 1) - timedelta(days=20)
        for _ in range(60):
            try:
                dt_start = ephem.Date(f'{test_date.year}/{test_date.month}/{test_date.day} 0:00:00')
                lon_start = _get_solar_lon(dt_start)
                next_date = test_date + timedelta(days=1)
                dt_end = ephem.Date(f'{next_date.year}/{next_date.month}/{next_date.day} 0:00:00')
                lon_end = _get_solar_lon(dt_end)
                if _angle_before(lon_start, target_lon) and not _angle_before(lon_end, target_lon):
                    found_day = test_date
                    break
            except:
                pass
            test_date += timedelta(days=1)

    if found_day is None:
        return None

    # 第二级：逐小时搜索（搜索 found_day 当天 + 次日前6小时）
    found_hour = None
    found_hour_day = None
    search_days = [found_day, found_day + timedelta(days=1)]
    for search_day in search_days:
        max_h = 24 if search_day == found_day else 6  # 次日只搜前6小时
        for h in range(max_h):
            try:
                dt_h = ephem.Date(f'{search_day.year}/{search_day.month}/{search_day.day} {h}:00:00')
                lon_h = _get_solar_lon(dt_h)
                # 下一个小时
                h_next = h + 1
                day_next = search_day
                if h_next >= 24:
                    h_next = 0
                    day_next = search_day + timedelta(days=1)
                dt_h_next = ephem.Date(f'{day_next.year}/{day_next.month}/{day_next.day} {h_next}:00:00')
                lon_h_next = _get_solar_lon(dt_h_next)

                if _angle_before(lon_h, target_lon) and not _angle_before(lon_h_next, target_lon):
                    found_hour = h
                    found_hour_day = search_day
                    break
            except:
                continue
        if found_hour is not None:
            break

    if found_hour is None:
        # 降级：返回当天正午（UTC+8）
        from datetime import timedelta as _td
        return datetime(found_day.year, found_day.month, found_day.day, 12, 0) + _td(hours=8)

    # 第三级：逐分钟搜索
    found_minute = 0
    hour_start_dt = datetime(found_hour_day.year, found_hour_day.month, found_hour_day.day, found_hour, 0)
    for m in range(60):
        try:
            dt_m = hour_start_dt + timedelta(minutes=m)
            dt_m_ephem = ephem.Date(dt_m)
            lon_m = _get_solar_lon(dt_m_ephem)
            if not _angle_before(lon_m, target_lon):
                found_minute = m
                break
        except:
            continue

    # ephem使用UTC时间计算，需转换为北京时间(UTC+8)
    utc_dt = datetime(found_hour_day.year, found_hour_day.month, found_hour_day.day, found_hour, found_minute)
    from datetime import timedelta as _td
    bj_dt = utc_dt + _td(hours=8)
    return bj_dt


def _angle_before(lon, target):
    """判断太阳黄经lon是否在target之前（未到达target）

    处理0°/360°跨越的情况
    """
    if target == 0:
        # 春分特殊：0°即360°，lon < 360且lon > 0时算"在0°之前"（即还未到达春分）
        return lon > 180  # lon > 180° 说明还在春分之前
    else:
        return lon < target


def _lon_crossed(lon, target, step):
    """判断在一步（step度）范围内是否跨越了target角度"""
    if target == 0:
        return lon > 355 or lon < 5
    return abs(lon - target) < step + 0.5


def _jieqi_approx_month(name):
    """节气近似月份"""
    month_map = {
        '小寒':1,'大寒':1,'立春':2,'雨水':2,'惊蛰':3,'春分':3,
        '清明':4,'谷雨':4,'立夏':5,'小满':5,'芒种':6,'夏至':6,
        '小暑':7,'大暑':7,'立秋':8,'处暑':8,'白露':9,'秋分':9,
        '寒露':10,'霜降':10,'立冬':11,'小雪':11,'大雪':12,'冬至':12,
    }
    return month_map.get(name, 1)


def get_jieqi_times(year):
    """获取指定年份的节气时刻（带缓存）"""
    if not hasattr(get_jieqi_times, '_cache'):
        get_jieqi_times._cache = {}
    if year not in get_jieqi_times._cache:
        try:
            get_jieqi_times._cache[year] = _get_jieqi_times(year)
        except Exception as e:
            logger.error(f"节气计算异常({year}): {e}")
            get_jieqi_times._cache[year] = {}
    return get_jieqi_times._cache[year]


# ── Swiss Ephemeris 精确 Julian Day 节气计算 ──

def _swisseph_jieqi_jd(year, target_lon_deg):
    """使用 Swiss Ephemeris 二分搜索节令的 Julian Day（UTC）

    精度优于 0.001 秒，远超 ephem 逐分钟搜索。

    Args:
        year: 搜索年份
        target_lon_deg: 太阳黄经目标角度（如小寒=285）
    Returns:
        float: Julian Day number (UTC)，若失败返回 None
    """
    try:
        import swisseph as swe
    except ImportError:
        return None

    # 节气近似月份
    month_approx = {
        285:1, 300:1, 315:2, 330:2, 345:3, 0:3,
        15:4, 30:4, 45:5, 60:5, 75:6, 90:6,
        105:7, 120:7, 135:8, 150:8, 165:9, 180:9,
        195:10, 210:10, 225:11, 240:11, 255:12, 270:12,
    }

    month = month_approx.get(target_lon_deg, 1)
    # 搜索范围：近似月份前20天到后30天
    start_jd = swe.julday(year, month, 1, 0.0) - 20
    end_jd = start_jd + 50

    def get_sun_lon(jd):
        result = swe.calc_ut(jd, swe.SUN)
        return result[0][0] % 360

    # 二分搜索：找太阳黄经首次达到 >= target_lon_deg 的时刻
    lo, hi = start_jd, end_jd
    for _ in range(60):  # 60次迭代 → 精度 < 0.001秒
        mid = (lo + hi) / 2.0
        lon_mid = get_sun_lon(mid)
        if target_lon_deg == 0:
            # 春分特殊：0°即360°
            if lon_mid > 180:
                lo = mid
            else:
                hi = mid
        else:
            if lon_mid < target_lon_deg:
                lo = mid
            else:
                hi = mid

    return (lo + hi) / 2.0


# 24节气名称 → 太阳黄经角度映射
_JIEQI_LON_MAP = {
    '小寒':285,'大寒':300,'立春':315,'雨水':330,'惊蛰':345,'春分':0,
    '清明':15,'谷雨':30,'立夏':45,'小满':60,'芒种':75,'夏至':90,
    '小暑':105,'大暑':120,'立秋':135,'处暑':150,'白露':165,'秋分':180,
    '寒露':195,'霜降':210,'立冬':225,'小雪':240,'大雪':255,'冬至':270,
}


def get_jieqi_jd(year, jieqi_name):
    """获取指定年份指定节气的 Julian Day（UTC），带缓存

    使用 Swiss Ephemeris 高精度计算。如 swisseph 不可用则返回 None。

    Args:
        year: 年份
        jieqi_name: 节气名称（如'小寒'、'立春'等）
    Returns:
        float: Julian Day number (UTC)，失败返回 None
    """
    if not hasattr(get_jieqi_jd, '_cache'):
        get_jieqi_jd._cache = {}
    key = (year, jieqi_name)
    if key not in get_jieqi_jd._cache:
        lon = _JIEQI_LON_MAP.get(jieqi_name)
        if lon is None:
            return None
        jd = _swisseph_jieqi_jd(year, lon)
        get_jieqi_jd._cache[key] = jd
    return get_jieqi_jd._cache[key]


def get_all_jieqi_jd(year):
    """获取指定年份所有24节气的 Julian Day (UTC)，带缓存

    Returns:
        dict: {节气名: Julian Day number (UTC)}，不含失败的节气
    """
    if not hasattr(get_all_jieqi_jd, '_cache'):
        get_all_jieqi_jd._cache = {}
    if year not in get_all_jieqi_jd._cache:
        result = {}
        for name, lon in _JIEQI_LON_MAP.items():
            jd = _swisseph_jieqi_jd(year, lon)
            if jd is not None:
                # 验证找到的节气确实属于该年（二分搜索可能跨年）
                try:
                    import swisseph as swe
                    y_check, m_check, _, _ = swe.revjul(jd)
                    # 小寒/大寒可能在1月，属于前一年末到该年初
                    # 大雪/冬至可能在12月底，属于该年末到下年初
                    if y_check == year or (y_check == year + 1 and m_check == 1):
                        result[name] = jd
                except Exception:
                    pass
        get_all_jieqi_jd._cache[year] = result
    return get_all_jieqi_jd._cache[year]


def jd_to_datetime(jd):
    """Julian Day (UTC) → 北京时间 datetime"""
    try:
        import swisseph as swe
        y, m, d, h = swe.revjul(jd)
        from datetime import datetime as _dt
        utc_dt = _dt(y, m, d, int(h), int((h % 1) * 60), int(((h * 60) % 1) * 60))
        return utc_dt + timedelta(hours=8)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
# 四柱排盘核心
# ═══════════════════════════════════════════════════════════════

def gan_zhi_to_num(gan, zhi):
    """干支→六十甲子序号(0-59)"""
    tg = TIAN_GAN.index(gan)
    dz = DI_ZHI.index(zhi)
    for i in range(60):
        if i % 10 == tg and i % 12 == dz:
            return i
    return 0


def num_to_gan_zhi(num):
    """六十甲子序号→干支"""
    return TIAN_GAN[num % 10] + DI_ZHI[num % 12]


def get_nayin(gan, zhi):
    """获取纳音"""
    num = gan_zhi_to_num(gan, zhi)
    return NAYIN[num] if 0 <= num < 60 else ''


def get_xun_kong(gan, zhi):
    """获取旬首和空亡"""
    num = gan_zhi_to_num(gan, zhi)
    xun_head_num = (num // 10) * 10
    xun_head = num_to_gan_zhi(xun_head_num)
    kong = XUN_KONG.get(xun_head, '')
    return xun_head, kong


def calc_year_pillar(dt_solar, jieqi_times):
    """年柱 — 立春分界

    精确到时辰级别：
    - sxtwl 库以"日"为粒度判断年柱，认为立春当天全天属于新年
    - 但实际应以精确立春时刻为界：立春前 → 旧年年柱，立春后 → 新年年柱
    - 修复方法：如果 dt_solar 在立春当天且时刻 < 立春时刻，取前一天的年柱
    """
    import sxtwl

    lichun_dt = jieqi_times.get('立春')

    # 判断是否在立春当天且未到立春时刻
    if lichun_dt:
        # 同一天但时间在立春之前 → 用前一天的sxtwl结果（旧年）
        if (dt_solar.date() == lichun_dt.date() and dt_solar < lichun_dt):
            prev_day = dt_solar - timedelta(days=1)
            obj = sxtwl.fromSolar(prev_day.year, prev_day.month, prev_day.day)
            gz = obj.getYearGZ()
            return TIAN_GAN[gz.tg], DI_ZHI[gz.dz]

    # 正常情况（非立春当天，或立春当天但已过立春时刻）
    obj = sxtwl.fromSolar(dt_solar.year, dt_solar.month, dt_solar.day)
    gz = obj.getYearGZ()
    return TIAN_GAN[gz.tg], DI_ZHI[gz.dz]


def calc_month_pillar(dt_solar, year_gan, jieqi_times):
    """月柱 — 节令分界 + 五虎遁

    根据出生时刻确定当前节令月支，再用五虎遁定月干

    注意：本地月柱已精确到时辰（以节气时刻为界），比WZ API的日粒度更准确。
    在节气当天已过节气时刻时：
    - 本地判定已进入新月支（如立夏后→巳月）
    - WZ判定仍在旧月支（如立夏当天全天→辰月）
    此外，年柱差异（立春当天年干不同）也会通过五虎遁影响月干。
    混合模式下使用WZ结果，降级模式下使用本地结果（更精确）。
    """
    # 找出出生时刻之前最近的节令
    # 收集所有节气时刻，按时间排序，找到最后一个 <= dt_solar 的节令
    candidates = []
    for jie_name in JIE_ORDER:
        jie_dt = jieqi_times.get(jie_name)
        if jie_dt and jie_dt <= dt_solar:
            candidates.append((jie_dt, jie_name))

    if candidates:
        # 按时间排序，取最近的一个
        candidates.sort(key=lambda x: x[0])
        latest_jie_dt, latest_jie_name = candidates[-1]
        current_zhi = JIE_ZHI[latest_jie_name]
    else:
        current_zhi = None

    # 如果当年节气不够完整，用sxtwl降级
    if current_zhi is None:
        import sxtwl
        obj = sxtwl.fromSolar(dt_solar.year, dt_solar.month, dt_solar.day)
        gz = obj.getMonthGZ()
        return TIAN_GAN[gz.tg], DI_ZHI[gz.dz]

    # 五虎遁：年干决定寅月天干
    year_gan_idx = TIAN_GAN.index(year_gan)
    yin_gan_idx = WU_HU_DUN[year_gan_idx]
    month_zhi_idx = MONTH_ZHI.index(current_zhi)
    month_gan_idx = (yin_gan_idx + month_zhi_idx) % 10

    return TIAN_GAN[month_gan_idx], current_zhi


def calc_day_pillar(dt_solar):
    """日柱 — sxtwl万年历"""
    import sxtwl
    obj = sxtwl.fromSolar(dt_solar.year, dt_solar.month, dt_solar.day)
    gz = obj.getDayGZ()
    return TIAN_GAN[gz.tg], DI_ZHI[gz.dz]


def calc_hour_pillar(hour, day_gan, is_night_zi=False, next_day_gan=None, night_zi_mode='夜子时不换日'):
    """时柱 — 五鼠遁

    Args:
        hour: 出生小时(0-23)
        day_gan: 日干
        is_night_zi: 是否夜子时(23:00-00:00)
        next_day_gan: 次日天干（夜子时需要用次日天干推时干）
        night_zi_mode: 早晚子时模式
            '夜子时不换日' - 23:00-00:00用次日天干推时干（默认）
            '子时换日' - 23:00-00:00用次日天干推时干（日柱已换日）
    """
    # 时支
    if hour == 23 or hour == 0:
        zhi = '子'
    else:
        zhi_idx = (hour + 1) // 2 % 12
        zhi = DI_ZHI[zhi_idx]

    # 五鼠遁：日干决定子时天干
    # 无论哪种模式，23点的时柱天干都用次日天干来推
    if is_night_zi and next_day_gan:
        gan_idx = TIAN_GAN.index(next_day_gan)
    else:
        gan_idx = TIAN_GAN.index(day_gan)

    zi_gan_idx = WU_SHU_DUN[gan_idx]
    zhi_idx = DI_ZHI.index(zhi)
    hour_gan_idx = (zi_gan_idx + zhi_idx) % 10

    return TIAN_GAN[hour_gan_idx], zhi


# ═══════════════════════════════════════════════════════════════
# 十神计算
# ═══════════════════════════════════════════════════════════════

def calc_shi_shen(day_gan, target_gan):
    """计算十神：日干对目标天干的十神"""
    if not target_gan or not day_gan:
        return ''
    day_wx = GAN_WUXING.get(day_gan, '')
    target_wx = GAN_WUXING.get(target_gan, '')
    if not day_wx or not target_wx:
        return ''
    day_yy = GAN_YINYANG[day_gan]
    target_yy = GAN_YINYANG[target_gan]

    # 同我/我生/我克/生我/克我
    if day_wx == target_wx:
        rel = '同'
    elif _wo_sheng(day_wx) == target_wx:
        rel = '我生'
    elif _wo_ke(day_wx) == target_wx:
        rel = '我克'
    elif _sheng_wo(day_wx) == target_wx:
        rel = '生我'
    elif _ke_wo(day_wx) == target_wx:
        rel = '克我'
    else:
        return '未知'

    yinyang = '同' if day_yy == target_yy else '异'
    return SHI_SHEN_MAP.get((day_wx, target_wx, yinyang), '未知')


def _wo_sheng(wx):
    """我生""" 
    m = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
    return m.get(wx, '')

def _wo_ke(wx):
    """我克"""
    m = {'木':'土','土':'水','水':'火','火':'金','金':'木'}
    return m.get(wx, '')

def _sheng_wo(wx):
    """生我"""
    m = {'木':'水','火':'木','土':'火','金':'土','水':'金'}
    return m.get(wx, '')

def _ke_wo(wx):
    """克我"""
    m = {'木':'金','火':'水','土':'木','金':'火','水':'土'}
    return m.get(wx, '')


def calc_shi_shen_for_gan(day_gan, gan):
    """对天干计算十神"""
    if not gan:
        return ''
    if gan == day_gan:
        return '日主'
    return calc_shi_shen(day_gan, gan)


# ═══════════════════════════════════════════════════════════════
# 五行统计
# ═══════════════════════════════════════════════════════════════

def calc_wuxing_count(four_pillars):
    """统计四柱五行数量（天干+地支藏干全部计入）

    Returns:
        dict: {'金':N, '木':N, '水':N, '火':N, '土':N, 'lack': ['X', ...]}
        lack: 数量为0的五行列表（问真八字"缺五行"提示）
    """
    count = {'金':0, '木':0, '水':0, '火':0, '土':0}

    for pillar in ['year', 'month', 'day', 'hour']:
        gan = four_pillars[pillar]['gan']
        zhi = four_pillars[pillar]['zhi']

        # 天干五行
        wx = GAN_WUXING[gan]
        count[wx] += 1

        # 地支五行
        wx = ZHI_WUXING[zhi]
        count[wx] += 1

        # 藏干五行
        for cg in CANG_GAN[zhi]:
            wx = GAN_WUXING[cg]
            count[wx] += 0.5  # 藏干权重0.5

    # 四舍五入
    for k in list(count.keys()):
        count[k] = round(count[k])

    # 缺五行检测：天干+地支（不含藏干）中数量为0的五行
    # 问真八字的"缺X"判定标准：仅看天干+地支本气，藏干不计
    gan_zhi_wx = {'金':0, '木':0, '水':0, '火':0, '土':0}
    for pillar in ['year', 'month', 'day', 'hour']:
        gan = four_pillars[pillar]['gan']
        zhi = four_pillars[pillar]['zhi']
        gan_zhi_wx[GAN_WUXING[gan]] += 1
        gan_zhi_wx[ZHI_WUXING[zhi]] += 1
    lack = [wx for wx, c in gan_zhi_wx.items() if c == 0]
    count['lack'] = lack

    return count


# ═══════════════════════════════════════════════════════════════
# 神煞判定
# ═══════════════════════════════════════════════════════════════

def calc_shen_sha(four_pillars, gender, nayin_wx):
    """计算神煞列表"""
    result = []
    day_gan = four_pillars['day']['gan']
    day_zhi = four_pillars['day']['zhi']

    # 收集四柱所有地支
    all_zhi = [four_pillars[p]['zhi'] for p in ['year','month','day','hour']]
    all_gan = [four_pillars[p]['gan'] for p in ['year','month','day','hour']]

    # 天乙贵人（日干查四柱地支）
    guiren_zhi = TIAN_YI_GUI_REN.get(day_gan, [])
    for z in guiren_zhi:
        if z in all_zhi:
            result.append('天乙贵人')
            break

    # 太极贵人
    taiji_zhi = TAI_JI.get(day_gan, [])
    for z in taiji_zhi:
        if z in all_zhi:
            result.append('太极贵人')
            break

    # 天德贵人（月支对应月令查天德）
    month_zhi = four_pillars['month']['zhi']
    month_idx = DI_ZHI.index(month_zhi)
    month_num = ((month_idx - 1) % 12) + 1  # 寅=1月,卯=2月...
    tian_de_gan = TIAN_DE.get(month_num, '')
    if tian_de_gan and tian_de_gan in all_gan:
        result.append('天德贵人')

    # 月德贵人
    yue_de_gan = YUE_DE.get(month_num, '')
    if yue_de_gan and yue_de_gan in all_gan:
        result.append('月德贵人')

    # 德秀贵人（三合局查法：以月令地支查德和秀的天干）
    de_xiu = DE_XIU_MAP.get(month_zhi, ('', ''))
    if de_xiu:
        de_gan, xiu_gan = de_xiu
        if de_gan in all_gan or xiu_gan in all_gan:
            result.append('德秀贵人')

    # 驿马（日支查）
    yima_zhi = YIMA.get(day_zhi, '')
    if yima_zhi and yima_zhi in all_zhi:
        result.append('驿马')

    # 桃花（日支查）
    taohua_zhi = TAOHUA.get(day_zhi, '')
    if taohua_zhi and taohua_zhi in all_zhi:
        result.append('桃花')

    # 将星（日支查）
    jiangxing_zhi = JIANG_XING.get(day_zhi, '')
    if jiangxing_zhi and jiangxing_zhi in all_zhi:
        result.append('将星')

    # 华盖（日支查）
    huagai_zhi = HUA_GAI.get(day_zhi, '')
    if huagai_zhi and huagai_zhi in all_zhi:
        result.append('华盖')

    # 文昌（日干查）
    wenchang_zhi = WEN_CHANG.get(day_gan, '')
    if wenchang_zhi and wenchang_zhi in all_zhi:
        result.append('文昌')

    # 羊刃（日干查）
    yangren_zhi = YANG_REN.get(day_gan, '')
    if yangren_zhi and yangren_zhi in all_zhi:
        result.append('羊刃')

    # 禄神（日干查）
    lushen_zhi = LU_SHEN.get(day_gan, '')
    if lushen_zhi and lushen_zhi in all_zhi:
        result.append('禄神')

    # 金舆（日干查）
    jinyu_zhi = JIN_YU.get(day_gan, '')
    if jinyu_zhi and jinyu_zhi in all_zhi:
        result.append('金舆')

    # 学堂
    xuexi_zhi = XUE_TANG.get(GAN_WUXING[day_gan], '')
    if xuexi_zhi and xuexi_zhi in all_zhi:
        result.append('学堂')

    # 孤辰（日支查，男命看）
    guchen_zhi = GU_CHEN.get(day_zhi, '')
    if guchen_zhi and guchen_zhi in all_zhi and gender == '男':
        result.append('孤辰')

    # 寡宿（日支查，女命看）
    guasu_zhi = GUA_SU.get(day_zhi, '')
    if guasu_zhi and guasu_zhi in all_zhi and gender == '女':
        result.append('寡宿')

    # 亡神
    wangshen_zhi = WANG_SHEN.get(day_zhi, '')
    if wangshen_zhi and wangshen_zhi in all_zhi:
        result.append('亡神')

    # 劫煞
    jiesha_zhi = JIE_SHA.get(day_zhi, '')
    if jiesha_zhi and jiesha_zhi in all_zhi:
        result.append('劫煞')

    # 飞刃（羊刃对冲）
    yangren_zhi2 = YANG_REN.get(day_gan, '')
    if yangren_zhi2:
        chong_idx = (DI_ZHI.index(yangren_zhi2) + 6) % 12
        feiren_zhi = DI_ZHI[chong_idx]
        if feiren_zhi in all_zhi:
            result.append('飞刃')

    # ── 补全神煞（对齐问真八字） ──
    year_zhi = four_pillars['year']['zhi']

    # 文昌贵人（名称对齐：问真叫"文昌贵人"，我们之前叫"文昌"）
    # 上面已有"文昌"判断，这里改为"文昌贵人"名称
    # 为避免重复，在最终结果中去重并统一名称

    # 十灵日（日柱查）
    day_gz = day_gan + day_zhi
    if day_gz in SHI_LING_RI:
        result.append('十灵日')

    # 孤鸾煞（日柱查）
    if day_gz in GU_LUAN_SHA:
        result.append('孤鸾煞')

    # 月德合（月令查天干）
    yue_de_he_gan = YUE_DE_HE.get(month_num, '')
    if yue_de_he_gan and yue_de_he_gan in all_gan:
        result.append('月德合')

    # 灾煞（年支查）
    zaisha_zhi = ZAI_SHA.get(year_zhi, '')
    if zaisha_zhi and zaisha_zhi in all_zhi:
        result.append('灾煞')

    # 丧门（年支查）
    sangmen_zhi = SANG_MEN.get(year_zhi, '')
    if sangmen_zhi and sangmen_zhi in all_zhi:
        result.append('丧门')

    # 勾绞煞（年支查）
    gj = GOU_JIAO.get(year_zhi, {})
    if gj:
        if gj['勾'] in all_zhi:
            result.append('勾煞')
        if gj['绞'] in all_zhi:
            result.append('绞煞')

    # 红鸾（年支查）
    hongluan_zhi = HONG_LUAN.get(year_zhi, '')
    if hongluan_zhi and hongluan_zhi in all_zhi:
        result.append('红鸾')

    # 天罗地网（纳音+性别查）
    # 男命纳音火忌天罗(戌亥)，女命纳音水/土忌地网(辰巳)
    if gender == '男' and nayin_wx == '火':
        if '戌' in all_zhi or '亥' in all_zhi:
            result.append('天罗')
    if gender == '女' and nayin_wx in ('水', '土'):
        if '辰' in all_zhi or '巳' in all_zhi:
            result.append('地网')

    # 词馆（学堂的对冲位置，问真称"词馆"）
    # 已在 per_pillar 中有词馆，此处全局判断
    xuexi_zhi2 = XUE_TANG.get(GAN_WUXING[day_gan], '')
    if xuexi_zhi2:
        cguan_idx = (DI_ZHI.index(xuexi_zhi2) + 6) % 12
        cguan_zhi = DI_ZHI[cguan_idx]
        if cguan_zhi in all_zhi:
            result.append('词馆')

    # 空亡标注（四柱地支落入日柱空亡则为空亡）
    for p in ['year', 'month', 'day', 'hour']:
        zhi = four_pillars[p]['zhi']
        if zhi in kong_wang_list if 'kong_wang_list' in dir() else []:
            if '空亡' not in result:
                result.append('空亡')
            break
    # 使用日柱空亡判断
    _, day_kong = get_xun_kong(day_gan, day_zhi)
    day_kong_list = list(day_kong) if day_kong else []
    for p in ['year', 'month', 'hour']:  # 日柱自身不会空亡
        zhi = four_pillars[p]['zhi']
        if zhi in day_kong_list:
            result.append('空亡')
            break

    # 天医（月支查，月支前一位，四柱地支见之）
    tian_yi_yi_zhi = TIAN_YI_YI.get(month_zhi, '')
    if tian_yi_yi_zhi and tian_yi_yi_zhi in all_zhi:
        result.append('天医')

    # 天喜（年支查，年支对冲位逆数第五位，四柱地支见之）
    year_zhi = four_pillars['year']['zhi']
    tian_xi_zhi = TIAN_XI.get(year_zhi, '')
    if tian_xi_zhi and tian_xi_zhi in all_zhi:
        result.append('天喜')

    # 统一名称：文昌→文昌贵人
    result = ['文昌贵人' if x == '文昌' else x for x in result]

    # 去重
    seen = set()
    deduped = []
    for x in result:
        if x not in seen:
            seen.add(x)
            deduped.append(x)

    return deduped


# ═══════════════════════════════════════════════════════════════
# 旺衰判定
# ═══════════════════════════════════════════════════════════════

def calc_wang_shuai(day_gan, month_zhi):
    """日干在月令的旺衰

    简化版：根据日干五行与月令五行关系判断
    """
    day_wx = GAN_WUXING[day_gan]
    month_wx = ZHI_WUXING[month_zhi]

    if day_wx == month_wx:
        return '旺'
    elif _sheng_wo(day_wx) == month_wx:
        return '相'
    elif _wo_ke(day_wx) == month_wx:
        return '休'
    elif _ke_wo(day_wx) == month_wx:
        return '囚'
    elif _wo_sheng(day_wx) == month_wx:
        return '死'
    return '平'


def calc_wang_shuai_detail(four_pillars):
    """日干旺衰详细分析（问真八字风格）

    综合考量四个维度：
    1. 得令/失令：日干在月令的旺衰（得令=旺/相，失令=休/囚/死）
    2. 得地/失地：日干在地支十二长生中的位置（长生/帝旺/临官为得地）
    3. 得生/失生：四柱中有无印星（生我者）生扶日干
    4. 得助/失助：四柱中有无比劫（同我者）帮助日干

    Returns:
        dict: {
            'de_ling': bool,       # 得令
            'de_di': bool,         # 得地
            'de_sheng': bool,      # 得生
            'de_zhu': bool,        # 得助
            'score': int,          # 综合得分(0-8)
            'strength': str,       # '身旺' / '身弱' / '偏旺' / '偏弱' / '中和'
            'detail': {
                'ling': {'text': str, 'status': bool},
                'di': {'text': str, 'status': bool},
                'sheng': {'text': str, 'status': bool},
                'zhu': {'text': str, 'status': bool},
            }
        }
    """
    day_gan = four_pillars['day']['gan']
    day_wx = GAN_WUXING[day_gan]
    month_zhi = four_pillars['month']['zhi']
    month_wx = ZHI_WUXING[month_zhi]

    # 收集四柱所有天干地支
    all_gan = [four_pillars[p]['gan'] for p in ['year','month','day','hour']]
    all_zhi = [four_pillars[p]['zhi'] for p in ['year','month','day','hour']]

    # ── 1. 得令/失令 ──
    # 日干在月令的旺衰状态
    ws = calc_wang_shuai(day_gan, month_zhi)
    de_ling = ws in ('旺', '相')
    ling_text = f'日干{day_gan}在{month_zhi}月{ws}'

    # ── 2. 得地/失地 ──
    # 日干在其他地支（年日时）中的十二长生状态
    # 长生、帝旺、临官为得地
    de_di_positions = []
    DI_POSITIONS_GOOD = {'长生', '帝旺', '临官', '冠带'}
    for i, zhi in enumerate(all_zhi):
        cs = calc_shi_er_chang_sheng(day_gan, zhi)
        if cs in DI_POSITIONS_GOOD:
            pillar_name = ['年','月','日','时'][i]
            de_di_positions.append(f'{pillar_name}{zhi}{cs}')
    de_di = len(de_di_positions) >= 2  # 至少2个地支得地
    di_text = f'{"、".join(de_di_positions)}' if de_di_positions else '无长生/帝旺/临官'

    # ── 3. 得生/失生 ──
    # 四柱天干中有无印星（生我者）+ 地支藏干有无印星
    sheng_wo_wx = _sheng_wo(day_wx)  # 生我的五行
    sheng_gan_positions = []
    for i, gan in enumerate(all_gan):
        if i == 2:  # 跳过日干自身
            continue
        if GAN_WUXING[gan] == sheng_wo_wx:
            pillar_name = ['年','月','日','时'][i]
            sheng_gan_positions.append(f'{pillar_name}{gan}')
    # 藏干中的印星
    for i, zhi in enumerate(all_zhi):
        for cg in CANG_GAN[zhi]:
            if GAN_WUXING[cg] == sheng_wo_wx:
                pillar_name = ['年','月','日','时'][i]
                sheng_gan_positions.append(f'{pillar_name}藏{cg}')
    de_sheng = len(sheng_gan_positions) >= 1
    sheng_text = f'{"、".join(sheng_gan_positions[:4])}' if sheng_gan_positions else f'四柱无{_wx_name(sheng_wo_wx)}印星'

    # ── 4. 得助/失助 ──
    # 四柱天干中有无比劫（同我者）+ 地支藏干有无比劫
    zhu_positions = []
    for i, gan in enumerate(all_gan):
        if i == 2:  # 跳过日干自身
            continue
        if GAN_WUXING[gan] == day_wx:
            pillar_name = ['年','月','日','时'][i]
            zhu_positions.append(f'{pillar_name}{gan}')
    # 藏干中的比劫
    for i, zhi in enumerate(all_zhi):
        for cg in CANG_GAN[zhi]:
            if GAN_WUXING[cg] == day_wx:
                pillar_name = ['年','月','日','时'][i]
                zhu_positions.append(f'{pillar_name}藏{cg}')
    de_zhu = len(zhu_positions) >= 1
    zhu_text = f'{"、".join(zhu_positions[:4])}' if zhu_positions else f'四柱无{_wx_name(day_wx)}比劫'

    # ── 综合评分 ──
    score = 0
    if de_ling: score += 3   # 得令权重最高
    if de_di: score += 2
    if de_sheng: score += 2
    if de_zhu: score += 1

    if score >= 6:
        strength = '身旺'
    elif score >= 4:
        strength = '偏旺'
    elif score >= 3:
        strength = '中和'
    elif score >= 1:
        strength = '偏弱'
    else:
        strength = '身弱'

    return {
        'de_ling': de_ling,
        'de_di': de_di,
        'de_sheng': de_sheng,
        'de_zhu': de_zhu,
        'score': score,
        'strength': strength,
        'detail': {
            'ling': {'text': ling_text, 'status': de_ling},
            'di': {'text': di_text, 'status': de_di},
            'sheng': {'text': sheng_text, 'status': de_sheng},
            'zhu': {'text': zhu_text, 'status': de_zhu},
        }
    }


def _wx_name(wx):
    """五行名称映射"""
    return {'金':'金','木':'木','水':'水','火':'火','土':'土'}.get(wx, wx)
# ═══════════════════════════════════════════════════════════════

def calc_wang_xiang_xiu(month_zhi):
    """计算五行旺相休囚死

    以月令五行为基准：
    与月令同五行 → 旺
    月令生之 → 相
    月令克之 → 休（问真称"囚"）
    克月令 → 囚（问真称"休"）
    月令泄之（生月令） → 死

    问真八字PC版显示顺序：水旺/木相/金休/土囚/火死
    这里返回与问真一致的列表格式
    """
    month_wx = ZHI_WUXING[month_zhi]
    wx_list = ['金', '木', '水', '火', '土']
    wx_status = {}

    for wx in wx_list:
        if wx == month_wx:
            wx_status[wx] = '旺'
        elif _sheng_wo(wx) == month_wx:
            wx_status[wx] = '相'
        elif _wo_ke(wx) == month_wx:
            # 我克者 → 问真标记为"休"
            wx_status[wx] = '休'
        elif _ke_wo(wx) == month_wx:
            # 克我者 → 问真标记为"囚"
            wx_status[wx] = '囚'
        elif _wo_sheng(wx) == month_wx:
            wx_status[wx] = '死'
        else:
            wx_status[wx] = '平'

    # 返回问真格式的列表：["水旺", "木相", "金休", "土囚", "火死"]
    return [f"{wx}{wx_status[wx]}" for wx in wx_list]


# ═══════════════════════════════════════════════════════════════
# 十二长生计算
# ═══════════════════════════════════════════════════════════════

# 十二长生顺序
CHANG_SHENG_ORDER = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养']

# 阳干长生起始地支
YANG_GAN_CHANG_SHENG = {
    '甲': '亥',  # 木长生在亥
    '丙': '寅',  # 火长生在寅
    '戊': '寅',  # 土长生在寅（同火）
    '庚': '巳',  # 金长生在巳
    '壬': '申',  # 水长生在申
}

# 阴干长生起始地支
YIN_GAN_CHANG_SHENG = {
    '乙': '午',  # 阴木长生在午
    '丁': '酉',  # 阴火长生在酉
    '己': '酉',  # 阴土长生在酉（同阴火）
    '辛': '子',  # 阴金长生在子
    '癸': '卯',  # 阴水长生在卯
}


def calc_shi_er_chang_sheng(gan, zhi, reference_zhi=None):
    """计算天干在地支的十二长生状态

    阳干顺排，阴干逆排

    Args:
        gan: 天干
        zhi: 要查询的地支
        reference_zhi: 参考地支（用于"星运"按年支查、"自坐"按日支查）
                       如果为None，直接用zhi作为查询目标

    Returns:
        十二长生名称，如"临官"、"长生"等
    """
    is_yang = GAN_YINYANG[gan] == '阳'

    if is_yang:
        start_zhi = YANG_GAN_CHANG_SHENG.get(gan, '寅')
    else:
        start_zhi = YIN_GAN_CHANG_SHENG.get(gan, '午')

    start_idx = DI_ZHI.index(start_zhi)
    target_idx = DI_ZHI.index(zhi)

    if is_yang:
        # 阳干顺排
        steps = (target_idx - start_idx) % 12
    else:
        # 阴干逆排
        steps = (start_idx - target_idx) % 12

    return CHANG_SHENG_ORDER[steps]


def calc_xing_yun(four_pillars):
    """计算星运（十二长生 - 日主在各柱地支）

    问真八字的"星运"：以日主（day_gan）为基准，查日主在各柱地支的十二长生状态。
    这反映了命主（日主）在四柱各宫位环境中的旺衰状态。

    Returns:
        dict: {'year': '长生', 'month': '沐浴', 'day': '绝', 'hour': '长生'}
    """
    day_gan = four_pillars['day']['gan']
    result = {}
    for p in ['year', 'month', 'day', 'hour']:
        zhi = four_pillars[p]['zhi']
        result[p] = calc_shi_er_chang_sheng(day_gan, zhi)
    return result


def calc_di_shi(four_pillars):
    """计算地势（十二长生 - 按自身地支查）

    问真八字专业细盘：地势以每柱自身地支为基准，查该柱天干在自身地支的十二长生

    Returns:
        dict: {'year': '帝旺', 'month': '胎', 'day': '长生', 'hour': '胎'}
    """
    result = {}
    for p in ['year', 'month', 'day', 'hour']:
        gan = four_pillars[p]['gan']
        zhi = four_pillars[p]['zhi']
        result[p] = calc_shi_er_chang_sheng(gan, zhi)
    return result


def calc_zi_zuo(four_pillars):
    """计算自坐（十二长生 - 按日支查）

    问真八字：自坐以日支为基准，查每柱天干在日支的十二长生

    Returns:
        dict: {'year': '帝旺', 'month': '胎', 'day': '长生', 'hour': '胎'}
    """
    day_zhi = four_pillars['day']['zhi']
    result = {}
    for p in ['year', 'month', 'day', 'hour']:
        gan = four_pillars[p]['gan']
        result[p] = calc_shi_er_chang_sheng(gan, day_zhi)
    return result


# ═══════════════════════════════════════════════════════════════
# Per柱空亡计算
# ═══════════════════════════════════════════════════════════════

def calc_kong_wang_per_pillar(four_pillars):
    """计算每柱各自的旬空

    年柱：年柱干支所在旬的空亡
    月柱：月柱干支所在旬的空亡
    日柱：日柱干支所在旬的空亡
    时柱：时柱干支所在旬的空亡

    Returns:
        dict: {'year': '戌亥', 'month': '申酉', 'day': '戌亥', 'hour': '午未'}
    """
    result = {}
    for p in ['year', 'month', 'day', 'hour']:
        gan = four_pillars[p]['gan']
        zhi = four_pillars[p]['zhi']
        _, kong = get_xun_kong(gan, zhi)
        result[p] = kong
    return result


# ═══════════════════════════════════════════════════════════════
# Per柱神煞计算
# ═══════════════════════════════════════════════════════════════

def calc_shen_sha_per_pillar(four_pillars, gender, nayin_wx):
    """计算每柱独立的神煞列表

    与全局神煞不同，这里为每柱单独列出其地支/天干所带的星煞。
    以日干为基准查神煞，但按柱分类输出。

    问真八字做法：每个柱位独立显示该柱天干和地支所触发的神煞。

    Returns:
        dict: {'year': ['天厨贵人', '德秀贵人', ...], 'month': [...], 'day': [...], 'hour': [...]}
    """
    day_gan = four_pillars['day']['gan']
    day_zhi = four_pillars['day']['zhi']
    year_zhi = four_pillars['year']['zhi']
    year_gan = four_pillars['year']['gan']
    month_zhi = four_pillars['month']['zhi']
    hour_zhi = four_pillars['hour']['zhi']

    all_zhi = [four_pillars[p]['zhi'] for p in ['year', 'month', 'day', 'hour']]
    all_gan = [four_pillars[p]['gan'] for p in ['year', 'month', 'day', 'hour']]

    # 月令编号（寅=1, 卯=2, ..., 丑=12）
    month_num = MONTH_ZHI.index(month_zhi) + 1

    result = {p: [] for p in ['year', 'month', 'day', 'hour']}

    for p in ['year', 'month', 'day', 'hour']:
        p_gan = four_pillars[p]['gan']
        p_zhi = four_pillars[p]['zhi']
        stars = []

        # ── 天干查神煞 ──
        # 天乙贵人（日干查，但标注在出现贵人地支的柱位）
        guiren_zhi_list = TIAN_YI_GUI_REN.get(day_gan, [])
        if p_zhi in guiren_zhi_list:
            stars.append('天乙贵人')

        # 太极贵人（日干+年干查，问真八字同时用年干查太极）
        taiji_zhi_list = TAI_JI.get(day_gan, [])
        if p_zhi in taiji_zhi_list:
            stars.append('太极贵人')
        if p_zhi not in taiji_zhi_list:
            taiji_zhi_list_year = TAI_JI.get(year_gan, [])
            if p_zhi in taiji_zhi_list_year:
                if '太极贵人' not in stars:
                    stars.append('太极贵人')

        # 天德贵人（月令查天干）
        tian_de_gan = TIAN_DE.get(month_num, '')
        if tian_de_gan and p_gan == tian_de_gan:
            stars.append('天德贵人')
        # 天德贵人也查地支（问真八字：天德在月令地支也标注）
        if tian_de_gan and p_zhi == tian_de_gan:
            if '天德贵人' not in stars:
                stars.append('天德贵人')

        # 月德贵人
        yue_de_gan = YUE_DE.get(month_num, '')
        if yue_de_gan and p_gan == yue_de_gan:
            stars.append('月德贵人')

        # 德秀贵人（三合局查法：以月令地支查德和秀的天干）
        de_xiu = DE_XIU_MAP.get(month_zhi, ('', ''))
        if de_xiu:
            de_gan, xiu_gan = de_xiu
            if p_gan == de_gan or p_gan == xiu_gan:
                stars.append('德秀贵人')

        # 文昌贵人（日干+年干查地支，问真八字同时用年干查）
        wenchang_zhi = WEN_CHANG.get(day_gan, '')
        if p_zhi == wenchang_zhi:
            stars.append('文昌贵人')
        if p_zhi != wenchang_zhi:
            wenchang_zhi_year = WEN_CHANG.get(year_gan, '')
            if wenchang_zhi_year and p_zhi == wenchang_zhi_year:
                if '文昌贵人' not in stars:
                    stars.append('文昌贵人')

        # 学堂（日干五行查地支）
        xuexi_zhi = XUE_TANG.get(GAN_WUXING[day_gan], '')
        if p_zhi == xuexi_zhi:
            stars.append('学堂')

        # 词馆（学堂对冲位置，问真八字叫"词馆"）
        if xuexi_zhi:
            cguan_idx = (DI_ZHI.index(xuexi_zhi) + 6) % 12
            cguan_zhi = DI_ZHI[cguan_idx]
            if p_zhi == cguan_zhi:
                stars.append('词馆')

        # 禄神（日干查地支）
        lushen_zhi = LU_SHEN.get(day_gan, '')
        if p_zhi == lushen_zhi:
            stars.append('禄神')

        # 羊刃（日干查地支）
        yangren_zhi = YANG_REN.get(day_gan, '')
        if p_zhi == yangren_zhi:
            stars.append('羊刃')

        # 飞刃（羊刃对冲）
        if yangren_zhi:
            feiren_zhi = DI_ZHI[(DI_ZHI.index(yangren_zhi) + 6) % 12]
            if p_zhi == feiren_zhi:
                stars.append('飞刃')

        # 金舆（日干查地支）
        jinyu_zhi = JIN_YU.get(day_gan, '')
        if p_zhi == jinyu_zhi:
            stars.append('金舆')

        # 驿马（日支查，问真也用年支查）
        yima_zhi = YIMA.get(day_zhi, '')
        if p_zhi == yima_zhi:
            stars.append('驿马')
        # 年支查驿马（问真八字也查年支）
        if not yima_zhi or p_zhi != yima_zhi:
            yima_zhi_year = YIMA.get(year_zhi, '')
            if yima_zhi_year and p_zhi == yima_zhi_year:
                if '驿马' not in stars:
                    stars.append('驿马')

        # 桃花（日支查，问真也用年支查）
        taohua_zhi = TAOHUA.get(day_zhi, '')
        if p_zhi == taohua_zhi:
            stars.append('桃花')
        if not taohua_zhi or p_zhi != taohua_zhi:
            taohua_zhi_year = TAOHUA.get(year_zhi, '')
            if taohua_zhi_year and p_zhi == taohua_zhi_year:
                if '桃花' not in stars:
                    stars.append('桃花')

        # 将星（日支查，问真也用年支查，但年支自身柱位不标将星）
        jiangxing_zhi = JIANG_XING.get(day_zhi, '')
        if p_zhi == jiangxing_zhi:
            stars.append('将星')
        if not jiangxing_zhi or p_zhi != jiangxing_zhi:
            jiangxing_zhi_year = JIANG_XING.get(year_zhi, '')
            if jiangxing_zhi_year and p_zhi == jiangxing_zhi_year and p != 'year':
                if '将星' not in stars:
                    stars.append('将星')

        # 华盖（日支查，问真也用年支查）
        huagai_zhi = HUA_GAI.get(day_zhi, '')
        if p_zhi == huagai_zhi:
            stars.append('华盖')
        if not huagai_zhi or p_zhi != huagai_zhi:
            huagai_zhi_year = HUA_GAI.get(year_zhi, '')
            if huagai_zhi_year and p_zhi == huagai_zhi_year:
                if '华盖' not in stars:
                    stars.append('华盖')

        # 亡神
        wangshen_zhi = WANG_SHEN.get(day_zhi, '')
        if p_zhi == wangshen_zhi:
            stars.append('亡神')

        # 劫煞（日支查，问真也用年支查）
        jiesha_zhi = JIE_SHA.get(day_zhi, '')
        if p_zhi == jiesha_zhi:
            stars.append('劫煞')
        if not jiesha_zhi or p_zhi != jiesha_zhi:
            jiesha_zhi_year = JIE_SHA.get(year_zhi, '')
            if jiesha_zhi_year and p_zhi == jiesha_zhi_year:
                if '劫煞' not in stars:
                    stars.append('劫煞')

        # 孤辰/寡宿
        guchen_zhi = GU_CHEN.get(day_zhi, '')
        if p_zhi == guchen_zhi and gender == '男':
            stars.append('孤辰')
        guasu_zhi = GUA_SU.get(day_zhi, '')
        if p_zhi == guasu_zhi and gender == '女':
            stars.append('寡宿')

        # 天厨贵人（食神禄法：日干食神在地支的禄位，问真八字用此查法）
        # 也用年干查天厨贵人
        # 食神: 甲→丙, 乙→丁, 丙→戊, 丁→己, 戊→庚, 己→辛, 庚→壬, 辛→癸, 壬→甲, 癸→乙
        SHI_SHEN_GAN_MAP = {'甲':'丙','乙':'丁','丙':'戊','丁':'己','戊':'庚','己':'辛','庚':'壬','辛':'癸','壬':'甲','癸':'乙'}
        # 日干查天厨
        ss_gan = SHI_SHEN_GAN_MAP.get(day_gan, '')
        if ss_gan:
            ss_lushen = LU_SHEN.get(ss_gan, '')
            if ss_lushen and p_zhi == ss_lushen:
                stars.append('天厨贵人')
        # 年干查天厨
        ss_gan_year = SHI_SHEN_GAN_MAP.get(year_gan, '')
        if ss_gan_year:
            ss_lushen_year = LU_SHEN.get(ss_gan_year, '')
            if ss_lushen_year and p_zhi == ss_lushen_year and '天厨贵人' not in stars:
                stars.append('天厨贵人')

        # 国印贵人（日干查地支）
        GUO_YIN = {'甲':'戌','乙':'丑','丙':'丑','丁':'未','戊':'丑','己':'未','庚':'丑','辛':'戌','壬':'未','癸':'未'}
        guoyin_zhi = GUO_YIN.get(day_gan, '')
        if p_zhi == guoyin_zhi:
            stars.append('国印贵人')

        # 福星贵人（日干+年干查地支，问真八字同时用年干查）
        FU_XING = {'甲':'寅','乙':'丑','丙':'子','丁':'酉','戊':'未','己':'未','庚':'午','辛':'巳','壬':'辰','癸':'卯'}
        fuxing_zhi = FU_XING.get(day_gan, '')
        if p_zhi == fuxing_zhi:
            stars.append('福星贵人')
        if p_zhi != fuxing_zhi:
            fuxing_zhi_year = FU_XING.get(year_gan, '')
            if fuxing_zhi_year and p_zhi == fuxing_zhi_year:
                if '福星贵人' not in stars:
                    stars.append('福星贵人')

        # 红艳煞（日干查地支，也用年干查）
        hongyan_zhi = HONG_YAN.get(day_gan, '')
        if p_zhi == hongyan_zhi:
            stars.append('红艳煞')
        # 年干查红艳煞
        hongyan_zhi_year = HONG_YAN.get(year_gan, '')
        if hongyan_zhi_year and p_zhi == hongyan_zhi_year and '红艳煞' not in stars:
            stars.append('红艳煞')

        # 披麻（日支查，前三位）
        pima_zhi = DI_ZHI[(DI_ZHI.index(day_zhi) + 3) % 12]
        if p_zhi == pima_zhi:
            stars.append('披麻')

        # ── 补全神煞（对齐问真八字） ──
        # 十灵日（日柱查）
        day_gz = day_gan + day_zhi
        if p == 'day' and day_gz in SHI_LING_RI:
            stars.append('十灵日')

        # 孤鸾煞（日柱查）
        if p == 'day' and day_gz in GU_LUAN_SHA:
            stars.append('孤鸾煞')

        # 月德合（月令查天干）
        yue_de_he_gan = YUE_DE_HE.get(month_num, '')
        if yue_de_he_gan and p_gan == yue_de_he_gan:
            stars.append('月德合')

        # 天德合（月令查天干）
        # 天德合 = 天德天干的五合天干
        if tian_de_gan:
            tian_de_gan_idx = TIAN_GAN.index(tian_de_gan) if tian_de_gan in TIAN_GAN else -1
            if tian_de_gan_idx >= 0:
                WU_HE_GAN_IDX = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}
                tian_de_he_idx = WU_HE_GAN_IDX.get(tian_de_gan_idx, -1)
                if tian_de_he_idx >= 0:
                    tian_de_he_gan = TIAN_GAN[tian_de_he_idx]
                    if p_gan == tian_de_he_gan:
                        stars.append('天德合')

        # 灾煞（年支查）
        zaisha_zhi = ZAI_SHA.get(year_zhi, '')
        if p_zhi == zaisha_zhi:
            stars.append('灾煞')

        # 丧门（年支查）
        sangmen_zhi = SANG_MEN.get(year_zhi, '')
        if p_zhi == sangmen_zhi:
            stars.append('丧门')

        # 勾煞/绞煞（年支查）
        gj = GOU_JIAO.get(year_zhi, {})
        if gj:
            if p_zhi == gj['勾']:
                stars.append('勾煞')
            if p_zhi == gj['绞']:
                stars.append('绞煞')

        # 红鸾（年支查）
        hongluan_zhi = HONG_LUAN.get(year_zhi, '')
        if p_zhi == hongluan_zhi:
            stars.append('红鸾')

        # 天罗地网（纳音+性别查）
        if gender == '男' and nayin_wx == '火':
            if p_zhi in ('戌', '亥'):
                stars.append('天罗')
        if gender == '女' and nayin_wx in ('水', '土'):
            if p_zhi in ('辰', '巳'):
                stars.append('地网')

        # 空亡（日柱旬空+年柱旬空，四柱地支落入空亡则标注）
        _, day_kong = get_xun_kong(day_gan, day_zhi)
        day_kong_list = list(day_kong) if day_kong else []
        _, year_kong = get_xun_kong(year_gan, year_zhi)
        year_kong_list = list(year_kong) if year_kong else []
        combined_kong = set(day_kong_list) | set(year_kong_list)
        if p_zhi in combined_kong:
            stars.append('空亡')

        # 天医（月支查，月支前一位）
        tian_yi_yi_zhi = TIAN_YI_YI.get(month_zhi, '')
        if tian_yi_yi_zhi and p_zhi == tian_yi_yi_zhi:
            stars.append('天医')

        # 天喜（年支查）
        tian_xi_zhi = TIAN_XI.get(year_zhi, '')
        if tian_xi_zhi and p_zhi == tian_xi_zhi:
            stars.append('天喜')

        # 去重（保持顺序）
        seen = set()
        deduped = []
        for s in stars:
            if s not in seen:
                seen.add(s)
                deduped.append(s)

        result[p] = deduped

    return result


# ═══════════════════════════════════════════════════════════════
# 单组干支的神煞计算（用于大运/流年）
# ═══════════════════════════════════════════════════════════════

def _calc_shen_sha_for_ganzhi(gan, zhi, day_gan, year_gan, year_zhi, month_zhi, day_zhi, gender, nayin_wx):
    """为单组干支计算神煞列表（大运/流年使用）

    Args:
        gan: 天干
        zhi: 地支
        day_gan: 日主天干
        year_gan: 年干（用于年干查神煞）
        year_zhi: 年支
        month_zhi: 月支
        day_zhi: 日支
        gender: 性别
        nayin_wx: 纳音五行

    Returns:
        list: 神煞名称列表
    """
    stars = []

    # 天乙贵人
    guiren_zhi_list = TIAN_YI_GUI_REN.get(day_gan, [])
    if zhi in guiren_zhi_list:
        stars.append('天乙贵人')

    # 太极贵人
    taiji_zhi_list = TAI_JI.get(day_gan, [])
    if zhi in taiji_zhi_list:
        stars.append('太极贵人')

    # 文昌
    wenchang_zhi = WEN_CHANG.get(day_gan, '')
    if zhi == wenchang_zhi:
        stars.append('文昌')

    # 禄神
    lushen_zhi = LU_SHEN.get(day_gan, '')
    if zhi == lushen_zhi:
        stars.append('禄神')

    # 羊刃
    yangren_zhi = YANG_REN.get(day_gan, '')
    if zhi == yangren_zhi:
        stars.append('羊刃')

    # 驿马（年支查）
    yima_zhi = _calc_yi_ma(year_zhi)
    if zhi == yima_zhi:
        stars.append('驿马')

    # 桃花（年支查）
    taohua_zhi = _calc_tao_hua(year_zhi)
    if zhi == taohua_zhi:
        stars.append('桃花')

    # 华盖（年支查）
    huagai_zhi = _calc_hua_gai(year_zhi)
    if zhi == huagai_zhi:
        stars.append('华盖')

    # 将星（年支查）
    jiangxing_zhi = _calc_jiang_xing(year_zhi)
    if zhi == jiangxing_zhi:
        stars.append('将星')

    # 劫煞（年支查）
    jiesha_zhi = _calc_jie_sha(year_zhi)
    if zhi == jiesha_zhi:
        stars.append('劫煞')

    # 亡神（年支查）
    wangshen_zhi = _calc_wang_shen(year_zhi)
    if zhi == wangshen_zhi:
        stars.append('亡神')

    # 天德贵人
    month_idx = DI_ZHI.index(month_zhi)
    month_num = ((month_idx - 1) % 12) + 1
    tian_de_gan = TIAN_DE.get(month_num, '')
    if tian_de_gan and gan == tian_de_gan:
        stars.append('天德贵人')

    # 月德贵人
    yue_de_gan = YUE_DE.get(month_num, '')
    if yue_de_gan and gan == yue_de_gan:
        stars.append('月德贵人')

    # 德秀贵人（三合局查法：以月令地支查德和秀的天干）
    de_xiu = DE_XIU_MAP.get(month_zhi, ('', ''))
    if de_xiu:
        de_gan, xiu_gan = de_xiu
        if gan == de_gan or gan == xiu_gan:
            stars.append('德秀贵人')

    # 学堂
    xuexi_zhi = XUE_TANG.get(GAN_WUXING[day_gan], '')
    if zhi == xuexi_zhi:
        stars.append('学堂')

    # 孤辰寡宿（年支查）
    gu_chen_zhi = _calc_gu_chen(year_zhi, gender)
    gua_su_zhi = _calc_gua_su(year_zhi, gender)
    if zhi == gu_chen_zhi:
        stars.append('孤辰')
    if zhi == gua_su_zhi:
        stars.append('寡宿')

    # 红艳煞（日干查，也用年干查）
    hongyan_zhi = HONG_YAN.get(day_gan, '')
    if zhi == hongyan_zhi:
        stars.append('红艳煞')
    hongyan_zhi_year = HONG_YAN.get(year_gan, '')
    if hongyan_zhi_year and zhi == hongyan_zhi_year and '红艳煞' not in stars:
        stars.append('红艳煞')

    # 天厨贵人（食神禄法：日干食神在地支的禄位）
    SHI_SHEN_GAN_MAP = {'甲':'丙','乙':'丁','丙':'戊','丁':'己','戊':'庚','己':'辛','庚':'壬','辛':'癸','壬':'甲','癸':'乙'}
    ss_gan = SHI_SHEN_GAN_MAP.get(day_gan, '')
    if ss_gan:
        ss_lushen = LU_SHEN.get(ss_gan, '')
        if ss_lushen and zhi == ss_lushen:
            stars.append('天厨贵人')
    # 年干查天厨贵人
    ss_gan_year = SHI_SHEN_GAN_MAP.get(year_gan, '')
    if ss_gan_year:
        ss_lushen_year = LU_SHEN.get(ss_gan_year, '')
        if ss_lushen_year and zhi == ss_lushen_year and '天厨贵人' not in stars:
            stars.append('天厨贵人')

    # ── 补全神煞（对齐问真八字） ──
    # 文昌贵人（名称对齐）
    if '文昌' in stars:
        stars = ['文昌贵人' if x == '文昌' else x for x in stars]

    # 月德合
    yue_de_he_gan = YUE_DE_HE.get(month_num, '')
    if yue_de_he_gan and gan == yue_de_he_gan:
        stars.append('月德合')

    # 灾煞
    zaisha_zhi = ZAI_SHA.get(year_zhi, '')
    if zhi == zaisha_zhi:
        stars.append('灾煞')

    # 丧门
    sangmen_zhi = SANG_MEN.get(year_zhi, '')
    if zhi == sangmen_zhi:
        stars.append('丧门')

    # 勾煞/绞煞
    gj = GOU_JIAO.get(year_zhi, {})
    if gj:
        if zhi == gj['勾']:
            stars.append('勾煞')
        if zhi == gj['绞']:
            stars.append('绞煞')

    # 红鸾
    hongluan_zhi = HONG_LUAN.get(year_zhi, '')
    if zhi == hongluan_zhi:
        stars.append('红鸾')

    # 天罗地网
    if gender == '男' and nayin_wx == '火' and zhi in ('戌', '亥'):
        stars.append('天罗')
    if gender == '女' and nayin_wx in ('水', '土') and zhi in ('辰', '巳'):
        stars.append('地网')

    # 正词馆
    if xuexi_zhi:
        cguan_idx = (DI_ZHI.index(xuexi_zhi) + 6) % 12
        cguan_zhi = DI_ZHI[cguan_idx]
        if zhi == cguan_zhi:
            stars.append('正词馆')

    # 空亡（日柱旬空）
    _, day_kong = get_xun_kong(day_gan, day_zhi)
    day_kong_list = list(day_kong) if day_kong else []
    if zhi in day_kong_list:
        stars.append('空亡')

    # 天医（月支查）
    tian_yi_yi_zhi = TIAN_YI_YI.get(month_zhi, '')
    if tian_yi_yi_zhi and zhi == tian_yi_yi_zhi:
        stars.append('天医')

    # 天喜（年支查）
    tian_xi_zhi = TIAN_XI.get(year_zhi, '')
    if tian_xi_zhi and zhi == tian_xi_zhi:
        stars.append('天喜')

    return stars


def _calc_kong_wang_for_ganzhi(gan, zhi):
    """为单组干支计算空亡"""
    _, kong = get_xun_kong(gan, zhi)
    return kong


def _calc_yi_ma(year_zhi):
    """驿马：申子辰→寅, 寅午戌→申, 巳酉丑→亥, 亥卯未→巳"""
    YIMA_MAP = {'申':'寅','子':'寅','辰':'寅','寅':'申','午':'申','戌':'申',
                '巳':'亥','酉':'亥','丑':'亥','亥':'巳','卯':'巳','未':'巳'}
    return YIMA_MAP.get(year_zhi, '')

def _calc_tao_hua(year_zhi):
    """桃花：申子辰→酉, 寅午戌→卯, 巳酉丑→午, 亥卯未→子"""
    TAOHUA_MAP = {'申':'酉','子':'酉','辰':'酉','寅':'卯','午':'卯','戌':'卯',
                  '巳':'午','酉':'午','丑':'午','亥':'子','卯':'子','未':'子'}
    return TAOHUA_MAP.get(year_zhi, '')

def _calc_hua_gai(year_zhi):
    """华盖：申子辰→辰, 寅午戌→戌, 巳酉丑→丑, 亥卯未→未"""
    HUAGAI_MAP = {'申':'辰','子':'辰','辰':'辰','寅':'戌','午':'戌','戌':'戌',
                  '巳':'丑','酉':'丑','丑':'丑','亥':'未','卯':'未','未':'未'}
    return HUAGAI_MAP.get(year_zhi, '')

def _calc_jiang_xing(year_zhi):
    """将星：申子辰→子, 寅午戌→午, 巳酉丑→酉, 亥卯未→卯"""
    JIANGXING_MAP = {'申':'子','子':'子','辰':'子','寅':'午','午':'午','戌':'午',
                     '巳':'酉','酉':'酉','丑':'酉','亥':'卯','卯':'卯','未':'卯'}
    return JIANGXING_MAP.get(year_zhi, '')

def _calc_jie_sha(year_zhi):
    """劫煞：申子辰→巳, 寅午戌→亥, 巳酉丑→寅, 亥卯未→申"""
    JIESHA_MAP = {'申':'巳','子':'巳','辰':'巳','寅':'亥','午':'亥','戌':'亥',
                  '巳':'寅','酉':'寅','丑':'寅','亥':'申','卯':'申','未':'申'}
    return JIESHA_MAP.get(year_zhi, '')

def _calc_wang_shen(year_zhi):
    """亡神：申子辰→亥, 寅午戌→巳, 巳酉丑→申, 亥卯未→寅"""
    WANGSHEN_MAP = {'申':'亥','子':'亥','辰':'亥','寅':'巳','午':'巳','戌':'巳',
                    '巳':'申','酉':'申','丑':'申','亥':'寅','卯':'寅','未':'寅'}
    return WANGSHEN_MAP.get(year_zhi, '')

def _calc_gu_chen(year_zhi, gender):
    """孤辰：年支前两位"""
    idx = DI_ZHI.index(year_zhi)
    # 寅卯辰→巳, 巳午未→申, 申酉戌→亥, 亥子丑→寅
    GU_CHEN_MAP = {'寅':'巳','卯':'巳','辰':'巳','巳':'申','午':'申','未':'申',
                   '申':'亥','酉':'亥','戌':'亥','亥':'寅','子':'寅','丑':'寅'}
    return GU_CHEN_MAP.get(year_zhi, '')

def _calc_gua_su(year_zhi, gender):
    """寡宿：年支后两位"""
    GUA_SU_MAP = {'寅':'丑','卯':'丑','辰':'丑','巳':'辰','午':'辰','未':'辰',
                  '申':'未','酉':'未','戌':'未','亥':'戌','子':'戌','丑':'戌'}
    return GUA_SU_MAP.get(year_zhi, '')


# ═══════════════════════════════════════════════════════════════
# 十神缩写
# ═══════════════════════════════════════════════════════════════

SHISHEN_ABBREV = {
    '正印': '印', '偏印': '枭',
    '正官': '官', '偏官': '杀', '七杀': '杀',
    '正财': '财', '偏财': '才',
    '食神': '食', '伤官': '伤',
    '比肩': '比', '劫财': '劫',
    '日主': '日',
}


def shishen_abbrev(shishen_name):
    """十神全称→缩写

    印=正印, 枭=偏印, 官=正官, 杀=七杀/偏官,
    财=正财, 才=偏财, 食=食神, 伤=伤官,
    比=比肩, 劫=劫财
    """
    return SHISHEN_ABBREV.get(shishen_name, shishen_name)


# ═══════════════════════════════════════════════════════════════
# 藏干五行标注
# ═══════════════════════════════════════════════════════════════

def cang_gan_with_wuxing(cang_gan_dict):
    """将藏干从 ['丙','庚','戊'] 格式转为 ['丙火','庚金','戊土']

    Args:
        cang_gan_dict: {'year': ['丙','庚','戊'], ...}

    Returns:
        dict: {'year': ['丙火','庚金','戊土'], ...}
    """
    result = {}
    for p, cg_list in cang_gan_dict.items():
        result[p] = [f"{g}{GAN_WUXING[g]}" for g in cg_list]
    return result


# ═══════════════════════════════════════════════════════════════
# 小运计算
# ═══════════════════════════════════════════════════════════════

def calc_xiao_yun(four_pillars, current_age, gender, count=10):
    """计算小运

    小运规则：
    - 阳年男/阴年女：时柱顺排
    - 阴年男/阳年女：时柱逆排
    - 从1岁开始，每年一步小运

    Args:
        four_pillars: 四柱数据
        current_age: 当前年龄
        gender: 性别
        count: 计算步数

    Returns:
        list of dict: [{'age': 1, 'gan': '辛', 'zhi': '亥', 'gan_zhi': '辛亥'}, ...]
    """
    year_gan = four_pillars['year']['gan']
    is_yang_year = GAN_YINYANG[year_gan] == '阳'
    is_male = gender == '男'

    # 顺逆判断（与大运方向相反）
    shun = (is_yang_year and is_male) or (not is_yang_year and not is_male)

    # 时柱干支序号
    hour_gan = four_pillars['hour']['gan']
    hour_zhi = four_pillars['hour']['zhi']
    hour_num = gan_zhi_to_num(hour_gan, hour_zhi)

    xiao_yun = []
    direction = 1 if shun else -1

    for i in range(count):
        age = current_age + i
        gz_num = (hour_num + direction * age) % 60
        gz = num_to_gan_zhi(gz_num)
        xiao_yun.append({
            'age': age,
            'gan': gz[0],
            'zhi': gz[1],
            'gan_zhi': gz,
        })

    return xiao_yun


# ═══════════════════════════════════════════════════════════════
# 起运详情计算
# ═══════════════════════════════════════════════════════════════

def calc_qi_yun_detail(dt_solar, jieqi_times, four_pillars, gender):
    """计算起运详情文本

    Returns:
        dict: {
            'text': '出生后8年2月3天起运',
            'jiao_yun_text': '逢戊、癸年 立春后27天 交大运',
            'qi_yun_age': 8,
        }
    """
    year_gan = four_pillars['year']['gan']
    is_yang_year = GAN_YINYANG[year_gan] == '阳'
    is_male = gender == '男'
    shun = (is_yang_year and is_male) or (not is_yang_year and not is_male)

    # 收集节气
    year = dt_solar.year
    all_jie = []
    for y in [year - 1, year, year + 1]:
        jq = get_jieqi_times(y)
        for jie_name in JIE_ORDER:
            if jie_name in jq:
                all_jie.append((jq[jie_name], jie_name))

    all_jie.sort(key=lambda x: x[0])

    if shun:
        target = None
        target_name = ''
        for jie_dt, jie_name in all_jie:
            if jie_dt > dt_solar:
                target = jie_dt
                target_name = jie_name
                break
        if target is None:
            return {'text': '出生后5年起运', 'jiao_yun_text': '', 'qi_yun_age': 5}
        delta = target - dt_solar
    else:
        target = None
        target_name = ''
        for jie_dt, jie_name in reversed(all_jie):
            if jie_dt <= dt_solar:
                target = jie_dt
                target_name = jie_name
                break
        if target is None:
            return {'text': '出生后5年起运', 'jiao_yun_text': '', 'qi_yun_age': 5}
        delta = dt_solar - target

    total_seconds = delta.total_seconds()
    total_days = total_seconds / 86400.0

    # 问真八字标准换算（与问真APP对齐）
    # 算法：3天=1年, 1天=4月, 1小时=5天(先乘5再取整，保留小数精度)
    # S = 距离节令的天数（含小数）
    import math as _math
    S = total_days

    qiyun_years = int(S / 3)                                    # 年 (3天=1年)
    remaining_days = S - qiyun_years * 3                        # 提取年后剩余天数
    qiyun_months = int(remaining_days * 4)                      # 月 (1天=4月)
    remaining_after_months = remaining_days - qiyun_months / 4.0  # 提取月后剩余天数
    remaining_hours = remaining_after_months * 24               # 剩余天数→小时
    qiyun_days = int(remaining_hours * 5)                       # 天 (1小时=5天，先乘5再取整)
    qiyun_hours = 0                                             # 小时已转换为天，剩余为0

    # 起运岁数（四舍五入）
    qi_yun_age = qiyun_years + (1 if qiyun_months >= 6 else 0)
    qi_yun_age = max(1, qi_yun_age)

    # 起运文本（只显示非零部分，hours始终为0不显示）
    parts = []
    if qiyun_years: parts.append(f"{qiyun_years}年")
    if qiyun_months: parts.append(f"{qiyun_months}月")
    if qiyun_days: parts.append(f"{qiyun_days}天")
    qi_yun_text = f"出生后{''.join(parts)}起运" if parts else "出生后即起运"

    # 交运文本
    # "逢X、X年 节令后X天 交大运"
    # 问真八字使用起运年的天干来计算五合，而非出生年天干
    # 起运年 = 出生年 + 起运年数
    qiyun_year = dt_solar.year + qiyun_years
    # 起运年的天干：通过干支序号推算
    from datetime import timedelta as _td
    qiyun_year_base = qiyun_year - 4  # 甲子年基准
    qiyun_year_gan_idx = qiyun_year_base % 10
    WU_HE_GAN = {0:5, 1:6, 2:7, 3:8, 4:9, 5:0, 6:1, 7:2, 8:3, 9:4}
    he_gan_idx = WU_HE_GAN[qiyun_year_gan_idx]
    gan1 = TIAN_GAN[qiyun_year_gan_idx]
    gan2 = TIAN_GAN[he_gan_idx]

    # 交运节令后天数
    jiao_yun_days = int(total_days - qi_yun_age * 3)
    if jiao_yun_days < 0:
        jiao_yun_text = f"逢{gan1}、{gan2}年 {target_name}后0天 交大运" if target_name else ''
    else:
        jiao_yun_text = f"逢{gan1}、{gan2}年 {target_name}后{jiao_yun_days}天 交大运" if target_name else ''

    # 计算起运月（绝对月）
    from dateutil.relativedelta import relativedelta as _rd
    qiyun_date = dt_solar + _rd(years=qiyun_years, months=qiyun_months, days=qiyun_days)

    return {
        'text': qi_yun_text,
        'jiao_yun_text': jiao_yun_text,
        'qi_yun_age': qi_yun_age,
        'qiyun_year': qiyun_date.year,
        'qiyun_month': qiyun_date.month,
        'qiyun_day': qiyun_date.day,
    }


# ═══════════════════════════════════════════════════════════════
# 大运排盘
# ═══════════════════════════════════════════════════════════════

def calc_da_yun(four_pillars, gender, dt_solar, jieqi_times):
    """计算大运

    顺逆：阳年男/阴年女→顺，阴年男/阳年女→逆
    起运岁数：距最近节令天数÷3（3天=1岁）
    """
    year_gan = four_pillars['year']['gan']
    is_yang_year = GAN_YINYANG[year_gan] == '阳'
    is_male = gender == '男'

    # 顺逆判断
    shun = (is_yang_year and is_male) or (not is_yang_year and not is_male)

    # 计算起运岁数
    qi_yun_age = _calc_qi_yun_age(dt_solar, jieqi_times, shun)

    # 月柱干支序号
    month_gan = four_pillars['month']['gan']
    month_zhi = four_pillars['month']['zhi']
    month_num = gan_zhi_to_num(month_gan, month_zhi)

    # 生成12步大运（与问真八字一致，覆盖120年）
    da_yun = []
    direction = 1 if shun else -1
    birth_year = dt_solar.year

    for i in range(1, 13):
        gz_num = month_num + direction * i
        gz_num = gz_num % 60
        gz = num_to_gan_zhi(gz_num)

        start_age = qi_yun_age + 1 + (i - 1) * 10
        end_age = start_age + 9
        start_year = birth_year + start_age - 1  # 虚岁: 1岁=出生当年
        end_year = birth_year + end_age - 1

        da_yun.append({
            'index': i,
            'gan_zhi': gz,
            'gan': gz[0],
            'zhi': gz[1],
            'start_age': start_age,
            'end_age': end_age,
            'start_year': start_year,
            'end_year': end_year,
        })

    return da_yun, qi_yun_age, '顺' if shun else '逆'


def _calc_qi_yun_age(dt_solar, jieqi_times, shun):
    """计算起运岁数（使用问真算法：3天=1年, 1天=4月）

    顺排：出生→下一个节令
    逆排：出生→上一个节令
    3天=1年，1天=4月
    """

    # 获取当前年份和相邻年份的节气
    year = dt_solar.year
    all_jie = []

    # 收集连续3年的节令时刻
    for y in [year - 1, year, year + 1]:
        jq = get_jieqi_times(y)
        for jie_name in JIE_ORDER:
            if jie_name in jq:
                all_jie.append((jq[jie_name], jie_name))

    all_jie.sort(key=lambda x: x[0])

    if shun:
        # 找出生后最近的节令
        target = None
        for jie_dt, jie_name in all_jie:
            if jie_dt > dt_solar:
                target = jie_dt
                break
        if target is None:
            return 5  # 降级默认值
        delta = target - dt_solar
    else:
        # 找出生前最近的节令
        target = None
        for jie_dt, jie_name in reversed(all_jie):
            if jie_dt <= dt_solar:
                target = jie_dt
                break
        if target is None:
            return 5
        delta = dt_solar - target

    # delta 是 timedelta
    total_days = delta.total_seconds() / 86400.0

    # 问真算法：3天=1年, 1天=4月
    qiyun_years = int(total_days / 3)              # 年
    remaining_days = total_days - qiyun_years * 3   # 剩余天数
    qiyun_months = int(remaining_days * 4)          # 月 (1天=4月)

    # 起运岁数
    qi_yun_age = qiyun_years + (1 if qiyun_months >= 6 else 0)
    return max(1, qi_yun_age)


def check_wz_api_health():
    """检查问真八字API健康状态

    采用轻量级探测：发送一个简单的API请求，检查是否返回有效数据。
    结果缓存在 _WZ_HEALTH 中，避免每次排盘都检查。

    连续失败超过阈值时标记为不可用，之后每隔 _WZ_HEALTH_CHECK_INTERVAL 重试一次。
    一旦成功，立即恢复为可用状态。

    Returns:
        bool: True=可用, False=不可用
    """
    import time as _time
    import json as _json

    now = _time.time()

    # 如果在检查间隔内，直接返回缓存状态
    if now - _WZ_HEALTH['last_check'] < _WZ_HEALTH_CHECK_INTERVAL:
        return _WZ_HEALTH['available']

    # 需要重新检查
    _WZ_HEALTH['last_check'] = now

    try:
        import urllib.request
        import urllib.parse

        # 使用一个简单的测试参数
        test_url = "https://bzapi4.iwzbz.com/getbasebz8.php?d=2000-1-1-12-0&s=1&today=2000-1-1&vip=0&userguid=local&yzs=0"
        req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = _json.loads(resp.read().decode('utf-8'))

        if data and data.get('bz'):
            # 成功
            _WZ_HEALTH['available'] = True
            _WZ_HEALTH['fail_count'] = 0
            return True
        else:
            _WZ_HEALTH['fail_count'] += 1
    except Exception:
        _WZ_HEALTH['fail_count'] += 1

    # 判断是否超过阈值
    if _WZ_HEALTH['fail_count'] >= _WZ_HEALTH_FAIL_THRESHOLD:
        _WZ_HEALTH['available'] = False
    else:
        _WZ_HEALTH['available'] = True  # 还没超过阈值，暂且认为可用

    return _WZ_HEALTH['available']


def fetch_wenzhen_dayun(year, month, day, hour, minute, gender):
    """调用问真八字API获取完整排盘数据

    支持内存缓存：相同参数在 _WZ_CACHE_TTL 秒内不重复调用API。
    缓存key为 (year, month, day, hour, minute, gender)。
    可通过环境变量 WZ_CACHE_TTL 调整缓存时间（默认86400=24小时）。
    设置 WZ_CACHE_TTL=0 可禁用缓存。

    API地址: https://bzapi4.iwzbz.com/getbasebz8.php
    参数格式: d=YYYY-M-D-H-M, s=1(男)/2(女), today=YYYY-M-D

    返回数据包含:
    - bz: 四柱天干地支 (注意: hour字段API返回的始终是"X子", 时柱需本地计算)
    - dayun: 大运干支数组
    - qiyunsui/qiyunarr: 起运信息
    - shishen/canggan/shensha/nayin: 十神/藏干/神煞/纳音
    - taiyuan/minggong/shengong: 胎元/命宫/身宫

    Returns:
        dict with full paipan data, or None on failure
    """
    import json
    import time as _time

    # 健康检查：如果API已知不可用，直接跳过
    if not check_wz_api_health():
        return None

    # 检查缓存
    cache_key = (year, month, day, hour, minute, gender)
    if _WZ_CACHE_TTL > 0 and cache_key in _WZ_CACHE:
        cached_data, cached_ts = _WZ_CACHE[cache_key]
        if _time.time() - cached_ts < _WZ_CACHE_TTL:
            return cached_data

    try:
        import urllib.request
        import urllib.parse

        s = 1 if gender == '男' else 2
        from datetime import datetime as _dt
        now = _dt.now()
        today = f"{now.year}-{now.month}-{now.day}"
        # 使用短横线格式调用WZ API（与问真网站对齐）
        # 短横线格式：d=YYYY-M-D-H-MI，起运计算与传统排盘一致
        # 空格冒号格式：d=YYYY-M-D H:MI:SS，起运计算含精确分钟（与问真不一致）
        d = f"{year}-{month}-{day}-{hour}-{minute}"

        url = f"https://bzapi4.iwzbz.com/getbasebz8.php?d={urllib.parse.quote(d)}&s={s}&today={today}&vip=0&userguid=local&yzs=0"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=WZ_API_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        # 写入缓存
        if _WZ_CACHE_TTL > 0:
            _WZ_CACHE[cache_key] = (data, _time.time())
            # 清理过期缓存（避免内存泄漏）
            _clean_wz_cache()

        # 重置健康状态
        _WZ_HEALTH['available'] = True
        _WZ_HEALTH['fail_count'] = 0

        return data
    except Exception as e:
        logger.error(f"问真八字API调用失败: {e}")
        # 更新健康状态
        _WZ_HEALTH['fail_count'] += 1
        if _WZ_HEALTH['fail_count'] >= _WZ_HEALTH_FAIL_THRESHOLD:
            _WZ_HEALTH['available'] = False
        return None


def _clean_wz_cache():
    """清理过期的WZ API缓存条目"""
    global _WZ_CACHE
    import time as _time
    now = _time.time()
    expired_keys = [k for k, (_, ts) in _WZ_CACHE.items() if now - ts >= _WZ_CACHE_TTL]
    for k in expired_keys:
        del _WZ_CACHE[k]


def _parse_wz_bz(wz_data):
    """从问真API返回数据中解析四柱信息

    WZ API的bz字段格式有两种:
    1. 数字key: {"0":"庚","1":"午","2":"壬","3":"午","4":"辛","5":"亥","6":"戊","7":"子"}
    2. 嵌套对象: {"year":{"tg":"庚","dz":"午"}, ...}

    注意: WZ API的时柱(hour)始终返回"X子", 天干按五鼠遁正确但地支固定为子
    实际时柱需由本地根据出生时辰计算

    Returns:
        dict with 'year', 'month', 'day' pillars (hour from API is unreliable)
        or None if parsing fails
    """
    if not wz_data:
        return None

    bz = wz_data.get('bz', {})
    if not bz:
        return None

    try:
        if '0' in bz:
            # 数字key格式
            return {
                'year': {'gan': bz.get('0', ''), 'zhi': bz.get('1', '')},
                'month': {'gan': bz.get('2', ''), 'zhi': bz.get('3', '')},
                'day': {'gan': bz.get('4', ''), 'zhi': bz.get('5', '')},
                'hour_gan': bz.get('6', ''),  # WZ API hour天干可用，地支始终是"子"
            }
        elif 'year' in bz:
            # 嵌套对象格式
            yr = bz.get('year', {})
            mn = bz.get('month', {})
            dy = bz.get('day', {})
            hr = bz.get('hour', {})
            return {
                'year': {'gan': yr.get('tg', ''), 'zhi': yr.get('dz', '')},
                'month': {'gan': mn.get('tg', ''), 'zhi': mn.get('dz', '')},
                'day': {'gan': dy.get('tg', ''), 'zhi': dy.get('dz', '')},
                'hour_gan': hr.get('tg', ''),  # WZ API hour天干可用
            }
    except Exception as e:
        logger.error(f"解析问真API四柱失败: {e}")

    return None


def _build_dayun_from_wz(wz_data, four_pillars, dt_solar, jieqi_times):
    """从问真API数据构建大运列表

    Args:
        wz_data: 问真API返回的完整数据 (已有, 不重新获取)
        four_pillars: 四柱数据
        dt_solar: 出生时间
        jieqi_times: 节气时刻

    Returns:
        (da_yun, qi_yun_age, direction_str, source)
    """
    wz_dayun = wz_data.get('dayun', [])
    wz_qiyunsui = wz_data.get('qiyunsui', 0)
    wz_qiyunarr = wz_data.get('qiyunarr', [])

    # 解析起运岁数
    # qiyunarr = [year, month, day, hour, minute, age]
    # 优先级：
    #   1. age值合理（1-100）→ 直接使用
    #   2. age值异常但year/month/day合理 → 从起运日期推算虚岁
    #   3. qiyunsui值合理 → 使用qiyunsui
    #   4. 降级本地计算
    qi_yun_age = None
    birth_year = dt_solar.year

    if wz_qiyunarr and len(wz_qiyunarr) >= 6:
        age_from_arr = wz_qiyunarr[5]
        if 1 <= age_from_arr <= 100:
            qi_yun_age = age_from_arr - 1  # 虚岁→起运年数
        else:
            # age值异常，尝试从 qiyunarr[0:3]（起运年月日）推算虚岁
            qiyun_year = wz_qiyunarr[0] if wz_qiyunarr[0] > 1900 else None
            if qiyun_year and qiyun_year > birth_year:
                qi_yun_age = qiyun_year - birth_year  # 起运年数（不+1虚岁）
                if not (1 <= qi_yun_age <= 100):
                    qi_yun_age = None
                else:
                    logger.info(f"WZ API qiyunarr年龄异常({age_from_arr})，从起运年份推算={qi_yun_age}年")

    if qi_yun_age is None:
        if wz_qiyunsui and 1 <= wz_qiyunsui <= 100:
            qi_yun_age = wz_qiyunsui - 1  # 虚岁→起运年数
        else:
            # 降级：本地计算
            year_gan = four_pillars['year']['gan']
            is_yang_year = GAN_YINYANG[year_gan] == '阳'
            is_male = four_pillars.get('_gender', '男') == '男'
            shun = (is_yang_year and is_male) or (not is_yang_year and not is_male)
            qi_yun_age = _calc_qi_yun_age(dt_solar, jieqi_times, shun)

    # 判断顺逆
    if wz_dayun:
        first_gz = wz_dayun[0]
        month_num = gan_zhi_to_num(four_pillars['month']['gan'], four_pillars['month']['zhi'])
        first_num = gan_zhi_to_num(first_gz[0], first_gz[1])
        direction = 1 if (first_num - month_num) % 60 in range(1, 30) else -1
        direction_str = '顺' if direction == 1 else '逆'
    else:
        direction = 1
        direction_str = '顺'

    # 构建大运列表
    birth_year = dt_solar.year
    da_yun = []
    for i, gz in enumerate(wz_dayun):
        start_age = qi_yun_age + 1 + i * 10
        end_age = start_age + 9
        start_year = birth_year + start_age - 1  # 虚岁: 1岁=出生当年
        end_year = birth_year + end_age - 1
        da_yun.append({
            'index': i + 1,
            'gan_zhi': gz,
            'gan': gz[0],
            'zhi': gz[1],
            'start_age': start_age,
            'end_age': end_age,
            'start_year': start_year,
            'end_year': end_year,
        })

    return da_yun, qi_yun_age, direction_str, '问真八字'


def calc_da_yun_with_wenzhen(four_pillars, gender, dt_solar, jieqi_times):
    """计算大运，优先使用问真八字API，降级使用本地计算

    注意: 如果已经在 paipan() 中调用了 fetch_wenzhen_dayun，
    建议直接使用 _build_dayun_from_wz() 复用数据，避免重复API调用。

    Returns:
        (da_yun, qi_yun_age, direction_str, source)
    """
    wz_data = fetch_wenzhen_dayun(
        dt_solar.year, dt_solar.month, dt_solar.day,
        dt_solar.hour, dt_solar.minute, four_pillars.get('_gender', '男')
    )

    if wz_data and wz_data.get('dayun') and len(wz_data['dayun']) > 0:
        return _build_dayun_from_wz(wz_data, four_pillars, dt_solar, jieqi_times)
    else:
        da_yun, qi_yun_age, direction_str = calc_da_yun(four_pillars, gender, dt_solar, jieqi_times)
        return da_yun, qi_yun_age, direction_str, '本地计算'


# ═══════════════════════════════════════════════════════════════
# 流年排盘
# ═══════════════════════════════════════════════════════════════

def calc_liu_nian(current_year, day_gan, count=10):
    """计算流年（当前年前3年+后count年）"""
    import sxtwl

    liu_nian = []
    for offset in range(-3, count):
        year = current_year + offset
        try:
            obj = sxtwl.fromSolar(year, 6, 15)  # 用年中日期获取年柱
            gz = obj.getYearGZ()
            gan = TIAN_GAN[gz.tg]
            zhi = DI_ZHI[gz.dz]

            liu_nian.append({
                'year': year,
                'gan_zhi': gan + zhi,
                'gan': gan,
                'zhi': zhi,
                'shi_shen_gan': calc_shi_shen_for_gan(day_gan, gan),
            })
        except:
            pass

    return liu_nian


# ═══════════════════════════════════════════════════════════════
# 流月排盘
# ═══════════════════════════════════════════════════════════════

def calc_liu_yue(year, day_gan):
    """计算指定年份的12个流月

    流月天干由年干决定（五虎遁），地支固定为寅月至丑月。
    每个流月还计算天干十神和藏干十神。

    Args:
        year: 年份
        day_gan: 日主天干

    Returns:
        list of dict, 每项含:
          month_num, zhi, gan, gan_zhi, shi_shen_gan, cang_gan, cang_gan_shi_shen
    """
    import sxtwl

    # 获取年干
    try:
        obj = sxtwl.fromSolar(year, 6, 15)
        gz = obj.getYearGZ()
        year_gan = TIAN_GAN[gz.tg]
    except:
        return []

    # 五虎遁：年干→寅月天干
    year_gan_idx = TIAN_GAN.index(year_gan)
    yin_gan_idx = WU_HU_DUN[year_gan_idx]

    liu_yue = []
    for i, zhi in enumerate(MONTH_ZHI):  # 寅卯辰巳午未申酉戌亥子丑
        gan_idx = (yin_gan_idx + i) % 10
        gan = TIAN_GAN[gan_idx]
        gan_zhi = gan + zhi

        # 月份编号：寅=1, 卯=2, ..., 丑=12
        month_num = i + 1

        # 天干十神
        shi_shen_gan = calc_shi_shen_for_gan(day_gan, gan)

        # 藏干十神
        cg = CANG_GAN[zhi]
        cg_ss = [calc_shi_shen_for_gan(day_gan, c) for c in cg]

        # 纳音
        nayin = get_nayin(gan, zhi)

        liu_yue.append({
            'month_num': month_num,
            'zhi': zhi,
            'gan': gan,
            'gan_zhi': gan_zhi,
            'shi_shen_gan': shi_shen_gan,
            'cang_gan': cg,
            'cang_gan_shi_shen': cg_ss,
            'nayin': nayin,
        })

    return liu_yue


# ═══════════════════════════════════════════════════════════════
# 流日排盘
# ═══════════════════════════════════════════════════════════════

def calc_liu_ri(year, month, day_gan):
    """计算指定月份的流日

    每天一个干支，从当月1日到月末最后一天。
    同时计算天干十神和地支藏干十神。

    Args:
        year: 年份
        month: 月份(1-12)
        day_gan: 日主天干

    Returns:
        list of dict, 每项含:
          day, gan, zhi, gan_zhi, shi_shen_gan, cang_gan, cang_gan_shi_shen, lunar_str
    """
    import sxtwl
    import calendar

    # 获取当月天数
    _, last_day = calendar.monthrange(year, month)

    liu_ri = []
    for day in range(1, last_day + 1):
        try:
            obj = sxtwl.fromSolar(year, month, day)
            gz = obj.getDayGZ()
            gan = TIAN_GAN[gz.tg]
            zhi = DI_ZHI[gz.dz]
        except:
            continue

        gan_zhi = gan + zhi

        # 天干十神
        shi_shen_gan = calc_shi_shen_for_gan(day_gan, gan)

        # 藏干十神
        cg = CANG_GAN[zhi]
        cg_ss = [calc_shi_shen_for_gan(day_gan, c) for c in cg]

        # 农历
        try:
            lunar_str = solar_to_lunar_str(year, month, day)
        except:
            lunar_str = ''

        # 纳音
        nayin = get_nayin(gan, zhi)

        liu_ri.append({
            'day': day,
            'gan': gan,
            'zhi': zhi,
            'gan_zhi': gan_zhi,
            'shi_shen_gan': shi_shen_gan,
            'cang_gan': cg,
            'cang_gan_shi_shen': cg_ss,
            'nayin': nayin,
            'lunar_str': lunar_str,
        })

    return liu_ri


# ═══════════════════════════════════════════════════════════════
# 流日排盘（按八字月份，节令分界）
# ═══════════════════════════════════════════════════════════════

def calc_liu_ri_by_bazi_month(year, bazi_month_num, day_gan):
    """按八字月份计算流日（节令分界）

    八字月份以节令为界，与公历月份不同：
    - 寅月(1): 立春 → 惊蛰 (~2月4日 → ~3月6日)
    - 卯月(2): 惊蛰 → 清明 (~3月6日 → ~4月5日)
    - 辰月(3): 清明 → 立夏 (~4月5日 → ~5月5日)
    - ...以此类推

    Args:
        year: 年份（公历）
        bazi_month_num: 八字月序号 1-12 (1=寅月, 2=卯月, ..., 12=丑月)
        day_gan: 日主天干

    Returns:
        dict: {
            'liu_ri': [...],  # 流日列表
            'jie_name': str,  # 起始节令名
            'start_date': str, # 起始日期 YYYY-MM-DD
            'end_date': str,   # 结束日期 YYYY-MM-DD
            'month_zhi': str,  # 月支
        }
    """
    import sxtwl
    import calendar

    # bazi_month_num → JIE_ORDER 索引
    # JIE_ORDER = ['立春','惊蛰','清明','立夏','芒种','小暑',
    #              '立秋','白露','寒露','立冬','大雪','小寒']
    # bazi_month_num 1=寅月→立春(0), 2=卯月→惊蛰(1), ..., 12=丑月→小寒(11)
    jie_idx = bazi_month_num - 1
    if not (0 <= jie_idx < 12):
        return {'liu_ri': [], 'error': '八字月序号范围1-12'}

    jie_name = JIE_ORDER[jie_idx]
    month_zhi = JIE_ZHI[jie_name]

    # 获取节气时刻
    jieqi_times = get_jieqi_times(year)
    jieqi_next_year = get_jieqi_times(year + 1)

    # 当前节令时刻
    start_dt = jieqi_times.get(jie_name)
    if not start_dt:
        # 降级为公历月份
        greg_month = _bazi_month_to_gregorian_approx(bazi_month_num)
        return {
            'liu_ri': calc_liu_ri(year, greg_month, day_gan),
            'jie_name': jie_name,
            'start_date': f'{year}-{greg_month:02d}-01',
            'end_date': f'{year}-{greg_month:02d}-28',
            'month_zhi': month_zhi,
        }

    # 下一节令时刻
    next_jie_idx = (jie_idx + 1) % 12
    next_jie_name = JIE_ORDER[next_jie_idx]

    # 先尝试同年，如果同年的下一节令在起始节令之前，说明跨年了
    end_dt_same_year = jieqi_times.get(next_jie_name)
    end_dt_next_year = jieqi_next_year.get(next_jie_name)

    if end_dt_same_year and end_dt_same_year > start_dt:
        end_dt = end_dt_same_year
    elif end_dt_next_year:
        end_dt = end_dt_next_year
    elif end_dt_same_year:
        end_dt = end_dt_same_year  # fallback
    else:
        end_dt = start_dt + timedelta(days=30)

    # 转换为日期范围（节令当天开始，下一节令前一天结束）
    start_date = start_dt.date() if hasattr(start_dt, 'date') else start_dt
    end_date = end_dt.date() if hasattr(end_dt, 'date') else end_dt

    # 如果 start_dt 是 datetime，用其 date
    from datetime import date as date_type
    if isinstance(start_dt, datetime):
        start_date = start_dt.date()
    if isinstance(end_dt, datetime):
        end_date = end_dt.date()

    # 计算日期范围内的所有流日
    liu_ri = []
    current_date = start_date
    while current_date <= end_date:
        y, m, d = current_date.year, current_date.month, current_date.day
        try:
            obj = sxtwl.fromSolar(y, m, d)
            gz = obj.getDayGZ()
            gan = TIAN_GAN[gz.tg]
            zhi = DI_ZHI[gz.dz]
        except:
            current_date += timedelta(days=1)
            continue

        gan_zhi = gan + zhi
        shi_shen_gan = calc_shi_shen_for_gan(day_gan, gan)
        cg = CANG_GAN[zhi]
        cg_ss = [calc_shi_shen_for_gan(day_gan, c) for c in cg]

        try:
            lunar_str = solar_to_lunar_str(y, m, d)
        except:
            lunar_str = ''

        nayin = get_nayin(gan, zhi)

        liu_ri.append({
            'year': y,
            'month': m,
            'day': d,
            'gan': gan,
            'zhi': zhi,
            'gan_zhi': gan_zhi,
            'shi_shen_gan': shi_shen_gan,
            'cang_gan': cg,
            'cang_gan_shi_shen': cg_ss,
            'nayin': nayin,
            'lunar_str': lunar_str,
            'date_str': f'{y}-{m:02d}-{d:02d}',
        })

        current_date += timedelta(days=1)

    return {
        'liu_ri': liu_ri,
        'jie_name': jie_name,
        'start_date': f'{start_date}',
        'end_date': f'{end_date}',
        'month_zhi': month_zhi,
        'month_num': bazi_month_num,
    }


def _bazi_month_to_gregorian_approx(bazi_month_num):
    """八字月序号 → 近似公历月份（降级用）"""
    # 寅月≈2月, 卯月≈3月, ..., 丑月≈1月
    mapping = {1:2, 2:3, 3:4, 4:5, 5:6, 6:7,
               7:8, 8:9, 9:10, 10:11, 11:12, 12:1}
    return mapping.get(bazi_month_num, 1)


# ═══════════════════════════════════════════════════════════════
# 流时排盘
# ═══════════════════════════════════════════════════════════════

def calc_liu_shi(day_gan, day_zhi_for_gan=None):
    """计算12个流时（时辰）

    由日干决定子时天干（五鼠遁），地支固定为子时至亥时。
    同时计算天干十神和藏干十神。

    Args:
        day_gan: 当日天干（用于五鼠遁）
        day_zhi_for_gan: 日主天干（用于十神计算，通常是命盘日主）

    Returns:
        list of dict, 每项含:
          zhi, gan, gan_zhi, shi_shen_gan, cang_gan, cang_gan_shi_shen, hour_name
    """
    if day_zhi_for_gan is None:
        day_zhi_for_gan = day_gan

    # 五鼠遁：日干→子时天干
    day_gan_idx = TIAN_GAN.index(day_gan)
    zi_gan_idx = WU_SHU_DUN[day_gan_idx]

    liu_shi = []
    for i, zhi in enumerate(DI_ZHI):  # 子丑寅卯辰巳午未申酉戌亥
        gan_idx = (zi_gan_idx + i) % 10
        gan = TIAN_GAN[gan_idx]
        gan_zhi = gan + zhi

        # 天干十神
        shi_shen_gan = calc_shi_shen_for_gan(day_zhi_for_gan, gan)

        # 藏干十神
        cg = CANG_GAN[zhi]
        cg_ss = [calc_shi_shen_for_gan(day_zhi_for_gan, c) for c in cg]

        # 时辰名
        hour_name = zhi + '时'

        # 纳音
        nayin = get_nayin(gan, zhi)

        # 对应小时范围
        hour_range = ZHI_HOUR.get(zhi, (0, 0))
        hour_str = f"{hour_range[0]:02d}:00-{hour_range[1]:02d}:00" if hour_range != (23, 1) else "23:00-01:00"

        liu_shi.append({
            'zhi': zhi,
            'gan': gan,
            'gan_zhi': gan_zhi,
            'shi_shen_gan': shi_shen_gan,
            'cang_gan': cg,
            'cang_gan_shi_shen': cg_ss,
            'nayin': nayin,
            'hour_name': hour_name,
            'hour_str': hour_str,
        })

    return liu_shi


# ═══════════════════════════════════════════════════════════════
# 农历表示
# ═══════════════════════════════════════════════════════════════

def solar_to_lunar_str(year, month, day):
    """公历转农历字符串（如：庚午年五月廿三）"""
    try:
        from lunarcalendar import Lunar, Converter
        solar = Converter.Lunar2Solar  # 这不对，需要反过来
        # 用sxtwl获取农历
        import sxtwl
        obj = sxtwl.fromSolar(year, month, day)
        lunar_year = obj.getLunarYear()
        lunar_month = obj.getLunarMonth()
        lunar_day = obj.getLunarDay()
        is_leap = obj.isLunarLeap()

        # 年干支
        gz = obj.getYearGZ()
        year_gz = TIAN_GAN[gz.tg] + DI_ZHI[gz.dz]

        # 月份中文
        month_cn = ['正','二','三','四','五','六','七','八','九','十','冬','腊']
        month_str = ('闰' if is_leap else '') + month_cn[lunar_month - 1] + '月'

        # 日中文
        day_cn = ['初一','初二','初三','初四','初五','初六','初七','初八','初九','初十',
                   '十一','十二','十三','十四','十五','十六','十七','十八','十九','二十',
                   '廿一','廿二','廿三','廿四','廿五','廿六','廿七','廿八','廿九','三十']
        day_str = day_cn[lunar_day - 1] if 1 <= lunar_day <= 30 else str(lunar_day)

        return f"{year_gz}年{month_str}{day_str}"
    except Exception as e:
        logger.error(f"农历转换失败: {e}")
        return f"{year}年{month}月{day}日"


# ═══════════════════════════════════════════════════════════════
# 时辰名称
# ═══════════════════════════════════════════════════════════════

def hour_to_zhi_name(hour):
    """小时→时辰名"""
    if hour == 23 or hour == 0:
        return '子'
    return DI_ZHI[(hour + 1) // 2 % 12]


def zhi_to_hour_name(zhi):
    """地支→时辰名称（如 子时）"""
    return zhi + '时'


# ═══════════════════════════════════════════════════════════════
# 主入口函数
# ═══════════════════════════════════════════════════════════════

def paipan(name='', gender='男', birth_time='', cal_type='公历', birth_addr='',
           is_dst=False, night_zi_mode='夜子时不换日',
           sizi_pillars=None, use_solar_time=True, is_leap_month=False,
           longitude=None):
    """八字排盘主入口

    Args:
        name: 姓名
        gender: 性别（男/女）
        birth_time: 出生时间，格式 YYYYMMDDHHmm 或 YYYY-MM-DD HH:mm
        cal_type: 历法（公历/农历/四柱）
        birth_addr: 出生地（用于真太阳时校准）
        is_dst: 是否夏令时（1986-1991年中国实行夏令时，时钟拨快1小时）
        night_zi_mode: 早晚子时模式
            '夜子时不换日' - 23:00-00:00用当日干支，时柱天干用次日推(默认)
            '子时换日' - 23:00-00:00归入次日干支
        sizi_pillars: 四柱直接输入模式，格式 {'year':'甲子','month':'丙寅','day':'戊午','hour':'庚申'}
        use_solar_time: 是否启用真太阳时校准（默认True）
        is_leap_month: 农历月份是否为闰月（默认False）
        longitude: 精确经度（如果提供，优先于birth_addr字符串匹配）

    Returns:
        dict 排盘结果
    """
    # ── 1. 四柱直接输入模式 ──
    if cal_type == '四柱' and sizi_pillars:
        return _paipan_from_pillars(name, gender, sizi_pillars)

    # ── 2. 解析出生时间 ──
    birth_time = birth_time.strip().replace('-', '').replace(' ', '').replace(':', '')

    if len(birth_time) < 8:
        return {'success': False, 'error': '出生时间格式不正确，需要至少8位(YYYYMMDD)'}

    try:
        year = int(birth_time[0:4])
        month = int(birth_time[4:6])
        day = int(birth_time[6:8])
        hour = int(birth_time[8:10]) if len(birth_time) >= 10 else 12
        minute = int(birth_time[10:12]) if len(birth_time) >= 12 else 0
    except (ValueError, IndexError):
        return {'success': False, 'error': '出生时间格式解析失败'}

    # ── 3. 农历转公历 ──
    if cal_type == '农历':
        try:
            from lunarcalendar import Lunar, Converter
            lunar = Lunar(year, month, day, isleap=is_leap_month)
            solar = Converter.Lunar2Solar(lunar)
            year, month, day = solar.year, solar.month, solar.day
        except Exception as e:
            return {'success': False, 'error': f'农历转换失败: {e}'}

    # ── 4. 夏令时修正 ──
    if is_dst:
        # 夏令时期间时钟拨快1小时，需减1小时还原真实时间
        dt_tmp = datetime(year, month, day, hour, minute)
        dt_real = dt_tmp - timedelta(hours=1)
        year, month, day = dt_real.year, dt_real.month, dt_real.day
        hour, minute = dt_real.hour, dt_real.minute

    # ── 5. 真太阳时校准 ──
    dt_beijing = datetime(year, month, day, hour, minute)
    # 优先使用前端传递的精确经度，否则从地址字符串解析
    if longitude is None or longitude == 0:
        longitude = get_longitude(birth_addr)
    if use_solar_time:
        dt_solar = true_solar_time(dt_beijing, longitude)
    else:
        dt_solar = dt_beijing  # 不修正
    tz_offset_min = round((longitude - 120.0) * 4.0, 1)

    # ── 4. 节气时刻计算 ──
    jieqi_times = get_jieqi_times(year)
    # 也获取上一年和下一年的节气（用于跨年判断）
    prev_jieqi = get_jieqi_times(year - 1)
    next_jieqi = get_jieqi_times(year + 1)
    # 合并：以当前年份为主，前后年份只补充当前年份缺失的节气
    all_jieqi = {}
    # 先放前一年的（如前一年的小寒可能在当年1月初之前）
    for k, v in prev_jieqi.items():
        if v and v.year == year - 1:
            all_jieqi[k] = v
    # 当前年份覆盖
    for k, v in jieqi_times.items():
        if v:
            all_jieqi[k] = v
    # 下一年只补充当前年份缺失的
    for k, v in next_jieqi.items():
        if v and k not in all_jieqi:
            all_jieqi[k] = v

    # ── 6. 四柱排盘（优先使用问真八字API，降级本地计算） ──
    # 使用真太阳时确定时辰
    solar_hour = dt_solar.hour

    # 尝试调用问真八字API获取四柱
    # 注意: WZ API不做真太阳时校准(yzs=0), 所以用原始输入日期(dt_beijing)调用
    # 这样才能得到与问真八字网站一致的结果
    wz_data = fetch_wenzhen_dayun(
        dt_beijing.year, dt_beijing.month, dt_beijing.day,
        dt_beijing.hour, dt_beijing.minute, gender
    )
    wz_bz = _parse_wz_bz(wz_data)

    if wz_bz and wz_bz.get('year', {}).get('gan') and wz_bz.get('day', {}).get('gan'):
        # ✅ 问真API可用 — 使用其年/月/日柱（权威参考）
        # WZ API四柱特点:
        #   - 年柱/月柱: 以"日"粒度判断（立春当天整天算旧年）
        #   - 日柱: 完全可靠
        #   - 时柱: API固定返回"X子"，需本地计算
        year_gan = wz_bz['year']['gan']
        year_zhi = wz_bz['year']['zhi']
        month_gan = wz_bz['month']['gan']
        month_zhi = wz_bz['month']['zhi']
        day_gan = wz_bz['day']['gan']
        day_zhi = wz_bz['day']['zhi']
        pillar_source = '问真八字'
    else:
        # ❌ API不可用 — 降级本地计算
        # 年柱（立春分界）
        # 注意: 本地年柱精确到时辰（立春时刻为界），比WZ的日粒度更准确
        # 立春当天已过立春时刻 → 本地返回新年柱，WZ返回旧年柱
        # 这是本地算法更精确的体现，不是bug
        year_gan, year_zhi = calc_year_pillar(dt_solar, all_jieqi)

        # 月柱（节令分界+五虎遁）
        month_gan, month_zhi = calc_month_pillar(dt_solar, year_gan, all_jieqi)

        # 日柱
        day_gan, day_zhi = calc_day_pillar(dt_solar)
        pillar_source = '本地计算'

    # 时柱 — 始终本地计算（WZ API的时柱不可靠，始终返回"X子"）
    is_night_zi = (solar_hour == 23)

    if is_night_zi and night_zi_mode == '子时换日':
        # 子时换日模式：23:00-00:00归入次日干支
        dt_next = dt_solar + timedelta(days=1)
        next_day_gan, _ = calc_day_pillar(dt_next)
        hour_gan, hour_zhi = calc_hour_pillar(solar_hour, next_day_gan, is_night_zi, next_day_gan, night_zi_mode)
    else:
        # 夜子时不换日模式（默认）：23:00-00:00用当日干支，时干用次日推
        next_day_gan = None
        if is_night_zi:
            dt_next = dt_solar + timedelta(days=1)
            next_day_gan, _ = calc_day_pillar(dt_next)
        hour_gan, hour_zhi = calc_hour_pillar(solar_hour, day_gan, is_night_zi, next_day_gan, night_zi_mode)

    four_pillars = {
        'year':  {'gan': year_gan, 'zhi': year_zhi, 'gan_zhi': year_gan + year_zhi},
        'month': {'gan': month_gan, 'zhi': month_zhi, 'gan_zhi': month_gan + month_zhi},
        'day':   {'gan': day_gan, 'zhi': day_zhi, 'gan_zhi': day_gan + day_zhi},
        'hour':  {'gan': hour_gan, 'zhi': hour_zhi, 'gan_zhi': hour_gan + hour_zhi},
        '_gender': gender,  # 供大运顺逆判断使用
    }

    # ── 6. 纳音 ──
    for p in ['year', 'month', 'day', 'hour']:
        four_pillars[p]['nayin'] = get_nayin(four_pillars[p]['gan'], four_pillars[p]['zhi'])

    # ── 7. 十神 ──
    shi_shen = {}
    for p in ['year', 'month', 'day', 'hour']:
        gan = four_pillars[p]['gan']
        shi_shen[f'{p}_gan'] = calc_shi_shen_for_gan(day_gan, gan)

    # 藏干十神
    cang_gan = {}
    cang_gan_shi_shen = {}
    for p in ['year', 'month', 'day', 'hour']:
        zhi = four_pillars[p]['zhi']
        cg_list = CANG_GAN[zhi]
        cang_gan[p] = cg_list
        cang_gan_shi_shen[p] = [calc_shi_shen_for_gan(day_gan, cg) for cg in cg_list]

    # ── 8. 五行统计 ──
    wuxing_count = calc_wuxing_count(four_pillars)

    # ── 9. 空亡（日柱旬空） ──
    _, kong_wang = get_xun_kong(day_gan, day_zhi)
    kong_wang_list = list(kong_wang) if kong_wang else []

    # ── 10. 神煞 ──
    day_pillar_nayin = four_pillars['day']['nayin']
    nayin_wx = ''
    for wx in ['金','木','水','火','土']:
        if wx in day_pillar_nayin:
            nayin_wx = wx
            break
    shen_sha = calc_shen_sha(four_pillars, gender, nayin_wx)

    # ── 11. 旺衰 ──
    wang_shuai = calc_wang_shuai(day_gan, month_zhi)
    wang_shuai_detail = calc_wang_shuai_detail(four_pillars)

    # ── 12. 大运（复用问真八字API数据，降级本地计算） ──
    # 已在上面调用了 fetch_wenzhen_dayun，wz_data 可复用
    if wz_data and wz_data.get('dayun') and len(wz_data['dayun']) > 0:
        da_yun, qi_yun_age, da_yun_direction, da_yun_source = _build_dayun_from_wz(
            wz_data, four_pillars, dt_solar, all_jieqi
        )
    else:
        da_yun, qi_yun_age, da_yun_direction = calc_da_yun(four_pillars, gender, dt_beijing, all_jieqi)
        da_yun_source = '本地计算'

    # ── 12.5 起运前小运项（插入到大运列表最前面） ──
    # 如果起运岁数 > 1，在大运前面插入一个起运前小运项
    if qi_yun_age > 1 and da_yun:
        pre_end_age = qi_yun_age
        pre_start_year = dt_solar.year  # 虚岁1岁=出生当年
        pre_end_year = dt_solar.year + pre_end_age - 1
        pre_item = {
            'index': 0,
            'gan_zhi': '',
            'gan': '',
            'zhi': '',
            'start_age': 1,
            'end_age': pre_end_age,
            'start_year': pre_start_year,
            'end_year': pre_end_year,
        }
        da_yun.insert(0, pre_item)
        # 调整后续项的index
        for i, d in enumerate(da_yun):
            d['index'] = i + 1

    # ── 13. 流年 ──
    # 覆盖所有大运的年份范围 + 出生前后缓冲
    if da_yun:
        liunian_start = da_yun[0]['start_year'] - 3  # 大运前3年
        liunian_end = da_yun[-1]['end_year']  # 最后一个大运结束年
        liunian_count = liunian_end - dt_solar.year + 3  # 从出生年+前3年到结束
        liu_nian = calc_liu_nian(dt_solar.year, day_gan, count=liunian_count)
        # 过滤掉超出范围的年份
        liu_nian = [l for l in liu_nian if l['year'] >= liunian_start and l['year'] <= liunian_end]
    else:
        liu_nian = calc_liu_nian(dt_solar.year, day_gan, count=10)

    # ── 14. 当前流月 ──
    liu_yue = calc_liu_yue(dt_solar.year, day_gan)

    # ── 15. 当前流日（当月） ──
    liu_ri = calc_liu_ri(dt_solar.year, dt_solar.month, day_gan)

    # ── 16. 农历表示 ──
    lunar_str = solar_to_lunar_str(dt_solar.year, dt_solar.month, dt_solar.day)
    hour_zhi_name = zhi_to_hour_name(hour_zhi)

    # ── 17. 十二长生 - 星运（按年支查） ──
    xing_yun = calc_xing_yun(four_pillars)

    # ── 17.5 十二长生 - 地势（按自身地支查） ──
    di_shi = calc_di_shi(four_pillars)

    # ── 18. 十二长生 - 自坐（按日支查） ──
    zi_zuo = calc_zi_zuo(four_pillars)

    # ── 19. Per柱空亡 ──
    kong_wang_per_pillar = calc_kong_wang_per_pillar(four_pillars)

    # ── 20. Per柱神煞 ──
    shen_sha_per_pillar = calc_shen_sha_per_pillar(four_pillars, gender, nayin_wx)

    # ── 21. 藏干带五行 ──
    cang_gan_wx = cang_gan_with_wuxing(cang_gan)

    # ── 22. 日主标签（元男/元女） ──
    day_master_label = '元男' if gender == '男' else '元女'

    # ── 23. 生肖 ──
    SHENG_XIAO = ['子鼠','丑牛','寅虎','卯兔','辰龙','巳蛇','午马','未羊','申猴','酉鸡','戌狗','亥猪']
    sheng_xiao = ''
    for sx in SHENG_XIAO:
        if sx[0] == year_zhi:
            sheng_xiao = sx[1:]
            break

    # ── 24. 星座 ──
    xing_zuo = _calc_xing_zuo(month, day)

    # ── 25. 大运增强（增加十神缩写 + 纳音 + 长生十二运 + 星运 + 自坐 + 神煞 + 藏干） ──
    year_zhi = four_pillars['year']['zhi']
    day_zhi = four_pillars['day']['zhi']
    for dy_item in da_yun:
        dy_gan = dy_item.get('gan', '')
        dy_zhi = dy_item.get('zhi', '')
        # 起运前项（gan/zhi为空）跳过增强计算
        if not dy_gan or not dy_zhi:
            dy_item['gan_shishen_abbrev'] = ''
            dy_item['zhi_shishen_abbrev'] = ''
            dy_item['nayin'] = ''
            dy_item['chang_sheng'] = ''
            dy_item['xing_yun'] = ''
            dy_item['zi_zuo'] = ''
            dy_item['cang_gan'] = []
            dy_item['cang_gan_shi_shen'] = []
            dy_item['shen_sha'] = []
            dy_item['kong_wang'] = ''
            dy_item['pillar_relations'] = []
            continue
        dy_item['gan_shishen_abbrev'] = shishen_abbrev(calc_shi_shen_for_gan(day_gan, dy_gan))
        # 地支十神缩写：用本气（藏干第一个）
        dy_ben_qi = CANG_GAN[dy_zhi][0] if dy_zhi in CANG_GAN else ''
        dy_item['zhi_shishen_abbrev'] = shishen_abbrev(calc_shi_shen_for_gan(day_gan, dy_ben_qi)) if dy_ben_qi else ''
        # 纳音
        dy_item['nayin'] = get_nayin(dy_gan, dy_zhi)
        # 长生十二运（天干在地支的十二长生）
        dy_item['chang_sheng'] = calc_shi_er_chang_sheng(dy_gan, dy_zhi)
        # 星运（按年支查）
        dy_item['xing_yun'] = calc_shi_er_chang_sheng(dy_gan, year_zhi)
        # 自坐/通王（按日支查）
        dy_item['zi_zuo'] = calc_shi_er_chang_sheng(dy_gan, day_zhi)
        # 藏干 + 藏干十神
        dy_cang_gan = CANG_GAN.get(dy_zhi, [])
        dy_item['cang_gan'] = dy_cang_gan
        dy_item['cang_gan_shi_shen'] = [calc_shi_shen_for_gan(day_gan, c) for c in dy_cang_gan]
        # 神煞（大运天干地支查）
        dy_item['shen_sha'] = _calc_shen_sha_for_ganzhi(dy_gan, dy_zhi, day_gan, year_gan, year_zhi, month_zhi, day_zhi, gender, nayin_wx)
        # 空亡
        dy_item['kong_wang'] = _calc_kong_wang_for_ganzhi(dy_gan, dy_zhi)
        # 大运与原局冲合关系
        dy_item['pillar_relations'] = calc_ganzhi_relation_with_pillars(dy_gan, dy_zhi, four_pillars)

    # ── 26. 流年增强（增加十神缩写 + 小运干支 + 纳音 + 长生十二运 + 星运 + 自坐 + 神煞 + 藏干） ──
    for ln_item in liu_nian:
        ln_item['gan_shishen_abbrev'] = shishen_abbrev(ln_item.get('shi_shen_gan', ''))
        ln_zhi_ben_qi = CANG_GAN.get(ln_item['zhi'], [''])[0]
        ln_item['zhi_shishen_abbrev'] = shishen_abbrev(calc_shi_shen_for_gan(day_gan, ln_zhi_ben_qi)) if ln_zhi_ben_qi else ''
        # 纳音
        ln_item['nayin'] = get_nayin(ln_item['gan'], ln_item['zhi'])
        # 长生十二运
        ln_item['chang_sheng'] = calc_shi_er_chang_sheng(ln_item['gan'], ln_item['zhi'])
        # 星运（按年支查）
        ln_item['xing_yun'] = calc_shi_er_chang_sheng(ln_item['gan'], year_zhi)
        # 自坐/通王（按日支查）
        ln_item['zi_zuo'] = calc_shi_er_chang_sheng(ln_item['gan'], day_zhi)
        # 藏干 + 藏干十神
        ln_cang_gan = CANG_GAN.get(ln_item['zhi'], [])
        ln_item['cang_gan'] = ln_cang_gan
        ln_item['cang_gan_shi_shen'] = [calc_shi_shen_for_gan(day_gan, c) for c in ln_cang_gan]
        # 神煞
        ln_item['shen_sha'] = _calc_shen_sha_for_ganzhi(ln_item['gan'], ln_item['zhi'], day_gan, year_gan, year_zhi, month_zhi, day_zhi, gender, nayin_wx)
        # 空亡
        ln_item['kong_wang'] = _calc_kong_wang_for_ganzhi(ln_item['gan'], ln_item['zhi'])
        # 流年与原局冲合关系
        ln_item['pillar_relations'] = calc_ganzhi_relation_with_pillars(ln_item['gan'], ln_item['zhi'], four_pillars)

    # 计算小运（始终使用本地计算，WZ API的xiaoyun基于错误的时柱"X子"）
    birth_year_for_age = dt_solar.year
    max_age_in_liunian = max((ln_item.get('year', birth_year_for_age) - birth_year_for_age for ln_item in liu_nian), default=50)

    xiao_yun_list = calc_xiao_yun(four_pillars, 1, gender, count=max(max_age_in_liunian, 50))

    # 为流年匹配小运（虚岁: age=1 → birth_year, age=N → birth_year + N - 1）
    xiao_yun_map = {birth_year_for_age + xy['age'] - 1: xy for xy in xiao_yun_list}
    for ln_item in liu_nian:
        xy = xiao_yun_map.get(ln_item['year'])
        if xy:
            ln_item['xiao_yun_gan_zhi'] = xy['gan_zhi']
        else:
            ln_item['xiao_yun_gan_zhi'] = ''

    # ── 27. 起运详情 ──
    # 起运计算使用北京时(dt_beijing)，与问真APP对齐
    # 问真APP不使用真太阳时调整来计算起运
    qi_yun_detail = calc_qi_yun_detail(dt_beijing, all_jieqi, four_pillars, gender)

    # ── 28. 五行旺相休囚死 ──
    wang_xiang_xiu = calc_wang_xiang_xiu(month_zhi)

    # ── 29. 胎命身 ──
    tai_ming_shen = _calc_tai_ming_shen(four_pillars)
    if wz_data:
        ty_api = wz_data.get('taiyuan', '')
        if ty_api and len(ty_api) >= 2:
            tai_ming_shen['tai_yuan'] = {
                'gan_zhi': ty_api, 'gan': ty_api[0], 'zhi': ty_api[1],
                'nayin': wz_data.get('taiyuan_nayin', tai_ming_shen['tai_yuan']['nayin']),
            }

    # ── 30. 前后节气 ──
    jie_qi_range = _calc_jie_qi_range(dt_solar, all_jieqi)

    # ── 31. 胎息 ──
    tai_xi = _calc_tai_xi(four_pillars)

    # ── 32. 命卦 ──
    ming_gua = _calc_ming_gua(year, gender)

    # ── 33. 星宿 ──
    xing_su = _calc_xing_su(year, month, day)

    # ── 34. 袁天罡称骨 ──
    cheng_gu = _calc_cheng_gu(four_pillars)

    # ── 35. 干支关系 ──
    ganzhi_relations = _calc_ganzhi_relations(four_pillars)

    # ── 36. 格局 ──
    geju = _calc_geju(four_pillars, shi_shen, cang_gan_shi_shen)

    # ── 37. 调候用神 ──
    tiaohou = _calc_tiaohou(day_gan, month_zhi)

    # ── 38. 古籍参考 ──
    guji_refs = _calc_guji_refs(day_gan, month_zhi, geju)

    # ── 39. 性格简析与命理提示 ──
    personality = _calc_personality(day_gan, shi_shen, shen_sha, wang_shuai_detail, gender)

    # ── 40. 当天排盘（问真八字 tdbz 字段） ──
    today = datetime.now()
    today_jieqi = get_jieqi_times(today.year)
    today_year_gan, today_year_zhi = calc_year_pillar(today, today_jieqi)
    today_month_gan, today_month_zhi = calc_month_pillar(today, today_year_gan, today_jieqi)
    today_day_gan, today_day_zhi = calc_day_pillar(today)
    today_hour_zhi = DI_ZHI[(today.hour + 1) // 2 % 12]
    today_hour_gan, _ = calc_hour_pillar(today.hour, today_day_gan, False, None, night_zi_mode)
    today_paipan = {
        'date': f"{today.year}-{today.month:02d}-{today.day:02d}",
        'year': {'gan': today_year_gan, 'zhi': today_year_zhi, 'gan_zhi': today_year_gan + today_year_zhi},
        'month': {'gan': today_month_gan, 'zhi': today_month_zhi, 'gan_zhi': today_month_gan + today_month_zhi},
        'day': {'gan': today_day_gan, 'zhi': today_day_zhi, 'gan_zhi': today_day_gan + today_day_zhi},
        'hour': {'gan': today_hour_gan, 'zhi': today_hour_zhi, 'gan_zhi': today_hour_gan + today_hour_zhi},
    }

    # ── 组装结果 ──
    result = {
        'success': True,
        'name': name or '缘主',
        'gender': gender,
        'birth_solar': f"{dt_solar.year}-{dt_solar.month:02d}-{dt_solar.day:02d} {dt_solar.hour:02d}:{dt_solar.minute:02d}",
        'birth_input': f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
        'birth_lunar': f"{lunar_str} {hour_zhi_name}",
        'true_solar_time': f"{dt_solar.year}-{dt_solar.month:02d}-{dt_solar.day:02d} {dt_solar.hour:02d}:{dt_solar.minute:02d}",
        'location': {
            'addr': birth_addr or '默认',
            'lng': longitude,
            'tz_offset_min': tz_offset_min,
        },
        'four_pillars': four_pillars,
        'shi_shen': shi_shen,
        'cang_gan': cang_gan,
        'cang_gan_shi_shen': cang_gan_shi_shen,
        'wu_xing': wuxing_count,
        'lack_wuxing': wuxing_count.get('lack', []),  # 缺五行提示
        'kong_wang': kong_wang_list,
        'shen_sha': shen_sha,
        'wang_shuai': wang_shuai,
        'wang_shuai_detail': wang_shuai_detail,
        'da_yun': da_yun,
        'liu_nian': liu_nian,
        'liu_yue': liu_yue,
        'liu_ri': liu_ri,
        'qi_yun_age': qi_yun_age,
        'da_yun_direction': da_yun_direction,
        'da_yun_source': da_yun_source,
        'pillar_source': pillar_source,  # 四柱来源: '问真八字' 或 '本地计算'

        # ===== 新增字段 =====
        'day_master_label': day_master_label,
        'cang_gan_with_wx': cang_gan_wx,
        'xing_yun': xing_yun,
        'di_shi': di_shi,
        'zi_zuo': zi_zuo,
        'kong_wang_per_pillar': kong_wang_per_pillar,
        'shen_sha_per_pillar': shen_sha_per_pillar,
        'xiao_yun': xiao_yun_list,
        'qi_yun_detail': qi_yun_detail,
        'wang_xiang_xiu': wang_xiang_xiu,
        'sheng_xiao': sheng_xiao,
        'xing_zuo': xing_zuo,
        'tai_ming_shen': tai_ming_shen,
        'jie_qi_range': jie_qi_range,
        'tai_xi': tai_xi,
        'ming_gua': ming_gua,
        'xing_su': xing_su,
        'cheng_gu': cheng_gu,
        'ganzhi_relations': ganzhi_relations,
        'geju': geju,
        'tiaohou': tiaohou,
        'guji_refs': guji_refs,
        'personality': personality,  # 性格简析与命理提示
        'today_paipan': today_paipan,  # 当天排盘(问真tdbz)

        # 问真八字API原始数据（可用于前端交叉验证和展示）
        'wz_api_data': {
            'available': wz_data is not None,
            'dayun': wz_data.get('dayun', []) if wz_data else [],  # 大运干支列表（12组）
            'xiaoyun': wz_data.get('xiaoyun', []) if wz_data else [],
            'qiyunsui': wz_data.get('qiyunsui', None) if wz_data else None,
            'qiyunarr': wz_data.get('qiyunarr', []) if wz_data else [],
            'taiyuan': wz_data.get('taiyuan', '') if wz_data else '',
            'taixi': wz_data.get('taixi', '') if wz_data else '',
            'minggong': wz_data.get('minggong', '') if wz_data else '',
            'shenggong': wz_data.get('shenggong', '') if wz_data else '',
            'taiyuan_nayin': wz_data.get('taiyuan_nayin', '') if wz_data else '',
            'taixi_nayin': wz_data.get('taixi_nayin', '') if wz_data else '',
            'minggong_nayin': wz_data.get('minggong_nayin', '') if wz_data else '',
            'shenggong_nayin': wz_data.get('shenggong_nayin', '') if wz_data else '',
            'kongwang': wz_data.get('kongwang', '') if wz_data else '',
            'ss': wz_data.get('ss', []) if wz_data else [],       # 十神
            'cg': wz_data.get('cg', []) if wz_data else [],       # 藏干
            'cgss': wz_data.get('cgss', []) if wz_data else [],   # 藏干十神
            'ny': wz_data.get('ny', []) if wz_data else [],       # 纳音
            'kw': wz_data.get('kw', []) if wz_data else [],       # 空亡
            'xy': wz_data.get('xy', []) if wz_data else [],       # 长生十二运(星运)
            'zz': wz_data.get('zz', []) if wz_data else [],       # 长生十二运(自坐)
            'szshensha': wz_data.get('szshensha', []) if wz_data else [],  # 四柱神煞
            'dyshensha': wz_data.get('dyshensha', []) if wz_data else [],  # 大运神煞
        },
    }

    return result


def _paipan_from_pillars(name, gender, sizi_pillars):
    """四柱直接输入模式排盘 — 用户直接提供年月日时四柱干支

    Args:
        name: 姓名
        gender: 性别
        sizi_pillars: dict {'year':'甲子','month':'丙寅','day':'戊午','hour':'庚申'}

    Returns:
        dict 排盘结果（部分字段因无日期信息而简化）
    """
    # 解析四柱
    pillar_data = {}
    for p in ['year', 'month', 'day', 'hour']:
        gz = sizi_pillars.get(p, '')
        if not gz or len(gz) < 2:
            return {'success': False, 'error': f'{p}柱干支格式不正确，需要2字（如甲子）'}
        gan = gz[0]
        zhi = gz[1]
        if gan not in TIAN_GAN or zhi not in DI_ZHI:
            return {'success': False, 'error': f'{p}柱干支不合法：{gz}'}
        pillar_data[p] = {'gan': gan, 'zhi': zhi, 'gan_zhi': gan + zhi}

    pillar_data['_gender'] = gender  # 供大运顺逆判断使用
    four_pillars = pillar_data
    day_gan = four_pillars['day']['gan']
    day_zhi = four_pillars['day']['zhi']
    month_zhi = four_pillars['month']['zhi']
    year_zhi = four_pillars['year']['zhi']

    # 纳音
    for p in ['year', 'month', 'day', 'hour']:
        four_pillars[p]['nayin'] = get_nayin(four_pillars[p]['gan'], four_pillars[p]['zhi'])

    # 十神
    shi_shen = {}
    for p in ['year', 'month', 'day', 'hour']:
        gan = four_pillars[p]['gan']
        shi_shen[f'{p}_gan'] = calc_shi_shen_for_gan(day_gan, gan)

    # 藏干十神
    cang_gan = {}
    cang_gan_shi_shen = {}
    for p in ['year', 'month', 'day', 'hour']:
        zhi = four_pillars[p]['zhi']
        cg_list = CANG_GAN[zhi]
        cang_gan[p] = cg_list
        cang_gan_shi_shen[p] = [calc_shi_shen_for_gan(day_gan, cg) for cg in cg_list]

    # 五行统计
    wuxing_count = calc_wuxing_count(four_pillars)

    # 空亡
    _, kong_wang = get_xun_kong(day_gan, day_zhi)
    kong_wang_list = list(kong_wang) if kong_wang else []

    # 神煞
    day_pillar_nayin = four_pillars['day']['nayin']
    nayin_wx = ''
    for wx in ['金', '木', '水', '火', '土']:
        if wx in day_pillar_nayin:
            nayin_wx = wx
            break
    shen_sha = calc_shen_sha(four_pillars, gender, nayin_wx)

    # 旺衰
    wang_shuai = calc_wang_shuai(day_gan, month_zhi)
    wang_shuai_detail = calc_wang_shuai_detail(four_pillars)
    # 日主标签
    day_master_label = '元男' if gender == '男' else '元女'

    # 生肖
    SHENG_XIAO = ['子鼠', '丑牛', '寅虎', '卯兔', '辰龙', '巳蛇', '午马', '未羊', '申猴', '酉鸡', '戌狗', '亥猪']
    sheng_xiao = ''
    for sx in SHENG_XIAO:
        if sx[0] == year_zhi:
            sheng_xiao = sx[1:]
            break

    # 十二长生
    xing_yun = calc_xing_yun(four_pillars)
    di_shi = calc_di_shi(four_pillars)
    zi_zuo = calc_zi_zuo(four_pillars)

    # Per柱空亡
    kong_wang_per_pillar = calc_kong_wang_per_pillar(four_pillars)

    # Per柱神煞
    shen_sha_per_pillar = calc_shen_sha_per_pillar(four_pillars, gender, nayin_wx)

    # 藏干带五行
    cang_gan_wx = cang_gan_with_wuxing(cang_gan)

    # 五行旺相休囚死
    wang_xiang_xiu = calc_wang_xiang_xiu(month_zhi)

    # 胎命身
    tai_ming_shen = _calc_tai_ming_shen(four_pillars)

    # 胎息
    tai_xi = _calc_tai_xi(four_pillars)

    # 干支关系
    ganzhi_relations = _calc_ganzhi_relations(four_pillars)

    # 格局
    geju = _calc_geju(four_pillars, shi_shen, cang_gan_shi_shen)

    # 调候用神
    tiaohou = _calc_tiaohou(day_gan, month_zhi)

    # 称骨
    cheng_gu = _calc_cheng_gu(four_pillars)

    # 组装结果
    result = {
        'success': True,
        'name': name or '缘主',
        'gender': gender,
        'birth_solar': '四柱直接输入',
        'birth_input': f"{sizi_pillars.get('year','')}/{sizi_pillars.get('month','')}/{sizi_pillars.get('day','')}/{sizi_pillars.get('hour','')}",
        'birth_lunar': '四柱直接输入',
        'true_solar_time': '四柱直接输入',
        'location': {'addr': '', 'lng': 120.0, 'tz_offset_min': 0},
        'four_pillars': four_pillars,
        'shi_shen': shi_shen,
        'cang_gan': cang_gan,
        'cang_gan_shi_shen': cang_gan_shi_shen,
        'wu_xing': wuxing_count,
        'lack_wuxing': wuxing_count.get('lack', []),  # 缺五行提示
        'kong_wang': kong_wang_list,
        'shen_sha': shen_sha,
        'wang_shuai': wang_shuai,
        'wang_shuai_detail': wang_shuai_detail,
        'da_yun': [],
        'liu_nian': [],
        'liu_yue': [],
        'liu_ri': [],
        'qi_yun_age': None,
        'da_yun_direction': '',
        'da_yun_source': '四柱直接输入(无大运流年)',
        'day_master_label': day_master_label,
        'cang_gan_with_wx': cang_gan_wx,
        'xing_yun': xing_yun,
        'di_shi': di_shi,
        'zi_zuo': zi_zuo,
        'kong_wang_per_pillar': kong_wang_per_pillar,
        'shen_sha_per_pillar': shen_sha_per_pillar,
        'xiao_yun': [],
        'qi_yun_detail': {},
        'wang_xiang_xiu': wang_xiang_xiu,
        'sheng_xiao': sheng_xiao,
        'xing_zuo': '',
        'tai_ming_shen': tai_ming_shen,
        'jie_qi_range': {},
        'tai_xi': tai_xi,
        'ming_gua': '',
        'xing_su': '',
        'cheng_gu': cheng_gu,
        'ganzhi_relations': ganzhi_relations,
        'geju': geju,
        'tiaohou': tiaohou,
        'guji_refs': {},
        'personality': _calc_personality(day_gan, shi_shen, shen_sha, wang_shuai_detail, gender),
        'today_paipan': {},  # 四柱直接输入模式无当天排盘
    }

    return result


# ═══════════════════════════════════════════════════════════════
# 星座计算
# ═══════════════════════════════════════════════════════════════

def _calc_xing_zuo(month, day):
    """根据公历月日计算西方星座"""
    XING_ZUO_DATES = [
        (1, 20, '水瓶座'), (2, 19, '双鱼座'), (3, 21, '白羊座'),
        (4, 20, '金牛座'), (5, 21, '双子座'), (6, 22, '巨蟹座'),
        (7, 23, '狮子座'), (8, 23, '处女座'), (9, 23, '天秤座'),
        (10, 23, '天蝎座'), (11, 22, '射手座'), (12, 22, '摩羯座'),
    ]
    for m, d, name in XING_ZUO_DATES:
        if month < m or (month == m and day < d):
            # 返回上一个星座
            idx = XING_ZUO_DATES.index((m, d, name))
            return XING_ZUO_DATES[idx - 1][2] if idx > 0 else '摩羯座'
    return '摩羯座'


# ═══════════════════════════════════════════════════════════════
# 胎命身计算
# ═══════════════════════════════════════════════════════════════

def _calc_tai_ming_shen(four_pillars):
    """计算胎元、命宫、身宫

    胎元：月柱天干进1位，月柱地支进3位
    命宫：26 - (月支从寅数 + 时支从寅数)，从寅起1
    身宫：2 + 月支从寅数 + 时支从寅数，从寅起1

    Returns:
        dict: {
            'tai_yuan': {'gan_zhi': '丁卯', 'nayin': '炉中火'},
            'ming_gong': {'gan_zhi': '己巳', 'nayin': '大林木'},
            'shen_gong': {'gan_zhi': '丁丑', 'nayin': '涧下水'},
        }
    """
    month_gan = four_pillars['month']['gan']
    month_zhi = four_pillars['month']['zhi']

    # 胎元：月干进1，月支进3
    ty_gan_idx = (TIAN_GAN.index(month_gan) + 1) % 10
    ty_zhi_idx = (DI_ZHI.index(month_zhi) + 3) % 12
    ty_gan = TIAN_GAN[ty_gan_idx]
    ty_zhi = DI_ZHI[ty_zhi_idx]
    ty_gan_zhi = ty_gan + ty_zhi

    # 命宫、身宫
    year_gan = four_pillars['year']['gan']
    hour_zhi = four_pillars['hour']['zhi']
    yin_idx = DI_ZHI.index('寅')
    month_ord = (DI_ZHI.index(month_zhi) - yin_idx) % 12 + 1  # 寅=1
    hour_ord = (DI_ZHI.index(hour_zhi) - yin_idx) % 12 + 1    # 寅=1

    # 命宫地支：26 - (月序 + 时序)
    mg_ord = 26 - month_ord - hour_ord
    while mg_ord > 12: mg_ord -= 12
    while mg_ord < 1: mg_ord += 12
    mg_zhi = DI_ZHI[(yin_idx + mg_ord - 1) % 12]

    # 命宫天干：年干五虎遁
    year_gan_idx = TIAN_GAN.index(year_gan)
    yin_gan_idx = WU_HU_DUN[year_gan_idx]
    mg_offset = (DI_ZHI.index(mg_zhi) - yin_idx) % 12
    mg_gan = TIAN_GAN[(yin_gan_idx + mg_offset) % 10]
    mg_gan_zhi = mg_gan + mg_zhi

    # 身宫地支：2 + 月序 + 时序
    sg_ord = 2 + month_ord + hour_ord
    while sg_ord > 12: sg_ord -= 12
    while sg_ord < 1: sg_ord += 12
    sg_zhi = DI_ZHI[(yin_idx + sg_ord - 1) % 12]

    # 身宫天干：年干五虎遁
    sg_offset = (DI_ZHI.index(sg_zhi) - yin_idx) % 12
    sg_gan = TIAN_GAN[(yin_gan_idx + sg_offset) % 10]
    sg_gan_zhi = sg_gan + sg_zhi

    return {
        'tai_yuan': {
            'gan_zhi': ty_gan_zhi,
            'gan': ty_gan,
            'zhi': ty_zhi,
            'nayin': get_nayin(ty_gan, ty_zhi),
        },
        'ming_gong': {
            'gan_zhi': mg_gan_zhi,
            'gan': mg_gan,
            'zhi': mg_zhi,
            'nayin': get_nayin(mg_gan, mg_zhi),
        },
        'shen_gong': {
            'gan_zhi': sg_gan_zhi,
            'gan': sg_gan,
            'zhi': sg_zhi,
            'nayin': get_nayin(sg_gan, sg_zhi),
        },
    }


# ═══════════════════════════════════════════════════════════════
# 前后节气计算
# ═══════════════════════════════════════════════════════════════

def _calc_jie_qi_range(dt_solar, all_jieqi):
    """计算出生前后的节气时刻

    Returns:
        dict: {
            'prev_name': '大雪',
            'prev_time': '1989-12-07 11:20:57',
            'next_name': '小寒',
            'next_time': '1990-01-05 22:33:14',
            'after_text': '出生于大雪后24天12小时，小寒前4天22小时',
        }
    """
    # 收集所有节气时刻
    all_jieqi_list = []
    for name, dt in all_jieqi.items():
        if dt:
            all_jieqi_list.append((dt, name))

    all_jieqi_list.sort(key=lambda x: x[0])

    prev_jie = None
    next_jie = None

    for i, (jie_dt, jie_name) in enumerate(all_jieqi_list):
        if jie_dt <= dt_solar:
            prev_jie = (jie_dt, jie_name)
        elif jie_dt > dt_solar and next_jie is None:
            next_jie = (jie_dt, jie_name)
            break

    result = {
        'prev_name': prev_jie[1] if prev_jie else '',
        'prev_time': str(prev_jie[0]) if prev_jie else '',
        'next_name': next_jie[1] if next_jie else '',
        'next_time': str(next_jie[0]) if next_jie else '',
        'after_text': '',
    }

    if prev_jie and next_jie:
        delta_after = dt_solar - prev_jie[0]
        delta_before = next_jie[0] - dt_solar
        days_after = delta_after.total_seconds() / 86400
        days_before = delta_before.total_seconds() / 86400
        d_after = int(days_after)
        h_after = int((days_after - d_after) * 24)
        d_before = int(days_before)
        h_before = int((days_before - d_before) * 24)
        result['after_text'] = f"出生于{prev_jie[1]}后{d_after}天{h_after}小时，{next_jie[1]}前{d_before}天{h_before}小时"

    return result


# ═══════════════════════════════════════════════════════════════
# 胎息计算
# ═══════════════════════════════════════════════════════════════

def _calc_tai_xi(four_pillars):
    """计算胎息：日柱天干合化之干 + 日柱地支相合之支

    天干合：甲己合土→取己/甲, 乙庚合金→取庚/乙, 丙辛合水→取辛/丙,
            丁壬合木→取壬/丁, 戊癸合火→取癸/戊
    地支合：子丑合, 寅亥合, 卯戌合, 辰酉合, 巳申合, 午未合

    Returns:
        dict: {'gan_zhi': '辛亥', 'gan': '辛', 'zhi': '亥', 'nayin': '钗钏金'}
    """
    day_gan = four_pillars['day']['gan']
    day_zhi = four_pillars['day']['zhi']

    # 天干合
    GAN_HE = {'甲':'己','乙':'庚','丙':'辛','丁':'壬','戊':'癸',
              '己':'甲','庚':'乙','辛':'丙','壬':'丁','癸':'戊'}
    # 地支六合
    ZHI_HE = {'子':'丑','丑':'子','寅':'亥','亥':'寅','卯':'戌','戌':'卯',
              '辰':'酉','酉':'辰','巳':'申','申':'巳','午':'未','未':'午'}

    tx_gan = GAN_HE.get(day_gan, day_gan)
    tx_zhi = ZHI_HE.get(day_zhi, day_zhi)
    tx_gan_zhi = tx_gan + tx_zhi

    return {
        'gan_zhi': tx_gan_zhi,
        'gan': tx_gan,
        'zhi': tx_zhi,
        'nayin': get_nayin(tx_gan, tx_zhi),
    }


# ═══════════════════════════════════════════════════════════════
# 命卦计算（八宅法）
# ═══════════════════════════════════════════════════════════════

def _calc_ming_gua(birth_year, gender):
    """计算命卦（东四命/西四命）

    使用出生年份（四位数）和性别计算，传统八宅法公式：
    - 先将年数各位相加至个位
    - 男性：(11 - 个位数) % 9，若为0则=9，5→坤(2)
    - 女性：(4 + 个位数) % 9，若为0则=9，5→艮(8)

    另一种常见公式（1900-1999年）：
    - 男性：(100 - 年末两位) % 9
    - 女性：(年末两位 - 4) % 9

    通用公式（跨世纪）：
    - 将年份各位数字相加直至个位数
    - 男命：(11 - 个位) % 9，0→9，5→坤(2)
    - 女命：(4 + 个位) % 9，0→9，5→艮(8)

    东四命：1坎 3震 4巽 9离
    西四命：2坤 5中男→坤/中女→艮 6乾 7兑 8艮

    Returns:
        dict: {'gua_name': '坤卦', 'group': '西四命', 'gua_num': 2}
    """
    GUA_NAMES = {1: '坎卦', 2: '坤卦', 3: '震卦', 4: '巽卦',
                 5: '坤卦', 6: '乾卦', 7: '兑卦', 8: '艮卦', 9: '离卦'}
    DONG_SI = {1, 3, 4, 9}  # 东四命卦数

    # 将年份各位数字反复相加至个位数
    num = birth_year
    while num >= 10:
        num = sum(int(d) for d in str(num))

    # 传统八宅法公式
    if gender == '男':
        gua_num = (11 - num) % 9
        if gua_num == 0:
            gua_num = 9
        if gua_num == 5:
            gua_num = 2  # 男5→坤
    else:
        gua_num = (4 + num) % 9
        if gua_num == 0:
            gua_num = 9
        if gua_num == 5:
            gua_num = 8  # 女5→艮

    group = '东四命' if gua_num in DONG_SI else '西四命'
    gua_name = GUA_NAMES.get(gua_num, '未知')

    return {
        'gua_name': gua_name,
        'group': group,
        'gua_num': gua_num,
    }


# ═══════════════════════════════════════════════════════════════
# 星宿计算（二十八宿）
# ═══════════════════════════════════════════════════════════════

def _calc_xing_su(year, month, day):
    """计算二十八宿（根据公历日期）

    使用公式法计算当日值宿。
    二十八宿顺序：角亢氐房心尾箕 斗牛女虚危室壁 奎娄胃昴毕觜参 井鬼柳星张翼轸

    Returns:
        str: '心宿东方苍龙' 格式
    """
    XING_SU_LIST = [
        '角', '亢', '氐', '房', '心', '尾', '箕',
        '斗', '牛', '女', '虚', '危', '室', '壁',
        '奎', '娄', '胃', '昴', '毕', '觜', '参',
        '井', '鬼', '柳', '星', '张', '翼', '轸'
    ]
    # 四象分组
    SI_XIANG = {
        0: '东方苍龙', 1: '北方玄武', 2: '西方白虎', 3: '南方朱雀'
    }

    # 简化的二十八宿计算（使用公历日期推算）
    # 基于28日周期循环，以2000年1月7日=角宿为基准
    import datetime as _dt
    base = _dt.date(2000, 1, 7)  # 角宿
    target = _dt.date(year, month, day)
    delta = (target - base).days
    idx = delta % 28
    su_name = XING_SU_LIST[idx]
    group_idx = idx // 7
    group_name = SI_XIANG[group_idx]

    return f'{su_name}宿{group_name}'


# ═══════════════════════════════════════════════════════════════
# 袁天罡称骨算命
# ═══════════════════════════════════════════════════════════════

def _calc_cheng_gu(four_pillars):
    """袁天罡称骨算命

    根据四柱干支的骨重计算总重量和判词。

    Returns:
        dict: {'weight': '四两二钱', 'weight_gram': 42, 'poem': '判词'}
    """
    # 天干骨重（单位：钱，1两=10钱）
    GAN_WEIGHT = {
        '甲': 1.2, '乙': 1.2, '丙': 1.6, '丁': 1.6,
        '戊': 1.8, '己': 1.8, '庚': 0.8, '辛': 0.8,
        '壬': 0.7, '癸': 0.7,
    }
    # 地支骨重
    ZHI_WEIGHT = {
        '子': 1.6, '丑': 0.6, '寅': 0.7, '卯': 1.0,
        '辰': 0.9, '巳': 0.6, '午': 1.0, '未': 0.8,
        '申': 0.5, '酉': 0.6, '戌': 0.6, '亥': 0.6,
    }

    total = 0.0
    pillars = ['year', 'month', 'day', 'hour']
    details = {}
    for p in pillars:
        g = four_pillars[p]['gan']
        z = four_pillars[p]['zhi']
        gw = GAN_WEIGHT.get(g, 0)
        zw = ZHI_WEIGHT.get(z, 0)
        pw = round(gw + zw, 1)  # 修复浮点精度：0.5+0.8=1.3而非1.2999...
        total += pw
        details[p] = {'gan': g, 'gan_w': gw, 'zhi': z, 'zhi_w': zw, 'pillar_w': pw}

    # 四舍五入到0.1钱，再转换
    total_qian = round(total, 1)
    liang = int(total_qian)
    qian = round((total_qian - liang) * 10)

    # 格式化重量
    if qian == 0:
        weight_str = f'{liang}两'
    else:
        weight_str = f'{liang}两{qian}钱'

    # 判词（按两数查表）
    CHENG_GU_POEMS = {
        (2,0): '此命推来骨格轻，求谋作事事难成。妻迟子晚命中招，只好闲游度此生。',
        (2,1): '短命非业谓大凶，平生灾难事重重。凶祸频临陷逆境，终世困苦事不成。',
        (2,2): '身寒骨冷苦伶仃，此命推来行乞人。碌碌苦苦无乐日，终生孤单过一生。',
        (2,3): '此命推来骨格轻，求谋作事事难成。妻迟子晚命中招，只好闲游度此生。',
        (2,4): '此命推来福禄无，门庭困苦总难荣。六亲骨肉皆无靠，流落他乡作老翁。',
        (2,5): '此命推来祖业微，门庭营度似稀奇。六亲骨肉如冰炭，一世勤劳自把持。',
        (2,6): '平生衣禄苦中求，独自营谋事不休。离祖出门宜早计，晚来衣禄自无休。',
        (2,7): '一生作事少商量，难靠祖宗作主张。独马单枪空做去，早年晚岁总无长。',
        (2,8): '一生行事似飘蓬，祖宗产业在梦中。若不过房改名姓，也当移徒二三通。',
        (2,9): '初年不及半微尘，不及阴人不管身。若要兴旺重来过，除非借尸还魂人。',
        (3,0): '劳劳碌碌苦中求，东奔西走何日休。若使终身勤与俭，老来稍可免忧愁。',
        (3,1): '忙忙碌碌苦中求，何日云开见日头。难得祖业家可立，中年衣食渐无忧。',
        (3,2): '初年运限未曾亨，纵有功名在后成。须过四旬才可立，移居改姓始为良。',
        (3,3): '早年做事事难成，百计从劳枉费心。半世自如流水去，后来运到得黄金。',
        (3,4): '此命福气果如何，僧道门中衣禄多。离祖出家方为妙，朝晚拜佛念弥陀。',
        (3,5): '生平福量不周全，祖业根基觉少传。营事生涯宜守旧，时来衣食胜从前。',
        (3,6): '不须劳碌过平生，独自成家福不轻。早有福星常照命，任君行去百般成。',
        (3,7): '此命般般事不成，弟兄少力自孤行。虽然祖业须微有，来得明时去不明。',
        (3,8): '一身骨肉最清高，早入簧门姓氏标。待到年将三十六，蓝衫脱去换红袍。',
        (3,9): '此命终身运不通，劳劳作事尽皆空。苦心竭力成家计，到得那时在梦中。',
        (4,0): '平生衣禄是绵长，件件心中自主张。前面风霜多受过，后来必定享安康。',
        (4,1): '此命推来自不同，为人能干异凡庸。中年还有逍遥福，不比前时运未通。',
        (4,2): '得宽怀处且宽怀，何用双眉皱不开。若使中年命运济，那时名利一齐来。',
        (4,3): '为人心性最聪明，作事轩昂近贵人。衣禄一生天注定，不须劳碌是丰亨。',
        (4,4): '万事由天莫苦求，须知福禄赖前途。当年财帛非如意，晚景颠狂便不忧。',
        (4,5): '名利推来竟若何，前番辛苦后奔波。命中难养男与女，骨肉扶持也不多。',
        (4,6): '东西南北尽皆通，出姓移居更觉隆。衣禄无穷无数定，中年晚景一般同。',
        (4,7): '此命推来旺末年，妻荣子贵自怡然。平生原有滔滔福，可有财源如水源。',
        (4,8): '幼年运道未曾亨，若是蹉跎再不兴。兄弟六亲皆无靠，一身事业晚年成。',
        (4,9): '此命推来福不轻，自成自立显门庭。从来富贵人亲近，使婢差奴过一生。',
        (5,0): '为利为名终日劳，中年福禄也多遭。老来自有财星照，不比前番目下高。',
        (5,1): '一世荣华事事通，不须劳碌自然丰。弟兄叔侄皆如意，家业成时福禄宏。',
        (5,2): '一世亨通事事能，不须劳苦自然宁。宗族欣然心皆足，家道丰康百事成。',
        (5,3): '此格推来气象真，一身安泰贵人钦。聪明才学高天下，富贵荣华赛石崇。',
        (5,4): '此命推来厚且清，诗书满腹看功成。丰衣足食自然稳，正是人间有福人。',
        (5,5): '走马扬鞭争名利，少年做事费筹论。一朝福禄源源至，富贵荣华显六亲。',
        (5,6): '此格推来礼义通，一身福禄用无穷。甜酸苦辣皆尝过，滚滚财源稳且丰。',
        (5,7): '福禄丰盈万事全，一身荣耀乐天年。名扬威震人钦敬，处世逍遥似神仙。',
        (6,0): '一朝金榜快题名，显祖荣宗立大功。衣禄定然原裕足，田园财帛更丰盈。',
        (7,0): '此命推来福禄宏，不须愁虑苦劳心。一生天定衣与禄，富贵荣华主一生。',
    }

    # 查找判词
    poem = CHENG_GU_POEMS.get((liang, qian), '')
    if not poem:
        # 找最接近的
        for k in sorted(CHENG_GU_POEMS.keys()):
            if k[0] == liang and k[1] <= qian:
                poem = CHENG_GU_POEMS[k]
        if not poem:
            poem = CHENG_GU_POEMS.get((liang, 0), '命理玄妙，不可尽言。')

    return {
        'weight': weight_str,
        'weight_gram': total_qian,
        'poem': poem,
        'details': details,
    }


# ═══════════════════════════════════════════════════════════════
# 干支关系计算（天干合冲 + 地支合冲刑害破）
# ═══════════════════════════════════════════════════════════════

def _calc_ganzhi_relations(four_pillars):
    """计算四柱内部的干支关系：天干合/冲、地支三合/六合/三刑/六冲/六害/六破"""
    pillars = ['year', 'month', 'day', 'hour']
    gans = [four_pillars[p]['gan'] for p in pillars]
    zhis = [four_pillars[p]['zhi'] for p in pillars]

    relations = {
        'gan_he': [],       # 天干五合
        'gan_chong': [],    # 天干相冲
        'zhi_liu_he': [],   # 地支六合
        'zhi_san_he': [],   # 地支三合
        'zhi_ban_he': [],   # 地支半合
        'zhi_an_he': [],    # 地支暗合
        'zhi_san_hui': [],  # 地支三会
        'zhi_liu_chong': [],# 地支六冲
        'zhi_san_xing': [], # 地支三刑
        'zhi_liu_hai': [],  # 地支六害
        'zhi_liu_po': [],   # 地支六破
    }

    # ── 天干五合 ──
    # 甲己合土、乙庚合金、丙辛合水、丁壬合木、戊癸合火
    GAN_HE = {
        frozenset({'甲','己'}): '合化土',
        frozenset({'乙','庚'}): '合化金',
        frozenset({'丙','辛'}): '合化水',
        frozenset({'丁','壬'}): '合化木',
        frozenset({'戊','癸'}): '合化火',
    }
    for i in range(len(gans)):
        for j in range(i+1, len(gans)):
            pair = frozenset({gans[i], gans[j]})
            if pair in GAN_HE:
                relations['gan_he'].append({
                    'from': pillars[i], 'to': pillars[j],
                    'gan1': gans[i], 'gan2': gans[j],
                    'desc': f'{gans[i]}{gans[j]}{GAN_HE[pair]}'
                })

    # ── 天干相冲 ──
    # 甲庚冲、乙辛冲、丙壬冲、丁癸冲（戊己居中不冲）
    GAN_CHONG = {
        frozenset({'甲','庚'}), frozenset({'乙','辛'}),
        frozenset({'丙','壬'}), frozenset({'丁','癸'}),
    }
    for i in range(len(gans)):
        for j in range(i+1, len(gans)):
            pair = frozenset({gans[i], gans[j]})
            if pair in GAN_CHONG:
                relations['gan_chong'].append({
                    'from': pillars[i], 'to': pillars[j],
                    'gan1': gans[i], 'gan2': gans[j],
                    'desc': f'{gans[i]}{gans[j]}相冲'
                })

    # ── 地支六合 ──
    ZHI_LIU_HE = {
        frozenset({'子','丑'}): '合化土',
        frozenset({'寅','亥'}): '合化木',
        frozenset({'卯','戌'}): '合化火',
        frozenset({'辰','酉'}): '合化金',
        frozenset({'巳','申'}): '合化水',
        frozenset({'午','未'}): '合化土',
    }
    for i in range(len(zhis)):
        for j in range(i+1, len(zhis)):
            pair = frozenset({zhis[i], zhis[j]})
            if pair in ZHI_LIU_HE:
                relations['zhi_liu_he'].append({
                    'from': pillars[i], 'to': pillars[j],
                    'zhi1': zhis[i], 'zhi2': zhis[j],
                    'desc': f'{zhis[i]}{zhis[j]}{ZHI_LIU_HE[pair]}'
                })

    # ── 地支三合 ──
    ZHI_SAN_HE = [
        ({'申','子','辰'}, '水局'),
        ({'亥','卯','未'}, '木局'),
        ({'寅','午','戌'}, '火局'),
        ({'巳','酉','丑'}, '金局'),
    ]
    zhi_set = set(zhis)
    for trio, ju in ZHI_SAN_HE:
        present = trio & zhi_set
        if len(present) >= 2:
            involved = sorted([(pillars[k], zhis[k]) for k in range(4) if zhis[k] in trio],
                              key=lambda x: pillars.index(x[0]))
            if len(involved) >= 2:
                relations['zhi_san_he'].append({
                    'pillars': [x[0] for x in involved],
                    'zhis': [x[1] for x in involved],
                    'ju': ju,
                    'desc': f'{" ".join(x[1] for x in involved)} 三合{ju}'
                })

    # ── 地支六冲 ──
    ZHI_LIU_CHONG = {
        frozenset({'子','午'}), frozenset({'丑','未'}),
        frozenset({'寅','申'}), frozenset({'卯','酉'}),
        frozenset({'辰','戌'}), frozenset({'巳','亥'}),
    }
    for i in range(len(zhis)):
        for j in range(i+1, len(zhis)):
            pair = frozenset({zhis[i], zhis[j]})
            if pair in ZHI_LIU_CHONG:
                relations['zhi_liu_chong'].append({
                    'from': pillars[i], 'to': pillars[j],
                    'zhi1': zhis[i], 'zhi2': zhis[j],
                    'desc': f'{zhis[i]}{zhis[j]}相冲'
                })

    # ── 地支半合 ──
    # 三合局中的任意两个地支组合（含长生+帝旺、长生+墓库、帝旺+墓库）
    ZHI_BAN_HE = [
        # 申子辰水局：申子半合水、子辰半合水、申辰半合水
        ({'申','子'}, '半合水局'), ({'子','辰'}, '半合水局'), ({'申','辰'}, '半合水局'),
        # 亥卯未木局：亥卯半合木、卯未半合木、亥未半合木
        ({'亥','卯'}, '半合木局'), ({'卯','未'}, '半合木局'), ({'亥','未'}, '半合木局'),
        # 寅午戌火局：寅午半合火、午戌半合火、寅戌半合火
        ({'寅','午'}, '半合火局'), ({'午','戌'}, '半合火局'), ({'寅','戌'}, '半合火局'),
        # 巳酉丑金局：巳酉半合金、酉丑半合金、巳丑半合金
        ({'巳','酉'}, '半合金局'), ({'酉','丑'}, '半合金局'), ({'巳','丑'}, '半合金局'),
    ]
    for pair_set, ju_desc in ZHI_BAN_HE:
        for i in range(len(zhis)):
            for j in range(i+1, len(zhis)):
                if frozenset({zhis[i], zhis[j]}) == frozenset(pair_set):
                    # 排除已构成完整三合的半合关系（三合优先级更高）
                    # 检查是否存在对应的三合局
                    san_he_zhis = None
                    for trio, trio_ju in ZHI_SAN_HE:
                        if pair_set.issubset(trio):
                            san_he_zhis = trio
                            break
                    # 如果三合局中所有三个地支都在四柱中，则此半合被三合覆盖，跳过
                    if san_he_zhis and san_he_zhis.issubset(zhi_set):
                        continue
                    relations['zhi_ban_he'].append({
                        'from': pillars[i], 'to': pillars[j],
                        'zhi1': zhis[i], 'zhi2': zhis[j],
                        'desc': f'{zhis[i]}{zhis[j]}{ju_desc}'
                    })

    # ── 地支暗合 ──
    # 暗合：寅丑暗合、巳酉暗合、午亥暗合
    # （也有说法只取寅丑和巳酉，这里取最常见的三种）
    ZHI_AN_HE = {
        frozenset({'寅','丑'}): '暗合',
        frozenset({'巳','酉'}): '暗合',
        frozenset({'午','亥'}): '暗合',
    }
    for i in range(len(zhis)):
        for j in range(i+1, len(zhis)):
            pair = frozenset({zhis[i], zhis[j]})
            if pair in ZHI_AN_HE:
                relations['zhi_an_he'].append({
                    'from': pillars[i], 'to': pillars[j],
                    'zhi1': zhis[i], 'zhi2': zhis[j],
                    'desc': f'{zhis[i]}{zhis[j]}暗合'
                })

    # ── 地支三会 ──
    # 三会局：同一季节的三个地支聚在一起，力量最强
    # 寅卯辰三会木局、巳午未三会火局、申酉戌三会金局、亥子丑三会水局
    ZHI_SAN_HUI = [
        ({'寅','卯','辰'}, '木局'),
        ({'巳','午','未'}, '火局'),
        ({'申','酉','戌'}, '金局'),
        ({'亥','子','丑'}, '水局'),
    ]
    for trio, ju in ZHI_SAN_HUI:
        present = trio & zhi_set
        if len(present) >= 2:
            involved = sorted([(pillars[k], zhis[k]) for k in range(4) if zhis[k] in trio],
                              key=lambda x: pillars.index(x[0]))
            if len(involved) >= 2:
                is_full = len(present) == 3
                hui_desc = f'三会{ju}' if is_full else f'三会{ju}(缺{"".join(trio - present)})'
                relations['zhi_san_hui'].append({
                    'pillars': [x[0] for x in involved],
                    'zhis': [x[1] for x in involved],
                    'ju': ju,
                    'full': is_full,
                    'desc': f'{" ".join(x[1] for x in involved)} {hui_desc}'
                })

    # ── 地支三刑 ──
    # 寅巳申 无恩之刑, 丑戌未 恃势之刑, 子卯 无礼之刑, 辰辰/午午/酉酉/亥亥 自刑
    ZHI_SAN_XING = [
        ({'寅','巳','申'}, '无恩之刑'),
        ({'丑','戌','未'}, '恃势之刑'),
        ({'子','卯'}, '无礼之刑'),
    ]
    ZHI_ZI_XING = {'辰':'辰', '午':'午', '酉':'酉', '亥':'亥'}

    for trio, xing_name in ZHI_SAN_XING:
        present = trio & zhi_set
        if len(present) >= 2:
            involved = sorted([(pillars[k], zhis[k]) for k in range(4) if zhis[k] in trio],
                              key=lambda x: pillars.index(x[0]))
            if len(involved) >= 2:
                relations['zhi_san_xing'].append({
                    'pillars': [x[0] for x in involved],
                    'zhis': [x[1] for x in involved],
                    'xing': xing_name,
                    'desc': f'{" ".join(x[1] for x in involved)} {xing_name}'
                })

    # 自刑
    for i in range(len(zhis)):
        for j in range(i+1, len(zhis)):
            if zhis[i] == zhis[j] and zhis[i] in ZHI_ZI_XING:
                relations['zhi_san_xing'].append({
                    'pillars': [pillars[i], pillars[j]],
                    'zhis': [zhis[i], zhis[j]],
                    'xing': '自刑',
                    'desc': f'{zhis[i]}{zhis[j]} 自刑'
                })

    # ── 地支六害 ──
    ZHI_LIU_HAI = {
        frozenset({'子','未'}), frozenset({'丑','午'}),
        frozenset({'寅','巳'}), frozenset({'卯','辰'}),
        frozenset({'申','亥'}), frozenset({'酉','戌'}),
    }
    for i in range(len(zhis)):
        for j in range(i+1, len(zhis)):
            pair = frozenset({zhis[i], zhis[j]})
            if pair in ZHI_LIU_HAI:
                relations['zhi_liu_hai'].append({
                    'from': pillars[i], 'to': pillars[j],
                    'zhi1': zhis[i], 'zhi2': zhis[j],
                    'desc': f'{zhis[i]}{zhis[j]}相害'
                })

    # ── 地支六破 ──
    ZHI_LIU_PO = {
        frozenset({'子','酉'}), frozenset({'丑','辰'}),
        frozenset({'寅','亥'}), frozenset({'卯','午'}),
        frozenset({'巳','申'}), frozenset({'未','戌'}),
    }
    for i in range(len(zhis)):
        for j in range(i+1, len(zhis)):
            pair = frozenset({zhis[i], zhis[j]})
            if pair in ZHI_LIU_PO:
                relations['zhi_liu_po'].append({
                    'from': pillars[i], 'to': pillars[j],
                    'zhi1': zhis[i], 'zhi2': zhis[j],
                    'desc': f'{zhis[i]}{zhis[j]}相破'
                })

    return relations


def calc_ganzhi_relation_with_pillars(ext_gan, ext_zhi, four_pillars):
    """计算外部干支(大运/流年)与原局四柱的冲合关系

    Args:
        ext_gan: 外部天干（大运/流年天干）
        ext_zhi: 外部地支（大运/流年地支）
        four_pillars: 原局四柱

    Returns:
        dict: {'gan_he': [...], 'gan_chong': [...], 'zhi_liu_he': [...],
               'zhi_liu_chong': [...], 'zhi_liu_hai': [...], 'zhi_liu_po': [...]}
    """
    pillars = ['year', 'month', 'day', 'hour']
    gans = [four_pillars[p]['gan'] for p in pillars]
    zhis = [four_pillars[p]['zhi'] for p in pillars]

    rels = {
        'gan_he': [],
        'gan_chong': [],
        'zhi_liu_he': [],
        'zhi_liu_chong': [],
        'zhi_liu_hai': [],
        'zhi_liu_po': [],
    }

    # ── 天干五合 ──
    GAN_HE = {
        frozenset({'甲','己'}): '合化土', frozenset({'乙','庚'}): '合化金',
        frozenset({'丙','辛'}): '合化水', frozenset({'丁','壬'}): '合化木',
        frozenset({'戊','癸'}): '合化火',
    }
    for i, pg in enumerate(gans):
        pair = frozenset({ext_gan, pg})
        if pair in GAN_HE:
            rels['gan_he'].append({
                'pillar': pillars[i], 'gan': pg,
                'desc': f'{ext_gan}{pg}{GAN_HE[pair]}'
            })

    # ── 天干相冲 ──
    GAN_CHONG = {
        frozenset({'甲','庚'}), frozenset({'乙','辛'}),
        frozenset({'丙','壬'}), frozenset({'丁','癸'}),
    }
    for i, pg in enumerate(gans):
        pair = frozenset({ext_gan, pg})
        if pair in GAN_CHONG:
            rels['gan_chong'].append({
                'pillar': pillars[i], 'gan': pg,
                'desc': f'{ext_gan}{pg}相冲'
            })

    # ── 地支六合 ──
    ZHI_LIU_HE = {
        frozenset({'子','丑'}): '合化土', frozenset({'寅','亥'}): '合化木',
        frozenset({'卯','戌'}): '合化火', frozenset({'辰','酉'}): '合化金',
        frozenset({'巳','申'}): '合化水', frozenset({'午','未'}): '合化土',
    }
    for i, pz in enumerate(zhis):
        pair = frozenset({ext_zhi, pz})
        if pair in ZHI_LIU_HE:
            rels['zhi_liu_he'].append({
                'pillar': pillars[i], 'zhi': pz,
                'desc': f'{ext_zhi}{pz}{ZHI_LIU_HE[pair]}'
            })

    # ── 地支六冲 ──
    ZHI_LIU_CHONG = {
        frozenset({'子','午'}), frozenset({'丑','未'}),
        frozenset({'寅','申'}), frozenset({'卯','酉'}),
        frozenset({'辰','戌'}), frozenset({'巳','亥'}),
    }
    for i, pz in enumerate(zhis):
        pair = frozenset({ext_zhi, pz})
        if pair in ZHI_LIU_CHONG:
            rels['zhi_liu_chong'].append({
                'pillar': pillars[i], 'zhi': pz,
                'desc': f'{ext_zhi}{pz}相冲'
            })

    # ── 地支六害 ──
    ZHI_LIU_HAI = {
        frozenset({'子','未'}), frozenset({'丑','午'}),
        frozenset({'寅','巳'}), frozenset({'卯','辰'}),
        frozenset({'申','亥'}), frozenset({'酉','戌'}),
    }
    for i, pz in enumerate(zhis):
        pair = frozenset({ext_zhi, pz})
        if pair in ZHI_LIU_HAI:
            rels['zhi_liu_hai'].append({
                'pillar': pillars[i], 'zhi': pz,
                'desc': f'{ext_zhi}{pz}相害'
            })

    # ── 地支六破 ──
    ZHI_LIU_PO = {
        frozenset({'子','酉'}), frozenset({'丑','辰'}),
        frozenset({'寅','亥'}), frozenset({'卯','午'}),
        frozenset({'巳','申'}), frozenset({'未','戌'}),
    }
    for i, pz in enumerate(zhis):
        pair = frozenset({ext_zhi, pz})
        if pair in ZHI_LIU_PO:
            rels['zhi_liu_po'].append({
                'pillar': pillars[i], 'zhi': pz,
                'desc': f'{ext_zhi}{pz}相破'
            })

    return rels
# ═══════════════════════════════════════════════════════════════

def _calc_geju(four_pillars, shi_shen, cang_gan_shi_shen):
    """根据月支藏干透出情况判断格局
    
    传统命理格局判断规则：
    1. 建禄格/羊刃格：月支为日干之禄/刃
    2. 正格判断：月支藏干透出哪个天干就取哪个格局
    3. 透出优先级：
       a. 月干 = 月支藏干之一 → 该藏干以月干形式透出（月令司权，最有力）
       b. 藏干在年干/时干中出现 → 该藏干透出
       c. 藏干虽未透出，但月令本气司权，可直接定格局（次优先级）
    4. 藏干优先级：本气 > 中气 > 余气
    """
    day_gan = four_pillars['day']['gan']
    month_gan = four_pillars['month']['gan']
    month_zhi = four_pillars['month']['zhi']

    # 月支藏干列表（本气、中气、余气）
    cang_gan_list = CANG_GAN.get(month_zhi, [])

    # 特殊月支判断（建禄格/羊刃格）
    # 禄：日干在月支的禄位 → 建禄格
    # 刃：日干在月支的刃位 → 羊刃格（仅阳干有刃）
    GAN_LU = {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}
    GAN_REN = {'甲':'卯','丙':'午','戊':'午','庚':'酉','壬':'子'}  # 羊刃（仅阳干）

    if month_zhi == GAN_LU.get(day_gan):
        return {'geju': '建禄格', 'desc': '月支为日干之禄，不入正格，为建禄格'}
    if day_gan in GAN_REN and month_zhi == GAN_REN[day_gan]:
        return {'geju': '羊刃格', 'desc': '月支为日干之刃，不入正格，为羊刃格'}

    # 正格判断：月支藏干透出哪个天干就取哪个格局
    # 取透出的十神定格局名
    # 注意：SHI_SHEN_MAP 使用"偏官"，格局名使用"七杀格"，两者等价
    GEJU_NAME = {
        '正官': '正官格', '七杀': '七杀格', '偏官': '七杀格',
        '正财': '正财格', '偏财': '偏财格',
        '正印': '正印格', '偏印': '偏印格',
        '食神': '食神格', '伤官': '伤官格',
    }

    # ── 第一层：月干透出判断 ──
    # 月干本身就是月令藏干透出的通道。若月干存在于月支藏干列表中，
    # 则月干所对应的藏干视为"月干透出"，月令司权最为有力
    if month_gan in cang_gan_list and month_gan != day_gan:
        ss = calc_shi_shen_for_gan(day_gan, month_gan)
        if ss in GEJU_NAME:
            return {'geju': GEJU_NAME[ss], 'desc': f'月支{month_zhi}藏干{month_gan}以月干透出，{ss}当权'}

    # ── 第二层：年干/时干透出判断 ──
    # 获取年干和时干（排除日干自身和月干已在第一层处理）
    other_gans = []
    for p in ['year', 'hour']:
        g = four_pillars[p]['gan']
        if g != day_gan and g != month_gan:
            other_gans.append(g)

    # 对月支藏干按优先级（本气>中气>余气）检查在年干/时干中透出
    for cg in cang_gan_list:
        if cg == day_gan:
            continue
        if cg in other_gans:
            ss = calc_shi_shen_for_gan(day_gan, cg)
            if ss in GEJU_NAME:
                # 确定透出位置
                pos = []
                if four_pillars['year']['gan'] == cg:
                    pos.append('年干')
                if four_pillars['hour']['gan'] == cg:
                    pos.append('时干')
                return {'geju': GEJU_NAME[ss], 'desc': f'月支{month_zhi}藏干{cg}透于{"".join(pos)}，{ss}当权'}

    # ── 第三层：月令本气司权（未透出仍可定格局）──
    # 传统命理认为月令为八字提纲，月支本气司权即可定格局，
    # 即使藏干未透出四柱天干，月令本气的十神仍然有效
    if cang_gan_list:
        # 优先本气
        ben_qi = cang_gan_list[0]
        if ben_qi != day_gan:
            ss = calc_shi_shen_for_gan(day_gan, ben_qi)
            if ss in GEJU_NAME:
                return {'geju': GEJU_NAME[ss], 'desc': f'月支{month_zhi}本气{ben_qi}司权，{ss}当权（未透出）'}
        # 本气为比劫时，取中气
        if len(cang_gan_list) > 1:
            zhong_qi = cang_gan_list[1]
            if zhong_qi != day_gan:
                ss = calc_shi_shen_for_gan(day_gan, zhong_qi)
                if ss in GEJU_NAME:
                    return {'geju': GEJU_NAME[ss], 'desc': f'月支{month_zhi}中气{zhong_qi}司权，{ss}当权（本气为比劫，未透出）'}
        # 中气也为比劫时，取余气
        if len(cang_gan_list) > 2:
            yu_qi = cang_gan_list[2]
            if yu_qi != day_gan:
                ss = calc_shi_shen_for_gan(day_gan, yu_qi)
                if ss in GEJU_NAME:
                    return {'geju': GEJU_NAME[ss], 'desc': f'月支{month_zhi}余气{yu_qi}司权，{ss}当权（本气中气为比劫，未透出）'}

    return {'geju': '普通格', 'desc': '未成特殊格局'}


# ═══════════════════════════════════════════════════════════════
# 调候用神（穷通宝鉴查表）
# ═══════════════════════════════════════════════════════════════

def _calc_tiaohou(day_gan, month_zhi):
    """根据穷通宝鉴查表，确定日干在各月的调候用神"""
    # 穷通宝鉴简表：日干 → 月支 → (用神, 喜神, 忌神)
    # 数据来源：传统命理学穷通宝鉴经典口诀
    TIAOHOU = {
        '甲': {
            '寅': ('丙','癸','庚'), '卯': ('庚','丙','辛'), '辰': ('庚','壬','丙'),
            '巳': ('癸','丙','庚'), '午': ('癸','丁','丙'), '未': ('癸','丙','丁'),
            '申': ('庚','丙','丁'), '酉': ('庚','丙','丁'), '戌': ('庚','壬','丙'),
            '亥': ('庚','丙','丁'), '子': ('庚','丙','丁'), '丑': ('庚','丙','丁'),
        },
        '乙': {
            '寅': ('丙','癸','辛'), '卯': ('丙','癸','庚'), '辰': ('癸','丙','辛'),
            '巳': ('癸','丙','辛'), '午': ('癸','丙','辛'), '未': ('癸','丙','辛'),
            '申': ('丙','癸','庚'), '酉': ('丙','癸','庚'), '戌': ('癸','丙','辛'),
            '亥': ('丙','戊','庚'), '子': ('丙','戊','庚'), '丑': ('丙','戊','庚'),
        },
        '丙': {
            '寅': ('壬','己','辛'), '卯': ('壬','己','辛'), '辰': ('壬','己','辛'),
            '巳': ('壬','庚','己'), '午': ('壬','庚','己'), '未': ('壬','庚','己'),
            '申': ('壬','庚','辛'), '酉': ('壬','辛','庚'), '戌': ('壬','辛','庚'),
            '亥': ('甲','壬','癸'), '子': ('甲','壬','癸'), '丑': ('甲','壬','癸'),
        },
        '丁': {
            '寅': ('甲','庚','壬'), '卯': ('甲','庚','壬'), '辰': ('甲','庚','壬'),
            '巳': ('甲','壬','癸'), '午': ('甲','壬','癸'), '未': ('甲','壬','癸'),
            '申': ('甲','庚','壬'), '酉': ('甲','庚','壬'), '戌': ('甲','庚','壬'),
            '亥': ('甲','庚','壬'), '子': ('甲','庚','壬'), '丑': ('甲','庚','壬'),
        },
        '戊': {
            '寅': ('丙','甲','壬'), '卯': ('丙','甲','壬'), '辰': ('甲','丙','壬'),
            '巳': ('甲','丙','壬'), '午': ('壬','甲','丙'), '未': ('壬','甲','丙'),
            '申': ('丙','癸','甲'), '酉': ('丙','癸','甲'), '戌': ('甲','丙','壬'),
            '亥': ('甲','丙','壬'), '子': ('甲','丙','壬'), '丑': ('甲','丙','壬'),
        },
        '己': {
            '寅': ('丙','甲','壬'), '卯': ('丙','甲','壬'), '辰': ('甲','丙','壬'),
            '巳': ('癸','丙','甲'), '午': ('癸','丙','甲'), '未': ('癸','丙','甲'),
            '申': ('丙','癸','甲'), '酉': ('丙','癸','甲'), '戌': ('甲','丙','壬'),
            '亥': ('丙','甲','壬'), '子': ('丙','甲','壬'), '丑': ('丙','甲','壬'),
        },
        '庚': {
            '寅': ('丁','甲','壬'), '卯': ('丁','甲','壬'), '辰': ('丁','甲','壬'),
            '巳': ('壬','丁','丙'), '午': ('壬','己','丁'), '未': ('壬','丁','丙'),
            '申': ('丁','甲','壬'), '酉': ('丁','甲','壬'), '戌': ('丁','甲','壬'),
            '亥': ('丁','甲','丙'), '子': ('丁','甲','丙'), '丑': ('丁','甲','丙'),
        },
        '辛': {
            '寅': ('壬','甲','丙'), '卯': ('壬','甲','丙'), '辰': ('壬','甲','丙'),
            '巳': ('壬','己','丙'), '午': ('壬','己','丙'), '未': ('壬','甲','丙'),
            '申': ('壬','甲','丙'), '酉': ('壬','甲','丙'), '戌': ('壬','甲','丙'),
            '亥': ('丙','壬','甲'), '子': ('丙','壬','甲'), '丑': ('丙','壬','甲'),
        },
        '壬': {
            '寅': ('甲','丙','戊'), '卯': ('甲','丙','戊'), '辰': ('甲','庚','戊'),
            '巳': ('壬','辛','戊'), '午': ('壬','辛','戊'), '未': ('壬','辛','戊'),
            '申': ('甲','丙','戊'), '酉': ('甲','丙','戊'), '戌': ('甲','丙','戊'),
            '亥': ('戊','丙','甲'), '子': ('戊','丙','甲'), '丑': ('丙','甲','戊'),
        },
        '癸': {
            '寅': ('辛','丙','戊'), '卯': ('辛','丙','戊'), '辰': ('辛','丙','戊'),
            '巳': ('辛','丙','戊'), '午': ('辛','庚','戊'), '未': ('辛','丙','戊'),
            '申': ('丁','丙','戊'), '酉': ('丁','丙','戊'), '戌': ('辛','丙','戊'),
            '亥': ('戊','丙','辛'), '子': ('戊','丙','辛'), '丑': ('丙','丁','戊'),
        },
    }

    gan_data = TIAOHOU.get(day_gan, {})
    yong_shen, xi_shen, ji_shen = gan_data.get(month_zhi, ('','',''))

    return {
        'yong_shen': yong_shen,
        'xi_shen': xi_shen,
        'ji_shen': ji_shen,
        'desc': f'日干{day_gan}生于{month_zhi}月，调候用神为{yong_shen}，喜{xi_shen}，忌{ji_shen}' if yong_shen else ''
    }


# ═══════════════════════════════════════════════════════════════
# 古籍参考
# ═══════════════════════════════════════════════════════════════

def _calc_guji_refs(day_gan, month_zhi, geju_result):
    """根据日干、月支、格局匹配相关古籍条文

    返回:
        list of dict: [{source, title, text, match_type}, ...]
    """
    refs = []

    # ── 1. 穷通宝鉴调候条文 ──
    # 按日干×月支匹配，精选核心条文（120条中的重点条文）
    QIANTONG_REFS = {
        # 甲木
        ('甲', '寅'): '甲木生于寅月：用丙火暖局，取癸水润泽。寅月甲木初生，阳气渐升，先用丙火照暖，次用癸水滋培。若丙癸两透，科甲定然。',
        ('甲', '卯'): '甲木生于卯月：阳刃之地，先用庚金修剪，次用丙火暖局。卯月甲木最旺，无庚则木多无制，必用庚金制之。庚丙两透，富贵双全。',
        ('甲', '辰'): '甲木生于辰月：余寒未尽，先用庚金辟土，次用壬水润泽。辰月土旺，甲木有埋根之患，必用庚金制土为上。',
        ('甲', '巳'): '甲木生于巳月：火旺木衰，先用癸水制火润木，次用丙火为助。巳月火炎土燥，甲木枯焦，急用癸水解炎。',
        ('甲', '午'): '甲木生于午月：火炎土燥，先用癸水制火，次用丁火泄秀。午月甲木最弱，癸水为第一用神。',
        ('甲', '未'): '甲木生于未月：土旺木折，先用癸水润泽，次用丙火暖局。未月土旺，甲木需癸水养根。',
        ('甲', '申'): '甲木生于申月：金旺木伤，先用庚金制之反成栋梁，次用丙火制金。申月庚金七杀当令，有丙火制之则化杀为权。',
        ('甲', '酉'): '甲木生于酉月：金旺克木，先用庚金修剪成器，次用丙丁火制金。酉月正官当令，甲木需丙丁火配合。',
        ('甲', '戌'): '甲木生于戌月：土旺用庚，次用壬水。戌月土厚，甲木需庚金疏土、壬水润泽。',
        ('甲', '亥'): '甲木生于亥月：水旺木浮，先用庚金制水，次用丙火暖局。亥月水旺，甲木有漂泊之患。',
        ('甲', '子'): '甲木生于子月：水冷木寒，先用庚金，次用丙丁火暖局。子月冰寒，甲木全赖丙火照暖。',
        ('甲', '丑'): '甲木生于丑月：寒土用庚丙，次用壬水。丑月寒极，甲木需丙火解冻、庚金制疏。',
        # 丙火
        ('丙', '寅'): '丙火生于寅月：印绶当令，先用壬水取贵，次用己土制水。寅月丙火长生，壬水为用则水火既济。',
        ('丙', '午'): '丙火生于午月：火炎极盛，必用壬水制火，次用庚金生水。午月火旺至极，壬庚并透方为大贵。',
        # 庚金
        ('庚', '午'): '庚金生于午月：火旺金熔，必用壬水制火存金，次用己土生金。午月丁火当权，壬水为救金之第一用神。',
        # 辛金
        ('辛', '午'): '辛金生于午月：丁火七杀当权，先用壬水制杀，次用己土生身。午月辛金最弱，壬水制火为第一要务，己土生金为辅。',
        ('辛', '巳'): '辛金生于巳月：丙火正官当令，先用壬水淘洗，次用己土生身。巳月火旺，壬水既制火又洗金，金白水清为美。',
        ('辛', '寅'): '辛金生于寅月：木旺金衰，先用壬水泄金生木，次用甲木引从。寅月辛金休囚，壬甲并用则秀气流行。',
        # 壬水
        ('壬', '午'): '壬水生于午月：火旺水衰，先用壬水助身，次用辛金发水源。午月财旺，壬水需辛金生助方可任财。',
        # 癸水
        ('癸', '午'): '癸水生于午月：火炎水弱，先用辛金生水，次用庚金助之。午月癸水至弱，全赖金生方存。',
    }

    qt_key = (day_gan, month_zhi)
    if qt_key in QIANTONG_REFS:
        refs.append({
            'source': '穷通宝鉴',
            'title': (f'{day_gan}木' if day_gan in '甲乙' else f'{day_gan}火' if day_gan in '丙丁' else f'{day_gan}土' if day_gan in '戊己' else f'{day_gan}金' if day_gan in '庚辛' else f'{day_gan}水') + f'生于{month_zhi}月',
            'text': QIANTONG_REFS[qt_key],
            'match_type': 'tiaohou',
        })

    # ── 2. 三命通会 ──
    # 按格局匹配
    SAN_MING_REFS = {
        '正官格': '《三命通会》论正官：正官者，乃阴阳相配合之理。甲木见辛金，乙木见庚金，阴阳相配，如君臣上下，各得其宜。正官须在月令生旺，最忌伤官破格。若正官纯一不杂，无冲无破，主为人端厚有威，文章清秀。',
        '七杀格': '《三命通会》论偏官：偏官者，乃阳克阳、阴克阴之谓。甲木见庚金，乙木见辛金，同性相克，如敌国之君。偏官喜制伏，制之则为权柄，无制则多凶险。食神制杀为上，印绶化杀次之。',
        '正印格': '《三命通会》论正印：正印者，乃生我之物。甲木见癸水，乙木见壬水，异性相生，如慈母育子。正印主聪明多智，文章振发，为官清廉。最忌财星坏印，若印绶有官相生，主大贵。',
        '偏印格': '《三命通会》论偏印：偏印者，同性相生，甲木见壬水，乙木见癸水。偏印又曰枭神，有食则枭来夺食为忌，无食则偏印亦可取贵。偏印主人机智，善于变通，但多疑虑。',
        '正财格': '《三命通会》论正财：正财者，阴阳相克而为我所克之物。甲木见己土，乙木见戊土。正财主勤俭致富，为人实在。财喜食伤相生，忌比劫分夺。财旺身强则大富，财多身弱反为祸。',
        '偏财格': '《三命通会》论偏财：偏财者，同性相克。甲木见戊土，乙木见己土。偏财主慷慨大方，人缘广结，多意外之财。偏财喜身旺，忌比劫争夺，身旺财旺主大富。',
        '食神格': '《三命通会》论食神：食神者，我生之同性。甲木见丙火，乙木见丁火。食神主秀气发越，才华出众，有口福。食神制杀为上格，食神生财为富命。最忌枭神夺食。',
        '伤官格': '《三命通会》论伤官：伤官者，我生之异性。甲木见丁火，乙木见丙火。伤官主人聪明傲物，才华横溢而多是非。伤官配印则化凶为吉，伤官见官则为祸百端。金水伤官要见官，火土伤官忌见官。',
        '建禄格': '《三命通会》论建禄：建禄者，月支为日干之禄。禄者，养命之源。甲禄寅，乙禄卯，丙禄巳，丁禄午，戊禄巳，己禄午，庚禄申，辛禄酉，壬禄亥，癸禄子。建禄虽非正格，若官星财星得地，亦可取贵。',
        '羊刃格': '《三命通会》论羊刃：羊刃者，禄前一位，唯阳干有之。甲刃卯，丙刃午，戊刃午，庚刃酉，壬刃子。羊刃刚烈，喜官杀制之，则化为权柄。刃旺无制，主性刚暴戾。杀刃两全，为将帅之才。',
    }

    geju_name = geju_result.get('geju', '')
    if geju_name in SAN_MING_REFS:
        refs.append({
            'source': '三命通会',
            'title': f'论{geju_name}',
            'text': SAN_MING_REFS[geju_name],
            'match_type': 'geju',
        })

    # ── 3. 滴天髓 ──
    # 按日干五行匹配（精要条文）
    DI_TIAN_SUI_REFS = {
        '甲': '《滴天髓》论甲木：甲木参天，脱胎要火。春不容金，秋不容土。火炽乘龙，水荡骑虎。地润天和，植立千古。',
        '乙': '《滴天髓》论乙木：乙木虽柔，刲羊解牛。怀丁抱丙，跨凤乘猴。虚湿之地，骑马亦忧。藤罗系甲，可春可秋。',
        '丙': '《滴天髓》论丙火：丙火猛烈，欺霜侮雪。锻庚逐辛，性凡体刚。壬水交加，丙必遭克。己土混杂，丙必失光。',
        '丁': '《滴天髓》论丁火：丁火柔中，内性昭融。抱乙而孝，合壬而忠。旺而不烈，衰而不穷。如有嫡母，可秋可冬。',
        '戊': '《滴天髓》论戊土：戊土固重，既中且正。静翕动辟，万物司命。水润物生，火燥物病。若在艮坤，怕冲宜静。',
        '己': '《滴天髓》论己土：己土卑湿，中正蓄藏。不愁木盛，不畏水狂。火少火晦，金多金光。若要物旺，宜助宜帮。',
        '庚': '《滴天髓》论庚金：庚金带杀，刚健为最。得水而清，得火而锐。土润则生，土干则脆。能赢甲兄，输于乙妹。',
        '辛': '《滴天髓》论辛金：辛金软弱，温润而清。畏土之叠，乐水之盈。能扶社稷，能救生灵。热则喜母，寒则喜丁。',
        '壬': '《滴天髓》论壬水：壬水通河，能泄金气。刚中之德，周流不滞。通根透癸，冲天奔地。化则有情，从则相济。',
        '癸': '《滴天髓》论癸水：癸水至弱，达于天津。得龙而运，功化斯神。不愁火土，不论庚辛。合戊见火，化象斯真。',
    }

    if day_gan in DI_TIAN_SUI_REFS:
        refs.append({
            'source': '滴天髓',
            'title': f'论{day_gan}木' if day_gan in '甲乙' else f'论{day_gan}火' if day_gan in '丙丁' else f'论{day_gan}土' if day_gan in '戊己' else f'论{day_gan}金' if day_gan in '庚辛' else f'论{day_gan}水',
            'text': DI_TIAN_SUI_REFS[day_gan],
            'match_type': 'day_gan',
        })

    return refs


# ═══════════════════════════════════════════════════════════════
# 快速测试
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # 测试用例1：男命，公历1990年6月15日14时，北京
    print("=" * 60)
    print("测试1: 男命 1990-06-15 14:00 北京")
    r1 = paipan('张三', '男', '199006151400', '公历', '北京')
    if r1['success']:
        fp = r1['four_pillars']
        print(f"  四柱: {fp['year']['gan_zhi']} {fp['month']['gan_zhi']} {fp['day']['gan_zhi']} {fp['hour']['gan_zhi']}")
        print(f"  纳音: {fp['year']['nayin']} {fp['month']['nayin']} {fp['day']['nayin']} {fp['hour']['nayin']}")
        print(f"  十神: {r1['shi_shen']['year_gan']} {r1['shi_shen']['month_gan']} 日主 {r1['shi_shen']['hour_gan']}")
        print(f"  五行: {r1['wu_xing']}")
        print(f"  空亡: {r1['kong_wang']}")
        print(f"  神煞: {r1['shen_sha']}")
        print(f"  旺衰: {r1['wang_shuai']}")
        print(f"  大运: {'顺' if r1['da_yun_direction']=='顺' else '逆'} 起运{r1['qi_yun_age']}岁")
        for dy in r1['da_yun'][:3]:
            print(f"    {dy['start_age']}-{dy['end_age']}岁 {dy['gan_zhi']}")
    else:
        print(f"  错误: {r1['error']}")

    print()
    print("测试2: 女命 1985-12-20 08:00 上海")
    r2 = paipan('李四', '女', '198512200800', '公历', '上海')
    if r2['success']:
        fp = r2['four_pillars']
        print(f"  四柱: {fp['year']['gan_zhi']} {fp['month']['gan_zhi']} {fp['day']['gan_zhi']} {fp['hour']['gan_zhi']}")
        print(f"  大运方向: {r2['da_yun_direction']}")

    print()
    print("测试3: 夜子时 2000-01-01 23:30 广州")
    r3 = paipan('王五', '男', '200001012330', '公历', '广州')
    if r3['success']:
        fp = r3['four_pillars']
        print(f"  四柱: {fp['year']['gan_zhi']} {fp['month']['gan_zhi']} {fp['day']['gan_zhi']} {fp['hour']['gan_zhi']}")
        print(f"  日柱不换日: 日干={fp['day']['gan']} (应为己)")


# ═══════════════════════════════════════════════════════════════
# 性格简析与命理提示
# ═══════════════════════════════════════════════════════════════

def _calc_personality(day_gan, shi_shen, shen_sha, wang_shuai_detail, gender):
    """根据日主五行、十神分布、神煞等生成简要性格分析和命理提示

    Returns:
        dict: {
            'summary': str,          # 性格概述
            'traits': [str, ...],    # 性格特征列表
            'advice': str,           # 命理提示
            'career': str,           # 事业方向
            'wealth': str,           # 财运提示
            'relationship': str,     # 感情提示
        }
    """
    day_wx = GAN_WUXING[day_gan]

    # ── 日主五行性格 ──
    WX_PERSONALITY = {
        '木': {
            'summary': '木主仁，日主属木之人性格正直，富有同情心与上进心。',
            'traits': ['仁慈宽厚', '正直向上', '乐于助人', '刚直不阿'],
            'negative': '过于固执，不善变通',
        },
        '火': {
            'summary': '火主礼，日主属火之人热情开朗，重礼尚义，善于表达。',
            'traits': ['热情开朗', '重礼守义', '表达力强', '积极进取'],
            'negative': '急躁冲动，缺乏耐性',
        },
        '土': {
            'summary': '土主信，日主属土之人诚实守信，为人稳重，善于包容。',
            'traits': ['诚实守信', '稳重踏实', '包容大度', '重情重义'],
            'negative': '过于保守，不善变通',
        },
        '金': {
            'summary': '金主义，日主属金之人刚毅果断，重义轻财，行事果敢。',
            'traits': ['刚毅果决', '重义轻财', '行事果断', '是非分明'],
            'negative': '过于刚硬，不善柔和',
        },
        '水': {
            'summary': '水主智，日主属水之人聪明灵活，善于思考，适应力强。',
            'traits': ['聪慧灵活', '善于思考', '适应力强', '足智多谋'],
            'negative': '过于多变，缺乏坚持',
        },
    }

    base = WX_PERSONALITY.get(day_wx, {
        'summary': f'日主属{day_wx}，五行调和，性格平稳。',
        'traits': ['性格平和', '处事稳健'],
        'negative': '无明显弱点',
    })

    # ── 十神特征补充 ──
    # 统计十神分布
    ss_all = []
    for p in ['year_gan', 'month_gan', 'hour_gan']:
        ss_all.append(shi_shen.get(p, ''))
    # 藏干十神也计入
    # (简化处理，只看天干十神)

    ss_traits = []
    if '正官' in ss_all or '偏官' in ss_all:
        ss_traits.append('有责任感，重视规矩')
    if '正印' in ss_all or '偏印' in ss_all:
        ss_traits.append('好学多思，重视精神')
    if '正财' in ss_all or '偏财' in ss_all:
        ss_traits.append('务实勤恳，善于理财')
    if '食神' in ss_all or '伤官' in ss_all:
        ss_traits.append('才华横溢，表达力强')
    if '比肩' in ss_all or '劫财' in ss_all:
        ss_traits.append('独立自主，重朋友义气')

    # ── 神煞影响 ──
    sha_traits = []
    if '天乙贵人' in shen_sha:
        sha_traits.append('遇事有贵人相助')
    if '文昌贵人' in shen_sha or '文昌' in shen_sha:
        sha_traits.append('文昌照命，利读书考试')
    if '驿马' in shen_sha:
        sha_traits.append('奔波走动，利外出发展')
    if '桃花' in shen_sha:
        sha_traits.append('人缘佳，异性缘旺')
    if '华盖' in shen_sha:
        sha_traits.append('喜独处思考，有艺术天赋')

    # ── 旺衰提示 ──
    strength = wang_shuai_detail.get('strength', '中和') if wang_shuai_detail else '中和'
    if strength in ('身旺', '偏旺'):
        advice = '日主偏旺，宜以财官食伤泄秀为用，不宜再助。事业宜开拓进取，可担大任。'
        career = '适合管理、领导、创业等开拓性工作。'
        wealth = '财运较旺，但需注意不宜过于贪求，宜守成为主。'
    elif strength in ('身弱', '偏弱'):
        advice = '日主偏弱，宜以印比生扶为用。事业宜稳扎稳打，不宜冒进。'
        career = '适合技术、文职、教育等稳定性工作。'
        wealth = '财运需稳健理财，不宜投机冒进，宜聚不宜散。'
    else:
        advice = '日主中和，五行较为平衡，行运顺逆皆需注意因时制宜。'
        career = '适合多种行业发展，可根据兴趣和运势选择方向。'
        wealth = '财运平稳，量入为出，不宜过度冒险。'

    # ── 感情提示 ──
    if gender == '男':
        if '正财' in ss_all or '偏财' in ss_all:
            relationship = '命中财星透出，异性缘佳，感情生活较为丰富。'
        else:
            relationship = '命中财星不显，感情方面需主动创造机会。'
    else:
        if '正官' in ss_all or '偏官' in ss_all:
            relationship = '命中官星透出，异性缘佳，感情生活较为丰富。'
        else:
            relationship = '命中官星不显，感情方面需主动创造机会。'

    return {
        'summary': base['summary'],
        'traits': base['traits'] + ss_traits[:2],
        'negative': base['negative'],
        'advice': advice,
        'career': career,
        'wealth': wealth,
        'relationship': relationship,
        'sha_hints': sha_traits[:3],
    }
