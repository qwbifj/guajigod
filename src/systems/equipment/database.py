from src.systems.equipment.item import ItemType

EQUIPMENT_DB = {
    # Weapons
    "木剑": {"type": ItemType.WEAPON, "level": 1, "weight": 5, "stats": {"attack": (2, 5)}},
    "匕首": {"type": ItemType.WEAPON, "level": 1, "weight": 5, "stats": {"attack": (4, 8), "accuracy": (0, 1)}},
    "乌木剑": {"type": ItemType.WEAPON, "level": 1, "weight": 8, "stats": {"attack": (6, 12), "magic": (0, 1)}},
    "青铜斧": {"type": ItemType.WEAPON, "level": 13, "weight": 10, "stats": {"attack": (8, 15)}},
    "八荒": {"type": ItemType.WEAPON, "level": 15, "weight": 25, "stats": {"attack": (12, 20)}},
    "凝霜": {"type": ItemType.WEAPON, "level": 25, "weight": 20, "stats": {"attack": (10, 13), "accuracy": (1, 3)}},
    "炼狱": {"type": ItemType.WEAPON, "level": 26, "weight": 60, "stats": {"attack": (0, 25)}},
    "井中月": {"type": ItemType.WEAPON, "level": 28, "weight": 58, "stats": {"attack": (7, 22)}},
    "裁决之杖": {"type": ItemType.WEAPON, "level": 30, "weight": 80, "stats": {"attack": (0, 30)}},
    "屠龙": {"type": ItemType.WEAPON, "level": 34, "weight": 99, "stats": {"attack": (5, 35)}},

    # Armors (Clothes)
    "布衣": {"type": ItemType.ARMOR, "level": 1, "weight": 5, "stats": {"defense": (2, 2), "magic_defense": (0, 1)}},
    "轻型盔甲": {"type": ItemType.ARMOR, "level": 11, "weight": 8, "stats": {"defense": (3, 3), "magic_defense": (1, 2)}},
    "中型盔甲": {"type": ItemType.ARMOR, "level": 16, "weight": 12, "stats": {"defense": (3, 5), "magic_defense": (1, 2)}},
    "重盔甲": {"type": ItemType.ARMOR, "level": 22, "weight": 25, "stats": {"defense": (4, 7), "magic_defense": (2, 3)}},
    "战神盔甲": {"type": ItemType.ARMOR, "level": 33, "weight": 40, "stats": {"defense": (5, 9), "magic_defense": (3, 4)}},
    "天魔神甲": {"type": ItemType.ARMOR, "level": 40, "weight": 60, "stats": {"defense": (5, 12), "magic_defense": (4, 7), "attack": (1, 2)}},

    # Helmets
    "青铜头盔": {"type": ItemType.HELMET, "level": 10, "weight": 4, "stats": {"defense": (0, 1)}},
    "魔法头盔": {"type": ItemType.HELMET, "level": 14, "weight": 4, "stats": {"defense": (0, 1), "magic_defense": (0, 1)}},
    "道士头盔": {"type": ItemType.HELMET, "level": 24, "weight": 5, "stats": {"defense": (1, 2), "magic_defense": (1, 2)}},
    "黑铁头盔": {"type": ItemType.HELMET, "level": 38, "weight": 20, "stats": {"defense": (4, 5), "magic_defense": (2, 3)}},
    "圣战头盔": {"type": ItemType.HELMET, "level": 40, "weight": 10, "stats": {"defense": (4, 5), "magic_defense": (2, 3), "attack": (0, 1)}},

    # Necklaces
    "金项链": {"type": ItemType.NECKLACE, "level": 2, "weight": 1, "stats": {"accuracy": (0, 1), "attack": (0, 1)}},
    "灯笼项链": {"type": ItemType.NECKLACE, "level": 18, "weight": 1, "stats": {"accuracy": (1, 1), "attack": (0, 2)}},
    "白色虎齿项链": {"type": ItemType.NECKLACE, "level": 11, "weight": 1, "stats": {"dodge": (1, 2), "taoism": (1, 1)}},
    "幽灵项链": {"type": ItemType.NECKLACE, "level": 24, "weight": 1, "stats": {"attack": (0, 5)}},
    "绿色项链": {"type": ItemType.NECKLACE, "level": 35, "weight": 1, "stats": {"attack": (2, 5)}},
    "圣战项链": {"type": ItemType.NECKLACE, "level": 40, "weight": 2, "stats": {"attack": (3, 6)}},

    # Bracelets
    "铁手镯": {"type": ItemType.BRACELET, "level": 1, "weight": 1, "stats": {"accuracy": (0, 1)}},
    "大手镯": {"type": ItemType.BRACELET, "level": 9, "weight": 2, "stats": {"defense": (1, 1)}},
    "死神手套": {"type": ItemType.BRACELET, "level": 22, "weight": 3, "stats": {"attack": (1, 2)}},
    "金手镯": {"type": ItemType.BRACELET, "level": 23, "weight": 1, "stats": {"defense": (0, 1), "attack": (0, 1)}},
    "骑士手镯": {"type": ItemType.BRACELET, "level": 35, "weight": 2, "stats": {"attack": (2, 2)}},
    "圣战手镯": {"type": ItemType.BRACELET, "level": 40, "weight": 2, "stats": {"defense": (0, 1), "attack": (2, 3)}},

    # Rings
    "古铜戒指": {"type": ItemType.RING, "level": 3, "weight": 1, "stats": {"attack": (0, 1)}},
    "黑色水晶戒指": {"type": ItemType.RING, "level": 20, "weight": 1, "stats": {"attack": (0, 2)}},
    "珊瑚戒指": {"type": ItemType.RING, "level": 25, "weight": 1, "stats": {"attack": (0, 4)}},
    "龙之戒指": {"type": ItemType.RING, "level": 30, "weight": 1, "stats": {"attack": (0, 5)}},
    "力量戒指": {"type": ItemType.RING, "level": 35, "weight": 1, "stats": {"attack": (0, 6)}},
    "圣战戒指": {"type": ItemType.RING, "level": 40, "weight": 2, "stats": {"magic_defense": (0, 1), "attack": (0, 7)}},
    
    # Belts (Custom additions as Mir 2 belts came later)
    "布腰带": {"type": ItemType.BELT, "level": 10, "weight": 1, "stats": {"defense": (0, 1)}},
    "兽皮腰带": {"type": ItemType.BELT, "level": 20, "weight": 1, "stats": {"defense": (1, 2)}},
    "战神腰带": {"type": ItemType.BELT, "level": 40, "weight": 2, "stats": {"defense": (2, 4), "attack": (0, 1)}},

    # Boots (Custom)
    "布鞋": {"type": ItemType.BOOTS, "level": 10, "weight": 1, "stats": {"defense": (0, 1)}},
    "鹿皮靴": {"type": ItemType.BOOTS, "level": 20, "weight": 2, "stats": {"defense": (0, 2), "dodge": (0, 1)}},
    "战神靴子": {"type": ItemType.BOOTS, "level": 40, "weight": 3, "stats": {"defense": (1, 3), "attack": (0, 1)}},

    # Potions (Consumables)
    "金创药(小)": {"type": ItemType.CONSUMABLE, "level": 1, "weight": 1, "price": 88, "stats": {"hp": 30}},
    "金创药(中)": {"type": ItemType.CONSUMABLE, "level": 10, "weight": 2, "price": 220, "stats": {"hp": 60}},
    "强效金创药": {"type": ItemType.CONSUMABLE, "level": 20, "weight": 3, "price": 550, "stats": {"hp": 100}},
    "魔法药(小)": {"type": ItemType.CONSUMABLE, "level": 1, "weight": 1, "price": 88, "stats": {"mp": 40}},
    "魔法药(中)": {"type": ItemType.CONSUMABLE, "level": 10, "weight": 2, "price": 220, "stats": {"mp": 80}},
    "强效魔法药": {"type": ItemType.CONSUMABLE, "level": 20, "weight": 3, "price": 550, "stats": {"mp": 150}},
    "太阳水": {"type": ItemType.CONSUMABLE, "level": 25, "weight": 2, "price": 550, "stats": {"hp": 30, "mp": 40}},
    "万年雪霜": {"type": ItemType.CONSUMABLE, "level": 35, "weight": 2, "price": 1100, "stats": {"hp": 100, "mp": 100}},

    # Skill Books
    # Warrior
    "基本剑术": {"type": ItemType.SKILL_BOOK, "level": 7, "weight": 1, "price": 500, "stats": {}},
    "攻杀剑术": {"type": ItemType.SKILL_BOOK, "level": 19, "weight": 1, "price": 2000, "stats": {}},
    "刺杀剑术": {"type": ItemType.SKILL_BOOK, "level": 25, "weight": 1, "price": 5000, "stats": {}},
    "半月弯刀": {"type": ItemType.SKILL_BOOK, "level": 28, "weight": 1, "price": 10000, "stats": {}},
    "野蛮冲撞": {"type": ItemType.SKILL_BOOK, "level": 30, "weight": 1, "price": 20000, "stats": {}},
    "烈火剑法": {"type": ItemType.SKILL_BOOK, "level": 35, "weight": 1, "price": 50000, "stats": {}},
    
    # Mage
    "火球术": {"type": ItemType.SKILL_BOOK, "level": 7, "weight": 1, "price": 500, "stats": {}},
    "抗拒火环": {"type": ItemType.SKILL_BOOK, "level": 12, "weight": 1, "price": 1000, "stats": {}},
    "诱惑之光": {"type": ItemType.SKILL_BOOK, "level": 13, "weight": 1, "price": 1500, "stats": {}},
    "地狱火": {"type": ItemType.SKILL_BOOK, "level": 16, "weight": 1, "price": 2000, "stats": {}},
    "雷电术": {"type": ItemType.SKILL_BOOK, "level": 17, "weight": 1, "price": 3000, "stats": {}},
    "瞬息移动": {"type": ItemType.SKILL_BOOK, "level": 19, "weight": 1, "price": 4000, "stats": {}},
    "大火球": {"type": ItemType.SKILL_BOOK, "level": 22, "weight": 1, "price": 5000, "stats": {}},
    "爆裂火焰": {"type": ItemType.SKILL_BOOK, "level": 22, "weight": 1, "price": 5000, "stats": {}},
    "火墙": {"type": ItemType.SKILL_BOOK, "level": 24, "weight": 1, "price": 8000, "stats": {}},
    "疾光电影": {"type": ItemType.SKILL_BOOK, "level": 26, "weight": 1, "price": 10000, "stats": {}},
    "地狱雷光": {"type": ItemType.SKILL_BOOK, "level": 30, "weight": 1, "price": 20000, "stats": {}},
    "魔法盾": {"type": ItemType.SKILL_BOOK, "level": 31, "weight": 1, "price": 30000, "stats": {}},
    "圣言术": {"type": ItemType.SKILL_BOOK, "level": 32, "weight": 1, "price": 40000, "stats": {}},
    "冰咆哮": {"type": ItemType.SKILL_BOOK, "level": 35, "weight": 1, "price": 50000, "stats": {}},

    # Taoist
    "治愈术": {"type": ItemType.SKILL_BOOK, "level": 7, "weight": 1, "price": 500, "stats": {}},
    "精神力战法": {"type": ItemType.SKILL_BOOK, "level": 9, "weight": 1, "price": 1000, "stats": {}},
    "施毒术": {"type": ItemType.SKILL_BOOK, "level": 14, "weight": 1, "price": 2000, "stats": {}},
    "灵魂火符": {"type": ItemType.SKILL_BOOK, "level": 18, "weight": 1, "price": 3000, "stats": {}},
    "幽灵盾": {"type": ItemType.SKILL_BOOK, "level": 22, "weight": 1, "price": 5000, "stats": {}},
    "神圣战甲术": {"type": ItemType.SKILL_BOOK, "level": 25, "weight": 1, "price": 8000, "stats": {}},
    "困魔咒": {"type": ItemType.SKILL_BOOK, "level": 28, "weight": 1, "price": 10000, "stats": {}},
    "群体治愈术": {"type": ItemType.SKILL_BOOK, "level": 33, "weight": 1, "price": 20000, "stats": {}},
    "召唤神兽": {"type": ItemType.SKILL_BOOK, "level": 35, "weight": 1, "price": 50000, "stats": {}},
}
