class NPC:
    def __init__(self, name, title, description):
        self.name = name
        self.title = title
        self.description = description
        self.quests = [] # List of Quest IDs available from this NPC
        self.dialogs = {} # key: quest_stage_id, value: text
        self.has_quest_available = False
        self.has_quest_turn_in = False

    def __str__(self):
        return f"{self.name} <{self.title}>"

class NPCManager:
    def __init__(self):
        self.npcs = {}

    def add_npc(self, npc):
        self.npcs[npc.name] = npc

    def get_npc(self, name):
        return self.npcs.get(name)
