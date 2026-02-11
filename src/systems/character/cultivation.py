from enum import Enum

class CultivationType(Enum):
    NONE = "None"
    DEMONIC = "魔神之体" # Blood Essence (Physical)
    IMMORTAL = "仙灵之体" # Immortal Force (Magic)
    DUAL = "仙魔神体"     # Dual

class BodyCultivation:
    def __init__(self):
        self.type = CultivationType.NONE
        self.level = 0
        self.current_points = 0
        self.max_points = 0
        self.stats = {} # Bonus stats
        
    def get_max_points(self, level):
        # Level 1-10 table
        table = [
            1000, 3000, 6000, 10000, 15000, 
            21000, 28000, 36000, 45000, 55000
        ]
        if 0 <= level < len(table):
            return table[level]
        return 999999999

    def add_points(self, amount):
        if self.type == CultivationType.NONE:
            return False
            
        self.current_points += amount
        required = self.get_max_points(self.level)
        
        if self.current_points >= required:
            # Upgrade logic (Simplified, normally requires manual upgrade)
            # For now, auto-upgrade or just cap it?
            # Requirement says "Select type... then upgrade".
            # Assuming auto-upgrade for level 1-10 if type is selected.
            if self.level < 10:
                self.level += 1
                self.current_points -= required
                self.update_stats()
                return True
        return False

    def set_type(self, type: CultivationType):
        if self.type == CultivationType.NONE:
            self.type = type
            self.level = 0
            self.current_points = 0
            self.update_stats()
            return True
        return False

    def update_stats(self):
        # Calculate stats based on type and level
        self.stats = {"attack": 0, "defense": 0, "hp_pct": 0, "mp_pct": 0}
        
        if self.level == 0: return

        # Simplified formula based on description
        # Lv1: 2-2
        # ...
        # Lv10: 45-45, 28-28, 8%
        
        # Base multiplier
        mult = self.level
        
        if self.type == CultivationType.DEMONIC:
            self.stats["attack"] = 2 * mult * mult # Approx curve
            self.stats["defense"] = 1 * mult * mult
            if self.level >= 3:
                self.stats["hp_pct"] = self.level - 2
                
        elif self.type == CultivationType.IMMORTAL:
            self.stats["attack"] = 2 * mult * mult # Magic attack (using attack for now)
            self.stats["defense"] = 1 * mult * mult # Magic def
            if self.level >= 3:
                self.stats["mp_pct"] = self.level - 2

    def to_dict(self):
        return {
            "type": self.type.name,
            "level": self.level,
            "current_points": self.current_points
        }

    @classmethod
    def from_dict(cls, data):
        bc = cls()
        try:
            bc.type = CultivationType[data.get("type", "NONE")]
        except KeyError:
            bc.type = CultivationType.NONE
            
        bc.level = data.get("level", 0)
        bc.current_points = data.get("current_points", 0)
        bc.update_stats()
        return bc
