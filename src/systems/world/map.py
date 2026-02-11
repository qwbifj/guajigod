from src.systems.world.monster import Monster
import random

class Map:
    def __init__(self, name, min_level, width=20, height=15):
        self.name = name
        self.min_level = min_level
        self.width = width
        self.height = height
        self.monster_templates = []
        
        # Treasure Events
        # Key: (x, y), Value: {'quality': ItemQuality, 'timestamp': float}
        self.treasure_events = {}
        self.active_monsters = []

    def add_monster_type(self, monster_template: Monster):
        self.monster_templates.append(monster_template)

    def spawn_monster(self):
        if not self.monster_templates:
            return None
        template = random.choice(self.monster_templates)
        # Return a new instance based on template
        new_monster = Monster(template.name, template.level, template.max_hp, template.attack, template.defense, template.xp_reward)
        
        # Find a valid spawn location
        new_monster.x = random.randint(0, self.width - 1)
        new_monster.y = random.randint(0, self.height - 1)
        
        self.active_monsters.append(new_monster)
        return new_monster

    def remove_dead_monsters(self):
        self.active_monsters = [m for m in self.active_monsters if m.is_alive()]

    def is_valid_move(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def __str__(self):
        return f"Map: {self.name} (Recommended Level: {self.min_level})"
