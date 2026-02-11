from enum import Enum
import random

class ItemType(Enum):
    WEAPON = "武器"
    ARMOR = "衣服"
    HELMET = "头盔"
    NECKLACE = "项链"
    BRACELET = "手镯"
    RING = "戒指"
    BOOTS = "鞋子"
    BELT = "腰带"
    MEDAL = "勋章"
    CONSUMABLE = "消耗品"
    MATERIAL = "材料"
    SKILL_BOOK = "技能书"

class ItemQuality(Enum):
    NORMAL = "普通"     # White
    HIGH = "优良"       # Light Green
    RARE = "精品"       # Blue
    EPIC = "极品"       # Purple
    LEGENDARY = "传说"  # Orange
    MYTHIC = "史诗"     # Red
    DIVINE = "神话"     # Rainbow/Gradient

class Item:
    def __init__(self, name, item_type: ItemType, quality: ItemQuality = ItemQuality.NORMAL, price=0, stackable=False, max_stack=1, weight=1):
        self.name = name
        self.item_type = item_type
        self.quality = quality
        self.price = price
        self.stats = {} # e.g. {"attack": 5, "defense": 2}
        self.stackable = stackable
        self.max_stack = max_stack
        self.count = 1
        self.weight = weight
        self.is_equipment = False # Flag for recycle logic
        self.locked = False # Locked items cannot be recycled

    def add_stat(self, stat_name, value):
        self.stats[stat_name] = value

    def to_dict(self):
        return {
            "class": self.__class__.__name__,
            "name": self.name,
            "item_type": self.item_type.name,
            "quality": self.quality.name,
            "price": self.price,
            "stats": self.stats,
            "stackable": self.stackable,
            "max_stack": self.max_stack,
            "count": self.count,
            "weight": getattr(self, 'weight', 1),
            "is_equipment": self.is_equipment,
            "locked": getattr(self, 'locked', False)
        }

    @classmethod
    def from_dict(cls, data):
        # Handle subclasses based on 'class' field if needed, or caller handles it.
        # But here we are in Item, so we can dispatch.
        class_name = data.get("class", "Item")
        
        # Resolve Enum
        try:
            item_type = ItemType[data["item_type"]]
        except KeyError:
            item_type = ItemType.MATERIAL # Default fallback
            
        try:
            quality = ItemQuality[data["quality"]]
        except KeyError:
            quality = ItemQuality.NORMAL

        if class_name == "Equipment":
            return Equipment.from_dict(data)
        elif class_name == "UpgradeStone":
            item = UpgradeStone()
        elif class_name == "MythicUpgradeStone":
            item = MythicUpgradeStone()
        elif class_name == "BonePowder":
            item = BonePowder()
        else:
            item = cls(data["name"], item_type, quality, data.get("price", 0), 
                      data.get("stackable", False), data.get("max_stack", 1), data.get("weight", 1))
        
        item.stats = data.get("stats", {})
        item.count = data.get("count", 1)
        item.weight = data.get("weight", 1)
        item.is_equipment = data.get("is_equipment", False)
        item.locked = data.get("locked", False)
        return item

    def __str__(self):
        stats_str = ", ".join([f"{k}:{v}" for k, v in self.stats.items()])
        return f"[{self.quality.value}] {self.name} ({self.item_type.value}) x{self.count} - {stats_str}"

class Equipment(Item):
    def __init__(self, name, item_type: ItemType, quality: ItemQuality = ItemQuality.NORMAL, min_level=1, weight=1):
        super().__init__(name, item_type, quality, stackable=False, max_stack=1, weight=weight)
        self.min_level = min_level
        self.is_equipment = True # Flag for recycle logic
        self.durability = 100
        self.max_durability = 100
        self.enhancement_level = 0
        # Stats are now set manually or via factory

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "min_level": self.min_level,
            "durability": self.durability,
            "max_durability": self.max_durability,
            "enhancement_level": self.enhancement_level
        })
        return data

    @classmethod
    def from_dict(cls, data):
        # Resolve Enums again since this might be called directly or from Item.from_dict
        try:
            item_type = ItemType[data["item_type"]]
        except KeyError:
            item_type = ItemType.WEAPON
            
        try:
            quality = ItemQuality[data["quality"]]
        except KeyError:
            quality = ItemQuality.NORMAL
            
        item = cls(data["name"], item_type, quality, data.get("min_level", 1), data.get("weight", 1))
        item.stats = data.get("stats", {})
        item.count = data.get("count", 1)
        item.price = data.get("price", 0)
        item.is_equipment = True
        item.locked = data.get("locked", False)
        
        item.durability = data.get("durability", 100)
        item.max_durability = data.get("max_durability", 100)
        item.enhancement_level = data.get("enhancement_level", 0)
        
        return item

    @staticmethod
    def create_random_drop(target_level=None, min_level=None, max_level=None, allowed_items=None, force_quality=None):
        from src.systems.equipment.database import EQUIPMENT_DB
        
        # Filter items
        candidates = []
        
        if allowed_items:
            for name in allowed_items:
                if name in EQUIPMENT_DB:
                    candidates.append((name, EQUIPMENT_DB[name]))
        else:
            for name, data in EQUIPMENT_DB.items():
                # Filter out non-equipment items
                if data["type"] in [ItemType.CONSUMABLE, ItemType.SKILL_BOOK, ItemType.MATERIAL]:
                    continue

                lvl = data["level"]
                
                # Check Min/Max Level
                if min_level is not None and lvl < min_level:
                    continue
                if max_level is not None and lvl > max_level:
                    continue
                    
                # Legacy: Drop items around level if no specific range
                if target_level is not None and min_level is None and max_level is None:
                    if lvl <= target_level + 5:
                        candidates.append((name, data))
                    continue
                
                # If we have ranges, and passed checks
                if (min_level is not None or max_level is not None):
                    candidates.append((name, data))
        
        if not candidates:
            # Fallback if allowed_items was empty or filtered out?
            # Or if range was too strict.
            # Try legacy fallback if we have target_level and no candidates yet
            if not allowed_items and target_level is not None and not candidates:
                 for name, data in EQUIPMENT_DB.items():
                    if data["type"] in [ItemType.CONSUMABLE, ItemType.SKILL_BOOK, ItemType.MATERIAL]:
                        continue
                    if data["level"] <= target_level + 5:
                        candidates.append((name, data))
            
            if not candidates:
                return None

            
        # Weighted choice based on level proximity? Or just random
        name, data = random.choice(candidates)
        
        # Determine Quality
        if force_quality:
            q = force_quality
        else:
            roll = random.random()
            if roll < 0.005: q = ItemQuality.DIVINE
            elif roll < 0.02: q = ItemQuality.MYTHIC
            elif roll < 0.05: q = ItemQuality.LEGENDARY
            elif roll < 0.10: q = ItemQuality.EPIC
            elif roll < 0.25: q = ItemQuality.RARE
            elif roll < 0.50: q = ItemQuality.HIGH
            else: q = ItemQuality.NORMAL
        
        # Determine Multiplier based on final quality
        if q == ItemQuality.DIVINE: mult = 7.0
        elif q == ItemQuality.MYTHIC: mult = 6.0
        elif q == ItemQuality.LEGENDARY: mult = 5.0
        elif q == ItemQuality.EPIC: mult = 4.0
        elif q == ItemQuality.RARE: mult = 3.0
        elif q == ItemQuality.HIGH: mult = 2.0
        else: mult = 1.0

        weight = data.get("weight", 1)
        item = Equipment(name, data["type"], q, data["level"], weight)
        
        # Apply stats
        for stat, (min_v, max_v) in data["stats"].items():
            # User Request: 
            # 1. Base min at least 1
            # 2. Multiply range [min, max] by multiplier first, then random
            
            # Ensure base min is at least 1
            base_min = max(1, min_v)
            base_max = max(base_min, max_v) # Ensure max >= min
            
            # Calculate new range
            scaled_min = int(base_min * mult)
            scaled_max = int(base_max * mult)
            
            # Randomize within scaled range
            val = random.randint(scaled_min, scaled_max)
            
            item.add_stat(stat, val)
                
        return item

class UpgradeStone(Item):
    def __init__(self):
        super().__init__("强化石", ItemType.MATERIAL, ItemQuality.NORMAL, stackable=True, max_stack=99999)

class MythicUpgradeStone(Item):
    def __init__(self):
        super().__init__("神话强化石", ItemType.MATERIAL, ItemQuality.MYTHIC, stackable=True, max_stack=99999)

class BonePowder(Item):
    def __init__(self):
        super().__init__("骨粉", ItemType.MATERIAL, ItemQuality.RARE, stackable=True, max_stack=99999)
