import secrets
import datetime

TAROT_IMAGE_BASE_URL = "/static/tarot/rws/"

MAJOR_IMAGE_FILES = {idx: f"m{idx:02d}.jpg" for idx in range(22)}

MINOR_SUIT_META = {
    "权杖": {"name_en": "Wands", "prefix": "w"},
    "圣杯": {"name_en": "Cups", "prefix": "c"},
    "宝剑": {"name_en": "Swords", "prefix": "s"},
    "星币": {"name_en": "Pentacles", "prefix": "p"},
}

MINOR_NUMBER_META = {
    "Ace": {"name_en": "Ace", "image_index": 1},
    "2": {"name_en": "Two", "image_index": 2},
    "3": {"name_en": "Three", "image_index": 3},
    "4": {"name_en": "Four", "image_index": 4},
    "5": {"name_en": "Five", "image_index": 5},
    "6": {"name_en": "Six", "image_index": 6},
    "7": {"name_en": "Seven", "image_index": 7},
    "8": {"name_en": "Eight", "image_index": 8},
    "9": {"name_en": "Nine", "image_index": 9},
    "10": {"name_en": "Ten", "image_index": 10},
    "Page": {"name_en": "Page", "image_index": 11},
    "Knight": {"name_en": "Knight", "image_index": 12},
    "Queen": {"name_en": "Queen", "image_index": 13},
    "King": {"name_en": "King", "image_index": 14},
}


def _image_url(image_key):
    return TAROT_IMAGE_BASE_URL + image_key


def _minor_name_en(number, suit_name):
    number_meta = MINOR_NUMBER_META[number]
    suit_meta = MINOR_SUIT_META[suit_name]
    return f"{number_meta['name_en']} of {suit_meta['name_en']}"


def _minor_image_key(number, suit_name):
    number_meta = MINOR_NUMBER_META[number]
    suit_meta = MINOR_SUIT_META[suit_name]
    return f"{suit_meta['prefix']}{number_meta['image_index']:02d}.jpg"

MAJOR_ARCANA = [
    {"id": 0, "name": "愚者", "name_en": "The Fool", "keyword": "新的开始，冒险，天真", "keyword_reversed": "鲁莽，愚蠢，冒险"},
    {"id": 1, "name": "魔术师", "name_en": "The Magician", "keyword": "创造力，技能，自信", "keyword_reversed": "欺骗，浪费才能，失败"},
    {"id": 2, "name": "女祭司", "name_en": "The High Priestess", "keyword": "直觉，神秘，内省", "keyword_reversed": "秘密，拒绝倾听直觉"},
    {"id": 3, "name": "皇后", "name_en": "The Empress", "keyword": "丰饶，自然，呵护", "keyword_reversed": "依赖，缺乏创造力"},
    {"id": 4, "name": "皇帝", "name_en": "The Emperor", "keyword": "权威，稳定，保护", "keyword_reversed": "暴政，固执，缺乏纪律"},
    {"id": 5, "name": "教皇", "name_en": "The Hierophant", "keyword": "传统，信仰，教导", "keyword_reversed": "叛逆，个人主义"},
    {"id": 6, "name": "恋人", "name_en": "The Lovers", "keyword": "爱情，和谐，选择", "keyword_reversed": "不和，错误的选择"},
    {"id": 7, "name": "战车", "name_en": "The Chariot", "keyword": "意志力，决心，成功", "keyword_reversed": "缺乏方向，失控"},
    {"id": 8, "name": "力量", "name_en": "Strength", "keyword": "内在力量，勇气，耐心", "keyword_reversed": "软弱，自我怀疑"},
    {"id": 9, "name": "隐士", "name_en": "The Hermit", "keyword": "内省，智慧，独处", "keyword_reversed": "孤独，逃避，迷失"},
    {"id": 10, "name": "命运之轮", "name_en": "Wheel of Fortune", "keyword": "变化，循环，机会", "keyword_reversed": "厄运，抗拒变化"},
    {"id": 11, "name": "正义", "name_en": "Justice", "keyword": "公正，诚实，平衡", "keyword_reversed": "不公，欺骗，失衡"},
    {"id": 12, "name": "倒吊人", "name_en": "The Hanged Man", "keyword": "牺牲，放下，新视角", "keyword_reversed": "拖延，不愿牺牲"},
    {"id": 13, "name": "死神", "name_en": "Death", "keyword": "结束，转变，新生", "keyword_reversed": "抗拒改变，停滞"},
    {"id": 14, "name": "节制", "name_en": "Temperance", "keyword": "平衡，和谐，适度", "keyword_reversed": "失衡，过度，冲突"},
    {"id": 15, "name": "恶魔", "name_en": "The Devil", "keyword": "束缚，物质主义，欲望", "keyword_reversed": "解放，打破枷锁"},
    {"id": 16, "name": "塔", "name_en": "The Tower", "keyword": "突变，崩塌，觉醒", "keyword_reversed": "避免灾难，延迟"},
    {"id": 17, "name": "星星", "name_en": "The Star", "keyword": "希望，灵感，宁静", "keyword_reversed": "绝望，失去方向"},
    {"id": 18, "name": "月亮", "name_en": "The Moon", "keyword": "幻觉，恐惧，潜意识", "keyword_reversed": "释放恐惧，看清真相"},
    {"id": 19, "name": "太阳", "name_en": "The Sun", "keyword": "快乐，成功，活力", "keyword_reversed": "暂时的阻碍，乐观"},
    {"id": 20, "name": "审判", "name_en": "Judgement", "keyword": "重生，觉醒，评判", "keyword_reversed": "自我怀疑，拒绝召唤"},
    {"id": 21, "name": "世界", "name_en": "The World", "keyword": "完成，成就，圆满", "keyword_reversed": "未完成，停滞"},
]

MINOR_ARCANA = {
    "权杖": {"element": "火", "cards": [
        {"number": "Ace", "name": "权杖一", "keyword": "创造，开始，灵感", "keyword_reversed": "拖延，缺乏灵感"},
        {"number": "2", "name": "权杖二", "keyword": "计划，决策，未来", "keyword_reversed": "恐惧改变，犹豫"},
        {"number": "3", "name": "权杖三", "keyword": "远见，探索，贸易", "keyword_reversed": "障碍，延误"},
        {"number": "4", "name": "权杖四", "keyword": "庆祝，和谐，家园", "keyword_reversed": "不稳定，冲突"},
        {"number": "5", "name": "权杖五", "keyword": "竞争，冲突，挑战", "keyword_reversed": "合作，化解冲突"},
        {"number": "6", "name": "权杖六", "keyword": "胜利，骄傲，认可", "keyword_reversed": "失败，缺乏认可"},
        {"number": "7", "name": "权杖七", "keyword": "捍卫，坚持，勇气", "keyword_reversed": "放弃，不知所措"},
        {"number": "8", "name": "权杖八", "keyword": "速度，行动，进展", "keyword_reversed": "延误，缓慢"},
        {"number": "9", "name": "权杖九", "keyword": "坚韧，防守，警觉", "keyword_reversed": "疲惫，放弃"},
        {"number": "10", "name": "权杖十", "keyword": "重担，压力，责任", "keyword_reversed": "放下负担，减压"},
        {"number": "Page", "name": "权杖侍卫", "keyword": "热情，探索，消息", "keyword_reversed": "不成熟，缺乏方向"},
        {"number": "Knight", "name": "权杖骑士", "keyword": "冒险，激情，冲动", "keyword_reversed": "鲁莽，激进"},
        {"number": "Queen", "name": "权杖王后", "keyword": "温暖，活力，果敢", "keyword_reversed": "嫉妒，自私"},
        {"number": "King", "name": "权杖国王", "keyword": "领导力，远见，创业", "keyword_reversed": "傲慢，独断"},
    ]},
    "圣杯": {"element": "水", "cards": [
        {"number": "Ace", "name": "圣杯一", "keyword": "爱，情感，直觉", "keyword_reversed": "情感空虚，压抑"},
        {"number": "2", "name": "圣杯二", "keyword": "联结，吸引，和谐", "keyword_reversed": "分离，误解"},
        {"number": "3", "name": "圣杯三", "keyword": "庆祝，友谊，喜悦", "keyword_reversed": "过度放纵，流言"},
        {"number": "4", "name": "圣杯四", "keyword": "冥想，不满，厌倦", "keyword_reversed": "新的机会，行动"},
        {"number": "5", "name": "圣杯五", "keyword": "失落，悲伤，遗憾", "keyword_reversed": "接受，前行"},
        {"number": "6", "name": "圣杯六", "keyword": "怀旧，回忆，礼物", "keyword_reversed": "停滞，卡在过去"},
        {"number": "7", "name": "圣杯七", "keyword": "幻想，选择，梦境", "keyword_reversed": "清晰，专注"},
        {"number": "8", "name": "圣杯八", "keyword": "放下，追寻，孤独", "keyword_reversed": "逃避，不愿离开"},
        {"number": "9", "name": "圣杯九", "keyword": "满足，幸福，愿望", "keyword_reversed": "物质空虚，不满足"},
        {"number": "10", "name": "圣杯十", "keyword": "完美，和谐，幸福", "keyword_reversed": "破碎的家庭，争吵"},
        {"number": "Page", "name": "圣杯侍卫", "keyword": "灵感，消息，探索", "keyword_reversed": "压抑情感，失落"},
        {"number": "Knight", "name": "圣杯骑士", "keyword": "浪漫，魅力，邀请", "keyword_reversed": "嫉妒，欺骗"},
        {"number": "Queen", "name": "圣杯王后", "keyword": "关怀，直觉，温暖", "keyword_reversed": "情绪化，依赖"},
        {"number": "King", "name": "圣杯国王", "keyword": "智慧，慈悲，温和", "keyword_reversed": "情绪操控，冷漠"},
    ]},
    "宝剑": {"element": "风", "cards": [
        {"number": "Ace", "name": "宝剑一", "keyword": "真理，突破，清晰", "keyword_reversed": "困惑，误解"},
        {"number": "2", "name": "宝剑二", "keyword": "抉择，平衡，僵局", "keyword_reversed": "信息过载，纠结"},
        {"number": "3", "name": "宝剑三", "keyword": "心碎，痛苦，悲伤", "keyword_reversed": "疗愈，释怀"},
        {"number": "4", "name": "宝剑四", "keyword": "休息，冥想，恢复", "keyword_reversed": "焦躁，无法休息"},
        {"number": "5", "name": "宝剑五", "keyword": "冲突，失败，屈辱", "keyword_reversed": "和解，放下"},
        {"number": "6", "name": "宝剑六", "keyword": "过渡，疗愈，前行", "keyword_reversed": "被困，抗拒改变"},
        {"number": "7", "name": "宝剑七", "keyword": "策略，欺骗，隐密", "keyword_reversed": "诚实，忏悔"},
        {"number": "8", "name": "宝剑八", "keyword": "束缚，局限，恐惧", "keyword_reversed": "解放，释放"},
        {"number": "9", "name": "宝剑九", "keyword": "焦虑，噩梦，担忧", "keyword_reversed": "释然，放下恐惧"},
        {"number": "10", "name": "宝剑十", "keyword": "结束，痛苦，终结", "keyword_reversed": "重生，改善"},
        {"number": "Page", "name": "宝剑侍卫", "keyword": "警觉，求知，消息", "keyword_reversed": "欺骗，流言"},
        {"number": "Knight", "name": "宝剑骑士", "keyword": "冲刺，行动，勇气", "keyword_reversed": "冲动，鲁莽"},
        {"number": "Queen", "name": "宝剑王后", "keyword": "独立，公正，理性", "keyword_reversed": "冷酷，刻薄"},
        {"number": "King", "name": "宝剑国王", "keyword": "权威，真理，原则", "keyword_reversed": "滥用权力，专制"},
    ]},
    "星币": {"element": "土", "cards": [
        {"number": "Ace", "name": "星币一", "keyword": "财富，机会，开始", "keyword_reversed": "浪费，错失机会"},
        {"number": "2", "name": "星币二", "keyword": "平衡，适应，理财", "keyword_reversed": "失衡，财务困难"},
        {"number": "3", "name": "星币三", "keyword": "合作，技艺，规划", "keyword_reversed": "缺乏团队精神"},
        {"number": "4", "name": "星币四", "keyword": "守财，节俭，控制", "keyword_reversed": "挥霍，慷慨"},
        {"number": "5", "name": "星币五", "keyword": "贫困，困境，孤独", "keyword_reversed": "改善，走出困境"},
        {"number": "6", "name": "星币六", "keyword": "慈善，分享，慷慨", "keyword_reversed": "自私，债务"},
        {"number": "7", "name": "星币七", "keyword": "耐心，评估，投资", "keyword_reversed": "急于求成，浪费"},
        {"number": "8", "name": "星币八", "keyword": "勤奋，学徒，专注", "keyword_reversed": "粗心，缺乏动力"},
        {"number": "9", "name": "星币九", "keyword": "自律，富足，精致", "keyword_reversed": "虚荣，空虚"},
        {"number": "10", "name": "星币十", "keyword": "传承，财富，家族", "keyword_reversed": "家庭纠纷，败落"},
        {"number": "Page", "name": "星币侍卫", "keyword": "学习，实践，消息", "keyword_reversed": "拖延，缺乏计划"},
        {"number": "Knight", "name": "星币骑士", "keyword": "勤奋，责任，务实", "keyword_reversed": "懒惰，停滞"},
        {"number": "Queen", "name": "星币王后", "keyword": "富足，自然，务实", "keyword_reversed": "依赖，不安全感"},
        {"number": "King", "name": "星币国王", "keyword": "财富，成功，智慧", "keyword_reversed": "贪婪，腐败"},
    ]}
}

SPREADS = {
    "single": {
        "key": "single", "name": "单牌占卜", "card_count": 1,
        "description": "最简洁的占卜方式",
        "positions": [{"index": 0, "name": "核心指引", "meaning": "当前问题的核心能量与指引"}]
    },
    "three": {
        "key": "three", "name": "无牌阵三张", "card_count": 3,
        "description": "最经典的入门牌阵，简洁有力",
        "positions": [
            {"index": 0, "name": "第一张", "meaning": "过去/现状"},
            {"index": 1, "name": "第二张", "meaning": "现在/核心"},
            {"index": 2, "name": "第三张", "meaning": "未来/建议"},
        ]
    },
    "time_flow": {
        "key": "time_flow", "name": "时间流牌阵", "card_count": 5,
        "description": "以时间为轴线的线性牌阵",
        "positions": [
            {"index": 0, "name": "过去", "meaning": "事件的历史背景与起因"},
            {"index": 1, "name": "现在", "meaning": "当前的状态与处境"},
            {"index": 2, "name": "未来", "meaning": "近期发展趋向"},
            {"index": 3, "name": "挑战", "meaning": "过程中的阻碍与课题"},
            {"index": 4, "name": "结果", "meaning": "最终的结局与方向"},
        ]
    },
    "hexagram": {
        "key": "hexagram", "name": "六芒星牌阵", "card_count": 7,
        "description": "六芒星结构的深度牌阵",
        "positions": [
            {"index": 0, "name": "现状", "meaning": "当前的总体状况"},
            {"index": 1, "name": "阻碍", "meaning": "面临的挑战与阻碍"},
            {"index": 2, "name": "理想", "meaning": "内心真正的期望"},
            {"index": 3, "name": "基础", "meaning": "事件的基础与根基"},
            {"index": 4, "name": "过去", "meaning": "过去的经验与教训"},
            {"index": 5, "name": "未来", "meaning": "未来的发展趋势"},
            {"index": 6, "name": "结果", "meaning": "最终的答案与方向"},
        ]
    },
    "celtic_cross": {
        "key": "celtic_cross", "name": "凯尔特十字", "card_count": 10,
        "description": "最经典的全局面牌阵",
        "positions": [
            {"index": 0, "name": "现状", "meaning": "当前状况的核心"},
            {"index": 1, "name": "阻碍", "meaning": "交叉的阻碍与挑战"},
            {"index": 2, "name": "目标", "meaning": "内心真正的目标"},
            {"index": 3, "name": "根源", "meaning": "问题的根源与基础"},
            {"index": 4, "name": "过去", "meaning": "最近的过去经历"},
            {"index": 5, "name": "未来", "meaning": "近期的未来发展"},
            {"index": 6, "name": "自我", "meaning": "求问者自身的态度"},
            {"index": 7, "name": "环境", "meaning": "外部环境与他人"},
            {"index": 8, "name": "希望", "meaning": "希望与恐惧"},
            {"index": 9, "name": "结果", "meaning": "最终的结局"},
        ]
    },
    "relationship": {
        "key": "relationship", "name": "关系牌阵", "card_count": 5,
        "description": "分析两人关系的专属牌阵",
        "positions": [
            {"index": 0, "name": "自己", "meaning": "你在关系中的状态"},
            {"index": 1, "name": "对方", "meaning": "对方在关系中的状态"},
            {"index": 2, "name": "关系", "meaning": "你们关系当下的本质"},
            {"index": 3, "name": "挑战", "meaning": "关系中面临的挑战"},
            {"index": 4, "name": "发展", "meaning": "关系的未来发展趋向"},
        ]
    },
}

def _build_full_deck():
    deck = []
    card_id = 0
    for m in MAJOR_ARCANA:
        image_key = MAJOR_IMAGE_FILES[m["id"]]
        deck.append({
            "id": m["id"],
            "name": m["name"],
            "name_en": m["name_en"],
            "image_key": image_key,
            "image_url": _image_url(image_key),
            "type": "major",
            "suit": None,
            "number": None,
            "element": None,
            "keyword": m["keyword"],
            "keyword_reversed": m["keyword_reversed"],
        })
        card_id += 1
    for suit_name, suit_data in MINOR_ARCANA.items():
        for c in suit_data["cards"]:
            image_key = _minor_image_key(c["number"], suit_name)
            deck.append({
                "id": card_id,
                "name": c["name"],
                "name_en": _minor_name_en(c["number"], suit_name),
                "image_key": image_key,
                "image_url": _image_url(image_key),
                "type": "minor",
                "suit": suit_name,
                "number": c["number"],
                "element": suit_data["element"],
                "keyword": c["keyword"],
                "keyword_reversed": c["keyword_reversed"],
            })
            card_id += 1
    return deck

FULL_DECK = _build_full_deck()

def get_available_spreads():
    return list(SPREADS.values())

def verify_deck_integrity():
    return {"total": len(FULL_DECK), "major": 22, "minor": 56, "valid": len(FULL_DECK) == 78}

def draw_cards(spread_name="three", enable_reversed=True):
    if spread_name not in SPREADS:
        raise ValueError(f"未知牌阵: {spread_name}")
    spread = SPREADS[spread_name]
    card_count = spread["card_count"]
    shuffled = list(FULL_DECK)
    secrets.SystemRandom().shuffle(shuffled)
    selected = shuffled[:card_count]
    cards = []
    for i, card in enumerate(selected):
        is_reversed = False
        if enable_reversed:
            is_reversed = secrets.randbits(1) == 1
        pos = spread["positions"][i] if i < len(spread["positions"]) else {"index": i, "name": f"位置{i+1}", "meaning": ""}
        cards.append({
            "id": card["id"],
            "name": card["name"],
            "name_en": card["name_en"],
            "image_key": card["image_key"],
            "image_url": card["image_url"],
            "type": card["type"],
            "suit": card["suit"],
            "number": card["number"],
            "element": card["element"],
            "is_reversed": is_reversed,
            "orientation": "逆位" if is_reversed else "正位",
            "keyword": card["keyword_reversed"] if is_reversed else card["keyword"],
            "keyword_reversed": card["keyword_reversed"],
            "position_index": i,
            "position_name": pos["name"],
            "position_meaning": pos["meaning"],
        })
    now = datetime.datetime.now()
    return {
        "code": 0,
        "msg": "success",
        "data": {
            "spread": {
                "key": spread["key"],
                "name": spread["name"],
                "card_count": spread["card_count"],
                "description": spread["description"],
                "positions": spread["positions"],
            },
            "cards": cards,
            "draw_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "deck_info": {"total": len(FULL_DECK), "name": "韦特塔罗"},
        }
    }
