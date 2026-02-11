from enum import Enum

class SkillType(Enum):
    ACTIVE = "主动"
    PASSIVE = "被动"
    TOGGLE = "开关"

class Skill:
    def __init__(self, name, profession, level_req, damage_multiplier=1.0, mp_cost=0, range=1, cooldown=0.0, skill_type=SkillType.ACTIVE, description=""):
        self.name = name
        self.profession = profession # "Warrior", "Mage", "Taoist"
        self.level_req = level_req
        self.damage_multiplier = damage_multiplier
        self.mp_cost = mp_cost
        self.range = range
        self.cooldown = cooldown
        self.skill_type = skill_type
        self.description = description
        self.last_used = 0.0 # Timestamp
        self.icon = None # Path to icon

class SkillBook:
    def __init__(self):
        self.skills = {}
        self._init_skills()

    def _init_skills(self):
        # Warrior Skills
        self.skills["基本剑术"] = Skill("基本剑术", "WARRIOR", 7, damage_multiplier=1.0, skill_type=SkillType.PASSIVE, description="提高攻击准确度")
        self.skills["攻杀剑术"] = Skill("攻杀剑术", "WARRIOR", 19, damage_multiplier=1.2, skill_type=SkillType.PASSIVE, description="攻击时有几率造成额外伤害")
        self.skills["刺杀剑术"] = Skill("刺杀剑术", "WARRIOR", 25, damage_multiplier=1.0, mp_cost=0, range=2, skill_type=SkillType.TOGGLE, description="隔位刺杀，无视防御")
        self.skills["半月弯刀"] = Skill("半月弯刀", "WARRIOR", 28, damage_multiplier=0.6, mp_cost=2, range=1, skill_type=SkillType.TOGGLE, description="攻击面前的多个敌人")
        self.skills["野蛮冲撞"] = Skill("野蛮冲撞", "WARRIOR", 30, damage_multiplier=0, mp_cost=10, range=4, cooldown=3.0, description="推开前方等级低于自己的敌人")
        self.skills["烈火剑法"] = Skill("烈火剑法", "WARRIOR", 35, damage_multiplier=2.5, mp_cost=20, cooldown=10.0, description="召唤烈火精灵附着在剑上，造成巨大伤害")

        # Mage Skills
        self.skills["火球术"] = Skill("火球术", "MAGE", 7, damage_multiplier=1.1, mp_cost=4, range=8, cooldown=1.0, description="发射一枚火球攻击敌人")
        self.skills["抗拒火环"] = Skill("抗拒火环", "MAGE", 12, damage_multiplier=0, mp_cost=10, range=1, cooldown=2.0, description="推开身边的敌人")
        self.skills["诱惑之光"] = Skill("诱惑之光", "MAGE", 13, damage_multiplier=0, mp_cost=15, range=6, cooldown=2.0, description="有几率诱惑怪物成为宠物")
        self.skills["地狱火"] = Skill("地狱火", "MAGE", 16, damage_multiplier=1.3, mp_cost=10, range=5, cooldown=1.5, description="向前喷射火焰，攻击直线上的敌人")
        self.skills["雷电术"] = Skill("雷电术", "MAGE", 17, damage_multiplier=1.5, mp_cost=12, range=8, cooldown=1.2, description="召唤雷电攻击敌人")
        self.skills["瞬息移动"] = Skill("瞬息移动", "MAGE", 19, damage_multiplier=0, mp_cost=15, cooldown=5.0, description="随机传送到地图上的某点")
        self.skills["大火球"] = Skill("大火球", "MAGE", 22, damage_multiplier=1.4, mp_cost=15, range=8, cooldown=1.0, description="发射巨大的火球")
        self.skills["爆裂火焰"] = Skill("爆裂火焰", "MAGE", 22, damage_multiplier=1.2, mp_cost=18, range=8, cooldown=1.5, description="产生火焰爆炸，攻击范围敌人")
        self.skills["火墙"] = Skill("火墙", "MAGE", 24, damage_multiplier=0.5, mp_cost=25, range=8, cooldown=2.0, description="在地面产生一道火墙，持续造成伤害")
        self.skills["疾光电影"] = Skill("疾光电影", "MAGE", 26, damage_multiplier=1.6, mp_cost=25, range=10, cooldown=1.5, description="发射直线高能电光")
        self.skills["地狱雷光"] = Skill("地狱雷光", "MAGE", 30, damage_multiplier=1.4, mp_cost=30, range=2, cooldown=2.0, description="以自己为中心释放雷电风暴")
        self.skills["魔法盾"] = Skill("魔法盾", "MAGE", 31, damage_multiplier=0, mp_cost=30, cooldown=30.0, description="减少受到的物理和魔法伤害")
        self.skills["圣言术"] = Skill("圣言术", "MAGE", 32, damage_multiplier=0, mp_cost=40, range=8, cooldown=5.0, description="有几率秒杀不死系怪物")
        self.skills["冰咆哮"] = Skill("冰咆哮", "MAGE", 35, damage_multiplier=1.8, mp_cost=40, range=8, cooldown=2.0, description="召唤冰雪风暴，攻击范围敌人")

        # Taoist Skills
        self.skills["治愈术"] = Skill("治愈术", "TAOIST", 7, damage_multiplier=0, mp_cost=5, range=8, cooldown=1.0, description="恢复自己或他人的生命值")
        self.skills["精神力战法"] = Skill("精神力战法", "TAOIST", 9, damage_multiplier=1.0, skill_type=SkillType.PASSIVE, description="提高攻击准确度")
        self.skills["施毒术"] = Skill("施毒术", "TAOIST", 14, damage_multiplier=0, mp_cost=8, range=8, cooldown=2.0, description="使敌人中毒，持续扣血并降低防御")
        self.skills["灵魂火符"] = Skill("灵魂火符", "TAOIST", 18, damage_multiplier=1.3, mp_cost=10, range=8, cooldown=1.0, description="利用道符攻击敌人")
        self.skills["幽灵盾"] = Skill("幽灵盾", "TAOIST", 22, damage_multiplier=0, mp_cost=15, range=8, cooldown=5.0, description="增加魔法防御力")
        self.skills["神圣战甲术"] = Skill("神圣战甲术", "TAOIST", 25, damage_multiplier=0, mp_cost=15, range=8, cooldown=5.0, description="增加物理防御力")
        self.skills["困魔咒"] = Skill("困魔咒", "TAOIST", 28, damage_multiplier=0, mp_cost=20, range=8, cooldown=10.0, description="困住怪物使其无法移动")
        self.skills["群体治愈术"] = Skill("群体治愈术", "TAOIST", 33, damage_multiplier=0, mp_cost=30, range=8, cooldown=3.0, description="恢复范围内所有友军的生命值")
        self.skills["召唤神兽"] = Skill("召唤神兽", "TAOIST", 35, damage_multiplier=0, mp_cost=50, cooldown=60.0, description="召唤一只强大的神兽协助战斗")

        # Legacy Support
        self.skills["Basic Sword"] = self.skills["基本剑术"]
        self.skills["Fireball"] = self.skills["火球术"]
        self.skills["Heal"] = self.skills["治愈术"]
        self.skills["Hellfire"] = self.skills["烈火剑法"] # Mapping to warrior ultimate for now

    def get_skill(self, name):
        return self.skills.get(name)
