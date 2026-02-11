from enum import Enum
from src.systems.character.experience import ExperienceSystem
from src.systems.equipment.inventory import Inventory
from src.systems.character.cultivation import BodyCultivation
from src.systems.combat.skills import SkillBook

class Profession(Enum):
    WARRIOR = "战士"
    MAGE = "法师"
    TAOIST = "道士"

class Player:
    def __init__(self, name, profession: Profession, gender="男"):
        self.name = name
        self.profession = profession
        self.gender = gender
        self.level = 1
        self.current_xp = 0
        self.hp = 100
        self.max_hp = 100
        self.mp = 50
        self.max_mp = 50
        self.attack = 10
        self.magic = 0
        self.taoism = 0
        self.defense = 5
        self.magic_defense = 0
        self.accuracy = 5
        self.dodge = 5
        self.crit = 5
        self.luck = 0
        self.attack_speed = 0 # Extra attack speed
        self.cooldown_reduction = 0.0 # Percentage (0-100)
        self.inventory = Inventory() # List of Item objects
        self.gold = 0
        self.ingots = 0 # Yuanbao
        self.equipment = {
            "weapon": None,
            "armor": None,
            "helmet": None,
            "necklace": None,
            "bracelet_l": None,
            "bracelet_r": None,
            "ring_l": None,
            "ring_r": None,
            "belt": None,
            "boots": None,
            "medal": None
        }
        self.xp_system = ExperienceSystem()
        self.body_cultivation = BodyCultivation()
        self.skill_book = SkillBook()
        self.skills = [self.skill_book.get_skill("Hellfire")]
        self.active_skill = self.skills[0]
        self.x = 0
        self.y = 0
        self.map_id = "NoviceVillage" # Default Map ID
        
        # Equipment Slot Enhancement (Body Forging)
        # Levels for each slot: 0-15
        self.equipment_slot_levels = {
            "weapon": 0,
            "armor": 0,
            "helmet": 0,
            "necklace": 0,
            "bracelet_l": 0,
            "bracelet_r": 0,
            "ring_l": 0,
            "ring_r": 0,
            "belt": 0,
            "boots": 0,
            "medal": 0
        }
        
        # Auto Potion Settings
        self.auto_potion_settings = {
            "enabled": False,
            "hp_threshold": 70, # Percent
            "mp_threshold": 30, # Percent
            "hp_potion": "金创药(中)", # Default preference
            "mp_potion": "魔法药(中)"
        }
        self.last_potion_time = 0.0 # Timestamp
        
        self.stats_version = 4 # Current Stats Version
        
        self.initialize_stats()

    def initialize_stats(self):
        # Base stats
        self.base_magic = 0
        self.base_taoism = 0
        self.base_magic_defense = 0
        
        if self.profession == Profession.WARRIOR:
            self.base_max_hp = 150
            self.base_attack = 15
            self.base_defense = 10
            self.base_magic_defense = 5
        elif self.profession == Profession.MAGE:
            self.base_max_hp = 80
            self.base_max_mp = 150
            self.base_attack = 5
            self.base_magic = 15
            self.base_magic_defense = 8
        elif self.profession == Profession.TAOIST:
            self.base_max_hp = 110
            self.base_max_mp = 100
            self.base_attack = 10
            self.base_taoism = 12
            self.base_defense = 5
            self.base_magic_defense = 5
        
        # Apply base stats
        self.max_hp = self.base_max_hp + (self.level - 1) * 20
        self.max_mp = getattr(self, 'base_max_mp', 50) + (self.level - 1) * 10
        self.attack = self.base_attack
        self.magic = self.base_magic
        self.taoism = self.base_taoism
        self.defense = getattr(self, 'base_defense', 5)
        self.magic_defense = self.base_magic_defense
        
        self.hp = self.max_hp
        self.mp = self.max_mp
        
        # Weight Limits
        # Reference Mir 2 formulas (simplified based on Level)
        self.max_bag_weight = 50 + self.level * 5
        self.max_wear_weight = 15 + self.level # For Armor/Helmet
        self.max_hand_weight = 20 + self.level # For Weapon
        
        if hasattr(self, 'inventory'):
            self.inventory.max_weight = self.max_bag_weight

    def __setstate__(self, state):
        """Handle unpickling of legacy save data"""
        self.__dict__.update(state)
        
        # Migration: Add auto_potion_settings if missing
        if not hasattr(self, 'auto_potion_settings'):
            self.auto_potion_settings = {
                "enabled": False,
                "hp_threshold": 70,
                "mp_threshold": 30,
                "hp_potion": "金创药(中)",
                "mp_potion": "魔法药(中)"
            }
            
        if not hasattr(self, 'last_potion_time'):
            self.last_potion_time = 0.0
            
        # Migration: Add equipment_slot_levels if missing
        if not hasattr(self, 'equipment_slot_levels'):
             self.equipment_slot_levels = {
                "weapon": 0, "armor": 0, "helmet": 0, "necklace": 0,
                "bracelet_l": 0, "bracelet_r": 0, "ring_l": 0, "ring_r": 0,
                "belt": 0, "boots": 0, "medal": 0
            }

    def recalculate_stats(self):
        # Reset to base stats (level dependent)
        self.max_hp = self.base_max_hp + (self.level - 1) * 20
        self.max_mp = getattr(self, 'base_max_mp', 50) + (self.level - 1) * 10
        
        # Recalculate Weight Limits
        self.max_bag_weight = 50 + self.level * 5
        self.max_wear_weight = 15 + self.level
        self.max_hand_weight = 20 + self.level

        # Update Inventory Weight Limit
        if self.inventory:
            self.inventory.max_weight = self.max_bag_weight

        self.attack = self.base_attack
        self.magic = getattr(self, 'base_magic', 0)
        self.taoism = getattr(self, 'base_taoism', 0)
        self.defense = getattr(self, 'base_defense', 5)
        self.magic_defense = getattr(self, 'base_magic_defense', 0)
        self.accuracy = 5
        self.dodge = 5
        self.crit = 5
        self.luck = 0
        self.attack_speed = 0
        self.cooldown_reduction = 0.0

        # Add equipment stats
        for slot, item in self.equipment.items():
            if item:
                # 1. Item Enhancement: Flat +1 point per level
                item_enh_level = getattr(item, 'enhancement_level', 0)
                item_flat_bonus = item_enh_level
                
                # 2. Slot Enhancement: Base * (slot_level%)
                slot_enh_level = self.equipment_slot_levels.get(slot, 0)
                
                for k, v in item.stats.items():
                    base_val = v
                    
                    # Calculate Slot Bonus
                    slot_bonus_val = int(base_val * slot_enh_level * 0.01)
                    if slot_enh_level > 0 and slot_bonus_val < 1:
                        slot_bonus_val = 1
                        
                    effective_val = base_val + item_flat_bonus + slot_bonus_val
                    
                    if k == "hp": self.max_hp += effective_val
                    elif k == "mp": self.max_mp += effective_val
                    elif k == "attack": self.attack += effective_val
                    elif k == "magic": self.magic += effective_val
                    elif k == "taoism": self.taoism += effective_val
                    elif k == "defense": self.defense += effective_val
                    elif k == "magic_defense": self.magic_defense += effective_val
                    elif k == "accuracy": self.accuracy += effective_val
                    elif k == "dodge": self.dodge += effective_val
                    elif k == "crit": self.crit += effective_val
                    elif k == "luck": self.luck += effective_val
                    elif k == "attack_speed": self.attack_speed += effective_val
                    elif k == "cooldown_reduction": self.cooldown_reduction += effective_val
        
        # Full Body Enhancement Bonus
        # If all worn equipment (slots) reach level n, add n% to all stats.
        # "Depends on the lowest enhancement level of all worn equipment"
        # We assume this means all 11 main slots must be equipped to have a "Full Body" level > 0.
        check_slots = ["weapon", "armor", "helmet", "necklace", "bracelet_l", "bracelet_r", "ring_l", "ring_r", "belt", "boots", "medal"]
        min_enh_level = 15
        equipped_count = 0
        
        for s in check_slots:
            if self.equipment.get(s):
                equipped_count += 1
                lvl = getattr(self.equipment[s], 'enhancement_level', 0)
                if lvl < min_enh_level:
                    min_enh_level = lvl
            else:
                min_enh_level = 0
        
        if equipped_count < len(check_slots):
            min_enh_level = 0
            
        if min_enh_level > 0:
            multiplier = 1.0 + (min_enh_level * 0.01)
            # Apply to main attributes
            self.max_hp = int(self.max_hp * multiplier)
            self.max_mp = int(self.max_mp * multiplier)
            self.attack = int(self.attack * multiplier)
            self.magic = int(self.magic * multiplier)
            self.taoism = int(self.taoism * multiplier)
            self.defense = int(self.defense * multiplier)
            self.magic_defense = int(self.magic_defense * multiplier)
        
        # Add cultivation stats
        if self.body_cultivation:
            self.attack += self.body_cultivation.stats.get("attack", 0)
            self.defense += self.body_cultivation.stats.get("defense", 0)
            # Percentages need to be applied to base + equipment usually, or just base? 
            # Assuming total for simplicity
            if self.body_cultivation.stats.get("hp_pct", 0) > 0:
                self.max_hp = int(self.max_hp * (1 + self.body_cultivation.stats["hp_pct"] / 100.0))
            if self.body_cultivation.stats.get("mp_pct", 0) > 0:
                self.max_mp = int(self.max_mp * (1 + self.body_cultivation.stats["mp_pct"] / 100.0))
        
        # Add Forging Bonus (Equipment Slot Levels) - Flat 1% per level to total stats? Or Base?
        # User said: "base stats by 1% per enhancement level" for Enhance.
        # User said: "Forging... increase base attributes +1%"
        # The logic above (recalculate_stats loop) already handles item_enh_level + slot_enh_level
        # total_enh_level = item_enh_level + slot_enh_level
        # bonus_rate = total_enh_level * 0.01
        # So it IS applied.
        
        # WAIT, if item is None, slot level is ignored in loop above!
        # Forging is on SLOT, so even if no item, maybe no stats?
        # Usually forging enhances the ITEM in the slot. If no item, 0 stats from slot.
        # That makes sense.
        
        # Check if the user meant "Forging adds 1% global stats"?
        # "锻体...增加装备基础属性的百分之1" -> "Increase equipment base stats by 1%"
        # So it requires equipment.
        
        # Cap current HP/MP to new max
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        if self.mp > self.max_mp:
            self.mp = self.max_mp

    def use_item(self, item, inventory_index=None):
        """
        Use a consumable or learn a skill book.
        :param item: Item object
        :param inventory_index: Index in inventory (optional, for removal)
        :return: (Success, Message)
        """
        from src.systems.equipment.item import ItemType
        import time

        if not item:
            return (False, "物品无效")

        # 1. Consumables (Potions)
        if item.item_type == ItemType.CONSUMABLE:
            used = False
            msg = ""
            
            # HP Recovery
            if "hp" in item.stats:
                heal = item.stats["hp"]
                if self.hp < self.max_hp:
                    self.hp = min(self.max_hp, self.hp + heal)
                    used = True
                    msg += f"生命恢复 {heal}. "
                else:
                    msg += "生命值已满. "
            
            # MP Recovery
            if "mp" in item.stats:
                recover = item.stats["mp"]
                if self.mp < self.max_mp:
                    self.mp = min(self.max_mp, self.mp + recover)
                    used = True
                    msg += f"魔法恢复 {recover}. "
                else:
                    msg += "魔法值已满. "

            # If it's a "special" potion that grants buffs, handle here (not implemented yet)
            
            if used:
                # Remove 1 count
                if inventory_index is not None:
                    # Logic handled by caller or specific remove logic
                    # If passed object is from inventory list, decrement count
                    if item.stackable and item.count > 1:
                        item.count -= 1
                    else:
                        self.inventory.items[inventory_index] = None
                else:
                    # Find and remove if index not provided
                    self.inventory.remove_item(item, count=1)
                return (True, msg.strip())
            else:
                return (False, "无需使用: " + msg.strip())

        # 2. Skill Books
        elif item.item_type == ItemType.SKILL_BOOK:
            skill_name = item.name # Assuming Item Name matches Skill Name in SkillBook
            skill = self.skill_book.get_skill(skill_name)
            
            if not skill:
                return (False, f"未知的技能书: {skill_name}")
            
            # Check Profession
            # Map Player Profession to Skill Profession String
            prof_map = {
                Profession.WARRIOR: "WARRIOR",
                Profession.MAGE: "MAGE",
                Profession.TAOIST: "TAOIST"
            }
            if skill.profession != prof_map.get(self.profession):
                return (False, f"职业不符 (需要: {skill.profession})")
            
            # Check Level
            if self.level < skill.level_req:
                return (False, f"等级不足 (需要: {skill.level_req})")
            
            # Check if already learned
            for s in self.skills:
                if s.name == skill.name:
                    return (False, "已学会该技能")
            
            # Learn
            self.skills.append(skill)
            
            # Remove Item
            if inventory_index is not None:
                self.inventory.items[inventory_index] = None
            else:
                self.inventory.remove_item(item)
                
            return (True, f"学会了技能: {skill_name}")

        return (False, "该物品无法直接使用")

    def check_auto_potion(self):
        """
        Check HP/MP and auto use potions if enabled.
        Should be called in game loop update.
        """
        # Lazy initialization for runtime safety
        if not hasattr(self, 'auto_potion_settings'):
            self.auto_potion_settings = {
                "enabled": False,
                "hp_threshold": 70,
                "mp_threshold": 30,
                "hp_potion": "金创药(中)",
                "mp_potion": "魔法药(中)"
            }
        if not hasattr(self, 'last_potion_time'):
            self.last_potion_time = 0.0

        if not self.auto_potion_settings.get("enabled", False):
            return

        import time
        current_time = time.time()
        if current_time - self.last_potion_time < 1.0: # 1 second global potion cooldown
            return

        used_any = False

        # Helper to find potion
        from src.systems.equipment.item import ItemType
        def find_potion_index(preferred_name, stat_type):
            # 1. Exact match
            idx = self.inventory.find_item_index(preferred_name)
            if idx != -1: return idx
            
            # 2. Fuzzy match (Any consumable with stat)
            # Prioritize lower value potions to save big ones? Or just first found?
            # Inventory sort puts consumables at end usually.
            # Let's find *any* suitable potion.
            for i, item in enumerate(self.inventory.items):
                if item and item.item_type == ItemType.CONSUMABLE:
                    if stat_type in item.stats and item.stats[stat_type] > 0:
                        return i
            return -1

        # Check HP
        hp_pct = (self.hp / self.max_hp) * 100
        threshold_hp = self.auto_potion_settings.get("hp_threshold", 70)
        
        if hp_pct < threshold_hp:
            potion_name = self.auto_potion_settings.get("hp_potion", "")
            # Find in inventory with fallback
            idx = find_potion_index(potion_name, "hp")
            
            if idx != -1:
                item = self.inventory.items[idx]
                success, msg = self.use_item(item, idx)
                if success:
                    # print(f"[Auto Potion] Used {item.name}: {msg}")
                    used_any = True

        # Check MP (if not already used potion, or separate cooldown? Let's share cooldown for now to simulate animation delay)
        if not used_any:
            mp_pct = (self.mp / self.max_mp) * 100
            threshold_mp = self.auto_potion_settings.get("mp_threshold", 30)
            
            if mp_pct < threshold_mp:
                potion_name = self.auto_potion_settings.get("mp_potion", "")
                idx = find_potion_index(potion_name, "mp")
                
                if idx != -1:
                    item = self.inventory.items[idx]
                    success, msg = self.use_item(item, idx)
                    if success:
                        # print(f"[Auto Potion] Used {item.name}: {msg}")
                        used_any = True
        
        if used_any:
            self.last_potion_time = current_time

    def recycle_items(self, recycle_qualities):
        """
        Recycle items in inventory based on quality settings.
        :param recycle_qualities: Dict {quality_name: bool}
        :return: Dict with results {count, gold, ingots, stone, mythic_stone}
        """
        from src.systems.equipment.item import UpgradeStone, MythicUpgradeStone
        
        to_remove = []
        rewards = {"gold": 0, "ingots": 0, "stone": 0, "mythic_stone": 0, "count": 0}
        
        for i, item in enumerate(self.inventory.items):
            if not item: continue
            
            # Check is_equipment flag
            if not getattr(item, 'is_equipment', False):
                continue
            
            # Skip locked items
            if getattr(item, 'locked', False):
                continue

            q = item.quality.value
            if q in recycle_qualities and recycle_qualities[q]:
                to_remove.append(i)
                rewards["count"] += 1
                
                if q in ["普通", "优良", "精品"]:
                    rewards["gold"] += 100 
                    if q == "优良": rewards["gold"] += 100
                    elif q == "精品": rewards["gold"] += 200
                    rewards["stone"] += 1
                    
                elif q == "极品":
                    rewards["ingots"] += 1
                    rewards["stone"] += 2
                    
                elif q == "传说":
                    rewards["ingots"] += 2
                    rewards["stone"] += 3
                    
                elif q == "史诗":
                    rewards["ingots"] += 3
                    rewards["stone"] += 4
                    
                elif q == "神话":
                    rewards["ingots"] += 4
                    rewards["mythic_stone"] += 1
                    rewards["stone"] += 5
                    
        # Remove items
        for idx in to_remove:
            self.inventory.items[idx] = None
            
        # Add rewards
        if rewards["gold"] > 0: self.gold += rewards["gold"]
        if rewards["ingots"] > 0: self.ingots += rewards["ingots"]
        
        for _ in range(rewards["stone"]):
            self.inventory.add_item(UpgradeStone())
        for _ in range(rewards["mythic_stone"]):
            self.inventory.add_item(MythicUpgradeStone())
            
        return rewards

    def equip_item(self, item, target_slot=None):
        # Determine slot based on item type
        from src.systems.equipment.item import ItemType
        
        # Check Level Requirement
        if self.level < getattr(item, 'min_level', 1):
             return (False, f"佩戴等级不够 (需要: {item.min_level})")

        # Check Weight Requirement
        # Body Weight limits Armor/Helmet/etc.
        # Hand Weight limits Weapon.
        weight_limit = self.max_wear_weight
        limit_name = "穿戴重量"
        
        # Robust check for item type (handles Enum value changes by checking name)
        def check_type(itype, target_enum):
            return itype == target_enum or (hasattr(itype, 'name') and itype.name == target_enum.name)

        if check_type(item.item_type, ItemType.WEAPON):
             weight_limit = self.max_hand_weight
             limit_name = "腕力"
        
        if getattr(item, 'weight', 0) > weight_limit:
             return (False, f"佩戴失败: {limit_name}不足 (需要: {item.weight}, 当前: {weight_limit})")

        slot = None

        # Mapping type to slots
        if check_type(item.item_type, ItemType.WEAPON): slot = "weapon"
        elif check_type(item.item_type, ItemType.ARMOR): slot = "armor"
        elif check_type(item.item_type, ItemType.HELMET): slot = "helmet"
        elif check_type(item.item_type, ItemType.NECKLACE): slot = "necklace"
        elif check_type(item.item_type, ItemType.BELT): slot = "belt"
        elif check_type(item.item_type, ItemType.BOOTS): slot = "boots"
        elif check_type(item.item_type, ItemType.MEDAL): slot = "medal"
        elif check_type(item.item_type, ItemType.BRACELET):
            if target_slot:
                slot = target_slot
            else:
                if not self.equipment["bracelet_l"]: slot = "bracelet_l"
                elif not self.equipment["bracelet_r"]: slot = "bracelet_r"
                else: slot = "bracelet_l" # Default swap left
        elif check_type(item.item_type, ItemType.RING):
            if target_slot:
                slot = target_slot
            else:
                if not self.equipment["ring_l"]: slot = "ring_l"
                elif not self.equipment["ring_r"]: slot = "ring_r"
                else: slot = "ring_l" # Default swap left
        
        if slot:
            # Safer swap logic
            # 1. Remove new item from inventory to free up space
            if not self.inventory.remove_item(item):
                return (False, "无法从背包移除物品")
            
            # 2. Unequip existing if any
            if self.equipment[slot]:
                # Add old item to inventory
                if not self.inventory.add_item(self.equipment[slot]):
                    # Failed to add old item (should rarely happen if we just removed one, unless item size differs or something)
                    # Rollback
                    self.inventory.add_item(item)
                    return (False, "背包已满，无法替换装备")
            
            # 3. Equip new
            self.equipment[slot] = item
            self.recalculate_stats()
            return (True, "success")
        return (False, "无法佩戴此物品")

    def unequip_item(self, slot):
        if self.equipment[slot]:
            item = self.equipment[slot]
            if self.inventory.add_item(item):
                self.equipment[slot] = None
                self.recalculate_stats()
                return True
        return False

    def gain_xp(self, amount):
        print(f"{self.name} gained {amount} XP.")
        self.current_xp += amount
        leveled_up, remaining_xp = self.xp_system.check_level_up(self.current_xp, self.level)
        if leveled_up:
            self.level_up(remaining_xp)

    def level_up(self, remaining_xp):
        self.level += 1
        self.current_xp = remaining_xp
        print(f"Congratulations! {self.name} reached level {self.level}!")
        # Increase stats
        self.max_hp += 20
        self.max_mp += 10
        self.hp = self.max_hp
        self.mp = self.max_mp
        # Check for multi-level up
        leveled_up, remaining_xp = self.xp_system.check_level_up(self.current_xp, self.level)
        if leveled_up:
            self.level_up(remaining_xp)

    def __str__(self):
        return f"[{self.profession.value}] {self.name} Lv.{self.level} (HP: {self.hp}/{self.max_hp})"

    def to_dict(self):
        # Serialize equipment
        equip_data = {}
        for slot, item in self.equipment.items():
            if item:
                equip_data[slot] = item.to_dict()
            else:
                equip_data[slot] = None

        # Serialize skills (just names)
        skill_names = [s.name for s in self.skills]

        return {
            "name": self.name,
            "profession": self.profession.name,
            "gender": self.gender,
            "level": self.level,
            "current_xp": self.current_xp,
            "hp": self.hp,
            "mp": self.mp,
            "gold": self.gold,
            "ingots": self.ingots,
            "inventory": self.inventory.to_dict(),
            "equipment": equip_data,
            "body_cultivation": self.body_cultivation.to_dict(),
            "skills": skill_names,
            "x": self.x,
            "y": self.y,
            "map_id": self.map_id,
            "equipment_slot_levels": self.equipment_slot_levels,
            "auto_potion_settings": self.auto_potion_settings,
            "stats_version": getattr(self, 'stats_version', 1)
            # Base stats might be needed if modified permanently, 
            # but usually they are recalculated from level + equip + cultivation.
            # We trust recalculate_stats to restore them.
        }

    @classmethod
    def from_dict(cls, data):
        # Resolve Profession
        try:
            prof = Profession[data["profession"]]
        except KeyError:
            prof = Profession.WARRIOR
            
        player = cls(data["name"], prof, data.get("gender", "男"))
        player.level = data.get("level", 1)
        player.current_xp = data.get("current_xp", 0)
        player.gold = data.get("gold", 0)
        player.ingots = data.get("ingots", 0)
        player.x = data.get("x", 0)
        player.y = data.get("y", 0)
        player.map_id = data.get("map_id", "NoviceVillage")
        player.equipment_slot_levels = data.get("equipment_slot_levels", player.equipment_slot_levels)
        player.stats_version = data.get("stats_version", 1)
        
        # Restore Auto Potion Settings
        # Use update to merge with default to ensure all keys exist
        saved_ap_settings = data.get("auto_potion_settings", {})
        player.auto_potion_settings.update(saved_ap_settings)
        
        # Restore Inventory
        if "inventory" in data:
            player.inventory = Inventory.from_dict(data["inventory"])
            
        # Restore Equipment
        # We need Item class here. It is not imported at top level.
        from src.systems.equipment.item import Item
        
        equip_data = data.get("equipment", {})
        for slot, item_data in equip_data.items():
            if item_data:
                player.equipment[slot] = Item.from_dict(item_data)
        
        # Restore Cultivation
        if "body_cultivation" in data:
            player.body_cultivation = BodyCultivation.from_dict(data["body_cultivation"])
            
        # Restore Skills
        skill_names = data.get("skills", ["Basic Sword"]) # Default if missing
        player.skills = []
        for name in skill_names:
            skill = player.skill_book.get_skill(name)
            if skill:
                player.skills.append(skill)
        
        # Ensure active skill is valid
        if player.skills:
            player.active_skill = player.skills[0]
            
        # Recalculate derived stats
        player.initialize_stats() # Set base based on level
        player.recalculate_stats() # Add equip/cultivation bonuses
        
        # Restore HP/MP (clamped by max)
        player.hp = min(data.get("hp", player.max_hp), player.max_hp)
        player.mp = min(data.get("mp", player.max_mp), player.max_mp)
        
        return player
