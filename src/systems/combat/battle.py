import random
from src.systems.character.player import Player
from src.systems.world.monster import Monster

class BattleSystem:
    @staticmethod
    def fight(player: Player, monster: Monster):
        print(f"Battle started: {player.name} vs {monster.name}")
        
        while player.hp > 0 and monster.is_alive():
            # Player turn
            damage = max(1, player.attack - monster.defense)
            monster.take_damage(damage)
            print(f"You hit {monster.name} for {damage} damage.")
            
            if not monster.is_alive():
                print(f"You defeated {monster.name}!")
                player.gain_xp(monster.xp_reward)
                return True

            # Monster turn
            m_damage = max(1, monster.attack - player.defense)
            player.hp -= m_damage
            print(f"{monster.name} hits you for {m_damage} damage. Your HP: {player.hp}/{player.max_hp}")
            
            if player.hp <= 0:
                print("You have been defeated...")
                return False
        return False
