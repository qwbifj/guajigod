import random

class Monster:
    def __init__(self, name, level, hp, attack, defense, xp_reward, drops=None):
        self.name = name
        self.level = level
        self.max_hp = hp
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.xp_reward = xp_reward
        self.drops = drops or []
        self.x = 0
        self.y = 0
        
        # Movement AI
        self.move_timer = 0
        self.move_interval = random.randint(60, 180) # 1-3 seconds (assuming 60 FPS)
        self.is_aggro = False # Aggro state
        
        # Spawn Animation
        self.spawn_anim_progress = 0.0 # 0.0 to 1.0
        self.spawn_anim_speed = 0.05 # Speed of animation

    def update_spawn_animation(self):
        if self.spawn_anim_progress < 1.0:
            self.spawn_anim_progress += self.spawn_anim_speed
            if self.spawn_anim_progress >= 1.0:
                self.spawn_anim_progress = 1.0

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        damage = max(0, amount - self.defense)
        self.hp -= damage
        print(f"{self.name} took {damage} damage. HP: {self.hp}/{self.max_hp}")
        
        # Trigger Aggro
        if not self.is_aggro:
            self.is_aggro = True
            # Speed up movement (0.5s = 30 frames)
            self.move_interval = 30
            self.move_timer = 0 # Act immediately or reset
            
        return damage

    def __str__(self):
        return f"{self.name} (Lv.{self.level})"

    @staticmethod
    def create_from_db(monster_key):
        from src.data.monsters_db import MONSTERS_DB
        data = MONSTERS_DB.get(monster_key)
        if not data:
            return None
        
        m = Monster(
            name=data["name"],
            level=data["level"],
            hp=data["hp"],
            attack=data["attack"],
            defense=data["defense"],
            xp_reward=data["xp"],
            drops=data.get("drops", [])
        )
        return m
