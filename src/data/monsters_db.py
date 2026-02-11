
# Legend of Mir 2 Monster Database

MONSTERS_DB = {
    # ----------------------------------------
    # Level 1-10: Novice Village & Surroundings
    # ----------------------------------------
    "Hen": {
        "name": "鸡",
        "level": 1,
        "hp": 15,
        "attack": 2,
        "defense": 0,
        "xp": 5,
        "type": "animal",
        "drops": ["木剑", "布衣", "金项链", "铁手镯", "古铜戒指"]
    },
    "Deer": {
        "name": "鹿",
        "level": 3,
        "hp": 25,
        "attack": 4,
        "defense": 0,
        "xp": 15,
        "type": "animal",
        "drops": ["木剑", "布衣", "金项链", "铁手镯", "古铜戒指", "匕首"]
    },
    "Scarecrow": {
        "name": "稻草人",
        "level": 5,
        "hp": 30,
        "attack": 6,
        "defense": 0,
        "xp": 20,
        "type": "undead",
        "drops": ["匕首", "青铜头盔", "大手镯", "布鞋", "布腰带", "古铜戒指"]
    },
    "RakeCat": {
        "name": "钉耙猫",
        "level": 7,
        "hp": 50,
        "attack": 8,
        "defense": 1,
        "xp": 30,
        "type": "beast",
        "drops": ["匕首", "青铜头盔", "大手镯", "布鞋", "布腰带", "乌木剑"]
    },
    "HookCat": {
        "name": "多钩猫",
        "level": 8,
        "hp": 55,
        "attack": 9,
        "defense": 1,
        "xp": 32,
        "type": "beast",
        "drops": ["匕首", "青铜头盔", "大手镯", "布鞋", "布腰带", "乌木剑"]
    },

    # ----------------------------------------
    # Level 10-15: Skull Cave / Ancient Tombs
    # ----------------------------------------
    "Skeleton": {
        "name": "骷髅",
        "level": 10,
        "hp": 90,
        "attack": 12,
        "defense": 2,
        "xp": 80,
        "type": "undead",
        "drops": ["乌木剑", "轻型盔甲", "魔法头盔", "灯笼项链", "黑色水晶戒指"]
    },
    "SkeletonWarrior": {
        "name": "掷斧骷髅",
        "level": 12,
        "hp": 110,
        "attack": 15,
        "defense": 3,
        "xp": 100,
        "type": "undead",
        "drops": ["乌木剑", "轻型盔甲", "魔法头盔", "灯笼项链", "黑色水晶戒指", "青铜斧"]
    },
    "SkeletonChampion": {
        "name": "骷髅战将",
        "level": 14,
        "hp": 150,
        "attack": 18,
        "defense": 4,
        "xp": 150,
        "type": "undead",
        "drops": ["青铜斧", "中型盔甲", "白色虎齿项链", "兽皮腰带", "鹿皮靴"]
    },
    "SkullElf": {
        "name": "骷髅精灵",
        "level": 15,
        "hp": 500,
        "attack": 30,
        "defense": 8,
        "xp": 500,
        "type": "boss", # Mini Boss
        "drops": ["青铜斧", "中型盔甲", "白色虎齿项链", "兽皮腰带", "鹿皮靴", "八荒", "重盔甲"]
    },

    # ----------------------------------------
    # Level 15-20: Zombie Mines
    # ----------------------------------------
    "Zombie": {
        "name": "僵尸",
        "level": 16,
        "hp": 160,
        "attack": 20,
        "defense": 5,
        "xp": 160,
        "type": "undead",
        "drops": ["青铜斧", "中型盔甲", "白色虎齿项链", "兽皮腰带", "鹿皮靴"]
    },
    "CrawlerZombie": {
        "name": "爬行僵尸",
        "level": 17,
        "hp": 180,
        "attack": 25,
        "defense": 4,
        "xp": 170,
        "type": "undead",
        "drops": ["八荒", "重盔甲", "道士头盔", "死神手套", "金手镯", "珊瑚戒指"]
    },
    "CorpseKing": {
        "name": "尸王",
        "level": 20,
        "hp": 1000,
        "attack": 45,
        "defense": 15,
        "xp": 1500,
        "type": "boss",
        "drops": ["八荒", "重盔甲", "道士头盔", "死神手套", "金手镯", "珊瑚戒指", "凝霜", "炼狱"]
    },

    # ----------------------------------------
    # Level 20-25: Centipede Cave
    # ----------------------------------------
    "Centipede": {
        "name": "蜈蚣",
        "level": 22,
        "hp": 230,
        "attack": 30,
        "defense": 8,
        "xp": 280,
        "type": "insect",
        "drops": ["八荒", "重盔甲", "道士头盔", "死神手套", "金手镯", "珊瑚戒指"]
    },
    "Maggot": {
        "name": "跳跳蜂",
        "level": 23,
        "hp": 210,
        "attack": 35,
        "defense": 6,
        "xp": 290,
        "type": "insect",
        "drops": ["八荒", "重盔甲", "道士头盔", "死神手套", "金手镯", "珊瑚戒指"]
    },
    "Tongs": {
        "name": "钳虫",
        "level": 24,
        "hp": 280,
        "attack": 32,
        "defense": 10,
        "xp": 320,
        "type": "insect",
        "drops": ["凝霜", "炼狱", "战神盔甲", "黑铁头盔", "幽灵项链", "绿色项链"]
    },
    "EvilTongs": {
        "name": "邪恶钳虫",
        "level": 25,
        "hp": 1500,
        "attack": 60,
        "defense": 20,
        "xp": 2000,
        "type": "boss",
        "drops": ["凝霜", "炼狱", "战神盔甲", "黑铁头盔", "幽灵项链", "绿色项链", "骑士手镯", "龙之戒指", "井中月"]
    },

    # ----------------------------------------
    # Level 25-30: Zuma Temple
    # ----------------------------------------
    "ZumaRat": {
        "name": "祖玛雕像",
        "level": 28,
        "hp": 350,
        "attack": 40,
        "defense": 15,
        "xp": 450,
        "type": "zuma",
        "drops": ["凝霜", "炼狱", "战神盔甲", "黑铁头盔", "幽灵项链", "绿色项链", "骑士手镯", "龙之戒指"]
    },
    "ZumaArcher": {
        "name": "祖玛弓箭手",
        "level": 29,
        "hp": 320,
        "attack": 55,
        "defense": 10,
        "xp": 480,
        "type": "zuma",
        "drops": ["凝霜", "炼狱", "战神盔甲", "黑铁头盔", "幽灵项链", "绿色项链", "骑士手镯", "龙之戒指"]
    },
    "ZumaGuardian": {
        "name": "祖玛卫士",
        "level": 30,
        "hp": 450,
        "attack": 50,
        "defense": 20,
        "xp": 550,
        "type": "zuma",
        "drops": ["凝霜", "炼狱", "战神盔甲", "黑铁头盔", "幽灵项链", "绿色项链", "骑士手镯", "龙之戒指", "井中月", "力量戒指"]
    },
    "ZumaLeader": {
        "name": "祖玛教主",
        "level": 35,
        "hp": 3000,
        "attack": 100,
        "defense": 40,
        "xp": 5000,
        "type": "boss",
        "drops": ["裁决之杖", "天魔神甲", "圣战头盔", "圣战项链", "圣战手镯", "圣战戒指", "战神腰带", "战神靴子"]
    },

    # ----------------------------------------
    # Level 30-35: Stone Tomb (Pig Hole)
    # ----------------------------------------
    "BlackBoar": {
        "name": "黑野猪",
        "level": 31,
        "hp": 380,
        "attack": 45,
        "defense": 18,
        "xp": 480,
        "type": "beast",
        "drops": ["井中月", "力量戒指", "凝霜", "炼狱"]
    },
    "RedBoar": {
        "name": "红野猪",
        "level": 32,
        "hp": 360,
        "attack": 50,
        "defense": 16,
        "xp": 490,
        "type": "beast",
        "drops": ["井中月", "力量戒指", "凝霜", "炼狱"]
    },
    "WhiteBoar": {
        "name": "白野猪",
        "level": 35,
        "hp": 1200,
        "attack": 70,
        "defense": 30,
        "xp": 2500,
        "type": "boss", # Mini Boss
        "drops": ["裁决之杖", "天魔神甲", "圣战头盔", "圣战项链", "圣战手镯", "圣战戒指"]
    },

    # ----------------------------------------
    # Level 35-40: Wooma Temple
    # ----------------------------------------
    "WoomaWarrior": {
        "name": "沃玛战士",
        "level": 36,
        "hp": 400,
        "attack": 50,
        "defense": 20,
        "xp": 520,
        "type": "wooma",
        "drops": ["井中月", "力量戒指", "凝霜", "炼狱"]
    },
    "WoomaFighter": {
        "name": "沃玛勇士",
        "level": 38,
        "hp": 450,
        "attack": 55,
        "defense": 22,
        "xp": 560,
        "type": "wooma",
        "drops": ["裁决之杖", "天魔神甲", "圣战头盔", "圣战项链", "圣战手镯", "圣战戒指"]
    },
    "WoomaLeader": {
        "name": "沃玛教主",
        "level": 40,
        "hp": 4000,
        "attack": 120,
        "defense": 50,
        "xp": 8000,
        "type": "boss",
        "drops": ["裁决之杖", "天魔神甲", "圣战头盔", "圣战项链", "圣战手镯", "圣战戒指", "战神腰带", "战神靴子", "屠龙"]
    },

    # ----------------------------------------
    # Level 40-45: Red Moon (Spider Cave)
    # ----------------------------------------
    "BlackSpider": {
        "name": "黑锷蜘蛛",
        "level": 42,
        "hp": 800,
        "attack": 80,
        "defense": 30,
        "xp": 1000,
        "type": "spider",
        "drops": ["裁决之杖", "天魔神甲", "圣战头盔", "圣战项链", "圣战手镯", "圣战戒指", "战神腰带", "战神靴子"]
    },
    "MoonSpider": {
        "name": "月魔蜘蛛",
        "level": 43,
        "hp": 900,
        "attack": 70,
        "defense": 40,
        "xp": 1200,
        "type": "spider",
        "drops": ["裁决之杖", "天魔神甲", "圣战头盔", "圣战项链", "圣战手镯", "圣战戒指", "战神腰带", "战神靴子"]
    },
    "RedMoonDemon": {
        "name": "赤月恶魔",
        "level": 45,
        "hp": 8000,
        "attack": 200,
        "defense": 80,
        "xp": 20000,
        "type": "boss",
        "drops": ["屠龙", "裁决之杖", "天魔神甲", "圣战头盔", "圣战项链", "圣战手镯", "圣战戒指", "战神腰带", "战神靴子"]
    }
}
