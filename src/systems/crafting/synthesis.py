from src.systems.equipment.item import Item, ItemType, ItemQuality

class SynthesisSystem:
    @staticmethod
    def synthesize_gems(gems_list):
        if len(gems_list) < 3:
            print("Need 3 gems to synthesize.")
            return None
        
        # Simple logic: 3 Normal -> 1 High
        base_gem = gems_list[0]
        new_quality = ItemQuality.HIGH
        
        print(f"Synthesized 3 {base_gem.name} into 1 High Quality Gem!")
        return Item(f"High {base_gem.name}", ItemType.MATERIAL, new_quality)
