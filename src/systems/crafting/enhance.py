import random
from src.systems.equipment.item import Item, ItemType

class EnhancementSystem:
    @staticmethod
    def enhance_weapon(weapon: Item, material: Item):
        if weapon.item_type != ItemType.WEAPON:
            print("Can only enhance weapons.")
            return False
        
        print(f"Attempting to enhance {weapon.name}...")
        
        success_rate = 0.5 # 50% chance
        if random.random() < success_rate:
            weapon.add_stat("attack", weapon.stats.get("attack", 0) + 1)
            weapon.name += " (+1)"
            print("Enhancement Successful!")
            return True
        else:
            print("Enhancement Failed! Weapon shattered!")
            return False # Weapon destroyed
